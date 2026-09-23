from django.test import TestCase
from catalog.models import Category, Product
from interactions.models import Interaction, InteractionType
from recommender.graph_builder import build_interaction_graph
from users.models import User


class GraphBuilderTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Электроника')
        self.product_a = Product.objects.create(
            title='Товар A', category=self.category, price=100
        )
        self.product_b = Product.objects.create(
            title='Товар B', category=self.category, price=200
        )
        self.user = User.objects.create_user(username='alice', password='test1234')

    def test_creates_nodes_and_edge(self):
        Interaction.objects.create(
            user=self.user, product=self.product_a, type=InteractionType.VIEW
        )
        graph = build_interaction_graph()

        self.assertIn(f'u_{self.user.id}', graph.nodes)
        self.assertIn(f'p_{self.product_a.id}', graph.nodes)
        self.assertTrue(graph.has_edge(f'u_{self.user.id}', f'p_{self.product_a.id}'))

    def test_repeated_interactions_sum_weight(self):
        Interaction.objects.create(
            user=self.user, product=self.product_a, type=InteractionType.VIEW
        )
        Interaction.objects.create(
            user=self.user, product=self.product_a, type=InteractionType.PURCHASE
        )
        graph = build_interaction_graph()

        edge_weight = graph[f'u_{self.user.id}'][f'p_{self.product_a.id}']['weight']
        # view (1.0) + purchase (5.0) = 6.0
        self.assertEqual(edge_weight, 6.0)

    def test_no_edge_between_unrelated_user_and_product(self):
        Interaction.objects.create(
            user=self.user, product=self.product_a, type=InteractionType.VIEW
        )
        graph = build_interaction_graph()

        self.assertFalse(graph.has_edge(f'u_{self.user.id}', f'p_{self.product_b.id}'))

    def test_min_weight_filter_removes_weak_edges(self):
        Interaction.objects.create(
            user=self.user, product=self.product_a, type=InteractionType.VIEW  # weight=1.0
        )
        graph = build_interaction_graph(min_weight=2.0)

        self.assertFalse(graph.has_edge(f'u_{self.user.id}', f'p_{self.product_a.id}'))