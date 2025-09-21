from import_export import resources

from product.models import *

EXCLUDE_FOR_API = ('date_created', 'date_updated')


class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class SubCategoryResource(resources.ModelResource):
    class Meta:
        model = SubCategory
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class BrandResource(resources.ModelResource):
    class Meta:
        model = Brand
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductImageResource(resources.ModelResource):
    class Meta:
        model = ProductImage
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductAttributeResource(resources.ModelResource):
    class Meta:
        model = ProductAttribute
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductAttributeValueResource(resources.ModelResource):
    class Meta:
        model = ProductAttributeValue
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductVariantResource(resources.ModelResource):
    class Meta:
        model = ProductVariant
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductVariantAttributeResource(resources.ModelResource):
    class Meta:
        model = ProductVariantAttribute
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class CartResource(resources.ModelResource):
    class Meta:
        model = Cart
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class CartItemResource(resources.ModelResource):
    class Meta:
        model = CartItem
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class WishlistResource(resources.ModelResource):
    class Meta:
        model = Wishlist
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class CouponResource(resources.ModelResource):
    class Meta:
        model = Coupon
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class OrderItemResource(resources.ModelResource):
    class Meta:
        model = OrderItem
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class PaymentResource(resources.ModelResource):
    class Meta:
        model = Payment
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ShippingMethodResource(resources.ModelResource):
    class Meta:
        model = ShippingMethod
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ShipmentResource(resources.ModelResource):
    class Meta:
        model = Shipment
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ReviewResource(resources.ModelResource):
    class Meta:
        model = Review
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductViewResource(resources.ModelResource):
    class Meta:
        model = ProductView
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ReturnResource(resources.ModelResource):
    class Meta:
        model = Return
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class StockMovementResource(resources.ModelResource):
    class Meta:
        model = StockMovement
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class FlashSaleResource(resources.ModelResource):
    class Meta:
        model = FlashSale
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class FlashSaleItemResource(resources.ModelResource):
    class Meta:
        model = FlashSaleItem
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductRecommendationResource(resources.ModelResource):
    class Meta:
        model = FlashSaleItem
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductFAQResource(resources.ModelResource):
    class Meta:
        model = ProductFAQ
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ProductTaxResource(resources.ModelResource):
    class Meta:
        model = ProductTax
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class OrderStatusHistoryResource(resources.ModelResource):
    class Meta:
        model = OrderStatusHistory
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class BannerResource(resources.ModelResource):
    class Meta:
        model = Banner
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API