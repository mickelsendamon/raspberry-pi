from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'subject', 'sent_on', 'delivered')
    list_filter = ('notification_type', 'delivered', 'sent_on')
    search_fields = ('subject', 'user__email', 'template_name')
