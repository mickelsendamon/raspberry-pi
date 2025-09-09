from django.forms import ModelForm, Select, NumberInput, ValidationError
from .models import ChoreSchedule, ChoreScheduleOrder, ScheduleTask


class ChoreScheduleForm(ModelForm):
    class Meta:
        model = ChoreSchedule
        fields = [
            "chore", "rotation_type"
        ]


class ChoreScheduleOrderForm(ModelForm):
    class Meta:
        model = ChoreScheduleOrder
        fields = ["schedule", "user", "order"]
        widgets = {
            "schedule": Select(attrs={"class": "form-select"}),
            "user": Select(attrs={"class": "form-select"}),
            "order": NumberInput(attrs={"class": "form-control", "min": 1}),
        }
        labels = {
            "schedule": "Chore Schedule",
            "user": "Assigned User",
            "order": "Order Number",
        }
        help_texts = {
            "order": "1 = first, 2 = second, etc.",
        }


class ScheduleTaskForm(ModelForm):
    class Meta:
        model = ScheduleTask
        fields = '__all__'
        widgets = {
            'schedule': Select(attrs={'class': 'form-select'}),
            'start_day_of_week': Select(attrs={'class': 'form-select'}),
            'due_day_of_week': Select(attrs={'class': 'form-select'}),
        }
        labels = {
            "start_day_of_week": "Start Day",
            "due_day_of_week": "Due Day"
        }

    def clean(self):
        cleaned_data = super().clean()
        schedule = cleaned_data.get('schedule')
        start = cleaned_data.get('start_day_of_week')
        due = cleaned_data.get('due_day_of_week')

        # Basic validation
        if start is not None and due is not None and due < start:
            self.add_error('due_day_of_week', '"Due Day" cannot be before "Start Day"')

        if not schedule or start is None or due is None:
            return cleaned_data

        # Fetch existing tasks in the same schedule
        overlapping_tasks = ScheduleTask.objects.filter(schedule=schedule)
        if self.instance.pk:
            overlapping_tasks = overlapping_tasks.exclude(pk=self.instance.pk)

        # Check for overlaps
        for task in overlapping_tasks:
            task_start = task.start_day_of_week
            task_due = task.due_day_of_week

            # Check exact boundary conflicts
            if start == task_start:
                self.add_error('start_day_of_week', f'"Start Day" cannot be on the same day as another task ({task}).')
            if due == task_due:
                self.add_error('due_day_of_week', f'"Due Day" cannot be on the same day as another task ({task}).')
            if start == task_due:
                self.add_error('start_day_of_week', f'"Start Day" cannot be on the same day that another task is due ({task}).')
            if due == task_start:
                self.add_error('due_day_of_week', f'"Due Day" cannot be on the same day another task starts ({task}).')

            # General overlap check
            if not (due < task_start or start > task_due):
                self.add_error(None, f'Task cannot overlap another task ({task}).')

        return cleaned_data
