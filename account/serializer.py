from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from account.models import *


class UserSerializer(serializers.Serializer):

    class meta:
        model = User
        fields = '__all__'


class CreateAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class StateSerializer(serializers.ModelSerializer):

    class Meta:
        model = State
        fields = ('id', 'name')


class CitySerializer(serializers.ModelSerializer):
    state = StateSerializer(read_only=True)

    class Meta:
        model = City
        fields = ('id', 'name', 'state')


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = '__all__'


class ListAddressSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    def get_state(self, obj):
        return {'id': obj.state.id, 'name': obj.state.name}

    def get_city(self, obj):
        return {'id': obj.city.id, 'name': obj.city.name}

    class Meta:
        model = Address
        exclude = ('user', 'created_at', 'updated_on', 'status')


class SearchQuerySerializer(serializers.Serializer):

    class meta:
        model = SearchQuery
        fields = '__all__'


class ComplaintSerializer(serializers.Serializer):

    class meta:
        model = Complaint
        fields = '__all__'


class ComplaintUpdateSerializer(serializers.Serializer):

    class meta:
        model = ComplaintUpdate
        fields = '__all__'


class AdminActivityLogSerializer(serializers.Serializer):

    class meta:
        model = AdminActivityLog
        fields = '__all__'


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'user_type', 'gender', 'profile_image'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password and password confirmation don't match.")
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserGoogleRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "username", "email", "password", "password_confirm",
            "first_name", "last_name", "phone_number",
            "date_of_birth", "user_type", "gender", "profile_image"
        ]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        if not self.context.get("social_login", False):
            if attrs.get("password") != attrs.get("password_confirm"):
                raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        social_login = self.context.get("social_login", False)
        if social_login:
            validated_data.pop("password", None)
            validated_data.pop("password_confirm", None)
            email = validated_data["email"]
            user, created = User.objects.get_or_create(
                username=email, defaults=validated_data
            )
            return user
        else:
            validated_data.pop("password_confirm")
            password = validated_data.pop("password")
            user = User.objects.create_user(**validated_data)
            user.set_password(password)
            user.save()
            return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include username/email and password.")


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'user_type', 'gender',
            'profile_image', 'is_verified', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'is_verified']


class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["first_name", "last_name", "date_of_birth", "gender", "profile_image"]


class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = ["id", "name", "email", "phone_number", "subject", "message"]


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ["id", "email"]