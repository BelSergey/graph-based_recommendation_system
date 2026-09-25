from decimal import Decimal

from django.test import TestCase

from .models import Category, Product


class CategoryModelTestCase(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(name="Электроника")

        self.assertEqual(category.name, "Электроника")
        self.assertEqual(str(category), "Электроника")

    def test_category_name_is_unique(self):
        Category.objects.create(name="Электроника")

        with self.assertRaises(Exception):
            Category.objects.create(name="Электроника")

    def test_parent_category(self):
        parent = Category.objects.create(name="Электроника")
        child = Category.objects.create(
            name="Смартфоны",
            parent=parent,
        )

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())


class ProductModelTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Электроника")

    def test_product_creation(self):
        product = Product.objects.create(
            title="Смартфон",
            description="Тестовый смартфон",
            category=self.category,
            price=Decimal("29999.99"),
        )

        self.assertEqual(product.title, "Смартфон")
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.price, Decimal("29999.99"))
        self.assertEqual(str(product), "Смартфон")

    def test_product_belongs_to_category(self):
        product = Product.objects.create(
            title="Ноутбук",
            category=self.category,
            price=Decimal("100000.00"),
        )

        self.assertEqual(self.category.products.count(), 1)
        self.assertEqual(self.category.products.first(), product)


