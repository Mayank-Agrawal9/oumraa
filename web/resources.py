from import_export import resources

from web.models import *

EXCLUDE_FOR_API = ('date_created', 'date_updated')


class BlogCategoryResource(resources.ModelResource):
    class Meta:
        model = BlogCategory
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class BlogTagResource(resources.ModelResource):
    class Meta:
        model = BlogTag
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class BlogPostResource(resources.ModelResource):
    class Meta:
        model = BlogPost
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class BlogCommentResource(resources.ModelResource):
    class Meta:
        model = BlogComment
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API


class BlogPostViewResource(resources.ModelResource):
    class Meta:
        model = BlogPostView
        import_id_fields = ('id',)
        exclude = EXCLUDE_FOR_API