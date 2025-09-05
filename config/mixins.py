from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages import add_message, WARNING


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_superuser:
            add_message(self.request, WARNING, 'You do not have permission to access this resource.')
            return False
        return True
