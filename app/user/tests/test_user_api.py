from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test that users API (public)"""
    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'top4glory',
            'name': 'Test name'
        }

        # Check if the HTTP post request is returned with a 201 HTTP Code
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Check if the password of the created user is same as specified in
        # payload
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))

        # Check if the password is not returned as part of the JSON response
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating a user that already exists"""

        # Create a dummy user in the db
        payload = {
            'email': 'test@gmail.com',
            'password': 'top4glory',
            'name': 'Test name'
        }
        create_user(**payload)

        # Now create a user that already exists with API, the response should
        # be a BAD REQUEST
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 5 characters"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'pw',
            'name': 'Test name'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Now check that the user should not be created
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a new token is generated for the user"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'top4glory'
        }

        # First let's create a user in the system so that we can fetch its
        # user token
        create_user(**payload)

        # Now make API call to generate token
        res = self.client.post(TOKEN_URL, payload)

        # Check now that the token is in the API response
        self.assertIn('token', res.data)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        # First let's create a different user in the system
        create_user(email='test@gmail.com', password='top4glory')

        # Now let's try generating a token with wrong password
        payload = {
            'email': 'test@gmail.com',
            'password': 'wrong'
        }
        res = self.client.post(TOKEN_URL, payload)

        # Check now that the token should not be generated
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user doesn't exist"""
        # Now let's try generating a token with a user that is not in the
        # system
        payload = {
            'email': 'test@gmail.com',
            'password': 'top4glory'
        }
        res = self.client.post(TOKEN_URL, payload)

        # Check now that the token should not be generated
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""
        res = self.client.post(TOKEN_URL, {'email': 'one', 'password': ''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for /me endpoint"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""
    def setUp(self) -> None:
        self.user = create_user(
            email='test@gmail.com',
            password='top4glory',
            name='Test User'
        )
        self.client = APIClient()
        # This method forces Django to authenticate all the requests for the
        # specified user by bypassing authentication at backend
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)
        # API returns 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # The properties of returned user are same as the requesting user
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def post_me_not_allowed(self):
        """Test that post is not required on the /me URL"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        # Make a patch request to update user profile properties
        payload = {
            'name': 'New Name',
            'password': 'New Password'
        }
        res = self.client.patch(ME_URL, payload)

        # refrest the user from the db so that changes made by the api are
        # reflected
        self.user.refresh_from_db()

        # Check that the user properties are set equal to specified in payload
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
