"""Editorial models matching SCHEMA.dbml.

The scoped unique keys below prepare for the schema's composite foreign keys.
Ordinary Django ForeignKeys do NOT enforce matching tenant/translation tuples.
Add those composite foreign keys in explicit PostgreSQL migrations before use.
Publication authorization, sanitization, and snapshot immutability belong to the
transactional write services; model declarations alone do not implement them.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import CreatedAtModel, TimestampedModel


class Language(models.Model):

    code = models.CharField(max_length=35, primary_key=True)
    english_name = models.CharField(max_length=80)
    native_name = models.CharField(max_length=80)
    class Meta:
        db_table = "languages"

    def __str__(self):
        return self.english_name


class Collection(TimestampedModel):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT,
        related_name="collections",
    )
    internal_name = models.CharField(max_length=200)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_public = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "collections"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "organization"], name="collection_id_org_uq",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "archived_at"], name="collection_org_archive_idx"),
        ]

    def __str__(self):
        return self.internal_name


class Stop(TimestampedModel):
    """A collection's stop; QR and NFC share its canonical public URL."""

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT, related_name="stops",
    )
    collection = models.ForeignKey(
        Collection, on_delete=models.PROTECT, related_name="stops",
    )
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    internal_name = models.CharField(max_length=200)
    source_language = models.ForeignKey(
        Language, on_delete=models.PROTECT, db_column="source_language_code",
        related_name="source_for_stops",
    )
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "stops"
        
        indexes = [
            models.Index(fields=["organization", "collection"], name="stop_org_collection_idx"),
        ]

    def __str__(self):
        return self.internal_name

    def get_absolute_url(self):
        """Stable visitor path, independent of names and collection membership.

        The visitor application must serve this path. Keep public_id unchanged
        after issuance; editable=False only prevents ordinary form edits.
        """
        return f"/s/{self.public_id}/"

    @property
    def public_url(self):
        """Absolute URL to encode in both the QR code and an NFC URI record.

        Keep PUBLIC_BASE_URL's domain active for the lifetime of issued tags.
        """
        return f"{settings.PUBLIC_BASE_URL.rstrip('/')}{self.get_absolute_url()}"


class StopTranslation(TimestampedModel):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT,
        related_name="stop_translations",
    )
    # Migration: (stop_id, organization_id) -> stops(id, organization_id).
    stop = models.ForeignKey(Stop, on_delete=models.PROTECT, related_name="translations")
    language = models.ForeignKey(
        Language, on_delete=models.PROTECT, db_column="language_code",
        related_name="stop_translations",
    )
    # Each pointer needs a composite FK including this translation's id, stop,
    # and organization, matching the corresponding revision tuple in SCHEMA.dbml.
    working_revision = models.ForeignKey(
        "ContentRevision", on_delete=models.PROTECT, null=True, blank=True,
        related_name="working_for_translations",
    )
    published_revision = models.ForeignKey(
        "ContentRevision", on_delete=models.PROTECT, null=True, blank=True,
        related_name="published_for_translations",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="published_stop_translations",
    )

    class Meta:
        db_table = "stop_translations"
        constraints = [
            models.UniqueConstraint(fields=["stop", "language"], name="stop_language_uq"),
            models.UniqueConstraint(
                fields=["id", "stop", "organization"], name="translation_id_stop_org_uq",
            )
        ]

    def __str__(self):
        return f"Stop {self.stop_id} ({self.language_id})"


class ContentRevision(CreatedAtModel):
    """Snapshot; future write services must prevent edits to saved revisions."""

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT,
        related_name="content_revisions",
    )
    stop = models.ForeignKey(Stop, on_delete=models.PROTECT, related_name="revisions")
    # Migration: (translation, stop, organization) must match one translation.
    stop_translation = models.ForeignKey(
        StopTranslation, on_delete=models.PROTECT, related_name="revisions",
    )
    revision_number = models.IntegerField()
    title = models.CharField(max_length=250, blank=True)
    introduction = models.TextField(blank=True, default="")
    body_html = models.TextField(blank=True, default="")
    # Migration: both asset references must include organization_id.
    hero_image_asset = models.ForeignKey(
        "media.MediaAsset", on_delete=models.PROTECT, null=True, blank=True,
        related_name="hero_revisions",
    )
    hero_image_alt = models.TextField(blank=True, default="")
    hero_image_caption = models.TextField(blank=True, default="")
    audio_asset = models.ForeignKey(
        "media.MediaAsset", on_delete=models.PROTECT, null=True, blank=True,
        related_name="audio_revisions",
    )
    audio_transcript = models.TextField(blank=True, default="")
    source_notes = models.TextField(blank=True, default="")
    # Migration: source revision reference must include stop_id and organization_id.
    based_on_source_revision = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        related_name="derived_revisions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="created_content_revisions",
    )

    class Meta:
        db_table = "content_revisions"
        constraints = [
            models.UniqueConstraint(
                fields=["stop_translation", "revision_number"], name="revision_translation_num_uq",
            ),
            models.UniqueConstraint(
                fields=["id", "stop_translation", "stop", "organization"],
                name="revision_identity_scope_uq",
            ),
            models.UniqueConstraint(
                fields=["id", "stop", "organization"], name="revision_id_stop_org_uq",
            ),
            models.UniqueConstraint(fields=["id", "organization"], name="revision_id_org_uq"),
            models.CheckConstraint(
                condition=models.Q(revision_number__gt=0), name="revision_number_ck",
            ),
            models.CheckConstraint(
                condition=(models.Q(based_on_source_revision__isnull=True)
                           | ~models.Q(based_on_source_revision=models.F("id"))),
                name="revision_source_not_self_ck",
            ),
        ]

    def __str__(self):
        return f"Translation {self.stop_translation_id}, revision {self.revision_number}"


class RevisionImage(models.Model):
    """Gallery snapshot; immutable together with its content revision."""

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT,
        related_name="revision_images",
    )
    # Migration: both references must include organization_id.
    content_revision = models.ForeignKey(
        ContentRevision, on_delete=models.PROTECT, related_name="images",
    )
    media_asset = models.ForeignKey(
        "media.MediaAsset", on_delete=models.PROTECT, related_name="revision_images",
    )
    position = models.IntegerField()
    alt_text = models.TextField(blank=True, default="")
    caption = models.TextField(blank=True, default="")

    class Meta:
        db_table = "revision_images"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_revision", "position"], name="revision_image_position_uq",
            ),
            models.CheckConstraint(
                condition=models.Q(position__gte=0), name="revision_image_position_ck",
            ),
        ]

    def __str__(self):
        return f"Revision {self.content_revision_id}, image {self.position}"


class ApprovalDecision(models.TextChoices):
    APPROVED = "approved", "Approved"
    CHANGES_REQUESTED = "changes_requested", "Changes requested"
    REVOKED = "revoked", "Revoked"


class ApprovalRecord(models.Model):
    """Decision history; corrections must append a new record via write services."""

    content_revision = models.ForeignKey(
        ContentRevision, on_delete=models.PROTECT, related_name="approval_records",
    )
    decision = models.CharField(max_length=20, choices=ApprovalDecision.choices)
    reviewer_name = models.CharField(max_length=200)
    reviewer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="review_decisions",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="recorded_approvals",
    )
    evidence_reference = models.TextField(blank=True, default="")
    comment = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField()
    recorded_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "approval_records"
        get_latest_by = ["recorded_at", "id"]
        indexes = [
            models.Index(
                fields=["content_revision", "recorded_at", "id"],
                name="approval_revision_time_idx",
            ),
        ]

    def __str__(self):
        return f"Revision {self.content_revision_id}: {self.decision}"
