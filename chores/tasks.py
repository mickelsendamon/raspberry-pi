import logging
from celery import shared_task
from notifications.emails.services import send_email
from django.core.management import call_command

logger = logging.getLogger(__name__)

@shared_task
def run_overnight_chore_check_task():
    logger.info("Overnight chore check task started")
    msg = send_email('emails/system/overnight_chore_task_start',
               "Overnight System Task: started", ['damon.mickelsen@gmail.com'])
    print(msg)
    # try:
    #     call_command("run_overnight_chore_check")
    #     send_email('emails/system/overnight_chore_task_complete',
    #                "Overnight System Task: complete", ['damon.mickelsen@gmail.com'])
    #     logger.info("Overnight chore check task completed successfully")
    # except Exception as e:
    #     send_email('emails/system/overnight_chore_task_error',
    #                "Overnight System Task: error", ['damon.mickelsen@gmail.com'])
    #     logger.exception("Overnight chore check task failed")
