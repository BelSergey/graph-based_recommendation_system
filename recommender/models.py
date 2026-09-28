from django.conf import settings
from django.db import models
from catalog.models import Product


class RecommendationModel(models.Model):
    """Метаданные обученной рекомендательной модели."""

    algorithm = models.CharField(max_length=32)
    version = models.CharField(max_length=32)
    trained_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=255)
    metrics = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=False)
    parameters = models.JSONField(default=dict)

    class Meta:
        unique_together = ("algorithm", "version")
        constraints = [
            models.UniqueConstraint(
                fields=["algorithm"],
                condition=models.Q(is_active=True),
                name="unique_active_model_per_algorithm",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.algorithm} v{self.version}"


class RecommendationResult(models.Model):
    """Предвычисленная рекомендация товара пользователю."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    model = models.ForeignKey(RecommendationModel, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    score = models.FloatField()
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "model", "product"],
                name="unique_recommendation_result",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "model"]),
        ]
        ordering = ["-score"]
