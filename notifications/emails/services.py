from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from notifications.models import Notification


def send_email(template_prefix, subject, to, context=None, from_email="the.chores.chart.app@gmail.com"):
    """
    Generic email sender that handles both HTML and plain text templates.

    Args:
        template_prefix (str): Path prefix for the email templates (e.g. "emails/chores/task_assigned")
        subject (str): Subject line for the email.
        to (list): List of recipient emails.
        context (dict, optional): Context passed to templates.
        from_email (str, optional): The "from" email address.
    """
    if context is None:
        context = {}
    context.setdefault("year", timezone.now().year)

    text_template = f"{template_prefix}.txt"
    html_template = f"{template_prefix}.html"

    try:
        text_content = render_to_string(text_template, context)
    except Exception:
        text_content = ""

    html_content = render_to_string(html_template, context)

    # Send email
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
        delivered = True
    except Exception:
        delivered = False

    # Log to database
    for recipient in to:
        safe_context = {
            k: (v.id if hasattr(v, "id") else v)
            for k, v in context.items()
        }
        Notification.objects.create(
            user=context.get("usertask").user,
            notification_type="email",
            subject=subject,
            message=html_content,
            template_name=template_prefix,
            delivered=delivered,
            meta={
                "recipients": to,
                "context": safe_context,
            }
        )


def send_task_assigned_email(usertask, task_url):
    """Wrapper for 'task assigned' emails."""
    subject = f"New Chore Assigned: {usertask.schedule_task.name}"
    to = [usertask.user.email]
    context = {
        "usertask": usertask,
        "task_url": task_url,
    }
    send_email("emails/chores/task_assigned", subject, to, context)


def send_task_overdue_email(usertask, task_url):
    """Wrapper for 'task overdue' emails."""
    subject = f"Chore Overdue: {usertask.schedule_task.name}"
    to = [usertask.user.email]
    context = {
        "usertask": usertask,
        "task_url": task_url,
    }
    send_email("emails/chores/task_overdue", subject, to, context)


def send_task_incomplete_email(usertask, task_url):
    """Wrapper for 'task overdue' emails."""
    subject = f"Task Is Incomplete: {usertask.schedule_task.name}"
    to = [usertask.user.email]
    context = {
        "usertask": usertask,
        "task_url": task_url,
    }
    send_email("emails/chores/task_incomplete", subject, to, context)


def send_task_complete_email(usertask, task_url):
    """Wrapper for 'task complete' emails."""
    subject = f'Chore Complete: {usertask.schedule_task.name}'
    to = [usertask.user.email]
    context = {
        'usertask': usertask,
        'task_url': task_url,
    }
    send_email('emails/chores/task_complete', subject, to, context)


def send_task_up_next_email(usertask, task_url):
    subject = f"Coming Up: {usertask.schedule_task.name}"
    to = [usertask.user.email]
    context = {
        "usertask": usertask,
        "task_url": task_url,
    }
    send_email("emails/chores/task_up_next", subject, to, context)
