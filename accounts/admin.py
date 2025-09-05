# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_email_active', 'sms_phone_number']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'is_email_active']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'sms_phone_number')}),
        (_('Access levels'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('System info'), {'fields': ('is_email_active', 'last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )


admin.site.register(CustomUser, CustomUserAdmin)
