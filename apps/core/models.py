"""Shared model mechanics; no concrete tables.

Bulk updates must set updated_at explicitly. auto_now only covers Model.save().
"""

from django.db import models
from django.utils import timezone


class CreatedAtModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(CreatedAtModel):
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
