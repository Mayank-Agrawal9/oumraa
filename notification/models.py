from django.contrib.auth.models import User
from django.db import models

from utils.models import ModelMixin


# Create your models here.

class Notification(ModelMixin):
    NOTIFICATION_TYPES = (
        ('order_confirmed', 'Order Confirmed'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('payment_success', 'Payment Success'),
        ('payment_failed', 'Payment Failed'),
        ('promotion', 'Promotion'),
        ('system', 'System'),
    )
    NOTIFY_TYPE = (
        ('in_app', 'In App'),
        ('app', 'App'),
        ('web', 'Website')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'is_read'])
        ]