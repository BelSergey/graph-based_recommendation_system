from django.test import SimpleTestCase

from recommender.serializers import RecommendationQuerySerializer


class RecommendationQuerySerializerTestCase(SimpleTestCase):
    def test_valid_data(self):
        serializer = RecommendationQuerySerializer(
            data={
                "user_id": 1,
                "top_k": 10,
            }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["user_id"], 1)
        self.assertEqual(serializer.validated_data["top_k"], 10)

    def test_top_k_default(self):
        serializer = RecommendationQuerySerializer(data={"user_id": 1})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["top_k"], 10)

    def test_user_id_is_required(self):
        serializer = RecommendationQuerySerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn("user_id", serializer.errors)

    def test_zero_user_id_is_invalid(self):
        serializer = RecommendationQuerySerializer(data={"user_id": 0})

        self.assertFalse(serializer.is_valid())

    def test_negative_user_id_is_invalid(self):
        serializer = RecommendationQuerySerializer(data={"user_id": -1})

        self.assertFalse(serializer.is_valid())

    def test_zero_top_k_is_invalid(self):
        serializer = RecommendationQuerySerializer(
            data={
                "user_id": 1,
                "top_k": 0,
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_top_k_over_100_is_invalid(self):
        serializer = RecommendationQuerySerializer(
            data={
                "user_id": 1,
                "top_k": 101,
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_top_k_100_is_valid(self):
        serializer = RecommendationQuerySerializer(
            data={
                "user_id": 1,
                "top_k": 100,
            }
        )

        self.assertTrue(serializer.is_valid())
