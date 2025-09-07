from django.urls import path

from web.views import *

urlpatterns = [
    path('category/', GetCategoryView.as_view(), name='get-category'),
    path('product/', GetProductView.as_view(), name='get-product'),
    path('product/<str:id>/', GetProductDetailView.as_view(), name='get-product-details'),
    path('blogs/', GetBlogsView.as_view(), name='get-blog'),
    path('blog/<str:id>/', GetBlogDetailView.as_view(), name='get-blog-details'),
]
