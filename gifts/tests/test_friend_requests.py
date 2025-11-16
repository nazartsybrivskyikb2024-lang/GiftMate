from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from gifts.friends import Friend
from gifts.models import Profile


class FriendRequestTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user_one = User.objects.create_user(username='user_one', password='pass12345')
        self.user_two = User.objects.create_user(username='user_two', password='pass12345')
        # Ensure profiles exist for both users
        Profile.objects.get_or_create(user=self.user_one)
        Profile.objects.get_or_create(user=self.user_two)

    def test_send_friend_request_creates_pending_record(self):
        self.client.force_login(self.user_one)
        response = self.client.post(reverse('gifts:add_friend', args=[self.user_two.username]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'sent')
        self.assertTrue(
            Friend.objects.filter(
                sender=self.user_one.profile,
                receiver=self.user_two.profile,
                status='pending'
            ).exists()
        )

    def test_accept_request_makes_users_friends(self):
        self.client.force_login(self.user_one)
        self.client.post(reverse('gifts:add_friend', args=[self.user_two.username]))
        friend_request = Friend.objects.get(sender=self.user_one.profile, receiver=self.user_two.profile)

        self.client.force_login(self.user_two)
        response = self.client.post(reverse('gifts:accept_friend_request', args=[friend_request.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'accepted')
        self.assertTrue(self.user_one.profile.is_friend_with(self.user_two.profile))
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, 'accepted')

    def test_sending_request_to_existing_pending_accepts(self):
        # user_two sends request first
        self.client.force_login(self.user_two)
        self.client.post(reverse('gifts:add_friend', args=[self.user_one.username]))
        self.assertTrue(Friend.objects.filter(sender=self.user_two.profile, receiver=self.user_one.profile).exists())

        # user_one sends request -> should auto-accept
        self.client.force_login(self.user_one)
        response = self.client.post(reverse('gifts:add_friend', args=[self.user_two.username]))
        self.assertEqual(response.json()['status'], 'accepted')
        self.assertTrue(self.user_one.profile.is_friend_with(self.user_two.profile))
