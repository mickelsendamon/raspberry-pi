import datetime
import logging
from celery import shared_task
from django.utils import timezone
from chores.models import UserTask, ScheduleTask, ChoreSchedule
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
        ['damon.mickelsen@gmail.com', 'the.chore.chart.app@gmail.com'],
        logger=logger,
    )
    logger.info(msg)


@shared_task
def run_rotate_schedules_check():
    logger.info("Checking Chore Schedules")
    today = timezone.now().date().isoweekday()
    if today == 1:  # Monday
        all_schedules = ChoreSchedule.objects.all()
        for sched in all_schedules:
            order_count = sched.order.count()

            if order_count == 0:
                continue

            if sched.active_order_id < order_count:
                sched.active_order_id += 1
                print(f'{sched.id}: Increment schedule order')
            else:
                sched.active_order_id = 1  # wrap back to first
                print(f'{sched.id}: Reset schedule order')

            sched.save()
    else:
        logger.info(f"Not Monday ({today}), no rotate scheduled")


@shared_task
def run_overnight_chore_check_task():
    logger.info("Overnight chore check task started")

    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)
    today_dow = today.isoweekday()  # Monday=1, Sunday=7

    logger.info(f"today={today}, yesterday={yesterday}, today_dow={today_dow}")

    # 1) Preload the ScheduleTask rows that will generate tasks today
    to_generate_qs = (
        ScheduleTask.objects
        .filter(start_day_of_week=today_dow)
        .select_related('schedule')               # access sched_task.schedule without extra query
        .prefetch_related('schedule__order')     # prefetch ChoreScheduleOrder rows for schedule
    )
    to_generate_ids = set(to_generate_qs.values_list('pk', flat=True))
    logger.info(f"to_generate_tasks={len(to_generate_ids)}")

    # 2) UserTask rows that are due on-or-before yesterday
    unfinished_qs = (
        UserTask.objects
        .filter(due_by__lte=yesterday, is_complete=False, is_incomplete=False)
        .select_related('schedule_task')   # we will check schedule_task_id quickly
    )
    total_unfinished = unfinished_qs.count()
    logger.info(f"Found {total_unfinished} unfinished tasks due <= {yesterday}")

    # Mark each unfinished task either incomplete (if that schedule_task is regenerated today)
    #                           or overdue (otherwise).
    #
    # We call the model methods in case they perform side effects.
    for task in unfinished_qs:
        if task.schedule_task_id in to_generate_ids:
            logger.info(f">>>>> Mark incomplete - UserTask(id={task.pk}, schedule_task_id={task.schedule_task_id})")
            task.mark_incomplete()
        else:
            logger.info(f">>>>> Mark overdue - UserTask(id={task.pk}, schedule_task_id={task.schedule_task_id})")
            task.mark_overdue()

    logger.info("Finished marking overdue/incomplete tasks")

    # 3) Generate new UserTasks for today's ScheduleTask rows
    logger.info(f"Generating new tasks for {to_generate_qs.count()} schedule tasks")
    for sched_task in to_generate_qs:
        schedule = sched_task.schedule

        # find the ChoreScheduleOrder object that matches the schedule.active_order_id
        # schedule.order is prefetched (schedule__order), so this is in-memory
        current_order = next(
            (o for o in schedule.order.all() if o.order == schedule.active_order_id),
            None
        )

        # require a valid order and user
        if not current_order or not getattr(current_order, "user", None):
            logger.info(f">>>>> Skipping ScheduleTask(id={sched_task.pk}) — no active order/user.")
            continue

        assigned_user = current_order.user

        # compute due_by using schedule_task.due_day_of_week
        due_date = today + datetime.timedelta(days=(sched_task.due_day_of_week - today_dow) % 7)

        # avoid creating duplicate tasks for the same schedule_task + due date
        already_exists = UserTask.objects.filter(schedule_task=sched_task, due_by=due_date).exists()
        if already_exists:
            logger.info(f">>>>> Skipping creation for ScheduleTask(id={sched_task.pk}) — task for {due_date} already exists.")
            continue

        # create the user task (order is a FK to ChoreScheduleOrder)
        UserTask.objects.create(
            schedule_task=sched_task,
            user=assigned_user,
            order=current_order,
            due_by=due_date,
        )
        logger.info(f">>>>> Generated new task for user={assigned_user.pk} (ScheduleTask id={sched_task.pk}) due {due_date}")

    logger.info("Overnight chore check complete.")
