from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import merchant, branch, Role, user, giftCard

class MerchantGiftCardViewTest(APITestCase):
    def setUp(self):
        # Create required related objects
        
         # Create the merchant first
        self.merchant = merchant.objects.create(
            businessname="Test Merchant",
            merchantemailaddress="merchant@example.com",
            active=True,
            serviceID="12345"
    )
        self.branch = branch.objects.create(branchname="Main Branch", merchID=self.merchant)
        self.role_manager = Role.objects.create(name="Manager")
        self.merchant = merchant.objects.create(
            businessname="Test Merchant",
            merchantemailaddress="merchant@example.com",
            active=True,
            serviceID="12345"
        )
        # Create a user with Manager role
        self.manager_user = user.objects.create(
            username="manager1",
            name="Manager One",
            userpassword="testpass123",  # You may need to hash this if your model requires
            branchID=self.branch,
            merchID=self.merchant,
            role=self.role_manager
        )
        # Issue JWT token for the manager
        refresh = RefreshToken.for_user(self.manager_user)
        self.access_token = str(refresh.access_token)
        # Set endpoint URL (adjust if your route is different)
        self.url = '/merchantgiftcard/'  # Use your actual route name

    def test_authentication_required(self):
        """Test that authentication is required."""
        data = {
            "count": 1,
            "merchID": self.merchant.id,
            "name": "Promo Card",
            "amount": 1000,
            "voucher_date": "2025-12-31"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_can_create_giftcard(self):
        """Test that a manager can create gift cards."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        data = {
            "count": 2,
            "merchID": self.merchant.id,
            "name": "Promo Card",
            "amount": 1000,
            "voucher_date": "2025-12-31"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['status'], 'True')
        self.assertEqual(giftCard.objects.filter(merchID=self.merchant).count(), 2)

    def test_non_manager_cannot_create_giftcard(self):
        """Test that a non-manager cannot create gift cards."""
        # Create a user with a different role
        role_accountant = Role.objects.create(name="Accountant")
        accountant_user = user.objects.create(
            username="accountant1",
            name="Accountant One",
            userpassword="testpass123",
            branchID=self.branch,
            merchID=self.merchant,
            role=role_accountant
        )
        refresh = RefreshToken.for_user(accountant_user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        data = {
            "count": 1,
            "merchID": self.merchant.id,
            "name": "Promo Card",
            "amount": 1000,
            "voucher_date": "2025-12-31"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)