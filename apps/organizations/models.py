from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel


class Organization(TimestampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    default_language = models.ForeignKey(
        "content.Language", on_delete=models.PROTECT,
        db_column="default_language_code", related_name="default_for_organizations",
    )
    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "organizations"

    def __str__(self):
        return self.name


class MembershipRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    PUBLISHER = "publisher", "Publisher"
    EDITOR = "editor", "Editor"
    REVIEWER = "reviewer", "Reviewer"
    VIEWER = "viewer", "Viewer"


class Membership(TimestampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="organization_memberships",
    )
    role = models.CharField(max_length=20, choices=MembershipRole.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "organization_memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="membership_org_user_uq",
            )
        ]

    def __str__(self):
        return f"{self.user_id} @ {self.organization_id}: {self.role}"
