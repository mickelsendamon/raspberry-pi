import datetime
import logging
from celery import shared_task
from django.utils import timezone
from chores.models import UserTask, ScheduleTask
from notifications.emails.services import send_email

logger = logging.getLogger(__name__)


@shared_task
def test_task():
    """A simple task that outputs 'Success' into the log."""
    logger.info('Success')


@shared_task
def test_email():
    """
    A simple task that sends an email and logs the result.
    Used to validate email backend.
    """
    msg = send_email(
        'emails/system/test_email',
        'Test Email',
        ['damon.mickelsen@gmail.com', 'the.chore.chart.app@gmail.com']
    )
    logger.info(msg)


@shared_task
def run_overnight_chore_check_task():
    logger.info("Overnight chore check task started")
    msg = send_email('emails/system/overnight_chore_task_start',
               "Overnight System Task: started", ['damon.mickelsen@gmail.com'])
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)
    today_dow = today.isoweekday()  # Monday=1, Sunday=7

    logger.info("Running overnight chore check...")
    logger.info(f"today={today}")
    logger.info(f"yesterday={yesterday}")
    logger.info(f"today_dow={today_dow}")

    # 1. Mark overdue
    to_mark_overdue = UserTask.objects.filter(
        due_by=yesterday,
        is_complete=False,
        is_incomplete=False,
    )
    overdue_count = to_mark_overdue.count()
    logger.info(f"to_mark_overdue={overdue_count}")

    for task in to_mark_overdue:
        logger.info(f">>>>>>>>>>>> Mark overdue - {task}.")
        task.mark_overdue()
    logger.info(f"Marked {to_mark_overdue.count()} tasks as overdue.")

    # 2. Generate new tasks for today
    to_generate_tasks = ScheduleTask.objects.filter(start_day_of_week=today_dow)
    logger.info(f'to_generate_tasks={to_generate_tasks.count()}')

    # 3. Mark incomplete (for tasks that should have been done before new ones are assigned)
    to_mark_incomplete = UserTask.objects.filter(
        is_complete=False,
        is_incomplete=False,
        schedule_task__schedule_id__in=to_generate_tasks.values_list('schedule_id', flat=True).distinct(),
    )
    logger.info(f"to_mark_incomplete={to_mark_incomplete.count()}")

    for task in to_mark_incomplete:
        logger.info(f">>>>>>>>>>>> Mark incomplete - {task}.")
        task.mark_incomplete()
    logger.info(f"Marked {to_mark_incomplete.count()} tasks as incomplete.")

    # 4. Create new UserTasks for today
    for sched_task in to_generate_tasks:
        # Grab schedule and its current order
        schedule = sched_task.schedule
        assigned_user = schedule.assigned_user
        current_order = schedule.order.filter(order=schedule.active_order_id).first()

        if not assigned_user or not current_order:
            logger.info(f">>>>>>>>>>>> Skipping {sched_task} — no active order.")
            continue

        logger.info(f""">>>>>>>>>>>> Create Task:
        schedule_task={sched_task},
        user={assigned_user},
        order={current_order},
        due_by={today + datetime.timedelta(
            days=(sched_task.due_day_of_week - today_dow) % 7
        )}"""
                          )
        UserTask.objects.create(
            schedule_task=sched_task,
            user=assigned_user,
            order=current_order,
            due_by=today + timezone.timedelta(
                days=(sched_task.due_day_of_week - today_dow) % 7
            )
        )
        logger.info(f"Generated new task for {assigned_user} ({sched_task}).")

    logger.info("Overnight chore check complete.")
