
from datetime import datetime, timezone

from django.test import TestCase

from catalog.models import Category, Product
from interactions.models import Interaction, InteractionType
from recommender.graph_builder import build_interaction_graph
from users.models import User


class InteractionGraphTestCase(TestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user(
            username="user1"
        )
        self.user_2 = User.objects.create_user(
            username="user2"
        )

        self.category = Category.objects.create(
            name="Электроника"
        )

        self.product_1 = Product.objects.create(
            title="Товар 1",
            category=self.category,
            price=100,
        )

        self.product_2 = Product.objects.create(
            title="Товар 2",
            category=self.category,
            price=200,
        )

        timestamp = datetime(
            2024,
            1,
            1,
            tzinfo=timezone.utc,
        )

        Interaction.objects.create(
            user=self.user_1,
            product=self.product_1,
            type=InteractionType.VIEW,
            timestamp=timestamp,
        )

        Interaction.objects.create(
            user=self.user_1,
            product=self.product_1,
            type=InteractionType.CART,
            timestamp=timestamp,
        )

        Interaction.objects.create(
            user=self.user_2,
            product=self.product_2,
            type=InteractionType.PURCHASE,
            timestamp=timestamp,
        )

    def test_graph_contains_user_and_product_nodes(self):
        graph = build_interaction_graph()

        self.assertIn(
            f"u_{self.user_1.id}",
            graph,
        )
        self.assertIn(
            f"p_{self.product_1.id}",
            graph,
        )

    def test_graph_contains_interaction_edges(self):
        graph = build_interaction_graph()

        self.assertTrue(
            graph.has_edge(
                f"u_{self.user_1.id}",
                f"p_{self.product_1.id}",
            )
        )

    def test_weights_are_summed_for_same_user_product_pair(self):
        graph = build_interaction_graph()

        weight = graph[
            f"u_{self.user_1.id}"
        ][
            f"p_{self.product_1.id}"
        ]["weight"]

        self.assertEqual(weight, 4.0)

    def test_min_weight_filters_edges(self):
        graph = build_interaction_graph(
            min_weight=5.0
        )

        self.assertFalse(
            graph.has_edge(
                f"u_{self.user_1.id}",
                f"p_{self.product_1.id}",
            )
        )

        self.assertTrue(
            graph.has_edge(
                f"u_{self.user_2.id}",
                f"p_{self.product_2.id}",
            )
        )

