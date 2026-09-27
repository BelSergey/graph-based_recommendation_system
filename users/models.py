from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    preferred_category = models.ForeignKey(
        "catalog.Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
