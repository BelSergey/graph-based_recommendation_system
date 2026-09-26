from django.test import SimpleTestCase

from recommender.evaluation import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


class EvaluationMetricsTestCase(SimpleTestCase):
    def test_precision_at_k_perfect_prediction(self):
        recommended = [1, 2, 3]
        relevant = {1, 2, 3}

        result = precision_at_k(
            recommended,
            relevant,
            3,
        )

        self.assertEqual(result, 1.0)

    def test_precision_at_k_no_hits(self):
        recommended = [4, 5, 6]
        relevant = {1, 2, 3}

        result = precision_at_k(
            recommended,
            relevant,
            3,
        )

        self.assertEqual(result, 0.0)

    def test_precision_at_k_partial_prediction(self):
        recommended = [1, 4, 5, 6]
        relevant = {1, 2, 3}

        result = precision_at_k(
            recommended,
            relevant,
            4,
        )

        self.assertEqual(result, 0.25)

    def test_recall_at_k_perfect_prediction(self):
        recommended = [1, 2, 3]
        relevant = {1, 2, 3}

        result = recall_at_k(
            recommended,
            relevant,
            3,
        )

        self.assertEqual(result, 1.0)

    def test_recall_at_k_partial_prediction(self):
        recommended = [1, 4, 5]
        relevant = {1, 2, 3}

        result = recall_at_k(
            recommended,
            relevant,
            3,
        )

        self.assertAlmostEqual(result, 1 / 3)

    def test_recall_at_k_no_hits(self):
        recommended = [4, 5, 6]
        relevant = {1, 2, 3}

        result = recall_at_k(
            recommended,
            relevant,
            3,
        )

        self.assertEqual(result, 0.0)

    def test_ndcg_at_k_perfect_prediction(self):
        recommended = [1, 2, 3]
        relevant = {1, 2, 3}

        result = ndcg_at_k(
            recommended,
            relevant,
            3,
        )

        self.assertEqual(result, 1.0)

    def test_ndcg_at_k_no_hits(self):
        recommended = [4, 5, 6]
        relevant = {1, 2, 3}

        result = ndcg_at_k(
            recommended,
            relevant,
            3,
        )

        self.assertEqual(result, 0.0)

    def test_ndcg_rewards_higher_rank(self):
        relevant = {1}

        first = ndcg_at_k([1, 2, 3], relevant, 3)
        last = ndcg_at_k([2, 3, 1], relevant, 3)

        self.assertGreater(first, last)
