from django.db.models import Model, ForeignKey, CASCADE, CharField, TextField, DateTimeField, BooleanField, JSONField
from django.contrib.auth import get_user_model

User = get_user_model()

NOTIFICATION_TYPES = [
    ('email', 'Email'),
    ('text', 'Text'),
    ('push', 'Push'),
]


# Create your models here.
class Notification(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='notifications')
    notification_type = CharField(max_length=10, choices=NOTIFICATION_TYPES)
    subject = CharField(max_length=255)
    message = TextField(blank=True)  # optional for HTML/text content
    template_name = CharField(max_length=255)  # e.g., emails/chores/task_assigned
    sent_on = DateTimeField(auto_now_add=True)
    delivered = BooleanField(default=False)  # True if sending succeeded
    meta = JSONField(default=dict, blank=True)  # optional metadata, like task id, url, etc.

    class Meta:
        ordering = ['-sent_on']

    def __str__(self):
        return f"{self.notification_type.title()} to {self.user.email} ({self.subject})"
