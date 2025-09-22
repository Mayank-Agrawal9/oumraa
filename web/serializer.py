from decimal import Decimal

from django.db.models import Avg, Q, F, Count, Sum
from django.utils import timezone
from rest_framework import serializers

from account.models import User
from oumraa import settings
from product.models import Category, SubCategory, Product, ProductImage, Brand, ProductAttribute, ProductVariant, \
    Review, ProductTax, ProductVariantAttribute, Coupon, ProductFAQ, CartItem, Cart, Banner
from web.helpers import CartManager
from web.models import BlogCategory, BlogTag, BlogComment, BlogPost


class SubCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SubCategory
        exclude = ('created_at', 'updated_on', 'status')


class CategorySerializer(serializers.ModelSerializer):
    sub_categories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        exclude = ('created_at', 'updated_on', 'status', 'parent')


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'short_description', 'sku', 'price', 'primary_image_url', 'category_name',
                  'sub_category_name', 'is_featured', 'is_popular', 'is_best_seller')


class BlogCategorySerializer(serializers.ModelSerializer):
    """Serializer for blog categories"""
    posts_count = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = BlogCategory
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'full_name',
            'color', 'icon', 'image', 'posts_count', 'meta_title', 'meta_description'
        ]


class BlogTagSerializer(serializers.ModelSerializer):
    """Serializer for blog tags"""

    class Meta:
        model = BlogTag
        fields = ['id', 'name', 'slug', 'description', 'color', 'posts_count']


class BlogCommentSerializer(serializers.ModelSerializer):
    """Serializer for blog comments"""
    author_name = serializers.CharField(read_only=True)
    replies = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = [
            'id', 'content', 'author_name', 'created_at',
            'is_edited', 'edited_at', 'replies', 'can_edit'
        ]

    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.get_replies()
            return BlogCommentSerializer(replies, many=True, context=self.context).data
        return []

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user


class BlogPostListSerializer(serializers.ModelSerializer):
    """Serializer for blog post list view"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    reading_time_text = serializers.CharField(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'excerpt', 'featured_image', 'featured_image_alt',
            'author_name', 'category_name', 'category_color', 'tags', 'post_type',
            'views_count', 'comments_count',
            'reading_time_text', 'is_featured'
        ]


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single blog post"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_avatar = serializers.CharField(source='author.picture', read_only=True)
    category = BlogCategorySerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    related_posts = serializers.SerializerMethodField()
    reading_time_text = serializers.CharField(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content', 'post_type',
            'featured_image', 'featured_image_alt', 'gallery_images',
            'author_name', 'author_avatar', 'category', 'tags',
            'views_count', 'comments_count', 'shares_count',
            'reading_time_text', 'allow_comments', 'meta_title', 'meta_description', 'meta_keywords',
            'og_title', 'og_description', 'og_image', 'comments', 'related_posts'
        ]

    def get_comments(self, obj):
        if obj.allow_comments:
            # Get top-level approved comments
            top_level_comments = obj.comments.filter(
                comment_status='approved', parent=None
            ).order_by('-created_at')[:20]

            return BlogCommentSerializer(
                top_level_comments, many=True, context=self.context
            ).data
        return []

    def get_related_posts(self, obj):
        related = obj.get_related_posts(limit=4)
        return BlogPostListSerializer(related, many=True).data


class BlogPostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating blog posts"""

    class Meta:
        model = BlogPost
        fields = [
            'title', 'slug', 'excerpt', 'content', 'post_type', 'post_status',
            'category', 'tags', 'featured_image', 'featured_image_alt',
            'gallery_images', 'scheduled_at',
            'meta_title', 'meta_description', 'meta_keywords',
            'og_title', 'og_description', 'og_image',
            'allow_comments', 'is_featured', 'is_trending'
        ]

    def create(self, validated_data):
        # Set author from request user
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class BlogCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating blog comments"""

    class Meta:
        model = BlogComment
        fields = ['content', 'parent', 'guest_name', 'guest_email', 'guest_website']

    def create(self, validated_data):
        request = self.context['request']
        post = self.context['post']

        # Set post
        validated_data['post'] = post

        # Set user if authenticated
        if request.user.is_authenticated:
            validated_data['user'] = request.user
            # Clear guest fields for authenticated users
            validated_data.pop('guest_name', None)
            validated_data.pop('guest_email', None)
            validated_data.pop('guest_website', None)

        # Set metadata
        validated_data['ip_address'] = self.get_client_ip(request)
        validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        return super().create(validated_data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def validate(self, data):
        request = self.context['request']

        # Validate guest information for non-authenticated users
        if not request.user.is_authenticated:
            if not data.get('guest_name'):
                raise serializers.ValidationError({'guest_name': 'Name is required for guest comments'})
            if not data.get('guest_email'):
                raise serializers.ValidationError({'guest_email': 'Email is required for guest comments'})

        return data


class ProductImageDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for product images"""
    responsive_urls = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            'id', 'thumbnail_url', 'medium_url', 'large_url', 'original_url',
            'alt_text', 'is_primary', 'sort_order', 'original_filename',
            'original_width', 'original_height', 'responsive_urls', 'created_at'
        ]

    def get_responsive_urls(self, obj):
        """Get responsive image URLs for different screen sizes"""
        return {
            'mobile': obj.thumbnail_url,  # 300px
            'tablet': obj.medium_url,  # 600px
            'desktop': obj.large_url,  # 1200px
            'original': obj.original_url
        }


class BrandDetailSerializer(serializers.ModelSerializer):
    """Detailed brand serializer"""

    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'description', 'logo']


class SubCategoryDetailSerializer(serializers.ModelSerializer):
    """Detailed category serializer with parent chain"""
    category_path = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = [
            'id', 'name', 'slug', 'description', 'category_path', 'image'
        ]

    def get_category_path(self, obj):
        """Get full category path like: Electronics > Smartphones > Apple"""
        path = []
        category = obj.category
        if category:
            path.append({'id': category.id, 'name': category.name, 'slug': category.slug})
        return list(reversed(path))


class ProductAttributeDetailSerializer(serializers.ModelSerializer):
    """Product attribute with values"""
    values = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'slug', 'is_required', 'values']

    def get_values(self, obj):
        return [
            {'id': v.id, 'value': v.value}
            for v in obj.values.all().order_by('value')
        ]


class ProductVariantDetailSerializer(serializers.ModelSerializer):
    """Detailed product variant serializer"""
    attributes = serializers.SerializerMethodField()
    price_difference = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price', 'stock_quantity', 'status',
            'attributes', 'price_difference', 'in_stock', 'created_at'
        ]

    def get_attributes(self, obj):
        """Get variant attributes in structured format"""
        variant_attrs = obj.attributes.select_related('attribute', 'value').all()
        result = {}
        for attr in variant_attrs:
            result[attr.attribute.slug] = {
                'attribute_id': str(attr.attribute.id),
                'attribute_name': attr.attribute.name,
                'value_id': str(attr.value.id),
                'value': attr.value.value
            }
        return result

    def get_price_difference(self, obj):
        """Calculate price difference from base product"""
        if obj.price and obj.product.price:
            difference = obj.price - obj.product.price
            return {
                'amount': str(difference),
                'percentage': round((difference / obj.product.price) * 100, 2) if obj.product.price > 0 else 0,
                'is_higher': difference > 0,
                'formatted': f"+₹{difference}" if difference > 0 else f"₹{difference}" if difference < 0 else "Same price"
            }
        return None

    def get_in_stock(self, obj):
        """Check if variant is in stock"""
        return obj.stock_quantity > 0 if obj.stock_quantity is not None else obj.product.stock_quantity > 0


class ReviewSummarySerializer(serializers.ModelSerializer):
    """Serializer for product reviews"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    is_verified_purchase = serializers.BooleanField()
    helpful_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'rating', 'title', 'comment', 'user_name', 'user_avatar',
            'is_verified_purchase', 'helpful_count', 'helpful_percentage',
            'created_at'
        ]

    def get_user_avatar(self, obj):
        """Get user avatar URL"""
        if hasattr(obj.user, 'profile') and obj.user.profile.profile_image:
            return obj.user.profile.profile_image
        return None

    def get_helpful_percentage(self, obj):
        """Calculate helpful percentage (mock calculation)"""
        total_votes = obj.helpful_count + 5  # Mock total votes
        return round((obj.helpful_count / total_votes) * 100, 1) if total_votes > 0 else 0


class ProductTaxDetailSerializer(serializers.ModelSerializer):
    """Product tax details"""
    tax_name = serializers.CharField(source='tax_rate.name', read_only=True)
    tax_rate = serializers.DecimalField(source='tax_rate.rate', max_digits=5, decimal_places=2, read_only=True)
    is_inclusive = serializers.BooleanField(source='tax_rate.is_inclusive', read_only=True)

    class Meta:
        model = ProductTax
        fields = ['tax_name', 'tax_rate', 'is_inclusive']


class RelatedProductSerializer(serializers.ModelSerializer):
    """Serializer for related products"""
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'compare_price', 'primary_image',
            'category_name', 'brand_name', 'average_rating', 'reviews_count',
            'discount_percentage', 'is_featured'
        ]

    def get_primary_image(self, obj):
        primary_img = obj.images.filter(is_primary=True).first()
        if primary_img:
            return {
                'thumbnail': primary_img.thumbnail_url,
                'medium': primary_img.medium_url,
                'alt_text': primary_img.alt_text
            }
        return None

    def get_average_rating(self, obj):
        return getattr(obj, 'avg_rating', 0) or 0

    def get_reviews_count(self, obj):
        return getattr(obj, 'reviews_count', 0) or 0

    def get_discount_percentage(self, obj):
        if obj.compare_price and obj.price and obj.compare_price > obj.price:
            discount = ((obj.compare_price - obj.price) / obj.compare_price) * 100
            return round(discount, 1)
        return 0


class ProductDetailSerializer(serializers.ModelSerializer):
    """Complete product details serializer"""

    # Basic relationships
    sub_category = SubCategoryDetailSerializer(read_only=True)
    brand = BrandDetailSerializer(read_only=True)

    # Images
    images = ProductImageDetailSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()

    # Variants and attributes
    variants = ProductVariantDetailSerializer(many=True, read_only=True)
    available_attributes = serializers.SerializerMethodField()

    # Reviews and ratings
    reviews = serializers.SerializerMethodField()
    rating_summary = serializers.SerializerMethodField()

    # Pricing and discounts
    pricing_info = serializers.SerializerMethodField()
    applicable_coupons = serializers.SerializerMethodField()

    # Stock and availability
    stock_info = serializers.SerializerMethodField()

    # Taxes
    product_taxes = ProductTaxDetailSerializer(source='taxes', many=True, read_only=True)

    # Related products
    related_products = serializers.SerializerMethodField()

    # SEO and meta
    seo_data = serializers.SerializerMethodField()

    # Analytics
    popularity_score = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            # Basic product info
            'id', 'name', 'slug', 'description', 'short_description', 'sku',
            'price', 'compare_price', 'cost_price',

            # Relationships
            'sub_category', 'brand',

            # Media
            'images', 'primary_image',

            # Inventory
            'stock_quantity', 'low_stock_threshold', 'track_inventory', 'allow_backorder',
            'stock_info',

            # Physical properties
            'weight', 'length', 'width', 'height',

            # Variants and attributes
            'variants', 'available_attributes',

            # Reviews and ratings
            'reviews', 'rating_summary',

            # Pricing
            'pricing_info', 'applicable_coupons', 'product_taxes',

            # Features
            'is_featured',

            # SEO
            'meta_title', 'meta_description', 'seo_data',

            # Related products
            'related_products',

            # Analytics
            'popularity_score',

            # Timestamps
            'created_at', 'updated_on'
        ]

    def get_primary_image(self, obj):
        """Get primary image with all sizes"""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return ProductImageDetailSerializer(primary).data
        return None

    def get_available_attributes(self, obj):
        """Get all available attributes for product variants"""
        if not obj.variants.exists():
            return []

        # Get unique attributes across all variants
        attribute_ids = set()
        for variant in obj.variants.filter(status='active'):
            for attr in variant.attributes.all():
                attribute_ids.add(attr.attribute.id)

        attributes = ProductAttribute.objects.filter(
            id__in=attribute_ids
        ).prefetch_related('values')

        result = []
        for attr in attributes:
            # Get available values for this attribute from active variants
            variant_values = ProductVariantAttribute.objects.filter(
                variant__product=obj,
                variant__status='active',
                attribute=attr
            ).values_list('value__id', 'value__value').distinct()

            result.append({
                'id': str(attr.id),
                'name': attr.name,
                'slug': attr.slug,
                'is_required': attr.is_required,
                'values': [
                    {'id': str(value_id), 'value': value}
                    for value_id, value in variant_values
                ]
            })

        return result

    def get_reviews(self, obj):
        """Get recent reviews (limited)"""
        recent_reviews = obj.reviews.filter(is_approved=True
        ).select_related('user').order_by('-created_at')[:10]
        return ReviewSummarySerializer(recent_reviews, many=True).data

    def get_rating_summary(self, obj):
        """Get comprehensive rating summary"""
        reviews = obj.reviews.filter(is_approved=True)

        if not reviews.exists():
            return {
                'average_rating': 0,
                'total_reviews': 0,
                'rating_distribution': {str(i): 0 for i in range(1, 6)},
                'percentage_distribution': {str(i): 0 for i in range(1, 6)}
            }

        # Calculate rating distribution
        rating_counts = {}
        total_reviews = reviews.count()

        for i in range(1, 6):
            count = reviews.filter(rating=i).count()
            rating_counts[str(i)] = count

        # Calculate percentages
        percentage_distribution = {}
        for rating, count in rating_counts.items():
            percentage_distribution[rating] = round((count / total_reviews) * 100, 1) if total_reviews > 0 else 0

        # Calculate average
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

        return {
            'average_rating': round(avg_rating, 1),
            'total_reviews': total_reviews,
            'rating_distribution': rating_counts,
            'percentage_distribution': percentage_distribution,
            'verified_purchases': reviews.filter(is_verified_purchase=True).count()
        }

    def get_pricing_info(self, obj):
        """Get comprehensive pricing information"""
        pricing = {
            'base_price': str(obj.price),
            'compare_price': str(obj.compare_price) if obj.compare_price else None,
            'currency': 'INR',
            'discount_amount': None,
            'discount_percentage': None,
            'you_save': None,
            'price_range': None,
            'bulk_pricing': []
        }

        # Calculate discount
        if obj.compare_price and obj.compare_price > obj.price:
            discount_amount = obj.compare_price - obj.price
            discount_percentage = (discount_amount / obj.compare_price) * 100

            pricing.update({
                'discount_amount': str(discount_amount),
                'discount_percentage': round(discount_percentage, 1),
                'you_save': f"You save ₹{discount_amount} ({discount_percentage:.1f}%)"
            })

        # Price range for variants
        if obj.variants.filter(status='active').exists():
            variant_prices = obj.variants.filter(status='active').values_list('price', flat=True)
            variant_prices = [p for p in variant_prices if p is not None]

            if variant_prices:
                min_price = min(variant_prices)
                max_price = max(variant_prices)

                if min_price != max_price:
                    pricing['price_range'] = {
                        'min_price': str(min_price),
                        'max_price': str(max_price),
                        'formatted': f"₹{min_price} - ₹{max_price}"
                    }

        # Mock bulk pricing (you can implement real bulk pricing logic)
        pricing['bulk_pricing'] = [
            {'quantity': 10, 'price': str(obj.price * Decimal('0.95')), 'discount': '5%'},
            {'quantity': 50, 'price': str(obj.price * Decimal('0.90')), 'discount': '10%'},
            {'quantity': 100, 'price': str(obj.price * Decimal('0.85')), 'discount': '15%'}
        ]

        return pricing

    def get_applicable_coupons(self, obj):
        """Get coupons applicable to this product"""
        # Get active coupons that are currently valid
        now = timezone.now()
        coupons = Coupon.objects.filter(
            status='active', valid_from__lte=now, valid_until__gte=now,
            minimum_amount__lte=obj.price
        ).filter(
            Q(usage_limit__isnull=True) | Q(usage_limit__gt=F('used_count'))
        )[:5]

        coupon_data = []
        for coupon in coupons:
            discount_value = None
            max_discount = None

            if coupon.discount_type == 'percentage':
                discount_value = f"{coupon.discount_value}% OFF"
                if coupon.maximum_discount:
                    max_discount = f"Max ₹{coupon.maximum_discount}"
            elif coupon.discount_type == 'fixed':
                discount_value = f"₹{coupon.discount_value} OFF"
            elif coupon.discount_type == 'free_shipping':
                discount_value = "FREE SHIPPING"

            coupon_data.append({
                'code': coupon.code,
                'name': coupon.name,
                'description': coupon.description,
                'discount_value': discount_value,
                'max_discount': max_discount,
                'minimum_amount': str(coupon.minimum_amount),
                'valid_until': coupon.valid_until.isoformat()
            })

        return coupon_data

    def get_stock_info(self, obj):
        """Get comprehensive stock information"""
        stock_info = {
            'is_in_stock': obj.stock_quantity > 0,
            'stock_quantity': obj.stock_quantity,
            'low_stock_threshold': obj.low_stock_threshold,
            'is_low_stock': obj.stock_quantity <= obj.low_stock_threshold if obj.low_stock_threshold else False,
            'track_inventory': obj.track_inventory,
            'allow_backorder': obj.allow_backorder,
            'stock_status': 'in_stock',
            'availability_message': '',
            'estimated_delivery': None
        }

        # Determine stock status
        if obj.stock_quantity <= 0:
            stock_info['stock_status'] = 'out_of_stock'
            stock_info['availability_message'] = 'Out of stock'
            if obj.allow_backorder:
                stock_info['availability_message'] = 'Available on backorder'
                stock_info['estimated_delivery'] = '7-10 business days'
        elif obj.stock_quantity <= obj.low_stock_threshold:
            stock_info['stock_status'] = 'low_stock'
            stock_info['availability_message'] = f'Only {obj.stock_quantity} left in stock'
        else:
            stock_info['availability_message'] = 'In stock'
            stock_info['estimated_delivery'] = '2-3 business days'

        # Variant stock info
        if obj.variants.filter(status='active').exists():
            variant_stock = []
            for variant in obj.variants.filter(status='active'):
                variant_stock.append({
                    'variant_id': str(variant.id),
                    'sku': variant.sku,
                    'stock_quantity': variant.stock_quantity,
                    'is_in_stock': variant.stock_quantity > 0
                })
            stock_info['variant_stock'] = variant_stock

        return stock_info

    def get_related_products(self, obj):
        """Get related products"""
        related = Product.objects.active().filter(
            sub_category=obj.sub_category,
            status='active'
        ).exclude(id=obj.id).annotate(avg_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews')
        ).order_by('-is_featured', '-avg_rating')[:3]

        return RelatedProductSerializer(related, many=True).data

    def get_seo_data(self, obj):
        """Get SEO and structured data"""
        return {
            'canonical_url': f"/product/{obj.slug}",
            'structured_data': self._get_structured_data(obj)
        }

    def _get_structured_data(self, obj):
        """Generate JSON-LD structured data"""
        avg_rating = self.get_rating_summary(obj)['average_rating']
        total_reviews = self.get_rating_summary(obj)['total_reviews']

        structured_data = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": obj.name,
            "description": obj.short_description or obj.description[:160],
            "sku": obj.sku,
            "brand": {
                "@type": "Brand",
                "name": obj.brand.name if obj.brand else "Unknown"
            },
            "offers": {
                "@type": "Offer",
                "price": str(obj.price),
                "priceCurrency": "INR",
                "availability": "https://schema.org/InStock" if obj.stock_quantity > 0 else "https://schema.org/OutOfStock",
                "seller": {
                    "@type": "Organization",
                    "name": settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else "Oumraa Store"
                }
            }
        }

        # Add images
        if obj.images.exists():
            structured_data["image"] = [img.large_url for img in obj.images.all()[:5]]

        # Add ratings if available
        if total_reviews > 0:
            structured_data["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": avg_rating,
                "reviewCount": total_reviews,
                "bestRating": 5,
                "worstRating": 1
            }

        return structured_data

    def get_popularity_score(self, obj):
        """Calculate product popularity score"""
        # This is a mock calculation - implement based on your analytics
        views_weight = 0.3
        reviews_weight = 0.3
        sales_weight = 0.4  # You'd need order data for this

        # Mock calculation
        views_score = min(getattr(obj, 'views_count', 0) / 1000, 1)  # Normalize to 0-1
        reviews_score = min(len(self.get_reviews(obj)) / 100, 1)  # Normalize to 0-1
        sales_score = 0.5  # Mock sales score

        popularity = (views_score * views_weight +
                      reviews_score * reviews_weight +
                      sales_score * sales_weight) * 100

        return round(popularity, 1)


class ProductFaqSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductFAQ
        fields = ['id', 'question', 'answer']


class ProductVariantMinimalSerializer(serializers.ModelSerializer):
    """Minimal product variant info for cart"""
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'price', 'attributes']

    def get_attributes(self, obj):
        """Get variant attributes"""
        if hasattr(obj, 'attributes'):
            return {
                attr.attribute.name: attr.value.value
                for attr in obj.attributes.select_related('attribute', 'value').all()
            }
        return {}


class ProductMinimalSerializer(serializers.ModelSerializer):
    """Minimal product info for cart"""
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'stock_quantity', 'primary_image']

    def get_primary_image(self, obj):
        """Get primary image"""
        primary_img = obj.images.filter(is_primary=True).first()
        if primary_img:
            return {
                'thumbnail_url': primary_img.thumbnail_url,
                'alt_text': primary_img.alt_text
            }
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """Cart item serializer"""
    product = ProductMinimalSerializer(read_only=True)
    product_variant = ProductVariantMinimalSerializer(read_only=True)
    item_total = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    max_quantity = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_variant', 'quantity', 'unit_price',
            'item_total', 'is_available', 'max_quantity', 'created_on', 'updated_on'
        ]

    def get_item_total(self, obj):
        """Calculate item total"""
        return obj.unit_price * obj.quantity

    def get_is_available(self, obj):
        """Check if product is still available"""
        if obj.product_variant:
            return obj.product_variant.stock_quantity >= obj.quantity
        return obj.product.stock_quantity >= obj.quantity

    def get_max_quantity(self, obj):
        """Get maximum available quantity"""
        if obj.product_variant:
            return obj.product_variant.stock_quantity
        return obj.product.stock_quantity


class CartSerializer(serializers.ModelSerializer):
    """Complete cart serializer"""
    items = CartItemSerializer(many=True, read_only=True)
    totals = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'totals', 'items_count',
            'created_on', 'updated_on'
        ]

    def get_totals(self, obj):
        """Get cart totals"""
        return CartManager.calculate_cart_totals(obj)

    def get_items_count(self, obj):
        """Get total items count"""
        return obj.items.aggregate(total=Sum('quantity'))['total'] or 0


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product_id = serializers.UUIDField()
    product_variant_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, value):
        """Validate product exists and is active"""
        try:
            product = Product.objects.active().get(id=value, status='active')
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")

    def validate_product_variant_id(self, value):
        """Validate product variant if provided"""
        if value:
            try:
                variant = ProductVariant.objects.get(id=value, is_active=True)
                return value
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found or inactive")
        return value

    def validate(self, data):
        """Cross-field validation"""
        product_id = data['product_id']
        variant_id = data.get('product_variant_id')
        quantity = data['quantity']

        # Get product
        product = Product.objects.get(id=product_id)

        # Check stock availability
        if variant_id:
            variant = ProductVariant.objects.get(id=variant_id)
            if variant.product != product:
                raise serializers.ValidationError("Variant does not belong to the specified product")

            available_stock = variant.stock_quantity
            unit_price = variant.price or product.price
        else:
            available_stock = product.stock_quantity
            unit_price = product.price

        # Validate stock
        if available_stock < quantity:
            raise serializers.ValidationError(f"Only {available_stock} items available in stock")

        # Add calculated fields to validated data
        data['unit_price'] = unit_price
        data['available_stock'] = available_stock

        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    quantity = serializers.IntegerField(min_value=0)  # 0 to remove item

    def validate_quantity(self, value):
        """Validate quantity against stock"""
        cart_item = self.context.get('cart_item')
        if not cart_item:
            return value

        if value > 0:
            # Check stock availability
            if cart_item.product_variant:
                available_stock = cart_item.product_variant.stock_quantity
            else:
                available_stock = cart_item.product.stock_quantity

            if value > available_stock:
                raise serializers.ValidationError(f"Only {available_stock} items available in stock")

        return value


class BannerSerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Banner
        fields = ["id", "title", "image", "subcategories", "created_at"]


class BrandsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand
        fields = ["id", "name", "logo"]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information in comments"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'full_name', 'email']


class CommentReplySerializer(serializers.ModelSerializer):
    """Serializer for comment replies"""
    user = UserSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = [
            'id', 'content', 'user', 'guest_name', 'guest_email', 'created_at', 'replies_count'
        ]
        read_only_fields = ['id', 'created_at']

    def get_replies_count(self, obj):
        return obj.replies.filter(comment_status='approved').count()


class CommentSerializer(serializers.ModelSerializer):
    """Main serializer for blog comments"""
    user = UserSerializer(read_only=True)
    replies = CommentReplySerializer(many=True, read_only=True)
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = [
            'id', 'content', 'user', 'guest_name', 'guest_email',
            'guest_phone_number', 'comment_status', 'created_at', 'updated_on',
            'replies', 'replies_count'
        ]
        read_only_fields = [
            'id', 'comment_status', 'created_at', 'updated_on'
        ]

    def get_replies_count(self, obj):
        return obj.replies.filter(comment_status='approved').count()

    def validate(self, data):
        request = self.context.get('request')

        if not request.user.is_authenticated:
            if not data.get('guest_name'):
                raise serializers.ValidationError({
                    'guest_name': 'This field is required for guest comments.'
                })
            if not data.get('guest_email'):
                raise serializers.ValidationError({
                    'guest_email': 'This field is required for guest comments.'
                })

        return data


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""
    parent_id = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = BlogComment
        fields = [
            'content', 'guest_name', 'guest_email', 'guest_phone_number', 'parent_id'
        ]

    def validate_parent_id(self, value):
        if value:
            try:
                parent = BlogComment.objects.get(id=value, comment_status='approved')
                if parent.parent:
                    raise serializers.ValidationError(
                        "Cannot reply to a reply. Please reply to the main comment."
                    )
            except BlogComment.DoesNotExist:
                raise serializers.ValidationError("Parent comment not found.")
        return value

    def validate(self, attrs):
        request = self.context['request']
        user = request.user

        if user and user.is_authenticated:
            # Authenticated → enforce user presence
            # Remove guest_name/email requirement
            attrs['guest_name'] = None
            attrs['guest_email'] = None
        else:
            # Guest user → guest_name and guest_email are required
            if not attrs.get('guest_name'):
                raise serializers.ValidationError(
                    {"guest_name": "This field is required for guest users."}
                )
            if not attrs.get('guest_email'):
                raise serializers.ValidationError(
                    {"guest_email": "This field is required for guest users."}
                )

        return attrs


class BlogPostSerializer(serializers.ModelSerializer):
    """Basic serializer for blog post in comment context"""
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'comments_count']
        read_only_fields = ['id', 'title', 'slug', 'comments_count']

    def get_comments_count(self, obj):
        return obj.comments.filter(comment_status='approved').count()