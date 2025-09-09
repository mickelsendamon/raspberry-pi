from django.urls import path
from django.views.generic import TemplateView
from .views import CustomUserCreateView, ActivateAccountView

app_name = 'accounts'

urlpatterns = [
    path('signup/', CustomUserCreateView.as_view(), name='signup'),
    path('signup/done/', TemplateView.as_view(template_name='registration/signup_done.html'), name='signup_done'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('activate/successful/', TemplateView.as_view(template_name='registration/activate_successful.html'), name='activate_successful'),

]
