from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.shortcuts import redirect
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.views import View
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from two_factor.views import LoginView as TFLoginView

from .forms import CustomUserCreateForm, CustomAuthenticationForm, CustomAuthenticationTokenForm, CustomBackupTokenForm
from .models import CustomUser
from .tokens import account_activation_token

User = get_user_model()

class CustomUserCreateView(CreateView):
    model = CustomUser
    form_class = CustomUserCreateForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('signup_done')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_email_active = False
        user.save()

        current_site = get_current_site(self.request)
        mail_subject = 'Activate your account'
        message = render_to_string('registration/account_activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        email = EmailMessage(mail_subject, message, to=[user.email])
        email.send()
        return redirect('signup_done')


class CustomLoginView(TFLoginView):
    form_list = (
                ('auth', CustomAuthenticationForm),
                ('token', CustomAuthenticationTokenForm),
                ('backup', CustomBackupTokenForm)
            )

    def get_form_class(self, step):
        if step == 'auth':
            return CustomAuthenticationForm
        elif step == 'token':
            return CustomAuthenticationTokenForm
        elif step == 'backup':
            return CustomBackupTokenForm
        return super().get_form_class(step)


class ActivateAccountView(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_email_active = True
            user.save()
            return redirect('activate_successful')
        else:
            return HttpResponse('Activation link is invalid!')
