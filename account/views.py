from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from account.helpers import get_client_ip, get_tokens_for_user
from account.serializer import *
from utils.base_viewset import BaseViewSetSetup


# Create your views here.

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=['last_login_ip'])
            tokens = get_tokens_for_user(user)

            return Response({
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.last_login = timezone.now()
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=['last_login', 'last_login_ip'])
            tokens = get_tokens_for_user(user)

            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserLogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    'message': 'Successfully logged out'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Something went wrong'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(BaseViewSetSetup):
    serializer_classes = {
        'list': UserSerializer,
        'retrieve': UserSerializer,
        'update': UserUpdateSerializer,
        'partial_update': UserUpdateSerializer,
    }
    default_serializer_class = UserSerializer
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }

    def get_queryset(self):
        return User.user_type.filter(id=self.request.user.id)


class UpdateUserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressViewSet(BaseViewSetSetup):
    serializer_classes = {
        'create': CreateAddressSerializer,
        'list': ListAddressSerializer,
        'retrieve': ListAddressSerializer,
    }
    default_serializer_class = AddressSerializer
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }

    def get_queryset(self):
        return Address.active_objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CityViewSet(BaseViewSetSetup):
    default_serializer_class = CitySerializer
    queryset = City.active_objects.all()
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }


class StateViewSet(BaseViewSetSetup):
    default_serializer_class = StateSerializer
    queryset = State.active_objects.all()
    enable_standard_response = {
        'create': True,
        'update': True
    }
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }