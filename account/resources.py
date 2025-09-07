from import_export import resources

from account.models import *

EXCLUDE_FOR_API = ('date_created', 'date_updated')


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class AddressResource(resources.ModelResource):
    class Meta:
        model = Address
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class SearchQueryResource(resources.ModelResource):
    class Meta:
        model = SearchQuery
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ComplaintResource(resources.ModelResource):
    class Meta:
        model = Complaint
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class ComplaintUpdateResource(resources.ModelResource):
    class Meta:
        model = ComplaintUpdate
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class AdminActivityLogResource(resources.ModelResource):
    class Meta:
        model = AdminActivityLog
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class StateResource(resources.ModelResource):
    class Meta:
        model = State
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class CityResource(resources.ModelResource):
    class Meta:
        model = City
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class CountryResource(resources.ModelResource):
    class Meta:
        model = Country
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API