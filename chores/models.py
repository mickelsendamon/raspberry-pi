from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Model, CharField, ForeignKey, CASCADE, OneToOneField, IntegerField, SET_NULL, \
    DateField, BooleanField, UniqueConstraint, PROTECT, PositiveIntegerField, DateTimeField
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser

DAYS = [(1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')]
SCHEDULE_RECURRENCE_UNITS = [('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')]
SCHEDULE_ROTATION_TYPES = [('daily', 'Daily'), ('weekly', 'Weekly')]


# Create your models here.
class Chore(Model):
    title = CharField(max_length=255)
    description = CharField(max_length=255)

    def __str__(self):
        return f'{self.title}'

    def get_absolute_url(self):
        return reverse('chores:chore_detail', args=[self.pk])

    @property
    def tooltip(self):
        return f'Confused?\n\n{self.description}'


class ChoreSchedule(Model):
    chore = OneToOneField(Chore, on_delete=PROTECT, related_name='schedule')
    rotation_type = CharField(max_length=255, choices=SCHEDULE_ROTATION_TYPES)
    active_order_id = IntegerField(default=0)

    def __str__(self):
        return f'Schedule for {self.chore.title}'

    def get_absolute_url(self):
        return reverse('chores:chore_schedule_detail', args=[self.pk])

    def get_day_map(self):
        from collections import defaultdict

        day_map = defaultdict(list)

        for task in self.tasks.all():
            start = task.start_day_of_week
            due = task.due_day_of_week
            # Start day
            day_map[start].append("start")
            # Due day
            day_map[due].append("due")
            # In-between days
            for day in range(start + 1, due):
                day_map[day].append("scheduled")

        return day_map

    @property
    def next_due_date(self):
        """
        Return the next due date for this schedule.
        1. If there are active UserTasks, return the earliest due_by.
        2. Otherwise, calculate from the ScheduleTasks.
        """
        # 1. Check for active user tasks
        active_due = (
            UserTask.objects
            .filter(
                schedule_task__schedule=self,
                is_complete=False,
                is_incomplete=False
            )
            .order_by("due_by")
            .values_list("due_by", flat=True)
            .first()
        )
        if active_due:
            return active_due

        # 2. Fallback: calculate based on ScheduleTasks
        today = timezone.now().date()
        today_weekday = today.weekday()  # Monday=1, Sunday=7

        soonest_due = None
        for task in self.tasks.all():  # self.tasks is from ScheduleTask.schedule related_name
            days_until_due = (task.due_day_of_week - today_weekday) % 7
            if days_until_due == 0:
                days_until_due = 7  # next week if "today"
            candidate = today + timedelta(days=days_until_due)

            if soonest_due is None or candidate < soonest_due:
                soonest_due = candidate

        return soonest_due

    @property
    def assigned_user(self):
        if not self.active_order_id:
            return None
        order = self.order.filter(order=self.active_order_id).first()
        return getattr(order, "user", None)


class ScheduleTask(Model):
    name = CharField(max_length=255)
    schedule = ForeignKey(ChoreSchedule, on_delete=CASCADE, related_name='tasks')
    start_day_of_week = IntegerField(choices=DAYS)
    due_day_of_week = IntegerField(choices=DAYS)

    def __str__(self):
        return f'{self.name}: {self.get_start_day_of_week_display()} - {self.get_due_day_of_week_display()}'


class ChoreScheduleOrder(Model):
    schedule = ForeignKey(ChoreSchedule, on_delete=CASCADE, related_name='order')
    user = ForeignKey(CustomUser, on_delete=SET_NULL, related_name='chore_schedule_orders', null=True, blank=True)
    order = IntegerField()

    class Meta:
        ordering = ['order']
        constraints = [
            UniqueConstraint(fields=['schedule', 'order'], name='unique_schedule_order'),
            UniqueConstraint(fields=['schedule', 'user'], name='unique_schedule_user')
        ]

    def __str__(self):
        return f'{self.order} - {self.user.first_name}'

    def get_absolute_url(self):
        return reverse('chores:chore_schedule_detail', args=[self.schedule.pk])

    def save(self, *args, **kwargs):
        # Check uniqueness
        try:
            super().save(*args, **kwargs)
        except IntegrityError as e:
            # Translate DB constraint errors into friendly ValidationError
            if "unique_schedule_order" in str(e):
                raise ValidationError(
                    {"order": f"Someone is already assigned to order {self.order} for this schedule."}
                )
            elif "unique_schedule_user" in str(e):
                raise ValidationError(
                    {"user": f"{self.user} is already assigned to this schedule."}
                )
            raise


class UserTask(Model):
    schedule_task = ForeignKey(ScheduleTask, on_delete=CASCADE, related_name='tasks')
    user = ForeignKey(CustomUser, on_delete=CASCADE, related_name='tasks')
    order = ForeignKey(ChoreScheduleOrder, on_delete=CASCADE, related_name='tasks')
    due_by = DateField()
    is_complete = BooleanField(default=False)
    completed_on = DateField(null=True, blank=True)
    completed_by = ForeignKey(CustomUser, on_delete=CASCADE, related_name='completed_tasks', null=True, blank=True)
    overdue = BooleanField(default=False)
    overdue_on = DateField(null=True, blank=True)
    is_incomplete = BooleanField(default=False)
    marked_incomplete_on = DateField(null=True, blank=True)
    created_on = DateTimeField(auto_now_add=True)

    @classmethod
    def get_next_task(cls, current_task: "UserTask"):
        """
        Called when a UserTask is marked complete or incomplete.
        Decides whether to assign the next ScheduleTask for the current order,
        or rotate to the next person in the ChoreScheduleOrder.
        """
        schedule = current_task.order.schedule
        all_tasks = list(schedule.tasks.order_by("start_day_of_week"))

        # Find current index in tasks
        try:
            current_index = all_tasks.index(current_task.schedule_task)
        except ValueError:
            # If for some reason the schedule_task isn't in the list
            return None

        # Check if there’s a "next" ScheduleTask
        if current_index + 1 < len(all_tasks):
            next_schedule_task = all_tasks[current_index + 1]
            now = timezone.now()
            now_dow = now.isoweekday()
            next_dow = next_schedule_task.due_day_of_week
            due_by = now.date() + timedelta(
                days=next_dow - now_dow \
                    if next_dow > now_dow \
                    else (7 + next_dow) - now_dow
            )
            return cls.objects.create(
                schedule_task=next_schedule_task,
                user=current_task.user,
                order=current_task.order,
                due_by=due_by
            )

        # No more tasks → rotate to next user in order
        all_orders = list(schedule.order.order_by("order"))
        try:
            order_index = all_orders.index(current_task.order)
        except ValueError:
            return None

        next_order = all_orders[(order_index + 1) % len(all_orders)]
        first_task = all_tasks[0] if all_tasks else None
        if first_task is None:
            return None  # no tasks exist at all

        return cls.objects.create(
            schedule_task=first_task,
            user=next_order.user,
            order=next_order,
        )

    def mark_complete(self, user=None):
        """
        Mark this task as complete
        """
        if not self.is_complete and not self.is_incomplete:
            self.is_complete = True
            self.completed_on = timezone.now()
            if user:
                self.completed_by = user
            self.save()

    def mark_incomplete(self):
        """
        Mark this task as incomplete
        """

        if not self.is_complete and not self.is_incomplete:
            self.is_incomplete = True
            self.marked_incomplete_on = timezone.now()
            self.save()

    def mark_overdue(self):
        """
        Mark this task as overdue
        """
        if not self.overdue:
            self.overdue = True
            self.save()
