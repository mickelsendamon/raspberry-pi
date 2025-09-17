from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from chores.models import UserTask
from notifications.emails.services import send_task_assigned_email, send_task_overdue_email, send_task_incomplete_email, \
    send_task_complete_email


@receiver(post_save, sender=UserTask)
def send_assigned_task_notification(sender, instance, created, **kwargs):
    """
    Sends task notification for newly created tasks
    """
    print('`send_assigned_task_notification signal triggered.')
    task_url = f"http://localhost:8000/tasks/{instance.id}/"

    if created:
        print('send_task_assigned_email')
        send_task_assigned_email(instance, task_url)
        return


@receiver(pre_save, sender=UserTask)
def send_overdue_and_incomplete_task_notification(sender, instance, **kwargs):
    """
    Sends appropriate task notification emails:
    - Assigned (on create)
    - Overdue (if marked overdue)
    - Incomplete (if marked incomplete)
    - Complete (if marked complete)
    - Up Next (optional)
    """
    print('`send_overdue_and_incomplete_task_notification` signal triggered.')
    task_url = f"http://localhost:8000/tasks/{instance.id}/"  # adjust domain

    # Load previous instance from DB
    try:
        previous = UserTask.objects.get(pk=instance.pk)
    except UserTask.DoesNotExist:
        print('Unexpected error: No Previous Task Found')
        return

    # Send overdue email if task is now overdue and was not previously overdue
    if not instance.is_complete and instance.overdue and (not previous or not previous.overdue):
        print('send_task_overdue_email')
        send_task_overdue_email(instance, task_url)
        return

    # Send incomplete email if is_incomplete is set and wasn't before
    if instance.is_incomplete and (not previous or not previous.is_incomplete):
        print('send_task_incomplete_email')
        send_task_incomplete_email(instance, task_url)
        return

    # Send complete email if is_complete is True and was previously False
    if instance.is_complete and (not previous or not previous.is_complete):
        print('send_task_complete_email')
        send_task_complete_email(instance, task_url)
