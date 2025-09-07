from django.contrib import admin

# Register your models here.

EXCLUDE_FOR_API = ('date_created', 'date_updated')


class CustomModelAdminMixin(object):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name not in EXCLUDE_FOR_API]
        super(CustomModelAdminMixin, self).__init__(model, admin_site)