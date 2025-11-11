from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Gift(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='gifts/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='gifts')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('gifts:gift_detail', args=[str(self.id)])

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birthday = models.DateField(null=True, blank=True)
    interests = models.TextField(max_length=500, blank=True, help_text="Інтереси та хобі")
    website = models.URLField(max_length=200, blank=True)
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return self.display_name or self.user.username
    
    def add_friend(self, friend_profile):
        """Додає друга (симетричне відношення)"""
        if friend_profile != self:
            self.friends.add(friend_profile)
            friend_profile.friends.add(self)
            return True
        return False
    
    def remove_friend(self, friend_profile):
        """Видаляє друга (симетричне відношення)"""
        self.friends.remove(friend_profile)
        friend_profile.friends.remove(self)
    
    def is_friend_with(self, profile):
        """Перевіряє чи є другом"""
        return self.friends.filter(id=profile.id).exists()
    
    def get_friends(self):
        """Повертає всіх друзів"""
        return self.friends.all()

    def has_friend_request_from(self, profile):
        """Перевіряє чи є вхідний запит в друзі від певного профілю"""
        try:
            from .friends import Friend
            return Friend.objects.filter(sender=profile, receiver=self, status='pending').exists()
        except Exception:
            return False

    def get_pending_friend_requests(self):
        """Повертає QuerySet вхідних запитів в друзі"""
        try:
            from .friends import Friend
            return Friend.objects.filter(receiver=self, status='pending')
        except Exception:
            return Profile.objects.none()


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.gift}"


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'gift')


class SavedItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_items')
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'gift')



