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
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from two_factor.urls import urlpatterns as tf_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(tf_urls)),  # MFA login & setup
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('account/', include('django.contrib.auth.urls')),  # built-in auth
    path('account/login/', RedirectView.as_view(pattern_name='two_factor:login')),  # enforce login via `two_factor:login`
    path('account/', include('accounts.urls')),
    path('chores/', include('chores.urls', namespace='chores')),
    # path('properties/', include('properties.urls')),
]
