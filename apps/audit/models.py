from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditEvent(models.Model):
    """Operational history; append-only behavior belongs to write services."""

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT, related_name="audit_events",
    )
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=60)
    # Deliberately no target FK: audit history survives permitted draft cleanup.
    entity_id = models.BigIntegerField()
    details = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "audit_events"
        indexes = [
            models.Index(fields=["organization", "occurred_at"], name="audit_org_time_idx"),
            models.Index(
                fields=["organization", "entity_type", "entity_id"], name="audit_org_entity_idx",
            ),
        ]

    def __str__(self):
        return f"{self.action}: {self.entity_type} {self.entity_id}"
