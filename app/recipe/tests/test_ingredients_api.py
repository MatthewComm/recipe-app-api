"""
Tests for ingredients API
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(tag_id):
    """Create and return a tag detail URL."""
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicIngredientsApi(TestCase):
    """Tests for unauthenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to make api call"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApi(TestCase):
    """Tests for authenticated API requests."""

    def setUp(self) -> None:
        self.user = create_user(
            email='test@eexample.com',
            password='testpass123',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(
            user=self.user,
            name='Ingredient1'
        )
        Ingredient.objects.create(
            user=self.user,
            name='Ingredient2'
        )

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients limited to authenticated user. """
        user2 = create_user(email='user2@example.com', password='test2pass123')
        Ingredient.objects.create(user=user2, name='Peanuts')
        ingredient = Ingredient.objects.create(user=self.user, name='Kale')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)
