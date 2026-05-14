"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path(f'{settings.ADMIN_URL}', admin.site.urls),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/auth/', include("djoser.urls")),
    path('api/v1/auth/', include('core_apps.user_auth.urls')),

]

admin.site.site_header = "FINTECH-BANKING API"
admin.site.site_title = "FINTECH-BANKING Admin Portal"
admin.site.index_title = "Welcome to FINTECH-BANKING Admin Portal"