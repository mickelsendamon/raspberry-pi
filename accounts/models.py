from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db.models import EmailField, CharField, BooleanField
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None  # remove the username field
    email = EmailField(_('email address'), unique=True)
    first_name = CharField(_('first name'), max_length=150)
    last_name = CharField(_('last name'), max_length=150)
    sms_phone_number = PhoneNumberField()

    is_email_active = BooleanField(default=False)  # required for email verification

    USERNAME_FIELD = 'email'  # use email to log in
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'
