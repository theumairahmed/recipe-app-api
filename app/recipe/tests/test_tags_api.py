from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTest(TestCase):
    """Test the publicly available Tags API"""
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        # let's create some tags for our user
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        # make an api call to the endpoint to get all the tags of the recipe
        res = self.client.get(TAGS_URL)

        # now manually fetch the tags from the db and compare with res
        tags = Tag.objects.all().order_by('-name')
        # serialize the django model objects into JSON
        serializer = TagSerializer(tags, many=True)

        # tests
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for authenticated user"""
        # create a second user and add some tags to it in DB
        user2 = get_user_model().objects.create_user(
            'other@gmail.com',
            'otherpass'
        )
        Tag.objects.create(user=user2, name='Fruity')

        # create a tag for the authenticated user
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        # now make an API call and compare the retrieved tags
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        # create a tag by API
        payload = {'name': 'Test tag'}
        self.client.post(TAGS_URL, payload)

        # Now check if the Tag exists in DB
        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertEqual(exists, True)

    def test_create_tag_invalid(self):
        """Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        # Create two tags, one assigned to a recipe, other not
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title='Coriander eggs on toast',
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe.tags.add(tag1)

        # Now make API call to fetch only the tags assigned to some recipe
        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        # create a test tag and assign it to two recipes
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=3.00,
            user=self.user
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=2.00,
            user=self.user
        )
        recipe2.tags.add(tag)

        # We need to create a dummy tag so this test fails otherwise since we
        # would only have 1 tag, the count will be 1 only
        Tag.objects.create(user=self.user, name='Lunch')
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
