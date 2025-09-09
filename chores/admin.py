from django.contrib.admin import ModelAdmin, register
from .models import Chore, ChoreSchedule, ChoreScheduleOrder, ScheduleTask, UserTask


# Register your models here.
@register(Chore)
class ChoreAdmin(ModelAdmin):
    list_display = ('id', 'title', 'description')


@register(ChoreSchedule)
class ChoreScheduleAdmin(ModelAdmin):
    list_display = (
        'id', 'chore', 'rotation_type', 'active_order_id',
    )


@register(ScheduleTask)
class ScheduleTaskAdmin(ModelAdmin):
    list_display = (
        'id', 'schedule', 'start_day_of_week', 'due_day_of_week'
    )


@register(ChoreScheduleOrder)
class ChoreScheduleOrderAdmin(ModelAdmin):
    list_display = ('id', 'schedule', 'user', 'order')


@register(UserTask)
class UserTaskAdmin(ModelAdmin):
    list_display = (
        'id', 'schedule_task', 'user', 'order', 'due_by', 'is_complete',
        'completed_on', 'completed_by', 'overdue',
        'is_incomplete', 'marked_incomplete_on', 'created_on',
    )
