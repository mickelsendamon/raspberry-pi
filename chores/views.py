from datetime import date, timedelta

from django.contrib import messages
from django.contrib.messages import ERROR
from django.db.models import OuterRef, Subquery, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, DeleteView, UpdateView, TemplateView
from two_factor.views import OTPRequiredMixin

from .forms import ChoreScheduleForm, ChoreScheduleOrderForm, ScheduleTaskForm
from .models import Chore, ChoreSchedule, ChoreScheduleOrder, ScheduleTask, UserTask
from config.mixins import SuperuserRequiredMixin

class HomeView(OTPRequiredMixin, TemplateView):
    template_name = "chores_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Current tasks for this user
        cat = UserTask.objects.filter(
            user=self.request.user,
            is_complete=False,
            is_incomplete=False,
        )

        context['my_assignments'] = [
            {
                "title": task.schedule_task.name,
                "due_by": task.due_by,
                "description": task.schedule_task.schedule.chore.description,
                "overdue": task.overdue,
                "pk": task.pk,
            } for task in cat
        ]

        # Overdue count for badge
        context['overdue_task_count'] = cat.filter(overdue=True).count()

        # User’s chore schedules, with the assignment information
        user_chore_schedules = []
        for order in self.request.user.chore_schedule_orders.all():
            active_assignment = UserTask.objects.filter(schedule_task__schedule=order.schedule).order_by("-due_by").first()
            user_chore_schedules.append({
                'title': order.schedule.chore.title,
                'task_date': active_assignment.completed_on if active_assignment.is_complete else active_assignment.due_by,
                'assigned_to': active_assignment.user,
                'status': 3 if active_assignment.is_complete else 2 if active_assignment.overdue else 1,
                'pk': order.schedule.pk
            })

        context['user_chore_schedules'] = sorted(user_chore_schedules, key=lambda x: x["status"])

        # Previous assignments (completed OR ever assigned to the user)
        context["previous_assignments"] = (
                UserTask.objects.filter(
                    user=self.request.user
                )
                | UserTask.objects.filter(completed_by=self.request.user)
        ).distinct()

        return context


class ChoreCreateView(OTPRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Chore
    fields = '__all__'
    template_name = 'chore_create_update.html'


class ChoreDetailView(OTPRequiredMixin, DetailView):
    model = Chore
    template_name = 'chore_detail.html'


class ChoreListView(OTPRequiredMixin, ListView):
    model = Chore
    template_name = 'chore_list.html'

    def get_queryset(self):
        # Grab the "next due assignment" for each ChoreSchedule
        assignment_qs = (
            UserTask.objects
            .filter(
                is_complete=False,
                is_incomplete=False,
                schedule_task__schedule__chore=OuterRef("pk")
            )
            .order_by("due_by")  # earliest due date
        )

        return Chore.objects.annotate(
            next_due_by=Subquery(assignment_qs.values("due_by")[:1]),
            next_user=Subquery(assignment_qs.values("user__first_name")[:1]),
        )


class ChoreUpdateView(OTPRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Chore
    fields = '__all__'
    template_name = 'chore_create_update.html'


class ChoreDeleteView(OTPRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = Chore
    template_name = 'chore_delete.html'

    def get_success_url(self):
        return reverse('chores:chore_list')


class ChoreScheduleCreateView(OTPRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = ChoreSchedule
    template_name = 'chore_schedule_create_update.html'
    form_class = ChoreScheduleForm


class ChoreScheduleDetailView(OTPRequiredMixin, DetailView):
    model = ChoreSchedule
    template_name = 'chore_schedule_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = ChoreScheduleOrder.objects.filter(schedule=self.object).order_by('order')
        context['DAYS'] = [1, 2, 3, 4, 5, 6, 7]

        from collections import defaultdict

        day_map = defaultdict(list)

        for task in self.object.tasks.all():
            start = task.start_day_of_week
            due = task.due_day_of_week
            # Start day
            day_map[start].append("start")
            # Due day
            day_map[due].append("due")
            # In-between days
            for day in range(start + 1, due):
                day_map[day].append("scheduled")

        context['day_map'] = day_map

        context['active_task'] = UserTask.objects.filter(schedule_task__schedule=self.object).order_by('-due_by').first()

        context['active_order'] = ChoreScheduleOrder.objects.get(id=self.object.active_order_id) if self.object.active_order_id != 0 else None

        return context


class ChoreScheduleListView(OTPRequiredMixin, ListView):
    model = ChoreSchedule
    template_name = 'chore_schedule_list.html'

    def get_queryset(self):
        # Grab the "next due assignment" for each ChoreSchedule
        assignment_qs = (
            UserTask.objects
            .filter(
                is_complete=False,
                is_incomplete=False,
                schedule_task__schedule=OuterRef("pk")
            )
            .order_by("due_by")  # earliest due date
        )
        order_qs = (
            ChoreScheduleOrder.objects.filter(schedule=OuterRef("pk"), order=OuterRef("active_order_id"))
        )

        return (
            ChoreSchedule.objects.annotate(
                next_due_by=Subquery(assignment_qs.values("due_by")[:1]),
                next_user=Subquery(order_qs.values("user__first_name")[:1]),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['DAYS'] = [1, 2, 3, 4, 5, 6, 7]
        return context


class ChoreScheduleUpdateView(OTPRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = ChoreSchedule
    template_name = 'chore_schedule_create_update.html'
    form_class = ChoreScheduleForm


class ChoreScheduleDeleteView(OTPRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = ChoreSchedule
    template_name = 'chore_schedule_delete.html'
    success_url = reverse_lazy('chores:chore_schedule_list')


class ChoreScheduleOrderCreateView(OTPRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = ChoreScheduleOrder
    template_name = 'chore_schedule_order_create_update.html'
    form_class = ChoreScheduleOrderForm


class ChoreScheduleOrderDetailView(OTPRequiredMixin, DetailView):
    model = ChoreScheduleOrder
    template_name = 'chore_schedule_detail.html'


class ChoreScheduleOrderListView(OTPRequiredMixin, ListView):
    model = ChoreScheduleOrder
    template_name = 'chore_schedule_list.html'


class ChoreScheduleOrderUpdateView(OTPRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = ChoreScheduleOrder
    template_name = 'chore_schedule_order_create_update.html'
    form_class = ChoreScheduleForm


class ChoreScheduleOrderDeleteView(OTPRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = ChoreScheduleOrder
    template_name = 'chore_schedule_delete.html'


class ScheduleTaskCreateView(OTPRequiredMixin, CreateView):
    model = ScheduleTask
    template_name = 'schedule_task_create.html'
    form_class = ScheduleTaskForm

    def get_success_url(self):
        return reverse_lazy('chores:chore_schedule_detail', args=[self.object.schedule.pk])


class UserTaskListView(OTPRequiredMixin, ListView):
    model = UserTask
    template_name = 'user_task_list.html'
    queryset = UserTask.objects.all().order_by('-due_by')


class UserTaskMarkCompleteView(OTPRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        task = get_object_or_404(UserTask, pk=pk)
        sched_pk = task.schedule_task.schedule.pk
        if task.is_complete:
            messages.add_message(request, ERROR, 'This chore is already completed.')
            return redirect('chores:chores_home')
        task.mark_complete(request.user)

        return redirect('chores:chore_schedule_detail', pk=sched_pk)
