from django.conf import settings
from django.db import models
from catalog.models import Product


class InteractionType(models.TextChoices):
    VIEW = 'view', 'Просмотр'
    CART = 'cart', 'В корзину'
    PURCHASE = 'purchase', 'Покупка'


WEIGHTS = {
    InteractionType.VIEW: 1.0,
    InteractionType.CART: 3.0,
    InteractionType.PURCHASE: 5.0,
}


class Interaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.CharField(max_length=16, choices=InteractionType.choices)
    weight = models.FloatField(editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['product']),
        ]

    def save(self, *args, **kwargs):
        self.weight = WEIGHTS[self.type]
        super().save(*args, **kwargs)
