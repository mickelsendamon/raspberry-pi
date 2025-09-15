from celery import shared_task

@shared_task
def run_overnight_chore_check_task():
    from django.core.management import call_command
    call_command("run_overnight_chore_check")
