from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from utils.admin import CustomModelAdminMixin
from web.resources import *


# Register your models here.


@admin.register(BlogCategory)
class UserAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = BlogCategoryResource
    search_fields = ['id', 'name']
    raw_id_fields = ('parent', )
    list_filter = ('status', )


@admin.register(BlogTag)
class BlogTagAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = BlogTagResource
    search_fields = ['id', 'name']
    list_filter = ('status', )


@admin.register(BlogPost)
class BlogPostAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = BlogPostResource
    search_fields = ['id', 'title']
    raw_id_fields = ('author', 'category', 'tags')
    list_filter = ('status', )


@admin.register(BlogComment)
class BlogCommentAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = BlogCommentResource
    search_fields = ['id', 'guest_name', 'guest_email']
    raw_id_fields = ('post', 'parent', 'user')
    list_filter = ('status', )


@admin.register(BlogPostView)
class BlogPostViewAdmin(CustomModelAdminMixin, ImportExportModelAdmin):
    resource_class = BlogPostViewResource
    search_fields = ['id', 'session_key']
    raw_id_fields = ('post', 'user')
    list_filter = ('status', )