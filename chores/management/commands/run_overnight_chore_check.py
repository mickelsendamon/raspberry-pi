from django.core.management.base import BaseCommand
from django.utils import timezone
from chores.models import UserTask, ScheduleTask

class Command(BaseCommand):
    help = "Runs the overnight chore check (mark overdue, mark incomplete, and generate new tasks)."

    def handle(self, *args, **options):
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)
        today_dow = today.isoweekday()  # Monday=1, Sunday=7

        self.stdout.write("Running overnight chore check...")
        self.stdout.write(f"``\ntoday={today}\n```")
        self.stdout.write(f"```\nyesterday={yesterday}\n```")
        self.stdout.write(f"```\ntoday_dow={today_dow}\n```")

        # 1. Mark overdue
        to_mark_overdue = UserTask.objects.filter(
            due_by=yesterday,
            is_complete=False,
            is_incomplete=False,
        )
        overdue_count = to_mark_overdue.count()
        self.stdout.write(f"```\nto_mark_overdue={overdue_count}\n```")

        for task in to_mark_overdue:
            self.stdout.write(f">>>>>>>>>>>> Mark overdue - {task}.")
            # task.mark_overdue()
        # self.stdout.write(f"Marked {to_mark_overdue.count()} tasks as overdue.")

        # 2. Generate new tasks for today
        to_generate_tasks = ScheduleTask.objects.filter(start_day_of_week=today_dow)
        self.stdout.write(f'```\nto_generate_tasks={to_generate_tasks.count()}\n```')

        # 3. Mark incomplete (for tasks that should have been done before new ones are assigned)
        to_mark_incomplete = UserTask.objects.filter(
            is_complete=False,
            is_incomplete=False,
            schedule_task__in=to_generate_tasks,
        )
        self.stdout.write(f"```\nto_mark_incomplete={to_mark_incomplete.count()}\n```")

        for task in to_mark_incomplete:
            self.stdout.write(f">>>>>>>>>>>> Mark incomplete - {task}.")
            # task.mark_incomplete()
        # self.stdout.write(f"Marked {to_mark_incomplete.count()} tasks as incomplete.")

        # 4. Create new UserTasks for today
        for sched_task in to_generate_tasks:
            # Grab schedule and its current order
            schedule = sched_task.schedule
            assigned_user = schedule.assigned_user
            current_order = schedule.order.filter(order=schedule.active_order_id).first()

            if not assigned_user or not current_order:
                self.stdout.write(f">>>>>>>>>>>> Skipping {sched_task} — no active order.")
                continue

            self.stdout.write(f""">>>>>>>>>>>> Create Task:
    schedule_task={sched_task},
    user={assigned_user},
    order={current_order},
    due_by={today + timezone.timedelta(
        days=(sched_task.due_day_of_week - today_dow) % 7
)}"""
           )
            # UserTask.objects.create(
            #     schedule_task=sched_task,
            #     user=assigned_user,
            #     order=current_order,
            #     due_by=today + timezone.timedelta(
            #         days=(sched_task.due_day_of_week - today_dow) % 7
            #     )
            # )
            # self.stdout.write(f"Generated new task for {assigned_user} ({sched_task}).")

        self.stdout.write("Overnight chore check complete.")
