from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Model, CharField, ForeignKey, CASCADE, OneToOneField, IntegerField, SET_NULL, \
    DateField, BooleanField, UniqueConstraint, PROTECT, PositiveIntegerField, DateTimeField
from django.urls import reverse
from accounts.models import CustomUser
from chores.utils import send_text_message, chore_upcoming_notification_message, chore_overdue_notification_message, \
    chore_assigned_notification_message

DAYS = [(1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')]
SCHEDULE_RECURRENCE_UNITS = [('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')]


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
    chore = ForeignKey(Chore, on_delete=PROTECT, related_name='schedules')
    due_monday = BooleanField()
    due_tuesday = BooleanField()
    due_wednesday = BooleanField()
    due_thursday = BooleanField()
    due_friday = BooleanField()
    due_saturday = BooleanField()
    due_sunday = BooleanField()

    def __str__(self):
        return f'Schedule for {self.chore.title}'

    def get_absolute_url(self):
        return reverse('chores:chore_schedule_detail', args=[self.pk])

    def get_due_weekdays(self):
        """Return a list of integers representing active weekdays (0=Monday ... 6=Sunday)."""
        mapping = [
            (0, self.due_monday),
            (1, self.due_tuesday),
            (2, self.due_wednesday),
            (3, self.due_thursday),
            (4, self.due_friday),
            (5, self.due_saturday),
            (6, self.due_sunday),
        ]
        return [weekday for weekday, active in mapping if active]

    def next_due_date(self, from_date=None):
        """
        Calculate the next due date for this schedule based on the
        selected weekdays. Returns a `date`.
        """
        if from_date is None:
            from_date = date.today()

        weekdays = self.get_due_weekdays()
        if not weekdays:
            return None  # No schedule set up

        for i in range(7):  # look at the next 7 days max
            candidate = from_date + timedelta(days=i)
            if candidate.weekday() in weekdays:
                return candidate
        return None  # should not happen if weekdays not empty


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

    @property
    def assignment(self):
        return ChoreAssignment.objects.filter(assigned_to__schedule=self.schedule, complete=False)[0]

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

        self.check_assignment()

    def check_assignment(self):
        # if this is the first ChoreSchduleOrder created for this ChoreSchedule
        #   we need to create a new ChoreAssignment
        if not ChoreScheduleOrder.objects.filter(schedule=self.schedule).exclude(pk=self.pk):
            assignment = ChoreAssignment.objects.create(
                assigned_to=self,
                due_by=self.schedule.next_due_date()
            )
            assignment.notify_new_assignment()


class ChoreAssignment(Model):
    assigned_to = ForeignKey(ChoreScheduleOrder, on_delete=SET_NULL, related_name='chore_assignments', null=True, blank=True)
    due_by = DateField()
    overdue = BooleanField(default=False)
    complete = BooleanField(default=False)
    completed_by = ForeignKey(CustomUser, on_delete=SET_NULL, related_name='completed_chore_assignments', null=True, blank=True)
    completed_on = DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.assigned_to.schedule.chore} due {self.due_by}'

    def notify_due_soon(self):
        send_text_message(
            phone_number=str(self.assigned_to.user.sms_phone_number),
            body=chore_upcoming_notification_message(
                chore_title=self.assigned_to.schedule.chore.title,
                due_date=self.due_by
            )
        )

    def notify_overdue(self):
        send_text_message(
            phone_number=str(self.assigned_to.user.sms_phone_number),
            body=chore_overdue_notification_message(
                chore_title=self.assigned_to.schedule.chore.title,
                due_date=self.due_by,
                user_first_name=self.assigned_to.user.first_name
            )
        )

    def notify_new_assignment(self):
        send_text_message(
            phone_number=str(self.assigned_to.user.sms_phone_number),
            body=chore_assigned_notification_message(
                chore_title=self.assigned_to.schedule.chore.title,
                due_date=self.due_by,
                user_first_name=self.assigned_to.user.first_name
            )
        )

    def mark_complete(self, user=None):
        """
        Mark this assignment as complete and create the next one.
        """

        self.complete = True
        if user:
            self.completed_by = user
        self.save()

        # Get the schedule from the assigned_to link
        schedule = self.assigned_to.schedule

        next_due = schedule.next_due_date(from_date=self.due_by + timedelta(days=1))
        if not next_due:
            return None  # No recurring days set up

        # Determine who’s next in rotation
        all_orders = list(schedule.order.all())  # thanks to related_name='order'
        if not all_orders:
            return None

        # Figure out this assignment’s order in the rotation
        current_index = all_orders.index(self.assigned_to)
        next_index = (current_index + 1) % len(all_orders)
        next_assignee = all_orders[next_index]

        assignment = ChoreAssignment.objects.create(
            assigned_to=next_assignee,
            due_by=next_due,
        )
        assignment.notify_new_assignment()
        return assignment