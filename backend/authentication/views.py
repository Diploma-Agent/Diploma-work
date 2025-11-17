from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer
)


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        operation_description="Реєстрація нового користувача з автоматичною генерацією JWT токенів",
        responses={
            201: openapi.Response(
                description="Користувача успішно зареєстровано",
                examples={
                    "application/json": {
                        "user": {
                            "id": 1,
                            "username": "newuser",
                            "email": "newuser@example.com",
                            "first_name": "New",
                            "last_name": "User",
                            "date_joined": "2025-11-01T12:00:00Z"
                        },
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "message": "Користувача успішно зареєстровано!"
                    }
                }
            ),
            400: "Помилка валідації (username вже існує, паролі не співпадають, тощо)"
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Користувача успішно зареєстровано!'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API endpoint for user login.
    POST /api/auth/login/
    """
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Успішний вхід",
                examples={
                    "application/json": {
                        "user": {
                            "id": 1,
                            "username": "testuser",
                            "email": "test@example.com",
                            "first_name": "Test",
                            "last_name": "User",
                            "date_joined": "2025-11-01T12:00:00Z"
                        },
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "message": "Успішний вхід!"
                    }
                }
            ),
            401: "Неправильні дані для входу"
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username_or_email = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Спробувати знайти користувача за email або username
        user = None
        
        # Якщо введено email
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            # Якщо введено username
            user = authenticate(username=username_or_email, password=password)
        
        if user is None:
            return Response({
                'error': 'Неправильні дані для входу'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': 'Обліковий запис деактивовано'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Успішний вхід!'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    API endpoint for user logout.
    POST /api/auth/logout/
    """
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Успішний вихід",
                examples={
                    "application/json": {
                        "message": "Успішний вихід! Видаліть токени на клієнті."
                    }
                }
            )
        }
    )
    def post(self, request):
        return Response({
            'message': 'Успішний вихід! Видаліть токени на клієнті.'
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to get and update user profile.
    GET/PUT/PATCH /api/auth/profile/
    """
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_description="Отримати профіль поточного авторизованого користувача",
        responses={
            200: UserSerializer,
            401: "Не авторизовано - потрібен Bearer token"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Оновити профіль користувача (повне оновлення)",
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: "Помилка валідації",
            401: "Не авторизовано"
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частково оновити профіль користувача",
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: "Помилка валідації",
            401: "Не авторизовано"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    API endpoint for changing password.
    POST /api/auth/change-password/
    """
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Пароль успішно змінено",
                examples={
                    "application/json": {
                        "message": "Пароль успішно змінено!"
                    }
                }
            ),
            400: "Старий пароль неправильний"
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Старий пароль неправильний'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Пароль успішно змінено!'
        }, status=status.HTTP_200_OK)
