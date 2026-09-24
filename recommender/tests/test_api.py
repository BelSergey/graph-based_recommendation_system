from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from catalog.models import Category, Product
from users.models import User
from recommender.models import RecommendationModel, RecommendationResult


class RecommendationAPITestCase(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(name='Электроника')
        self.product = Product.objects.create(
            title='Смартфон', category=self.category, price=29999.00
        )
        self.user = User.objects.create_user(
            username='testuser', password='password123'
        )


        self.model_record = RecommendationModel.objects.create(
            algorithm='pagerank',
            version='1',
            file_path='storage/models/pagerank_v1.pkl',
            is_active=True,
        )

        RecommendationResult.objects.create(
            user=self.user,
            model=self.model_record,
            product=self.product,
            score=0.95,
        )

    def test_get_algorithms_list(self):
        """Проверка получения списка доступных моделей/алгоритмов."""
        url = reverse('algorithms')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['algorithm'], 'pagerank')

    def test_recommendations_missing_user_id(self):
        """Проверка ошибки при запросе рекомендаций без параметра user_id."""
        url = reverse('recommendations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_id', response.data)

    def test_recommendations_no_model_found(self):
        """Проверка ошибки 404, если нет ни одной обученной модели."""
        RecommendationModel.objects.all().delete()
        url = reverse('recommendations')
        response = self.client.get(url, {'user_id': self.user.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'No trained model found')

    def test_recommendations_success(self):
        """Успешное получение рекомендаций для пользователя."""
        url = reverse('recommendations')
        response = self.client.get(url, {'user_id': self.user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['algorithm'], 'pagerank')
        self.assertEqual(response.data['version'], '1')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['product']['id'], self.product.id
        )
        self.assertEqual(response.data['results'][0]['score'], 0.95)