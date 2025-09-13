from django.db.models import Q
from google.oauth2 import id_token
from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from account.helpers import get_client_ip, get_tokens_for_user
from account.serializer import *
from oumraa import settings
from utils.base_viewset import BaseViewSetSetup
from account.tasks import send_contact_email_task, send_newsletter_joining_mail, send_instant_email
from google.auth.transport import requests


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
            send_instant_email.delay(subject="Thank You for registration", email_to=user.email,
                                     template='emails/registration.html',
                                     context={'name': user.get_full_name(), 'email': user.email})

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


class PasswordChangeAPI(APIView):
    '''When user is register then it will be able to change the password.'''
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")
        if not password and confirm_password:
            return Response({'error': 'Password and confirm password should be mandatory.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if password != confirm_password:
            return Response({'error': 'Invalid Password! Password does not match.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(pk=self.request.user.id)
        user.set_password(password)
        user.save()
        return Response({'status': True, 'message': 'Password changed successfully! '},
                        status=status.HTTP_200_OK)


class ForgotPasswordChangeAPI(APIView):
    '''When user is register then it will be able to change the password.'''

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")
        if not password and confirm_password and username:
            return Response({'error': 'Password and confirm password and username should be mandatory.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if password != confirm_password:
            return Response({'error': 'Invalid Password! Password does not match.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(Q(username=username) | Q(email=username)).last()
        if not user:
            return Response({'status': False, 'message': 'There is no user register with this email.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        return Response({'status': True, 'message': 'Password changed successfully! '},
                        status=status.HTTP_200_OK)


class TestAPIView(APIView):
    def post(self, request):
        # send_newsletter()
        return Response({'status': True, 'message': 'Password changed successfully! '},
                        status=status.HTTP_200_OK)


class ContactUsAPIView(APIView):
    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.save()
            send_contact_email_task.delay(
                contact.name, contact.email, contact.phone_number, contact.subject, contact.message
            )
            return Response(
                {"message": "Your request has been submitted successfully."}, status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewsLetterAPIView(APIView):
    def post(self, request):
        serializer = NewsletterSubscriberSerializer(data=request.data)
        if serializer.is_valid():
            newsletter = serializer.save()
            send_newsletter_joining_mail.delay(newsletter.email)
            return Response(
                {"message": "Thank you for subscribing to our newsletter."}, status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
        except Exception as e:
            return Response({"error": "Invalid token", "details": str(e)}, status=400)

        email = idinfo.get("email")
        first_name = idinfo.get("given_name", "")
        last_name = idinfo.get("family_name", "")
        picture = idinfo.get("picture", "")

        user = User.objects.filter(username=email).first()

        if not user:
            serializer = UserGoogleRegistrationSerializer(
                data={
                    "username": email, "email": email,
                    "first_name": first_name, "last_name": last_name,
                    "profile_image": picture,
                },
                context={"social_login": True}
            )
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

        tokens = get_tokens_for_user(user)

        return Response({
            "message": "User logged in with Google", "user": UserProfileSerializer(user).data,
            "tokens": tokens
        })
