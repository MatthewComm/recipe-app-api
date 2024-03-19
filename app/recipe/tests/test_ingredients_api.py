"""
Tests for ingredients API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(ingredient_id):
    """Create and return a tag detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


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

    def test_partial_ingredient_update(self):
        """Tests partial update of ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Kale')

        payload = {'name': 'Salt'}

        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test delete an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Kale')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by those assigned to recipes."""
        ingredient_1 = Ingredient.objects.create(
            user=self.user,
            name='Ingredient1'
        )
        ingredient_2 = Ingredient.objects.create(
            user=self.user,
            name='Ingredient2'
        )
        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )

        recipe.ingredients.add(ingredient_1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(ingredient_1)
        s2 = IngredientSerializer(ingredient_2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_unique(self):
        """Test filtered ingredients returns a unique list."""
        inggredient = Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Lentils')
        recipe_1 = Recipe.objects.create(
            title='Eggs Benedict',
            time_minutes=60,
            price=Decimal('7.00'),
            user=self.user
        )
        recipe_2 = Recipe.objects.create(
            title='Herb Eggs',
            time_minutes=20,
            price=Decimal('4.00'),
            user=self.user
        )

        recipe_1.ingredients.add(inggredient)
        recipe_2.ingredients.add(inggredient)

        res = self.client.get(INGREDIENTS_URL, {'assigend_only': 1})

        self.assertEqual(len(res.data), 1)
