from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Profile
from django.core.exceptions import ObjectDoesNotExist

@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile object when a new user is created"""
    if created:
        try:
            Profile.objects.create(user=instance)
        except Exception as e:
            print(f"Error creating profile for user {instance.username}: {e}")

@receiver(post_save, sender=get_user_model())
def save_user_profile(sender, instance, **kwargs):
    """Save the Profile when the user is saved"""
    try:
        profile = instance.profile
        profile.save()
    except ObjectDoesNotExist:
        try:
            Profile.objects.create(user=instance)
        except Exception as e:
            print(f"Error creating/saving profile for user {instance.username}: {e}")