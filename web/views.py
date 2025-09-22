
from django.core.cache import cache
from django.db import transaction
from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, permissions, generics
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from product.models import ProductFAQ, Banner
from web.helpers import GetClientIPMixin
from web.models import BlogPostView, BlogPost, BlogTag, BlogCategory
from web.serializer import *


# Create your views here.

# class GetCategoryView(APIView):
#     permission_classes = [permissions.AllowAny]
#
#     def get(self, request):
#         try:
#             response_data = {}
#             category_id = request.query_params.get('category_id')
#             categories = self._get_cached_categories(category_id)
#             response_data['categories'] = categories
#             subcategories = self._get_cached_subcategories(category_id)
#             response_data['subcategories'] = subcategories
#             return Response({'data': response_data}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#     def _get_cached_categories(self, category_id=None):
#         """Get categories from cache or database"""
#         if category_id:
#             cache_key = f'category_{category_id}'
#         else:
#             cache_key = 'categories_list_v1'
#
#         cache_timeout = getattr(settings, 'CATEGORY_CACHE_TIMEOUT', 7200)
#
#         categories = cache.get(cache_key)
#         if not categories or categories is None:
#             categories_queryset = Category.active_objects.all().order_by('name')
#             categories = CategorySerializer(categories_queryset, many=True).data
#             cache.set(cache_key, categories, cache_timeout)
#         return categories
#
#     def _get_cached_subcategories(self, category_id=None):
#         """Get subcategories from cache or database"""
#         if category_id:
#             cache_key = f'subcategories_category_{category_id}'
#         else:
#             cache_key = 'subcategories_all_v1'
#
#         cache_timeout = getattr(settings, 'SUBCATEGORY_CACHE_TIMEOUT', 3600)
#
#         subcategories = cache.get(cache_key)
#         if not subcategories or subcategories is None:
#             queryset = SubCategory.active_objects.filter(category__status='active').select_related('category')
#
#             if category_id:
#                 queryset = queryset.filter(category_id=category_id)
#
#             queryset = queryset.order_by('category__name', 'name')
#             subcategories = SubCategorySerializer(queryset, many=True).data
#             cache.set(cache_key, subcategories, cache_timeout)
#
#         return subcategories

class GetCategoryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            category_id = request.query_params.get("category_id")
            subcategory_id = request.query_params.get("subcategory_id")
            categories = self._get_cached_categories(category_id, subcategory_id)
            return Response({"data": {"categories": categories}}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_cached_categories(self, category_id=None, subcategory_id=None):
        cache_key = "categories_with_subcategories_v1"
        if category_id:
            cache_key += f"_cat{category_id}"
        if subcategory_id:
            cache_key += f"_sub{subcategory_id}"

        cache_timeout = getattr(settings, 'CATEGORY_CACHE_TIMEOUT', 7200)

        categories = cache.get(cache_key)
        if categories is None:
            queryset = Category.active_objects.prefetch_related("sub_categories").order_by("name")

            if category_id:
                queryset = queryset.filter(id=category_id)

            categories = CategorySerializer(queryset, many=True).data
            cache.set(cache_key, categories, cache_timeout)
        return categories


class GetProductView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            product_id = request.query_params.get("product_id")
            category_id = request.query_params.get("category")
            sub_category_id = request.query_params.get("subcategory")
            is_featured = request.query_params.get("is_featured")
            is_popular = request.query_params.get("is_popular")
            is_best_seller = request.query_params.get("is_best_seller")

            min_price = request.query_params.get("min_price")
            max_price = request.query_params.get("max_price")
            brand_id = request.query_params.get("brand_id")

            if is_featured or is_popular or is_best_seller:
                products = self._get_cached_featured_products(
                    product_id, category_id, sub_category_id,
                    is_featured, is_popular, is_best_seller,
                    min_price, max_price, brand_id
                )
            else:
                products = self._get_cached_products(
                    product_id, category_id, sub_category_id,
                    min_price, max_price, brand_id
                )

            return Response(products, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_cached_products(self, product_id=None, category_id=None, sub_category_id=None,
                             min_price=None, max_price=None, brand_id=None):
        cache_key = "products_v1"
        if product_id:
            cache_key += f"_id{product_id}"
        if category_id:
            cache_key += f"_cat{category_id}"
        if sub_category_id:
            cache_key += f"_subcat{sub_category_id}"
        if min_price:
            cache_key += f"_min{min_price}"
        if max_price:
            cache_key += f"_max{max_price}"
        if brand_id:
            cache_key += f"_brand{brand_id}"

        cache_timeout = getattr(settings, 'PRODUCT_CACHE_TIMEOUT', 7200)
        products = cache.get(cache_key)

        if products is None:
            queryset = Product.active_objects.all().select_related('sub_category').order_by("id")

            if product_id:
                queryset = queryset.filter(id=product_id)
            if category_id:
                queryset = queryset.filter(sub_category__category=category_id)
            if sub_category_id:
                queryset = queryset.filter(sub_category=sub_category_id)
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            if brand_id:
                queryset = queryset.filter(brand_id=brand_id)

            products = ProductSerializer(queryset, many=True).data
            cache.set(cache_key, products, cache_timeout)
        return products

    def _get_cached_featured_products(self, product_id=None, category_id=None, sub_category_id=None,
                                      is_featured=None, is_best_seller=None, is_popular=None,
                                      min_price=None, max_price=None, brand_id=None):
        cache_key = "featured_products_v1"
        if product_id:
            cache_key += f"_id{product_id}"
        if category_id:
            cache_key += f"_cat{category_id}"
        if sub_category_id:
            cache_key += f"_subcat{sub_category_id}"
        if is_featured:
            cache_key += f"_featured"
        if is_best_seller:
            cache_key += f"_is_best_seller"
        if is_popular:
            cache_key += f"_is_popular"
        if min_price:
            cache_key += f"_min{min_price}"
        if max_price:
            cache_key += f"_max{max_price}"
        if brand_id:
            cache_key += f"_brand{brand_id}"

        cache_timeout = getattr(settings, 'PRODUCT_CACHE_TIMEOUT', 7200)
        products = cache.get(cache_key)

        if products is None:
            queryset = Product.active_objects.all().select_related('sub_category').order_by("id")

            if product_id:
                queryset = queryset.filter(id=product_id)
            if category_id:
                queryset = queryset.filter(sub_category__category=category_id)
            if sub_category_id:
                queryset = queryset.filter(sub_category=sub_category_id)
            if is_featured:
                queryset = queryset.filter(is_featured=True)
            if is_best_seller:
                queryset = queryset.filter(is_best_seller=True)
            if is_popular:
                queryset = queryset.filter(is_popular=True)
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            if brand_id:
                queryset = queryset.filter(brand_id=brand_id)

            products = ProductSerializer(queryset, many=True).data
            cache.set(cache_key, products, cache_timeout)
        return products


class GetProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        try:
            product = Product.objects.filter(id=id).last()
            serializer = ProductDetailSerializer(product, many=False).data
            return Response(serializer, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetProductFaqView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        try:
            product_faq = ProductFAQ.objects.filter(product=id).order_by('sort_order')
            serializer = ProductFaqSerializer(product_faq, many=True).data
            return Response(serializer, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetBlogsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            blog_id = request.query_params.get("blog_id")
            is_featured = request.query_params.get("is_featured", False)
            search_query = request.query_params.get("search", "").strip()

            blogs = self._get_cached_blogs(blog_id, is_featured, search_query)
            return Response(blogs, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _get_cached_blogs(self, blog_id=None, is_featured=False, search_query=""):
        cache_key = "blogs_v1"
        if blog_id:
            cache_key += f"_id{blog_id}"

        if is_featured:
            cache_key += f"_featured_blogs"

        if search_query:
            cache_key += f"_search_{hash(search_query)}"

        cache_timeout = getattr(settings, 'BLOGS_CACHE_TIMEOUT', 7200)

        blogs = cache.get(cache_key)
        if blogs is None:
            queryset = BlogPost.active_objects.all().select_related('author', 'category').order_by("id")

            if blog_id:
                queryset = queryset.filter(id=blog_id)

            if is_featured:
                queryset = queryset.filter(is_featured=True)[:5]

            if search_query:
                search_filter = Q(title__icontains=search_query) | \
                                Q(content__icontains=search_query) | \
                                Q(category__name__icontains=search_query) | \
                                Q(author__username__icontains=search_query)

                queryset = queryset.filter(search_filter)

            blogs = BlogPostListSerializer(queryset, many=True).data

            if search_query:
                cache_timeout = min(cache_timeout, 1800)

            cache.set(cache_key, blogs, cache_timeout)

        return blogs


class GetBlogDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        try:
            blog = (BlogPost.objects.select_related("author", "category")
                    .prefetch_related("tags", "comments").filter(id=id).first())
            serializer = BlogPostDetailSerializer(blog, context={"request": request}).data
            return Response(serializer, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BlogPostViewSet(ModelViewSet):
    """ViewSet for blog posts"""

    def get_serializer_class(self):
        if self.action == 'list':
            return BlogPostListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BlogPostCreateUpdateSerializer
        return BlogPostDetailSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = BlogPost.objects.active().select_related(
            'author', 'category'
        ).prefetch_related('tags')

        # Filter by status for public views
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(post_status='published')

        # Filters
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__slug=tag)

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__id=author)

        # Featured posts
        if self.request.query_params.get('featured') == 'true':
            queryset = queryset.filter(is_featured=True)

        # Trending posts
        if self.request.query_params.get('trending') == 'true':
            queryset = queryset.filter(is_trending=True)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(content__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()

        return queryset.order_by('-created_at')

    def retrieve(self, request, *args, **kwargs):
        """Get single post and increment view count"""
        instance = self.get_object()

        # Increment view count
        if not request.user.is_staff:  # Don't count admin views
            instance.increment_views()

            # Track detailed view analytics
            self.track_post_view(instance, request)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def track_post_view(self, post, request):
        """Track post view for analytics"""
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Create view record
        BlogPostView.objects.create(
            post=post,
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referrer=request.META.get('HTTP_REFERER', '')
        )

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like/unlike a blog post"""
        post = self.get_object()

        # In a real app, you'd track individual likes
        # For now, just increment the counter
        post.likes_count += 1
        post.save(update_fields=['likes_count'])

        return Response({
            'message': 'Post liked',
            'likes_count': post.likes_count
        })

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Track post share"""
        post = self.get_object()

        post.shares_count += 1
        post.save(update_fields=['shares_count'])

        return Response({
            'message': 'Share tracked',
            'shares_count': post.shares_count
        })

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Get or create comments for a post"""
        post = self.get_object()

        if request.method == 'GET':
            comments = post.comments.filter(
                comment_status='approved', parent=None
            ).order_by('-created_at')

            serializer = BlogCommentSerializer(
                comments, many=True, context={'request': request}
            )
            return Response({
                'comments': serializer.data,
                'count': comments.count()
            })

        elif request.method == 'POST':
            if not post.allow_comments:
                return Response({
                    'error': 'Comments are disabled for this post'
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = BlogCommentCreateSerializer(
                data=request.data,
                context={'request': request, 'post': post}
            )

            if serializer.is_valid():
                comment = serializer.save()
                return Response({
                    'message': 'Comment submitted for approval',
                    'comment': BlogCommentSerializer(comment, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET'])
# @permission_classes([permissions.AllowAny])
# def blog_categories_list(request):
#     """Get all active blog categories"""
#     categories = BlogCategory.objects.active().annotate(
#         posts_count=Count('posts', filter=Q(posts__post_status='published'))
#     ).order_by('sort_order', 'name')
#
#     serializer = BlogCategorySerializer(categories, many=True)
#     return Response({
#         'categories': serializer.data,
#         'count': len(serializer.data)
#     })
#
#
# @api_view(['GET'])
# @permission_classes([permissions.AllowAny])
# def blog_tags_list(request):
#     """Get all active blog tags"""
#     tags = BlogTag.objects.active().annotate(
#         posts_count=Count('posts', filter=Q(posts__post_status='published'))
#     ).filter(posts_count__gt=0).order_by('-posts_count', 'name')
#
#     serializer = BlogTagSerializer(tags, many=True)
#     return Response({
#         'tags': serializer.data,
#         'count': len(serializer.data)
#     })


class CartSummaryView(APIView):

    def get(self, request):
        """Get user's current cart"""
        cart = CartManager.get_cart(request)

        if not cart:
            return Response({
                'success': True, 'cart': None, 'message': 'Cart is empty'
            })

        cart = Cart.objects.prefetch_related(
            'items__product__images',
            'items__product_variant__attributes__attribute',
            'items__product_variant__attributes__value'
        ).get(id=cart.id)

        serializer = CartSerializer(cart)

        return Response({
            'success': True, 'cart': serializer.data
        })


class AddToCartView(APIView):

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False, 'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        try:
            with transaction.atomic():
                cart, cart_created = CartManager.get_or_create_cart(request)
                product = Product.objects.get(id=validated_data['product_id'])
                product_variant = None
                if validated_data.get('product_variant_id'):
                    product_variant = ProductVariant.objects.get(id=validated_data['product_variant_id'])

                try:
                    cart_item = CartItem.objects.get(
                        cart=cart, product=product, product_variant=product_variant
                    )

                    # Update quantity
                    new_quantity = cart_item.quantity + validated_data['quantity']

                    # Check stock for new quantity
                    max_stock = validated_data['available_stock']
                    if new_quantity > max_stock:
                        return Response({
                            'success': False,
                            'error': f'Cannot add {validated_data["quantity"]} more. Only {max_stock - cart_item.quantity} more available.',
                            'current_quantity': cart_item.quantity,
                            'max_available': max_stock
                        }, status=status.HTTP_400_BAD_REQUEST)

                    cart_item.quantity = new_quantity
                    cart_item.unit_price = validated_data['unit_price']
                    cart_item.save()

                    action = 'updated'

                except Exception as e:
                    cart_item = CartItem.objects.create(
                        cart=cart, product=product,
                        product_variant=product_variant,
                        quantity=validated_data['quantity'],
                        unit_price=validated_data['unit_price']
                    )

                    action = 'added'

                # Get updated cart
                updated_cart = Cart.objects.prefetch_related(
                    'items__product__images',
                    'items__product_variant__attributes__attribute',
                    'items__product_variant__attributes__value'
                ).get(id=cart.id)

                cart_serializer = CartSerializer(updated_cart)

                return Response({
                    'success': True,
                    'message': f'Product {action} to cart successfully',
                    'cart': cart_serializer.data,
                    'added_item': CartItemSerializer(cart_item).data
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to add item to cart',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateToCartView(APIView):

    def post(self, request, id):
        """Update cart item quantity"""
        cart = CartManager.get_cart(request)
        if not cart:
            return Response({
                'success': False, 'error': 'Cart not found'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            cart_item = CartItem.objects.get(id=id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({
                'success': False, 'error': 'Cart item not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateCartItemSerializer(
            data=request.data,
            context={'cart_item': cart_item}
        )

        if not serializer.is_valid():
            return Response({
                'success': False, 'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        new_quantity = serializer.validated_data['quantity']

        try:
            with transaction.atomic():
                if new_quantity == 0:
                    # Remove item from cart
                    cart_item.delete()
                    message = 'Item removed from cart'
                else:
                    # Update quantity
                    cart_item.quantity = new_quantity
                    cart_item.save()
                    message = 'Cart item updated successfully'

                # Get updated cart
                updated_cart = Cart.objects.prefetch_related(
                    'items__product__images',
                    'items__product_variant__attributes__attribute',
                    'items__product_variant__attributes__value'
                ).get(id=cart.id)

                cart_serializer = CartSerializer(updated_cart)

                return Response({
                    'success': True, 'message': message, 'cart': cart_serializer.data
                })

        except Exception as e:
            return Response({
                'success': False, 'error': 'Failed to update cart item', 'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RemoveCartItemView(APIView):

    def post(self, request, item_id):
        """Remove item from cart"""
        cart = CartManager.get_cart(request)
        if not cart:
            return Response({
                'success': False, 'error': 'Cart not found'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            product_name = cart_item.product.name
            cart_item.delete()

            # Get updated cart
            updated_cart = Cart.objects.prefetch_related(
                'items__product__images',
                'items__product_variant__attributes__attribute',
                'items__product_variant__attributes__value'
            ).get(id=cart.id)

            cart_serializer = CartSerializer(updated_cart)

            return Response({
                'success': True,
                'message': f'{product_name} removed from cart',
                'cart': cart_serializer.data
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Cart item not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ClearCartView(APIView):

        def get(self, request):
            """Clear all items from cart"""
            cart = CartManager.get_cart(request)
            if not cart:
                return Response({
                    'success': False,
                    'error': 'Cart not found'
                }, status=status.HTTP_404_NOT_FOUND)

            items_count = cart.items.count()
            cart.items.all().delete()

            return Response({
                'success': True,
                'message': f'Cart cleared. {items_count} items removed.',
                'cart': None
            })


class CartSummeryView(APIView):

    def get(self, request):
        """Get cart summary (quick overview)"""
        cart = CartManager.get_cart(request)

        if not cart:
            return Response({
                'success': True,
                'summary': {
                    'items_count': 0,
                    'total_amount': '0.00',
                    'is_empty': True
                }
            })

        totals = CartManager.calculate_cart_totals(cart)

        return Response({
            'success': True,
            'summary': {
                'items_count': totals['total_items'],
                'total_amount': str(totals['total']),
                'subtotal': str(totals['subtotal']),
                'is_empty': totals['total_items'] == 0
            }
        })


class MergeCartAccountView(APIView):

    def post(self, request):
        try:
            CartManager.merge_guest_cart_to_user(request, request.user)

            user_cart = Cart.objects.filter(
                user=request.user,
                status='active'
            ).prefetch_related(
                'items__product__images',
                'items__product_variant__attributes__attribute',
                'items__product_variant__attributes__value'
            ).first()

            if user_cart:
                cart_serializer = CartSerializer(user_cart)
                return Response({
                    'success': True,
                    'message': 'Guest cart merged successfully',
                    'cart': cart_serializer.data
                })
            else:
                return Response({
                    'success': True,
                    'message': 'No items to merge',
                    'cart': None
                })

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to merge cart',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# 4. BULK CART OPERATIONS
# ============================================================================

# @api_view(['POST'])
# @permission_classes([permissions.AllowAny])
# @parser_classes([JSONParser])
# def bulk_add_to_cart(request):
#     """Add multiple products to cart at once"""
#     items = request.data.get('items', [])
#
#     if not items:
#         return Response({
#             'success': False,
#             'error': 'No items provided'
#         }, status=status.HTTP_400_BAD_REQUEST)
#
#     try:
#         with transaction.atomic():
#             cart, _ = CartManager.get_or_create_cart(request)
#             added_items = []
#             errors = []
#
#             for item_data in items:
#                 serializer = AddToCartSerializer(data=item_data)
#
#                 if serializer.is_valid():
#                     validated_data = serializer.validated_data
#
#                     # Get product and variant
#                     product = Product.objects.get(id=validated_data['product_id'])
#                     product_variant = None
#                     if validated_data.get('product_variant_id'):
#                         product_variant = ProductVariant.objects.get(id=validated_data['product_variant_id'])
#
#                     # Add or update cart item
#                     cart_item, created = CartItem.objects.get_or_create(
#                         cart=cart,
#                         product=product,
#                         product_variant=product_variant,
#                         defaults={
#                             'quantity': validated_data['quantity'],
#                             'unit_price': validated_data['unit_price']
#                         }
#                     )
#
#                     if not created:
#                         cart_item.quantity += validated_data['quantity']
#                         cart_item.unit_price = validated_data['unit_price']
#                         cart_item.save()
#
#                     added_items.append(CartItemSerializer(cart_item).data)
#                 else:
#                     errors.append({
#                         'item': item_data,
#                         'errors': serializer.errors
#                     })
#
#             # Get updated cart
#             updated_cart = Cart.objects.prefetch_related(
#                 'items__product__images',
#                 'items__product_variant__attributes__attribute',
#                 'items__product_variant__attributes__value'
#             ).get(id=cart.id)
#
#             cart_serializer = CartSerializer(updated_cart)
#
#             return Response({
#                 'success': True,
#                 'message': f'{len(added_items)} items added to cart',
#                 'cart': cart_serializer.data,
#                 'added_items': added_items,
#                 'errors': errors
#             })
#
#     except Exception as e:
#         return Response({
#             'success': False,
#             'error': 'Failed to add items to cart',
#             'details': str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductsBySubCategoryAPIView(APIView):

    def post(self, request, *args, **kwargs):
        subcategory_ids = request.data.get("subcategory_ids", [])
        page_number = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", 10)

        cache_key = f"products_subcategories_{'_'.join(map(str, subcategory_ids))}_page_{page_number}_size_{page_size}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        products = Product.objects.filter(subcategory_id__in=subcategory_ids).order_by("id")

        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(page, many=True)

        paginated_response = paginator.get_paginated_response(serializer.data)

        cache.set(cache_key, paginated_response.data, timeout=600)

        return paginated_response


class GetBannerView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            banner_id = request.query_params.get("banner_id")
            subcategory_id = request.query_params.get("subcategory_id")
            banners = self._get_cached_banners(banner_id, subcategory_id)
            return Response({"data": {"banners": banners}}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_cached_banners(self, banner_id=None, subcategory_id=None):
        cache_key = "banners_v1"
        if banner_id:
            cache_key += f"_id{banner_id}"
        if subcategory_id:
            cache_key += f"_subcat{subcategory_id}"

        cache_timeout = getattr(settings, "BANNER_CACHE_TIMEOUT", 7200)

        banners = cache.get(cache_key)
        if banners is None:
            queryset = Banner.objects.prefetch_related("subcategories").order_by("-sort_order")

            if banner_id:
                queryset = queryset.filter(id=banner_id)

            if subcategory_id:
                queryset = queryset.filter(subcategories=subcategory_id)

            banners = BannerSerializer(queryset, many=True).data
            cache.set(cache_key, banners, cache_timeout)

        return banners


class GetBrandAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            brands = self._get_cached_brands()
            return Response(brands, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _get_cached_brands(self, banner_id=None, subcategory_id=None):
        cache_key = "brands_v1"

        cache_timeout = getattr(settings, "BRAND_CACHE_TIMEOUT", 7200)

        brands = cache.get(cache_key)
        if brands is None:
            queryset = Brand.objects.active().order_by("created_at")

            brands = BrandsSerializer(queryset, many=True).data
            cache.set(cache_key, brands, cache_timeout)

        return brands


class PostCommentsListView(generics.ListAPIView):
    """List all approved comments for a specific blog post"""
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend,]
    ordering_fields = ['created_at', 'likes_count']
    ordering = ['-created_at']

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        post = get_object_or_404(BlogPost, id=post_id)

        return BlogComment.objects.filter(
            post=post, comment_status='approved', parent__isnull=True
        ).select_related('user').prefetch_related('replies__user')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CommentCreateView(GetClientIPMixin, generics.CreateAPIView):
    """Create a new comment or reply"""
    serializer_class = CommentCreateSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        post = get_object_or_404(BlogPost, id=self.kwargs['post_id'])

        parent = None
        parent_id = serializer.validated_data.get('parent_id')
        if parent_id:
            parent = get_object_or_404(
                BlogComment, id=parent_id, post=post
            )

        comment = serializer.save(
            post=post, parent=parent, ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            user=self.request.user if self.request.user.is_authenticated else None, comment_status='approved'
        )

        return comment

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {'message': 'Comment submitted posted.'},
            status=status.HTTP_200_OK
        )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific comment"""
    serializer_class = CommentSerializer

    def get_queryset(self):
        return BlogComment.objects.filter(comment_status='approved')

    def get_permissions(self):
        """Different permissions for different actions"""
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_object(self):
        obj = super().get_object()

        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.user != self.request.user and not self.request.user.is_staff:
                self.permission_denied(
                    self.request,
                    message="You can only modify your own comments."
                )

        return obj

    def perform_update(self, serializer):
        serializer.save(
            is_edited=True, edited_at=timezone.now()
        )

    def perform_destroy(self, instance):
        instance.comment_status = 'deleted'
        instance.save(update_fields=['comment_status'])


class CommentRepliesListView(generics.ListAPIView):
    """List all replies for a specific comment"""
    serializer_class = CommentReplySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        comment_id = self.kwargs['comment_id']
        parent_comment = get_object_or_404(
            BlogComment, id=comment_id, comment_status='approved'
        )
        return parent_comment.replies.filter(comment_status='approved').select_related('user').order_by('created_at')