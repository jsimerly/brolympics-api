"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.csrf import set_csrf_token

API_PREFIX = 'api/' if settings.ENV_TYPE == "DEV" else ""

urlpatterns = [
    path(f'{API_PREFIX}admin/', admin.site.urls),
    path(f'{API_PREFIX}auth/', include('apps.authentication.urls')),
    path(f'{API_PREFIX}brolympics/', include('apps.brolympics.urls')),
    path(f'{API_PREFIX}set-csrf-token/', set_csrf_token)
]

if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)