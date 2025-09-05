from django.urls import path, reverse_lazy
from django.views.generic import RedirectView, TemplateView
from .views import (
    HomeView,
    ChoreCreateView, ChoreDetailView, ChoreListView, ChoreDeleteView, ChoreUpdateView,
    ChoreScheduleCreateView, ChoreScheduleDetailView, ChoreScheduleListView, ChoreScheduleDeleteView, ChoreScheduleUpdateView,
    ChoreScheduleOrderCreateView, ChoreAssignmentMarkCompleteView, ChoreAssignmentListView
)

app_name = 'chores'

urlpatterns = [
    path('', HomeView.as_view(), name='chores_home'),
    path('chore/', ChoreListView.as_view(), name='chore_list'),
    path('chore/create/', ChoreCreateView.as_view(), name='chore_create'),
    path('chore/<int:pk>/', ChoreDetailView.as_view(), name='chore_detail'),
    path('chore/<int:pk>/update/', ChoreUpdateView.as_view(), name='chore_update'),
    path('chore/<int:pk>/delete/', ChoreDeleteView.as_view(), name='chore_delete'),

    path('schedule/', ChoreScheduleListView.as_view(), name='chore_schedule_list'),
    path('schedule/create/', ChoreScheduleCreateView.as_view(), name='chore_schedule_create'),
    path('schedule/<int:pk>/', ChoreScheduleDetailView.as_view(), name='chore_schedule_detail'),
    path('schedule/<int:pk>/update/', ChoreScheduleUpdateView.as_view(), name='chore_schedule_update'),
    path('schedule/<int:pk>/delete/', ChoreScheduleDeleteView.as_view(), name='chore_schedule_delete'),

    path('schedule/order/create/', ChoreScheduleOrderCreateView.as_view(), name='chore_schedule_order_create'),
    path('schedule/assignment/<int:pk>/complete/', ChoreAssignmentMarkCompleteView.as_view(), name='chore_assignment_mark_complete'),

    path('assignment/', ChoreAssignmentListView.as_view(), name='chore_assignment_list'),
]
