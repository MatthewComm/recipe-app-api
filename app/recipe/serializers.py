"""Serializers for recipe APIs"""
from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags',
                  'ingredients']
        read_only_fields = ['id']

    def _get_or_create(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        # Get the authenticated user
        auth_user = self.context['request'].user

        # Check if any of the tags from the request exists in the system,
        # if no then it creates it and adds it to the recipe.
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            recipe.Tags.add(tag_obj)

    def _get_or_create_ingredient(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        auth_user = self.context['request'].user

        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient
            )
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        "Create a recipe."

        # Get tags from data and remove it
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])

        # Create recipe with the remaing validated data
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create(tags, recipe),
        self._get_or_create_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.Tags.clear()
            self._get_or_create(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredient(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
