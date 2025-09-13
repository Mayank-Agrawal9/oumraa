# Create your models here.
from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from account.choices import *
from utils.models import ModelMixin, City, State, Country


class User(AbstractUser, ModelMixin):
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='customer')
    gender = models.CharField(max_length=20, choices=GENDER_TYPES, null=True, blank=True)
    profile_image = models.URLField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['user_type']),
        ]


class Address(ModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='home')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    alternate_phone_number = models.CharField(max_length=15, null=True, blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='cities')
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='states')
    postal_code = models.CharField(max_length=10)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'addresses'
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['postal_code']),
            models.Index(fields=['city']),
            models.Index(fields=['state']),
        ]


class SearchQuery(ModelMixin):
    query = models.CharField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    results_count = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField()

    class Meta:
        db_table = 'search_queries'
        indexes = [
            models.Index(fields=['query']),
        ]


class Complaint(ModelMixin):
    """Customer complaint management system"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    complaint_number = models.CharField(max_length=20, unique=True, blank=True)
    complaint_type = models.CharField(max_length=30, choices=COMPLAINT_TYPES)
    subject = models.CharField(max_length=255)
    description = models.TextField()

    # Priority and Status
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    complaint_status = models.CharField(max_length=20, choices=COMPLAINT_STATUS, default='open')

    # Contact Information
    contact_phone = models.CharField(max_length=15, blank=True)
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[('email', 'Email'), ('phone', 'Phone'), ('both', 'Both')],
        default='email'
    )

    # Resolution Details
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_complaints')
    resolution = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='resolved_complaints')
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Customer Satisfaction
    satisfaction_rating = models.IntegerField(
        null=True, blank=True,
        choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
        help_text='Customer satisfaction rating after resolution'
    )
    customer_feedback = models.TextField(blank=True, null=True)
    attachments = models.URLField(blank=True)

    class Meta:
        db_table = 'complaints'
        indexes = [
            models.Index(fields=['user', 'complaint_status']),
            models.Index(fields=['complaint_type', 'priority']),
            models.Index(fields=['complaint_status', 'priority']),
            models.Index(fields=['assigned_to', 'complaint_status']),
            models.Index(fields=['complaint_number']),
            models.Index(fields=['resolved_at']),
        ]

    def save(self, *args, **kwargs):
        """Auto-generate complaint number and set SLA dates"""
        if not self.complaint_number:
            self.complaint_number = self._generate_complaint_number()

        if not self.response_due_date and self.complaint_status == 'open':
            # Set response due date based on priority
            hours_map = {'urgent': 2, 'high': 8, 'medium': 24, 'low': 48}
            hours = hours_map.get(self.priority, 24)
            self.response_due_date = timezone.now() + timezone.timedelta(days=hours)

        if not self.resolved_at and self.complaint_status == 'open':
            # Set resolution due date based on priority
            days_map = {'urgent': 1, 'high': 3, 'medium': 7, 'low': 14}
            days = days_map.get(self.priority, 7)
            self.resolved_at = timezone.now() + timezone.timedelta(days=days)

        super().save(*args, **kwargs)

    def _generate_complaint_number(self):
        """Generate unique complaint number"""
        date_str = datetime.now().strftime('%Y%m%d')

        today_count = Complaint.objects.filter(
            complaint_number__startswith=f'OM{date_str}'
        ).count() + 1

        return f'OM{date_str}{today_count:04d}'

    def __str__(self):
        return f"{self.complaint_number} - {self.subject}"

    @property
    def is_overdue(self):
        """Check if complaint is overdue"""
        if self.complaint_status in ['resolved', 'closed']:
            return False
        return (
                self.resolution_due_date and
                timezone.now() > self.resolution_due_date
        )

    def assign_to(self, admin_user):
        """Assign complaint to admin"""
        self.assigned_to = admin_user
        if self.complaint_status == 'open':
            self.complaint_status = 'in_progress'
        self.save(update_fields=['assigned_to', 'complaint_status'])

    def resolve(self, admin_user, resolution_text):
        """Mark complaint as resolved"""
        self.resolution = resolution_text
        self.resolved_by = admin_user
        self.resolved_at = timezone.now()
        self.complaint_status = 'resolved'
        self.save(update_fields=['resolution', 'resolved_by', 'resolved_at', 'complaint_status'])


class ComplaintUpdate(ModelMixin):
    """Track communication and updates on complaints"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='updates')
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES)
    message = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaint_updates')

    # For status changes
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)

    # Attachments
    attachments = models.JSONField(default=list, blank=True)

    # Internal notes (not visible to customer)
    is_internal = models.BooleanField(default=False)

    class Meta:
        db_table = 'complaint_updates'
        indexes = [
            models.Index(fields=['complaint']),
            models.Index(fields=['update_type']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"Update for {self.complaint.complaint_number} - {self.update_type}"


class AdminActivityLog(ModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    class Meta:
        db_table = 'admin_activity_logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action_type']),
            models.Index(fields=['model_name']),
        ]


class ContactUs(ModelMixin):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    subject = models.CharField(max_length=255)
    message = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
            models.Index(fields=['phone_number'])
        ]


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class NewsletterCampaign(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)

    def __str__(self):
        return self.subject