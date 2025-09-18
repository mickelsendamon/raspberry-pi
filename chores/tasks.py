from celery import shared_task
from notifications.emails.services import send_email


@shared_task
def run_overnight_chore_check_task():
    send_email('emails/system/overnight_chore_task_start', "Overnight System Task: started", ['damon.mickelsen@gmail.com'])
    from django.core.management import call_command
    try:
        call_command("run_overnight_chore_check")
        send_email('emails/system/overnight_chore_task_complete', "Overnight System Task: complete", ['damon.mickelsen@gmail.com'])
    except Exception as e:
        send_email('emails/system/overnight_chore_task_error', "Overnight System Task: error", ['damon.mickelsen@gmail.com'])
