from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from account.resources import *
from utils.admin import CustomModelAdminMixin


# Register your models here.


@admin.register(User)
class UserAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = UserResource
    search_fields = ['id', 'phone_number']
    list_filter = ('status', )


@admin.register(Address)
class AddressAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = AddressResource
    search_fields = ['id', 'address_type', 'full_name']
    raw_id_fields = ('user', 'city', 'state')
    list_filter = ('status', )


@admin.register(SearchQuery)
class SearchQueryAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = SearchQueryResource
    search_fields = ['id', 'query']
    raw_id_fields = ('user', )
    list_filter = ('status', )


@admin.register(Complaint)
class ComplaintAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ComplaintResource
    search_fields = ['id', 'complaint_number']
    raw_id_fields = ('user', 'assigned_to', 'resolved_by')
    list_filter = ('status', )


@admin.register(ComplaintUpdate)
class ComplaintUpdateAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ComplaintUpdateResource
    search_fields = ['id', 'complaint_number']
    raw_id_fields = ('complaint', 'created_by')
    list_filter = ('status', )


@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = AdminActivityLogResource
    search_fields = ['id', 'action_type']
    raw_id_fields = ('user', )
    list_filter = ('status', )


@admin.register(City)
class CityLogAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = CityResource
    search_fields = ['id', 'name']
    raw_id_fields = ('state', )
    list_filter = ('status', )


@admin.register(State)
class StateLogAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = StateResource
    search_fields = ['id', 'name']
    raw_id_fields = ('country', )
    list_filter = ('status', )


@admin.register(Country)
class CountryAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = CountryResource
    search_fields = ['id', 'name']
    list_filter = ('status', )


@admin.register(ContactUs)
class ContactUsAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = ContactUsResource
    search_fields = ['id', 'name', 'email', 'phone_number']
    list_filter = ('status', )


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = NewsletterSubscriberResource
    search_fields = ['id', 'email']


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = NewsletterCampaignResource
    search_fields = ['id', 'subject']