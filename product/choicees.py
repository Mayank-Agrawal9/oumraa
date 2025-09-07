
DISCOUNT_TYPES = (
    ('percentage', 'Percentage'),
    ('fixed', 'Fixed Amount'),
    ('free_shipping', 'Free Shipping'),
)

ORDER_STATUS = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
    ('refunded', 'Refunded'),
    ('returned', 'Returned'),
)

PAYMENT_STATUS = (
    ('pending', 'Pending'),
    ('paid', 'Paid'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
    ('partial_refund', 'Partial Refund'),
)

PAYMENT_METHODS = (
    ('credit_card', 'Credit Card'),
    ('debit_card', 'Debit Card'),
    ('upi', 'UPI'),
    ('net_banking', 'Net Banking'),
    ('wallet', 'Wallet'),
    ('cod', 'Cash on Delivery'),
)

ORDER_PAYMENT_STATUS = (
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('cancelled', 'Cancelled'),
    ('refunded', 'Refunded'),
)

SHIPMENT_STATUS = (
    ('pending', 'Pending'),
    ('picked_up', 'Picked Up'),
    ('in_transit', 'In Transit'),
    ('out_for_delivery', 'Out for Delivery'),
    ('delivered', 'Delivered'),
    ('returned', 'Returned'),
    ('lost', 'Lost'),
)

RETURN_STATUS = (
    ('requested', 'Requested'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('picked_up', 'Picked Up'),
    ('received', 'Received'),
    ('refund_processed', 'Refund Processed'),
    ('completed', 'Completed'),
)

RETURN_REASON = (
    ('defective', 'Defective Product'),
    ('wrong_item', 'Wrong Item Received'),
    ('damaged', 'Damaged in Transit'),
    ('not_as_described', 'Not as Described'),
    ('changed_mind', 'Changed Mind'),
    ('size_issue', 'Size Issue'),
    ('other', 'Other'),
)

MOVEMENT_TYPE = (
    ('purchase', 'Purchase'),
    ('sale', 'Sale'),
    ('return', 'Return'),
    ('adjustment', 'Adjustment'),
    ('damaged', 'Damaged'),
    ('lost', 'Lost'),
)

RECOMMENDATION_TYPE = (
    ('similar', 'Similar Products'),
    ('frequently_bought', 'Frequently Bought Together'),
    ('recently_viewed', 'Recently Viewed'),
    ('trending', 'Trending'),
    ('personalized', 'Personalized'),
)