
from datetime import datetime, timezone

from django.test import TestCase

from catalog.models import Category, Product
from users.models import User

from .models import Interaction, InteractionType, WEIGHTS


class InteractionModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")

        self.category = Category.objects.create(name="Электроника")
        self.product = Product.objects.create(
            title="Смартфон",
            category=self.category,
            price=29999,
        )

    def test_view_weight_is_set_automatically(self):
        interaction = Interaction.objects.create(
            user=self.user,
            product=self.product,
            type=InteractionType.VIEW,
            timestamp=datetime(
                2024, 1, 1, 12, 0, tzinfo=timezone.utc
            ),
        )

        self.assertEqual(interaction.weight, WEIGHTS[InteractionType.VIEW])
        self.assertEqual(interaction.weight, 1.0)

    def test_cart_weight_is_set_automatically(self):
        interaction = Interaction.objects.create(
            user=self.user,
            product=self.product,
            type=InteractionType.CART,
            timestamp=datetime(
                2024, 1, 1, 12, 0, tzinfo=timezone.utc
            ),
        )

        self.assertEqual(interaction.weight, 3.0)

    def test_purchase_weight_is_set_automatically(self):
        interaction = Interaction.objects.create(
            user=self.user,
            product=self.product,
            type=InteractionType.PURCHASE,
            timestamp=datetime(
                2024, 1, 1, 12, 0, tzinfo=timezone.utc
            ),
        )

        self.assertEqual(interaction.weight, 5.0)

    def test_historical_timestamp_is_preserved(self):
        timestamp = datetime(
            1997, 1, 1, 12, 30, tzinfo=timezone.utc
        )

        interaction = Interaction.objects.create(
            user=self.user,
            product=self.product,
            type=InteractionType.VIEW,
            timestamp=timestamp,
        )

        interaction.refresh_from_db()

        self.assertEqual(
            interaction.timestamp,
            timestamp,
        )

    def test_weight_is_recalculated_when_type_changes(self):
        interaction = Interaction.objects.create(
            user=self.user,
            product=self.product,
            type=InteractionType.VIEW,
            timestamp=datetime(
                2024, 1, 1, tzinfo=timezone.utc
            ),
        )

        interaction.type = InteractionType.PURCHASE
        interaction.save()
        interaction.refresh_from_db()

        self.assertEqual(interaction.weight, 5.0)

