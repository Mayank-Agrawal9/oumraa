from decimal import Decimal

from django.db import transaction

from product.models import CartItem, Cart


class CartManager:
    """Utility class to manage cart operations for both authenticated and guest users"""

    @staticmethod
    def get_or_create_cart(request):
        """Get or create cart for both authenticated and guest users"""
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                user=request.user, status='active', defaults={'status': 'active'}
            )
            return cart, created
        else:
            if not request.session.session_key:
                request.session.create()

            session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(
                session_key=session_key, user=None, status='active', defaults={'status': 'active'}
            )
            return cart, created

    @staticmethod
    def get_cart(request):
        """Get existing cart for user/session"""
        if request.user.is_authenticated:
            return Cart.objects.filter(
                user=request.user, status='active'
            ).first()
        else:
            if not request.session.session_key:
                return None
            return Cart.objects.filter(
                session_key=request.session.session_key, user=None, status='active'
            ).first()

    @staticmethod
    def merge_guest_cart_to_user(request, user):
        """Merge guest cart with user cart when user logs in"""
        if not request.session.session_key:
            return

        guest_cart = Cart.objects.filter(
            session_key=request.session.session_key, user=None, status='active'
        ).first()

        if not guest_cart or not guest_cart.items.exists():
            return

        # Get or create user cart
        user_cart, _ = Cart.objects.get_or_create(
            user=user, status='active', defaults={'status': 'active'}
        )

        # Merge cart items
        with transaction.atomic():
            for guest_item in guest_cart.items.all():
                try:
                    # Check if item already exists in user cart
                    user_item = user_cart.items.get(
                        product=guest_item.product,
                        product_variant=guest_item.product_variant
                    )
                    # Update quantity
                    user_item.quantity += guest_item.quantity
                    user_item.save()
                except CartItem.DoesNotExist:
                    # Create new item in user cart
                    CartItem.objects.create(
                        cart=user_cart,
                        product=guest_item.product,
                        product_variant=guest_item.product_variant,
                        quantity=guest_item.quantity,
                        unit_price=guest_item.unit_price
                    )

            # Mark guest cart as merged
            guest_cart.status = 'inactive'  # Using your status field
            guest_cart.save()

    @staticmethod
    def calculate_cart_totals(cart):
        """Calculate cart totals"""
        items = cart.items.select_related('product', 'product_variant')

        subtotal = Decimal('0.00')
        total_items = 0

        for item in items:
            item_total = item.unit_price * item.quantity
            subtotal += item_total
            total_items += item.quantity

        # You can add tax calculation, shipping, discounts here
        tax_amount = Decimal('0.00')  # Implement tax calculation
        shipping_amount = Decimal('0.00')  # Implement shipping calculation
        discount_amount = Decimal('0.00')  # Implement discount calculation

        total = subtotal + tax_amount + shipping_amount - discount_amount

        return {
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'shipping_amount': shipping_amount,
            'discount_amount': discount_amount,
            'total': total,
            'total_items': total_items
        }
