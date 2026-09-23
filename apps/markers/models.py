import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel


def generate_marker_token():
    """192 random bits encoded as exactly 32 URL-safe characters."""
    return secrets.token_urlsafe(24)


class Marker(TimestampedModel):
    """Represent one physical QR/NFC placement linked to a stop.

    Print /r/<token>; it resolves to the stop page /s/<public-id>/.
    Separate markers let one placement retire without retiring the stop.
    Resolution and lifecycle guards still require implementation.
    """

    stop = models.ForeignKey("content.Stop", on_delete=models.PROTECT, related_name="markers")
    token = models.CharField(
        max_length=32, unique=True, default=generate_marker_token, editable=False,
    )
    label = models.CharField(max_length=150)
    placement_notes = models.TextField(blank=True, default="")
    has_qr = models.BooleanField(default=True)
    has_nfc = models.BooleanField(default=False)
    issued_at = models.DateTimeField(null=True, blank=True)
    installed_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)
    retirement_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "markers"

    def __str__(self):
        return self.label

    def get_absolute_url(self) -> str:
        """Return the permanent placement path, without a trailing slash.

        The resolver is implemented in TT-21. Never reuse issued tokens.
        """
        return f"/r/{self.token}"

    @property
    def public_url(self) -> str:
        """Return the URL shared by this placement's printed QR and NFC.

        Keep the configured visitor origin active for issued links.
        """
        return (
            f"{settings.PUBLIC_BASE_URL.rstrip('/')}"
            f"{self.get_absolute_url()}"
        )


class CheckResult(models.TextChoices):
    PASSED = "passed", "Passed"
    FAILED = "failed", "Failed"
    NOT_TESTED = "not_tested", "Not tested"
    NOT_PRESENT = "not_present", "Not present"


class MarkerCheck(models.Model):
    """Verification history; future write services must append rather than edit."""

    marker = models.ForeignKey(Marker, on_delete=models.PROTECT, related_name="checks")
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="marker_checks",
    )
    checked_at = models.DateTimeField(default=timezone.now)
    qr_result = models.CharField(
        max_length=12, choices=CheckResult.choices, default=CheckResult.NOT_TESTED,
    )
    nfc_result = models.CharField(
        max_length=12, choices=CheckResult.choices, default=CheckResult.NOT_TESTED,
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "marker_checks"
        get_latest_by = ["checked_at", "id"]

    def __str__(self):
        return f"Marker {self.marker_id}: QR {self.qr_result}, NFC {self.nfc_result}"
