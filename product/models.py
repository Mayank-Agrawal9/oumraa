from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from account.models import User
from oumraa.space_manager import DigitalOceanSpacesManager
from product.choicees import *
from utils.models import ModelMixin, TaxRate


# Create your models here.


class Category(ModelMixin):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.URLField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent'])
        ]


class SubCategory(ModelMixin):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sub_categories')
    image = models.URLField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'sub categories'
        verbose_name_plural = 'Sub Categories'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category'])
        ]


class Brand(ModelMixin):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    logo = models.URLField(null=True, blank=True)

    class Meta:
        db_table = 'brands'
        indexes = [
            models.Index(fields=['slug'])
        ]


class Product(ModelMixin):
    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True)
    description = models.TextField()
    short_description = models.TextField(max_length=500, null=True, blank=True)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.PROTECT, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products', null=True, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    low_stock_threshold = models.IntegerField(default=10)
    track_inventory = models.BooleanField(default=True)
    allow_backorder = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['sub_category']),
            models.Index(fields=['brand']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['price']),
        ]

    @property
    def primary_image(self):
        """Get primary product image"""
        return self.images.filter(is_primary=True).first()

    @property
    def primary_image_url(self):
        """Get primary image URL (medium size)"""
        primary = self.primary_image
        return primary.medium_url if primary else '/static/public/images/no-image.png'

    @property
    def image_gallery(self):
        """Get ordered image gallery"""
        return self.images.all().order_by('sort_order', 'created_at')

    def get_image_urls(self, size='medium'):
        """Get all image URLs of specified size"""
        size_attr = f'{size}_url'
        return [getattr(img, size_attr) for img in self.images.all()]


class ProductImage(ModelMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    thumbnail_url = models.URLField(max_length=1000)
    medium_url = models.URLField(max_length=1000)
    large_url = models.URLField(max_length=1000)
    original_url = models.URLField(max_length=1000)
    thumbnail_key = models.CharField(max_length=500)
    medium_key = models.CharField(max_length=500)
    large_key = models.CharField(max_length=500)
    original_key = models.CharField(max_length=500)
    file_id = models.CharField(max_length=100, db_index=True)
    original_filename = models.CharField(max_length=255)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    original_width = models.IntegerField(null=True)
    original_height = models.IntegerField(null=True)
    file_size_bytes = models.IntegerField(null=True)

    class Meta:
        db_table = 'product_images'
        indexes = [
            models.Index(fields=['product', 'is_primary']),
            models.Index(fields=['product', 'sort_order']),
            models.Index(fields=['file_id'])
        ]

    def __str__(self):
        return f"Image for {self.product.name} ({'Primary' if self.is_primary else 'Secondary'})"

    @property
    def image_url(self):
        """Default image URL (medium size for general use)"""
        return self.medium_url

    @property
    def responsive_srcset(self):
        """Generate srcset for responsive images"""
        return f"{self.thumbnail_url} 300w, {self.medium_url} 600w, {self.large_url} 1200w"

    def get_size_variants(self):
        """Get all size variants as dictionary"""
        return {
            'thumbnail': {
                'url': self.thumbnail_url,
                'width': 300,
                'height': 300,
                'use': 'Product listings, thumbnails'
            },
            'medium': {
                'url': self.medium_url,
                'width': 600,
                'height': 600,
                'use': 'Product cards, quick view'
            },
            'large': {
                'url': self.large_url,
                'width': 1200,
                'height': 1200,
                'use': 'Product detail, zoom'
            },
            'original': {
                'url': self.original_url,
                'width': self.original_width,
                'height': self.original_height,
                'use': 'Full resolution, download'
            }
        }

    def delete(self, *args, **kwargs):
        """Override delete to clean up DO Spaces storage"""
        keys_to_delete = [
            self.thumbnail_key,
            self.medium_key,
            self.large_key,
            self.original_key
        ]

        # Delete from Digital Ocean Spaces
        do_manager = DigitalOceanSpacesManager()
        do_manager.delete_image_variants(keys_to_delete)
        super().delete(*args, **kwargs)

    def make_primary(self):
        """Make this image the primary image for the product"""
        ProductImage.objects.filter(product=self.product).update(is_primary=False)
        self.is_primary = True
        self.save(update_fields=['is_primary'])

    @classmethod
    def reorder_images(cls, product, image_order_list):
        """Reorder images for a product
        Args:
            product: Product instance
            image_order_list: List of {'id': image_id, 'sort_order': order}
        """
        for item in image_order_list:
            try:
                image = cls.objects.get(id=item['id'], product=product)
                image.sort_order = item['sort_order']
                image.save(update_fields=['sort_order'])
            except cls.DoesNotExist:
                continue


class ProductAttribute(ModelMixin):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    is_required = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_attributes'
        unique_together = ['name', 'slug']


class ProductAttributeValue(ModelMixin):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=255)

    class Meta:
        db_table = 'product_attribute_values'
        unique_together = ['attribute', 'value']


class ProductVariant(ModelMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_variants'
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['sku']),
        ]


class ProductVariantAttribute(ModelMixin):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    value = models.ForeignKey(ProductAttributeValue, on_delete=models.CASCADE)

    class Meta:
        db_table = 'product_variant_attributes'
        unique_together = ['variant', 'attribute']


class Cart(ModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'carts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]


class CartItem(ModelMixin):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'product', 'product_variant']
        indexes = [
            models.Index(fields=['cart']),
        ]


class Wishlist(ModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        db_table = 'wishlists'
        unique_together = ['user', 'product']
        indexes = [
            models.Index(fields=['user']),
        ]


class Coupon(ModelMixin):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    class Meta:
        db_table = 'coupons'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['valid_from', 'valid_until'])
        ]


class Order(ModelMixin):
    order_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')

    # Order Status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Address Information
    billing_address = models.JSONField()
    shipping_address = models.JSONField()

    # Additional Info
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    # Timestamps
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
        ]


class OrderItem(ModelMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    product_name = models.CharField(max_length=500)
    product_sku = models.CharField(max_length=100)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'
        indexes = [
            models.Index(fields=['order']),
        ]


class Payment(ModelMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=ORDER_PAYMENT_STATUS)
    payment_gateway = models.CharField(max_length=100, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, unique=True)
    gateway_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    gateway_response = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]


class ShippingMethod(ModelMixin):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.IntegerField()

    class Meta:
        db_table = 'shipping_methods'


class Shipment(ModelMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='shipments')
    tracking_number = models.CharField(max_length=255, unique=True)
    carrier = models.CharField(max_length=100)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=SHIPMENT_STATUS, default='pending')
    shipped_at = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'shipments'
        indexes = [
            models.Index(fields=['tracking_number']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]


class Review(ModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255, null=True, blank=True)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    helpful_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'reviews'
        unique_together = ['user', 'product', 'order_item']
        indexes = [
            models.Index(fields=['product', 'is_approved']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
        ]


class ProductView(ModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    class Meta:
        db_table = 'product_views'
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['user']),
        ]


class Return(ModelMixin):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='returns')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    return_number = models.CharField(max_length=50, unique=True)
    reason = models.CharField(max_length=20, choices=RETURN_REASON)
    description = models.TextField()
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=RETURN_STATUS, default='requested')
    admin_notes = models.TextField(null=True, blank=True)
    images = models.JSONField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'returns'
        indexes = [
            models.Index(fields=['return_number']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]


class StockMovement(ModelMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE)
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    reference_id = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'stock_movements'
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['reference_id']),
        ]


class FlashSale(ModelMixin):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'flash_sales'
        indexes = [
            models.Index(fields=['start_time', 'end_time'])
        ]


class FlashSaleItem(ModelMixin):
    flash_sale = models.ForeignKey(FlashSale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_limit = models.IntegerField(null=True, blank=True)
    sold_quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'flash_sale_items'
        unique_together = ['flash_sale', 'product']
        indexes = [
            models.Index(fields=['flash_sale']),
        ]


class ProductRecommendation(ModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='base_recommendations')
    recommended_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE)
    score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000)  # Recommendation confidence

    class Meta:
        db_table = 'product_recommendations'
        unique_together = ['user', 'product', 'recommended_product', 'recommendation_type']
        indexes = [
            models.Index(fields=['product', 'recommendation_type']),
            models.Index(fields=['user', 'recommendation_type']),
            models.Index(fields=['score']),
        ]


class ProductFAQ(ModelMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='faqs', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='faqs', null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'faqs'
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['category']),
        ]


class ProductTax(ModelMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='taxes')
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.CASCADE)

    class Meta:
        db_table = 'product_taxes'
        unique_together = ['product', 'tax_rate']


class OrderStatusHistory(ModelMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    order_status = models.CharField(max_length=20, null=True)
    notes = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'order_status_history'
        indexes = [
            models.Index(fields=['order']),
        ]