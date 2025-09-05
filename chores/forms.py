# chores/forms.py
from django.forms import ModelForm, CheckboxInput, Select, NumberInput
from .models import ChoreSchedule, ChoreScheduleOrder


class ChoreScheduleForm(ModelForm):
    class Meta:
        model = ChoreSchedule
        fields = [
            "chore",
            "due_monday", "due_tuesday", "due_wednesday", "due_thursday",
            "due_friday", "due_saturday", "due_sunday"
        ]
        widgets = {
            "due_monday": CheckboxInput(attrs={"class": "form-check-input"}),
            "due_tuesday": CheckboxInput(attrs={"class": "form-check-input"}),
            "due_wednesday": CheckboxInput(attrs={"class": "form-check-input"}),
            "due_thursday": CheckboxInput(attrs={"class": "form-check-input"}),
            "due_friday": CheckboxInput(attrs={"class": "form-check-input"}),
            "due_saturday": CheckboxInput(attrs={"class": "form-check-input"}),
            "due_sunday": CheckboxInput(attrs={"class": "form-check-input"}),
        }


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


