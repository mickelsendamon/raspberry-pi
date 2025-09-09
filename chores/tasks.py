from django.utils import timezone
from chores.models import UserTask, ScheduleTask


def run_overnight_chore_check():
    """
    Runs at midnight to evaluate and progress the state of the chores
    Generates (assigns) new UserTask for ScheduleTasks with a matching start_day_of_week
        Marks UserTasks from that schedule overdue
        Marks UserTasks from that schedule incomplete
    """
    now = timezone.now()
    today_date = now.date()
    today_dow = now.isoweekday()

    # UserTask queries
    # tasks_due_today = UserTask.objects.filter(due_by=today_date, is_complete=False)
    late_tasks = UserTask.objects.filter(due_by__lt=today_date, is_complete=False, is_incomplete=False)

    # ScheduleTask queries
    schedule_tasks_start_today = ScheduleTask.objects.filter(start_day_of_week=today_dow)

    # Mark unfinished task tasks overdue
    late_tasks.filter(overdue=True).update(overdue=True, overdue_on=today_date)

    # Mark overdue task incomplete
    late_tasks.filter(overdue=False).update(is_incomplete=True, marked_incomplete_on=today_date)

    # todo Notify tasks due today
    # for task in tasks_due_today:
    #     pass

    # Generate new UserTasks for each ChoreSchedule
    for sched_task in schedule_tasks_start_today:
        last_user_task = UserTask.objects.filter(schedule_task__schedule=sched_task.schedule).order_by('-due_by').first()
        if last_user_task.due_by.isoweekday() != today_dow:
            UserTask.get_next_task(last_user_task)
        # todo Notify new tasks - maybe schedule for delivery

# from celery import shared_task
# from django.utils.timezone import now
# from datetime import timedelta
# from .models import ChoreAssignment
#
#
# def get_upcoming_assignments(days=2):
#     """
#     Fetches all incomplete tasks with a due date in the next `days`
#     Returns QuerySet[<ChoreAssignment>]
#     """
#     today = now().date()
#     return ChoreAssignment.objects.filter(
#         due_by__lte=today + timedelta(days=2), complete=False
#     )
#
#
# @shared_task()
# def check_chore_assignments():
#     assignments = get_upcoming_assignments()
#
#
# @shared_task()
# def notify_two_days_assignments():
#     """
#     Notifies all assignments that are due within the next two days
#     Calls `notify_overdue_assignment` to handle overdue assignments
#     """
#     assignments = get_upcoming_assignments(days=2)
#     notify_overdue_assignment(assignments)
#     for assignment in assignments:
#         if not assignment.overdue:
#             print(f'Upcoming task found: {assignment}')
#             # assignment.notify_due_soon()
#
#
# def notify_overdue_assignment(assignments):
#     """
#     Filters provided `ChoreAssignment`s, then marks the record overdue and notifies the assigned user
#     assignments: <QuerySet[ChoreAssignment]>
#     """
#     today = now().date()
#     overdue_assignments = assignments.filter(overdue=False)
#     for assignment in overdue_assignments:
#         if assignment.due_by < today:
#             assignment.overdue = True
#             assignment.save()
#             print(f'Overdue task found: {assignment}')
#             assignment.notify_overdue()
