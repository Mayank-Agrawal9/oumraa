from django.db import transaction
from django.utils.text import slugify
from django.views.generic import ListView
from rest_framework import status, permissions, generics
from rest_framework.decorators import permission_classes, api_view, action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from product.serializer import *
from utils.base_viewset import BaseViewSetSetup


# Create your views here.


def upload_product_image(request, product_id):
    """Upload and process product image"""
    try:
        # Verify product exists and user has permission
        product = Product.objects.get(id=product_id)

        # Check if user owns this product (if multi-vendor)
        # if hasattr(product, 'vendor') and product.vendor != request.user:
        #     return Response({'error': 'Permission denied'}, status=403)

    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    # Validate image file
    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

    # Check file size (10MB limit)
    if image_file.size > 10 * 1024 * 1024:
        return Response({'error': 'Image too large. Maximum 10MB allowed.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Check file type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if image_file.content_type not in allowed_types:
        return Response({'error': 'Invalid image format. Use JPEG, PNG or WebP.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Process and upload image
    do_manager = DigitalOceanSpacesManager()
    result = do_manager.process_and_upload_image(image_file)

    if not result['success']:
        return Response({'error': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Create database record
    try:
        product_image = ProductImage.objects.create(
            product=product,
            file_id=result['file_id'],
            original_filename=result['original_filename'],
            original_width=result['original_size'][0],
            original_height=result['original_size'][1],

            # URLs from CDN
            thumbnail_url=result['results']['thumbnail_url'],
            medium_url=result['results']['medium_url'],
            large_url=result['results']['large_url'],
            original_url=result['results']['original_url'],

            # Storage keys
            thumbnail_key=result['results']['thumbnail_key'],
            medium_key=result['results']['medium_key'],
            large_key=result['results']['large_key'],
            original_key=result['results']['original_key'],

            # Form data
            alt_text=request.data.get('alt_text', ''),
            is_primary=request.data.get('is_primary', False),
            sort_order=request.data.get('sort_order',
                                        product.images.count())  # Auto-increment sort order
        )

        # Handle primary image logic
        if product_image.is_primary:
            product_image.make_primary()
        elif not product.images.filter(is_primary=True).exists():
            # Make this primary if no primary image exists
            product_image.make_primary()

        # Return success response
        return Response({
            'id': str(product_image.id),
            'file_id': product_image.file_id,
            'urls': {
                'thumbnail': product_image.thumbnail_url,
                'medium': product_image.medium_url,
                'large': product_image.large_url,
                'original': product_image.original_url,
            },
            'metadata': {
                'original_filename': product_image.original_filename,
                'width': product_image.original_width,
                'height': product_image.original_height,
                'is_primary': product_image.is_primary,
                'alt_text': product_image.alt_text,
            },
            'responsive_srcset': product_image.responsive_srcset,
            'created_at': product_image.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        # If database creation fails, clean up uploaded files
        keys_to_delete = [
            result['results']['thumbnail_key'],
            result['results']['medium_key'],
            result['results']['large_key'],
            result['results']['original_key']
        ]
        do_manager.delete_image_variants(keys_to_delete)

        return Response({
            'error': f'Failed to save image metadata: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product_image(request, image_id):
    """Delete a product image"""
    try:
        image = ProductImage.objects.get(id=image_id)

        # Check permissions (if needed)
        # if hasattr(image.product, 'vendor') and image.product.vendor != request.user:
        #     return Response({'error': 'Permission denied'}, status=403)

        # If deleting primary image, make another image primary
        if image.is_primary:
            next_image = ProductImage.objects.filter(
                product=image.product
            ).exclude(id=image.id).first()

            if next_image:
                next_image.make_primary()

        # Delete (this will also clean up DO Spaces files)
        image.delete()

        return Response({
            'message': 'Image deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

    except ProductImage.DoesNotExist:
        return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_product_images(request, product_id):
    """Get all images for a product"""
    try:
        product = Product.objects.get(id=product_id)
        images = product.images.all().order_by('sort_order', 'created_at')

        images_data = []
        for img in images:
            images_data.append({
                'id': str(img.id),
                'urls': {
                    'thumbnail': img.thumbnail_url,
                    'medium': img.medium_url,
                    'large': img.large_url,
                    'original': img.original_url,
                },
                'metadata': {
                    'alt_text': img.alt_text,
                    'is_primary': img.is_primary,
                    'sort_order': img.sort_order,
                    'original_filename': img.original_filename,
                    'width': img.original_width,
                    'height': img.original_height,
                },
                'responsive_srcset': img.responsive_srcset,
                'created_at': img.created_at.isoformat()
            })

        return Response({
            'product_id': str(product.id),
            'images_count': len(images_data),
            'images': images_data
        })

    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reorder_product_images(request, product_id):
    """Reorder product images"""
    try:
        product = Product.objects.get(id=product_id)
        image_orders = request.data.get('images', [])

        if not image_orders:
            return Response({'error': 'No image order provided'}, status=400)

        ProductImage.reorder_images(product, image_orders)

        return Response({'message': 'Images reordered successfully'})

    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_primary_image(request, image_id):
    """Set an image as primary"""
    try:
        image = ProductImage.objects.get(id=image_id)
        image.make_primary()

        return Response({
            'message': 'Primary image updated',
            'image_id': str(image.id)
        })

    except ProductImage.DoesNotExist:
        return Response({'error': 'Image not found'}, status=404)


class AdminProductCreateAPIView(APIView):
    """Admin API for creating products with multiple images"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        """Create a new product with images"""
        try:
            with transaction.atomic():
                # Separate image files from other data
                images = request.FILES.getlist('images', [])
                image_metadata = self._parse_image_metadata(request.data)

                # Remove image-related data from product data
                product_data = request.data.copy()
                self._clean_image_data_from_product_data(product_data)

                # Validate product data
                serializer = ProductCreateSerializer(data=product_data)
                if not serializer.is_valid():
                    return Response({
                        'error': 'Validation failed',
                        'details': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create product
                product = self._create_product(serializer.validated_data)

                # Create variants if provided
                if serializer.validated_data.get('variants'):
                    self._create_product_variants(product, serializer.validated_data['variants'])

                # Upload and create images
                image_results = []
                if images:
                    image_results = self._process_product_images(product, images, image_metadata)

                # Apply taxes
                if serializer.validated_data.get('tax_rate_ids'):
                    self._apply_product_taxes(product, serializer.validated_data['tax_rate_ids'])

                # Return success response
                response_serializer = ProductResponseSerializer(product)
                return Response({
                    'message': 'Product created successfully',
                    'product': response_serializer.data,
                    'images_uploaded': len(image_results),
                    'image_upload_results': image_results
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': 'Product creation failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _parse_image_metadata(self, data):
        """Parse image metadata from form data"""
        metadata = []

        # Handle JSON string format
        if 'image_metadata' in data:
            try:
                metadata = json.loads(data['image_metadata'])
            except (json.JSONDecodeError, TypeError):
                metadata = []
        else:
            # Handle individual form fields
            alt_texts = data.getlist('image_alt_text', [])
            is_primary_list = data.getlist('image_is_primary', [])
            sort_orders = data.getlist('image_sort_order', [])

            for i in range(len(alt_texts)):
                metadata.append({
                    'alt_text': alt_texts[i] if i < len(alt_texts) else '',
                    'is_primary': str(is_primary_list[i]).lower() == 'true' if i < len(is_primary_list) else False,
                    'sort_order': int(sort_orders[i]) if i < len(sort_orders) and sort_orders[i].isdigit() else i
                })

        return metadata

    def _clean_image_data_from_product_data(self, product_data):
        """Remove image-related fields from product data"""
        image_fields = [
            'images', 'image_metadata', 'image_alt_text',
            'image_is_primary', 'image_sort_order'
        ]
        for field in image_fields:
            if field in product_data:
                del product_data[field]

    def _create_product(self, validated_data):
        """Create product instance"""
        # Generate slug if not provided
        if not validated_data.get('slug'):
            validated_data['slug'] = self._generate_unique_slug(validated_data['name'])

        # Get category and brand
        category = Category.objects.get(id=validated_data['category_id'])
        brand = None
        if validated_data.get('brand_id'):
            brand = Brand.objects.get(id=validated_data['brand_id'])

        # Create product
        product = Product.objects.create(
            name=validated_data['name'],
            slug=validated_data['slug'],
            description=validated_data['description'],
            short_description=validated_data.get('short_description', ''),
            category=category,
            brand=brand,
            sku=validated_data['sku'],
            price=validated_data['price'],
            compare_price=validated_data.get('compare_price'),
            cost_price=validated_data.get('cost_price'),
            stock_quantity=validated_data.get('stock_quantity', 0),
            low_stock_threshold=validated_data.get('low_stock_threshold', 10),
            track_inventory=validated_data.get('track_inventory', True),
            allow_backorder=validated_data.get('allow_backorder', False),
            weight=validated_data.get('weight'),
            length=validated_data.get('length'),
            width=validated_data.get('width'),
            height=validated_data.get('height'),
            meta_title=validated_data.get('meta_title', ''),
            meta_description=validated_data.get('meta_description', ''),
            status=validated_data.get('status', 'draft'),
            is_featured=validated_data.get('is_featured', False),
            is_digital=validated_data.get('is_digital', False),
        )

        return product

    def _generate_unique_slug(self, name):
        """Generate unique slug for product"""
        base_slug = slugify(name)
        slug = base_slug
        counter = 1

        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def _create_product_variants(self, product, variants_data):
        """Create product variants"""
        for variant_data in variants_data:
            # Create variant
            variant = ProductVariant.objects.create(
                product=product,
                sku=variant_data['sku'],
                price=variant_data.get('price'),
                stock_quantity=variant_data.get('stock_quantity', 0),
                is_active=variant_data.get('is_active', True)
            )

            # Create variant attributes
            if 'attributes' in variant_data and variant_data['attributes']:
                for attr_id, value_id in variant_data['attributes'].items():
                    try:
                        attribute = ProductAttribute.objects.get(id=attr_id)
                        attribute_value = ProductAttributeValue.objects.get(id=value_id, attribute=attribute)

                        ProductVariantAttribute.objects.create(
                            variant=variant,
                            attribute=attribute,
                            value=attribute_value
                        )
                    except (ProductAttribute.DoesNotExist, ProductAttributeValue.DoesNotExist):
                        continue

    def _process_product_images(self, product, images, metadata):
        """Process and upload product images"""
        do_manager = DigitalOceanSpacesManager()
        upload_results = []
        primary_set = False

        for i, image_file in enumerate(images):
            # Get metadata for this image
            img_metadata = metadata[i] if i < len(metadata) else {}

            # Validate image
            if not self._validate_image_file(image_file):
                upload_results.append({
                    'index': i,
                    'filename': image_file.name,
                    'success': False,
                    'error': 'Invalid image file'
                })
                continue

            # Upload image
            upload_result = do_manager.process_and_upload_image(image_file)

            if upload_result['success']:
                # Determine if this should be primary
                is_primary = img_metadata.get('is_primary', False)
                if not primary_set and (is_primary or i == 0):
                    is_primary = True
                    primary_set = True
                elif primary_set and is_primary:
                    is_primary = False  # Only one primary image allowed

                # Create database record
                try:
                    product_image = ProductImage.objects.create(
                        product=product,
                        file_id=upload_result['file_id'],
                        original_filename=upload_result['original_filename'],
                        original_width=upload_result['original_size'][0],
                        original_height=upload_result['original_size'][1],
                        thumbnail_url=upload_result['results']['thumbnail_url'],
                        medium_url=upload_result['results']['medium_url'],
                        large_url=upload_result['results']['large_url'],
                        original_url=upload_result['results']['original_url'],
                        thumbnail_key=upload_result['results']['thumbnail_key'],
                        medium_key=upload_result['results']['medium_key'],
                        large_key=upload_result['results']['large_key'],
                        original_key=upload_result['results']['original_key'],
                        alt_text=img_metadata.get('alt_text', ''),
                        is_primary=is_primary,
                        sort_order=img_metadata.get('sort_order', i)
                    )

                    upload_results.append({
                        'index': i,
                        'filename': image_file.name,
                        'success': True,
                        'image_id': str(product_image.id),
                        'is_primary': is_primary,
                        'urls': {
                            'thumbnail': product_image.thumbnail_url,
                            'medium': product_image.medium_url,
                            'large': product_image.large_url,
                            'original': product_image.original_url
                        }
                    })

                except Exception as e:
                    # Clean up uploaded files if database save fails
                    keys_to_delete = [
                        upload_result['results']['thumbnail_key'],
                        upload_result['results']['medium_key'],
                        upload_result['results']['large_key'],
                        upload_result['results']['original_key']
                    ]
                    do_manager.delete_image_variants(keys_to_delete)

                    upload_results.append({
                        'index': i,
                        'filename': image_file.name,
                        'success': False,
                        'error': f'Database save failed: {str(e)}'
                    })
            else:
                upload_results.append({
                    'index': i,
                    'filename': image_file.name,
                    'success': False,
                    'error': upload_result['error']
                })

        return upload_results

    def _validate_image_file(self, image_file):
        """Validate uploaded image file"""
        # Check file size (10MB limit)
        if image_file.size > 10 * 1024 * 1024:
            return False

        # Check content type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return False

        return True

    def _apply_product_taxes(self, product, tax_rate_ids):
        """Apply tax rates to product"""
        for tax_rate_id in tax_rate_ids:
            try:
                tax_rate = TaxRate.objects.get(id=tax_rate_id, is_active=True)
                ProductTax.objects.get_or_create(
                    product=product,
                    tax_rate=tax_rate
                )
            except TaxRate.DoesNotExist:
                continue


class CategoryViewSet(BaseViewSetSetup):
    serializer_classes = {
        'list': CategorySerializer,
        'retrieve': CategorySerializer,
    }
    default_serializer_class = CategorySerializer
    queryset = Category.objects.active()
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }


class SubCategoryViewSet(BaseViewSetSetup):
    serializer_classes = {
        'list': SubCategorySerializer,
        'retrieve': SubCategorySerializer,
    }
    default_serializer_class = SubCategorySerializer
    queryset = SubCategory.objects.active()
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }


class BrandViewSet(BaseViewSetSetup):
    serializer_classes = {
        'list': BrandSerializer,
        'retrieve': BrandSerializer,
    }
    default_serializer_class = BrandSerializer
    queryset = Brand.objects.active()
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }


class CartViewSet(BaseViewSetSetup):
    serializer_classes = {
        'list': CartSerializer,
        'retrieve': CartSerializer,
    }
    default_serializer_class = CartSerializer
    queryset = Cart.objects.active()
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }


class WishListViewSet(BaseViewSetSetup):
    serializer_classes = {
        'create': CreateWishlistSerializer,
        'list': ListWishlistSerializer,
        'retrieve': ListWishlistSerializer,
    }
    default_serializer_class = WishlistSerializer
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }

    def get_queryset(self):
        return Wishlist.active_objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViewSet(BaseViewSetSetup):
    serializer_classes = {
        'create': CreateWishlistSerializer,
        'list': ListWishlistSerializer,
        'retrieve': ListWishlistSerializer,
    }
    default_serializer_class = WishlistSerializer
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }

    def get_queryset(self):
        return Wishlist.active_objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['GET'], url_path='user')
    def get_order_items(self, request):
        queryset = OrderItem.active_objects.filter(order__user=self.request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ListOrderItemSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ListOrderItemSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewProductViewSet(BaseViewSetSetup):
    serializer_classes = {
        'create': CreateReviewSerializer,
        'list': ReviewSerializer,
        'retrieve': ReviewSerializer,
    }
    default_serializer_class = ReviewSerializer
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }

    def get_queryset(self):
        return Review.active_objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['GET'], url_path='user')
    def get_order_items(self, request):
        queryset = OrderItem.active_objects.filter(order__user=self.request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ListOrderItemSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ListOrderItemSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)