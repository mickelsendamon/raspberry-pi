from celery import shared_task
from django.utils.timezone import now
from datetime import timedelta
from .models import ChoreAssignment


def get_upcoming_assignments(days=2):
    """
    Fetches all incomplete tasks with a due date in the next `days`
    Returns QuerySet[<ChoreAssignment>]
    """
    today = now().date()
    return ChoreAssignment.objects.filter(
        due_by__lte=today + timedelta(days=2), complete=False
    )


@shared_task()
def check_chore_assignments():
    assignments = get_upcoming_assignments()


@shared_task()
def notify_two_days_assignments():
    """
    Notifies all assignments that are due within the next two days
    Calls `notify_overdue_assignment` to handle overdue assignments
    """
    assignments = get_upcoming_assignments(days=2)
    notify_overdue_assignment(assignments)
    for assignment in assignments:
        if not assignment.overdue:
            print(f'Upcoming task found: {assignment}')
            # assignment.notify_due_soon()


def notify_overdue_assignment(assignments):
    """
    Filters provided `ChoreAssignment`s, then marks the record overdue and notifies the assigned user
    assignments: <QuerySet[ChoreAssignment]>
    """
    today = now().date()
    overdue_assignments = assignments.filter(overdue=False)
    for assignment in overdue_assignments:
        if assignment.due_by < today:
            assignment.overdue = True
            assignment.save()
            print(f'Overdue task found: {assignment}')
            assignment.notify_overdue()
