from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
