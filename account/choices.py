
USER_TYPES = (
    ('customer', 'Customer'),
    ('admin', 'Admin'),
    ('support', 'Support'),
)
GENDER_TYPES = (
    ('male', 'Male'),
    ('female', 'Female'),
)

ADDRESS_TYPES = (
    ('home', 'Home'),
    ('work', 'Work')
)

COMPLAINT_TYPES = (
    ('product_quality', 'Product Quality Issue'),
    ('delivery_delay', 'Delivery Delay'),
    ('wrong_product', 'Wrong Product Received'),
    ('damaged_product', 'Damaged Product'),
    ('poor_service', 'Poor Customer Service'),
    ('billing_issue', 'Billing/Payment Issue'),
    ('website_bug', 'Website/App Bug'),
    ('refund_delay', 'Refund Delay'),
    ('other', 'Other'),
)

PRIORITY_LEVELS = (
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('urgent', 'Urgent'),
)

COMPLAINT_STATUS = (
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('pending_customer', 'Pending Customer Response'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed'),
    ('escalated', 'Escalated'),
)

UPDATE_TYPES = (
    ('customer_response', 'Customer Response'),
    ('admin_response', 'Admin Response'),
    ('status_change', 'Status Change'),
    ('assignment_change', 'Assignment Change'),
    ('system_update', 'System Update'),
)

ACTION_TYPES = (
    ('create', 'Create'),
    ('update', 'Update'),
    ('delete', 'Delete'),
    ('login', 'Login'),
    ('logout', 'Logout'),
    ('export', 'Export'),
    ('bulk_action', 'Bulk Action'),
)