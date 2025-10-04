import json

from django.db.models import Avg
from rest_framework import serializers

from product.models import *


class ProductImageUploadSerializer(serializers.Serializer):
    """Serializer for individual image upload"""
    image = serializers.ImageField(required=True)
    alt_text = serializers.CharField(max_length=255, required=False, allow_blank=True)
    is_primary = serializers.BooleanField(default=False)
    sort_order = serializers.IntegerField(default=0)


class ProductImageResponseSerializer(serializers.ModelSerializer):
    """Response serializer for product images"""

    class Meta:
        model = ProductImage
        fields = [
            'id', 'thumbnail_url', 'medium_url', 'large_url', 'original_url',
            'alt_text', 'is_primary', 'sort_order', 'original_filename',
            'original_width', 'original_height', 'created_at'
        ]


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer for dropdown/selection"""

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']


class SubCategorySerializer(serializers.ModelSerializer):
    """Sub Category serializer for dropdown/selection"""

    class Meta:
        model = SubCategory
        fields = '__all__'


class CartSerializer(serializers.ModelSerializer):
    """Sub Category serializer for dropdown/selection"""

    class Meta:
        model = Cart
        fields = '__all__'


class ListWishlistSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    rating_summary = serializers.SerializerMethodField()

    def get_product(self, obj):
        return ({
            'id': obj.product.id,
            'name': obj.product.name,
            'short_description': obj.product.short_description,
            'image': obj.product.primary_image_url,
            'price': obj.product.price,
            'is_featured': obj.product.is_featured,
            'is_popular': obj.product.is_popular,
            'is_best_seller': obj.product.is_best_seller
        })

    def get_rating_summary(self, obj):
        """Get comprehensive rating summary"""
        reviews = obj.product.reviews.filter(is_approved=True)

        if not reviews.exists():
            return {
                'average_rating': 0,
                'total_reviews': 0,
                'rating_distribution': {str(i): 0 for i in range(1, 6)},
                'percentage_distribution': {str(i): 0 for i in range(1, 6)}
            }

        rating_counts = {}
        total_reviews = reviews.count()

        for i in range(1, 6):
            count = reviews.filter(rating=i).count()
            rating_counts[str(i)] = count

        percentage_distribution = {}
        for rating, count in rating_counts.items():
            percentage_distribution[rating] = round((count / total_reviews) * 100, 1) if total_reviews > 0 else 0

        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

        return {
            'average_rating': round(avg_rating, 1),
            'total_reviews': total_reviews,
            'rating_distribution': rating_counts,
            'percentage_distribution': percentage_distribution,
            'verified_purchases': reviews.filter(is_verified_purchase=True).count()
        }

    class Meta:
        model = Wishlist
        fields = '__all__'


class WishlistSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wishlist
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = '__all__'


class CreateWishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'
        read_only_fields = ['user']

    def validate(self, attrs):
        user = self.context["request"].user
        product = attrs.get("product")

        if Wishlist.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError({"error": "This product is already in your wishlist."})

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ReviewMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewMedia
        fields = ['id', 'media_type', 'file']


class CreateReviewSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user']

    def validate(self, attrs):
        user = self.context["request"].user
        product = attrs.get("product")

        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError({"error": "You already submitted a review."})

        return attrs

    def create(self, validated_data):
        files = validated_data.pop("files", [])
        validated_data["user"] = self.context["request"].user

        review = Review.objects.create(**validated_data)

        for file in files:
            ReviewMedia.objects.create(review=review, media_type=self._guess_type(file), file=file)

        return review

    def _guess_type(self, file):
        """Helper to detect if it's image or video"""
        if file.content_type.startswith("image/"):
            return "image"
        elif file.content_type.startswith("video/"):
            return "video"
        return "image"



class BrandSerializer(serializers.ModelSerializer):
    """Brand serializer for dropdown/selection"""

    class Meta:
        model = Brand
        fields = ['id', 'name', 'logo']


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Product attribute serializer"""
    values = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'is_required', 'values']

    def get_values(self, obj):
        return [{'id': v.id, 'value': v.value} for v in obj.values.all()]


class ProductVariantCreateSerializer(serializers.Serializer):
    """Serializer for creating product variants"""
    sku = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    stock_quantity = serializers.IntegerField(default=0)
    attributes = serializers.DictField()  # {attribute_id: value_id}


class ProductVariantResponseSerializer(serializers.ModelSerializer):
    """Response serializer for product variants"""
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price', 'stock_quantity', 'is_active',
            'attributes', 'created_at'
        ]

    def get_attributes(self, obj):
        variant_attrs = obj.attributes.select_related('attribute', 'value').all()
        return {
            attr.attribute.name: {
                'attribute_id': attr.attribute.id,
                'value': attr.value.value,
                'value_id': attr.value.id
            }
            for attr in variant_attrs
        }


class ProductCreateSerializer(serializers.Serializer):
    """Complete serializer for product creation"""

    # Basic Product Information
    name = serializers.CharField(max_length=500)
    description = serializers.CharField(style={'base_template': 'textarea.html'})
    short_description = serializers.CharField(max_length=500, required=False, allow_blank=True)

    # Category and Brand
    category_id = serializers.UUIDField()
    brand_id = serializers.UUIDField(required=False, allow_null=True)

    # SKU and Pricing
    sku = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    compare_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    cost_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    # Inventory Management
    stock_quantity = serializers.IntegerField(default=0)
    low_stock_threshold = serializers.IntegerField(default=10)
    track_inventory = serializers.BooleanField(default=True)
    allow_backorder = serializers.BooleanField(default=False)

    # Physical Properties
    weight = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    length = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    width = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    height = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)

    # SEO
    meta_title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    meta_description = serializers.CharField(required=False, allow_blank=True)

    # Status and Features
    status = serializers.ChoiceField(choices=[('draft', 'Draft'), ('active', 'Active'), ('inactive', 'Inactive')],
                                     default='draft')
    is_featured = serializers.BooleanField(default=False)
    is_digital = serializers.BooleanField(default=False)

    # Tax Information
    tax_rate_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )

    # Product Variants (JSON string or list)
    variants = serializers.JSONField(required=False, allow_null=True)

    def validate_category_id(self, value):
        """Validate category exists and is active"""
        try:
            category = Category.objects.active().get(id=value)
            return value
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category not found or inactive")

    def validate_brand_id(self, value):
        """Validate brand exists and is active"""
        if value:
            try:
                brand = Brand.objects.active().get(id=value)
                return value
            except Brand.DoesNotExist:
                raise serializers.ValidationError("Brand not found or inactive")
        return value

    def validate_sku(self, value):
        """Validate SKU is unique"""
        if Product.objects.filter(sku=value).exists():
            raise serializers.ValidationError("SKU already exists")
        return value

    def validate_variants(self, value):
        """Validate variants data"""
        if not value:
            return []

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format for variants")

        if not isinstance(value, list):
            raise serializers.ValidationError("Variants must be a list")

        # Validate each variant
        skus = []
        for variant in value:
            if not isinstance(variant, dict):
                raise serializers.ValidationError("Each variant must be an object")

            required_fields = ['sku', 'attributes']
            for field in required_fields:
                if field not in variant:
                    raise serializers.ValidationError(f"Variant missing required field: {field}")

            # Check duplicate SKUs
            if variant['sku'] in skus:
                raise serializers.ValidationError(f"Duplicate variant SKU: {variant['sku']}")
            skus.append(variant['sku'])

            # Check if SKU already exists
            if ProductVariant.objects.filter(sku=variant['sku']).exists():
                raise serializers.ValidationError(f"Variant SKU already exists: {variant['sku']}")

        return value


class ProductResponseSerializer(serializers.ModelSerializer):
    """Response serializer for created product"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageResponseSerializer(many=True, read_only=True)
    variants = ProductVariantResponseSerializer(many=True, read_only=True)
    taxes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'short_description',
            'category', 'brand', 'sku', 'price', 'compare_price', 'cost_price',
            'stock_quantity', 'low_stock_threshold', 'track_inventory', 'allow_backorder',
            'weight', 'length', 'width', 'height',
            'meta_title', 'meta_description', 'status', 'is_featured', 'is_digital',
            'images', 'variants', 'taxes'
        ]

    def get_taxes(self, obj):
        return [{'id': tax.tax_rate.id, 'name': tax.tax_rate.name, 'rate': tax.tax_rate.rate}
                for tax in obj.taxes.select_related('tax_rate').all()]


class ListOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    product_variant = serializers.SerializerMethodField()

    def get_product(self, obj):
        return ({
            'id': obj.product.id,
            'name': obj.product.name,
            'short_description': obj.product.short_description,
            'image': obj.product.primary_image_url,
            'price': obj.product.price,

        })

    def get_product_variant(self, obj):
        if obj.product_variant:
            return ({
                'id': obj.product_variant.id,
                'sku': obj.product_variant.name
            })
        return None

    class Meta:
        model = OrderItem
        fields = '__all__'