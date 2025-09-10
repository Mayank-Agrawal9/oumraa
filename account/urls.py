from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from account.views import *

router = routers.DefaultRouter()
router.register(r'address', AddressViewSet, basename='address')
router.register(r'state', StateViewSet, basename='state')
router.register(r'city', CityViewSet, basename='city')
router.register(r'user', UserViewSet, basename='user')


urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('update-profile/', UpdateUserProfileView.as_view(), name='update-profile'),
    path('change-password/', PasswordChangeAPI.as_view(), name='password-change'),
    path('forgot-password/', ForgotPasswordChangeAPI.as_view(), name='forgot-password'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]