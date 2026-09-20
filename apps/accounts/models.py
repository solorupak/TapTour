"""Email-based user identity. Configure AUTH_USER_MODEL = 'accounts.User'."""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        return super().normalize_email(email.strip()).lower() if email else ""

    def get_by_natural_key(self, username):
        return self.get(email__iexact=self.normalize_email(username))

    async def aget_by_natural_key(self, username):
        return await self.aget(email__iexact=self.normalize_email(username))

    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        for field in ("is_staff", "is_superuser", "is_active"):
            if extra_fields[field] is not True:
                raise ValueError(f"A superuser must have {field}=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # unique=True also satisfies Django's default authentication model checks.
    # The functional constraint below additionally rejects case-only duplicates.
    email = models.EmailField(max_length=254, unique=True)
    display_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        db_table = "users"
        constraints = [
            models.UniqueConstraint(Lower("email"), name="users_email_ci_uq"),
        ]

    def clean(self):
        super().clean()
        self.email = type(self).objects.normalize_email(self.email)

    def __str__(self):
        return self.email
