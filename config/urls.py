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
import django.contrib.auth.views as auth_views
from django.urls import path, include
from django.views.generic import TemplateView
from two_factor.urls import urlpatterns as tf_urls
from accounts.forms import CustomSetPasswordForm, CustomAuthenticationForm, CustomAuthenticationTokenForm, \
    CustomBackupTokenForm
from accounts.views import CustomLoginView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Two-factor auth & setup URLs (except login, which is overridden below)
    path('', include(tf_urls)),

    # Custom login with all three custom forms
    path(
        "account/login/",
        CustomLoginView.as_view(),
        name="account_login"
    ),

    # Password reset confirm (overriding form)
    path(
        "account/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            form_class=CustomSetPasswordForm
        ),
        name="password_reset_confirm",
    ),

    # Built-in auth URLs (login/logout/password change, etc.)
    path('account/', include('django.contrib.auth.urls')),

    # Your app-specific URLs
    path('account/', include('accounts.urls')),
    path('chores/', include('chores.urls', namespace='chores')),
]

