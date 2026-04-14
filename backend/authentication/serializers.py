from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Паролі не співпадають."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            # використовуємо email як username
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        from django.db.models import Q
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        login_identifier = email or username

        if login_identifier and password:
            # Шукаємо користувача за email або username
            try:
                user = User.objects.get(
                    Q(email=login_identifier) | Q(username=login_identifier))
                # Перевіряємо пароль
                user = authenticate(username=user.username, password=password)
            except User.DoesNotExist:
                user = None

            if not user:
                raise serializers.ValidationError('Невірний логін або пароль')

            data['user'] = user
        else:
            raise serializers.ValidationError(
                'Email (або username) і пароль обов\'язкові')

        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'date_joined')
        read_only_fields = ('id', 'username', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "Паролі не співпадають."})
        return attrs
