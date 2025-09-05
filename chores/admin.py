from django.contrib import admin
from .models import Chore, ChoreSchedule, ChoreScheduleOrder, ChoreAssignment


# Register your models here.
@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')


@admin.register(ChoreSchedule)
class ChoreScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'chore', 'due_monday', 'due_tuesday', 'due_wednesday', 'due_thursday', 'due_friday', 'due_saturday', 'due_sunday'
    )


@admin.register(ChoreScheduleOrder)
class ChoreScheduleOrderAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'user', 'order')


@admin.register(ChoreAssignment)
class ChoreAssignmentAdmin(admin.ModelAdmin):
    list_display = ('assigned_to', 'due_by', 'overdue', 'complete', 'completed_by')
