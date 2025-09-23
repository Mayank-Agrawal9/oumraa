from django.urls import path

from web.views import *

urlpatterns = [
    path('category/', GetCategoryView.as_view(), name='get-category'),
    path('blog-category/', GetBlogCategoryView.as_view(), name='get-blog-category'),
    path('product/', GetProductView.as_view(), name='get-product'),
    path('product/<str:id>/', GetProductDetailView.as_view(), name='get-product-details'),
    path('product-faq/<str:id>/', GetProductFaqView.as_view(), name='get-product-faq'),
    path('blogs/', GetBlogsView.as_view(), name='get-blog'),
    path('blog/<str:id>/', GetBlogDetailView.as_view(), name='get-blog-details'),
    path('cart-summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('add-to-cart/', AddToCartView.as_view(), name='Add-to-cart'),
    path('update-to-cart/<str:id>/', UpdateToCartView.as_view(), name='update-to-cart'),
    path('remove-to-cart/<str:item_id>/', RemoveCartItemView.as_view(), name='remove-cart-item'),
    path('clear-cart/', ClearCartView.as_view(), name='clear-cart-item'),
    path('cart-summary/', CartSummeryView.as_view(), name='card-summary'),
    path('cart-summary/', MergeCartAccountView.as_view(), name='merge.card-summary'),
    path('banner-list/', GetBannerView.as_view(), name='get_homepage_banner'),
    path('sub-category/', ProductsBySubCategoryAPIView.as_view(), name='product_by_subcategory'),
    path('brands/', GetBrandAPIView.as_view(), name='get_brand'),

    path('posts/<str:post_id>/comments/', PostCommentsListView.as_view(), name='post-comments'),
    path('posts/<str:post_id>/comments/create/', CommentCreateView.as_view(), name='comment-create'),
    path('comments/<str:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('comments/<str:comment_id>/replies/', CommentRepliesListView.as_view(), name='comment-replies')
]
