import uuid

from django.db import models

from utils.choices import STATUS_TYPE


class ActiveQuerySet(models.QuerySet):
    """Custom QuerySet that provides methods for filtering by status"""

    def active(self):
        """Return only active records"""
        return self.filter(status='active')

    def inactive(self):
        """Return only inactive records"""
        return self.filter(status='inactive')

    def deleted(self):
        """Return only deleted records (soft deleted)"""
        return self.filter(status='deleted')

    def draft(self):
        """Return only draft records"""
        return self.filter(status='draft')

    def pending(self):
        """Return only pending records"""
        return self.filter(status='pending')

    def exclude_deleted(self):
        """Exclude soft deleted records"""
        return self.exclude(status='deleted')


# Custom Manager that uses the ActiveQuerySet
class ActiveManager(models.Manager):
    """
    Custom manager that automatically filters out deleted records
    and provides easy access to active records
    """

    def get_queryset(self):
        """Override default queryset to exclude deleted records by default"""
        return ActiveQuerySet(self.model, using=self._db).exclude_deleted()

    def active(self):
        """Return only active records"""
        return self.get_queryset().active()

    def inactive(self):
        """Return only inactive records"""
        return self.get_queryset().inactive()

    def with_deleted(self):
        """Return all records including deleted ones"""
        return ActiveQuerySet(self.model, using=self._db)

    def deleted_only(self):
        """Return only deleted records"""
        return ActiveQuerySet(self.model, using=self._db).deleted()


# Alternative Manager that filters only active records by default
class ActiveOnlyManager(models.Manager):
    """
    Manager that returns only active records by default
    Use this when you want most queries to return only active records
    """

    def get_queryset(self):
        """Override default queryset to return only active records"""
        return ActiveQuerySet(self.model, using=self._db).active()

    def all_statuses(self):
        """Return records with all statuses"""
        return ActiveQuerySet(self.model, using=self._db)

    def with_inactive(self):
        """Return active and inactive records (exclude only deleted)"""
        return ActiveQuerySet(self.model, using=self._db).exclude_deleted()


class ModelMixin(models.Model):
    """
    This mixin provides default fields and functionality for all models
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, default='active', choices=STATUS_TYPE,
                              help_text='Status of the record', db_index=True
    )

    # Custom managers
    objects = ActiveManager()
    active_objects = ActiveOnlyManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['status', 'updated_on']),
        ]

    def soft_delete(self):
        """Soft delete the record by setting status to deleted"""
        self.status = 'deleted'
        self.save(update_fields=['status', 'updated_on'])

    def restore(self):
        """Restore a soft deleted record"""
        self.status = 'active'
        self.save(update_fields=['status', 'updated_on'])

    def activate(self):
        """Set status to active"""
        self.status = 'active'
        self.save(update_fields=['status', 'updated_on'])

    def deactivate(self):
        """Set status to inactive"""
        self.status = 'inactive'
        self.save(update_fields=['status', 'updated_on'])

    @property
    def is_active(self):
        """Check if record is active"""
        return self.status == 'active'

    @property
    def is_deleted(self):
        """Check if record is soft deleted"""
        return self.status == 'deleted'

    @property
    def is_inactive(self):
        """Check if record is inactive"""
        return self.status == 'inactive'


class Country(ModelMixin):
    name = models.CharField(max_length=250, db_index=True)
    phone_code = models.CharField(max_length=10)
    capital = models.CharField(max_length=250)
    currency = models.CharField(max_length=100)
    currency_name = models.CharField(max_length=250)
    time_zone = models.CharField(max_length=250)

    class Meta:
        db_table = 'country'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['currency', 'currency_name']),
        ]


class State(ModelMixin):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='state_country', null=True)
    name = models.CharField(max_length=250)

    class Meta:
        db_table = 'state'
        indexes = [
            models.Index(fields=['name']),
        ]


class City(ModelMixin):
    name = models.CharField(max_length=250)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='district_state')
    latitude = models.CharField(max_length=50, null=True, blank=True)
    longitude = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'district'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['latitude', 'longitude']),
        ]


class Banner(ModelMixin):
    BANNER_TYPES = (
        ('hero', 'Hero Banner'),
        ('promotional', 'Promotional Banner'),
        ('category', 'Category Banner'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPES)
    image_url = models.URLField()
    link_url = models.URLField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'banners'
        indexes = [
            models.Index(fields=['banner_type', 'status']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]


class EmailTemplate(ModelMixin):
    TEMPLATE_TYPE = (
        ('order_confirmation', 'Order Confirmation'),
        ('payment_success', 'Payment Success'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('password_reset', 'Password Reset'),
        ('welcome', 'Welcome Email'),
        ('newsletter', 'Newsletter'),
    )

    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE, unique=True)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    text_content = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'email_templates'


class TaxRate(ModelMixin):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_inclusive = models.BooleanField(default=False)

    class Meta:
        db_table = 'tax_rates'
