"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, FileResponse, Http404
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def health_check(request):
    """Render.com health check endpoint — відповідає 200 без авторизації."""
    return JsonResponse({'status': 'ok'})


def spa_view(request, path=''):
    """Повертає React index.html для всіх не-API маршрутів (React Router)."""
    index_path = os.path.join(settings.BASE_DIR, 'frontend_dist', 'index.html')
    if os.path.exists(index_path):
        return FileResponse(open(index_path, 'rb'), content_type='text/html')
    # Якщо фронтенд не зібраний (локальна розробка) — показуємо API info
    return JsonResponse({
        'name': 'FinanceApp API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth/',
            'finance': '/api/finance/',
            'health': '/api/health/',
            'docs': '/swagger/',
        }
    })

# Swagger/OpenAPI schema
schema_view = get_schema_view(
    openapi.Info(
        title="Diploma API",
        default_version='v1',
        description="API documentation for Diploma project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@diploma.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check (Render.com, no auth required)
    path('api/health/', health_check, name='health_check'),

    # API endpoints
    path('api/auth/', include('authentication.urls')),
    path('api/finance/', include('finance.urls')),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # Catch-all — React SPA (повинен бути останнім!)
    path('', spa_view, name='spa-root'),
    path('<path:path>', spa_view, name='spa'),
]
