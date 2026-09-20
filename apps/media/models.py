from django.conf import settings
from django.db import models

from apps.core.models import CreatedAtModel


class AssetType(models.TextChoices):
    IMAGE = "image", "Image"
    AUDIO = "audio", "Audio"


class AssetStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class MediaAsset(CreatedAtModel):
    """File metadata; ready-file immutability requires the future upload service."""

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT, related_name="media_assets",
    )
    type = models.CharField(max_length=10, choices=AssetType.choices)
    status = models.CharField(
        max_length=12, choices=AssetStatus.choices, default=AssetStatus.PENDING,
    )
    storage_key = models.CharField(max_length=500, unique=True)
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    byte_size = models.BigIntegerField()
    duration_seconds = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True,
    )
    rights_notes = models.TextField(blank=True, default="")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_media_assets",
    )

    class Meta:
        db_table = "media_assets"

    def __str__(self):
        return self.original_filename
