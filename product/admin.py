from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from product.resources import *
from utils.admin import CustomModelAdminMixin


# Register your models here.


@admin.register(Category)
class CategoryAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = CategoryResource
    search_fields = ['id', 'name']
    raw_id_fields = ('parent', )
    list_filter = ('status', )


@admin.register(SubCategory)
class SubCategoryAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = SubCategoryResource
    search_fields = ['id', 'name']
    raw_id_fields = ('category', )
    list_filter = ('status', )


@admin.register(Brand)
class BrandAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = BrandResource
    search_fields = ['id', 'name']
    list_filter = ('status', )


@admin.register(Product)
class ProductAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductResource
    search_fields = ['id', 'name']
    raw_id_fields = ('sub_category', 'brand')
    list_filter = ('status', )


@admin.register(ProductImage)
class ProductImageAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductImageResource
    search_fields = ['id', 'product', 'product__id']
    raw_id_fields = ('product', )
    list_filter = ('status', )


@admin.register(ProductAttribute)
class ProductAttributeAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductAttributeResource
    search_fields = ['id', 'name']
    list_filter = ('status', )


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductAttributeValueResource
    search_fields = ['id', 'value']
    raw_id_fields = ('attribute', )
    list_filter = ('status', )


@admin.register(ProductVariant)
class ProductVariantAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductVariantResource
    search_fields = ['id', 'product', 'product__id', 'sku', 'price']
    raw_id_fields = ('product', )
    list_filter = ('status', )


@admin.register(ProductVariantAttribute)
class ProductVariantAttributeAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductVariantAttributeResource
    search_fields = ['id', 'name']
    raw_id_fields = ('variant', 'attribute', 'value')
    list_filter = ('status', )


@admin.register(Cart)
class CartAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = CartResource
    search_fields = ['id', ]
    raw_id_fields = ('user', )
    list_filter = ('status', )


@admin.register(CartItem)
class CartItemAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = CartItemResource
    search_fields = ['id', ]
    raw_id_fields = ('cart', 'product', 'product_variant')
    list_filter = ('status', )


@admin.register(Wishlist)
class WishlistAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = WishlistResource
    search_fields = ['id', ]
    raw_id_fields = ('user', 'product')
    list_filter = ('status', )


@admin.register(Coupon)
class CouponAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = CouponResource
    search_fields = ['id', 'name', 'code']
    list_filter = ('status', )


@admin.register(Order)
class OrderAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = OrderResource
    search_fields = ['id', 'order_number', 'order_status']
    raw_id_fields = ('user', 'coupon')
    list_filter = ('status', 'order_status')


@admin.register(OrderItem)
class OrderItemAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = OrderItemResource
    search_fields = ['id', 'product_name']
    raw_id_fields = ('order', 'product', 'product_variant')
    list_filter = ('status', )


@admin.register(Payment)
class PaymentAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = PaymentResource
    search_fields = ['id', 'transaction_id', 'gateway_transaction_id']
    raw_id_fields = ('order', )
    list_filter = ('status', )


@admin.register(ShippingMethod)
class ShippingMethodAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ShippingMethodResource
    search_fields = ['id', 'name']
    list_filter = ('status', )


@admin.register(Shipment)
class ShipmentAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ShipmentResource
    search_fields = ['id', 'tracking_number']
    raw_id_fields = ('order', 'shipping_method')
    list_filter = ('status', )


@admin.register(Review)
class ReviewAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ReviewResource
    search_fields = ['id', 'title']

    list_filter = ('status', 'rating')


@admin.register(ProductView)
class ProductViewAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductViewResource
    search_fields = ['id', 'name']
    list_filter = ('status', )


@admin.register(Return)
class ReturnAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ReturnResource
    search_fields = ['id', 'return_number']
    raw_id_fields = ('user', 'order_item')
    list_filter = ('status', )


@admin.register(StockMovement)
class StockMovementAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = StockMovementResource
    search_fields = ['id', 'movement_type']
    raw_id_fields = ('product', 'product_variant')
    list_filter = ('status', )


@admin.register(FlashSale)
class FlashSaleAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = FlashSaleResource
    search_fields = ['id', 'name', 'max_discount_percentage']
    list_filter = ('status', )


@admin.register(FlashSaleItem)
class FlashSaleItemAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = FlashSaleItemResource
    search_fields = ['id', 'product__id']
    raw_id_fields = ('flash_sale', 'product')
    list_filter = ('status', )


@admin.register(ProductRecommendation)
class ProductRecommendationAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductRecommendationResource
    search_fields = ['id', 'product__id']
    raw_id_fields = ('user', 'product', 'recommended_product')
    list_filter = ('status', )


@admin.register(ProductFAQ)
class ProductFAQAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductFAQResource
    search_fields = ['id', 'product__id']
    raw_id_fields = ('product', 'category')
    list_filter = ('status', )


@admin.register(ProductTax)
class ProductTaxAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ProductTaxResource
    search_fields = ['id', 'product__id']
    raw_id_fields = ('product', 'tax_rate')
    list_filter = ('status', )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = OrderStatusHistoryResource
    search_fields = ['id', 'notes']
    raw_id_fields = ('order', )
    list_filter = ('status', )


@admin.register(Banner)
class BannerAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = BannerResource
    search_fields = ['id', 'title']
    list_filter = ('status', )
