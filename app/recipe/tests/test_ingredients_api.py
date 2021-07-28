from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access this endpoint"""

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test APIs accessible by an authenticated user"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testpass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients"""
        # Manually create a few ingredients in DB
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        # Now fetch them manually
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        # Now call the API and compare the response with DB values
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that only ingredients for authenticated user are listed"""
        # Create a new user and add its ingredients
        user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            password='testpass2'
        )
        Ingredient.objects.create(user=user2, name='Banana')

        # Create an ingredient for the first user
        ingredient = Ingredient.objects.create(user=self.user, name='Mango')

        # Check that only ingredients from the authenticated user are returned
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        # Create the ingredient via the API call
        payload = {'name': 'Cabbage'}
        self.client.post(INGREDIENTS_URL, payload)

        # Check that the ingredient now exists in DB or not
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating invalid ingredient fails"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        # Check the status code of API
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
