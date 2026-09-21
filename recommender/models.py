from django.conf import settings
from django.db import models
from apps.catalog.models import Product


class RecommendationModel(models.Model):
    algorithm = models.CharField(max_length=32)
    version = models.CharField(max_length=32)
    trained_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=255)
    metrics = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('algorithm', 'version')

    def __str__(self):
        return f'{self.algorithm} v{self.version}'


class RecommendationResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    model = models.ForeignKey(RecommendationModel, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    score = models.FloatField()
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'model'])]
        ordering = ['-score']
