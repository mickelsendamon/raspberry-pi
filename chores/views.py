from datetime import date, timedelta

from django.contrib import messages
from django.contrib.messages import ERROR
from django.db.models import OuterRef, Subquery, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, DeleteView, UpdateView, TemplateView
from two_factor.views import OTPRequiredMixin

from .forms import ChoreScheduleForm, ChoreScheduleOrderForm
from .models import Chore, ChoreSchedule, ChoreScheduleOrder, ChoreAssignment
from config.mixins import SuperuserRequiredMixin

class HomeView(OTPRequiredMixin, TemplateView):
    template_name = "chores_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Current assignments for this user
        cas = ChoreAssignment.objects.filter(
            assigned_to__user=self.request.user,
            complete=False
        )

        context["my_assignments"] = [
            {
                "title": chore.assigned_to.schedule.chore.title,
                "due_by": chore.due_by,
                "description": chore.assigned_to.schedule.chore.description,
                "overdue": chore.overdue,
                "pk": chore.pk,
                "can_complete": date.today() > chore.due_by - timedelta(days=3),
            }
            for chore in cas
        ]

        # Overdue count for badge
        context["overdue_assignments_count"] = cas.filter(overdue=True).count()

        # User’s schedules, with the *next assignment* pulled in
        user_schedule_orders = self.request.user.chore_schedule_orders.all()

        user_chore_schedules = []
        for order in user_schedule_orders:
            active_assignment = ChoreAssignment.objects.filter(assigned_to__schedule=order.schedule, complete=False).order_by("-due_by").first()

            user_chore_schedules.append({
                'title': order.schedule.chore.title,
                'due_by': active_assignment.due_by,
                'assigned_to': active_assignment.assigned_to.user,
                'overdue': active_assignment.overdue,
                'pk': order.schedule.pk
            })


        context['user_chore_schedules'] = sorted(user_chore_schedules, key=lambda x: x["due_by"])

        # Previous assignments (completed OR ever assigned to the user)
        context["previous_assignments"] = (
                ChoreAssignment.objects.filter(
                    assigned_to__user=self.request.user
                )
                | ChoreAssignment.objects.filter(completed_by=self.request.user)
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
            ChoreAssignment.objects
            .filter(
                complete=False,
                assigned_to__schedule__chore=OuterRef("pk")
            )
            .order_by("due_by")  # earliest due date
        )

        return Chore.objects.annotate(
            next_due_by=Subquery(assignment_qs.values("due_by")[:1]),
            next_user=Subquery(assignment_qs.values("assigned_to__user__first_name")[:1]),
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
        try:
            assignment = ChoreAssignment.objects.filter(complete=False, assigned_to__schedule=self.object)[0]
            context['active_assignment'] = assignment
            context['can_complete'] = date.today() > assignment.due_by - timedelta(days=2) # allow to mark complete 2 days before due
        except IndexError:
            pass

        return context


class ChoreScheduleListView(OTPRequiredMixin, ListView):
    model = ChoreSchedule
    template_name = 'chore_schedule_list.html'

    def get_queryset(self):
        # Grab the "next due assignment" for each ChoreSchedule
        assignment_qs = (
            ChoreAssignment.objects
            .filter(
                complete=False,
                assigned_to__schedule=OuterRef("pk")
            )
            .order_by("due_by")  # earliest due date
        )

        return (
            ChoreSchedule.objects.annotate(
                next_due_by=Subquery(assignment_qs.values("due_by")[:1]),
                next_user=Subquery(assignment_qs.values("assigned_to__user__first_name")[:1]),
            )
        )


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


class ChoreAssignmentMarkCompleteView(OTPRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        assignment = get_object_or_404(ChoreAssignment, pk=pk)
        if assignment.complete:
            messages.add_message(request, ERROR, 'This chore is already completed.')
            return redirect('chores:chores_home')
        next_assignment = assignment.mark_complete(request.user)

        return redirect('chores:chore_schedule_detail', pk=next_assignment.assigned_to.schedule.pk)


class ChoreAssignmentListView(OTPRequiredMixin, SuperuserRequiredMixin, ListView):
    model = ChoreAssignment
    template_name = 'chore_assignment_list.html'
