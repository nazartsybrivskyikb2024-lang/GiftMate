from django.db import models
from django.conf import settings


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('friend_request', 'Friend Request'),
        ('new_message', 'New Message'),
    )
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    text = models.TextField()
    link = models.CharField(max_length=200)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    @classmethod
    def create_friend_request(cls, from_user, to_user):
        notification = cls.objects.create(
            recipient=to_user,
            sender=from_user,
            notification_type='friend_request',
            text=f'{from_user.username} хоче додати вас у друзі',
            link=f'/profile/{from_user.username}/'
        )
        return notification
        
    @classmethod
    def create_message(cls, from_user, to_user, conversation_id):
        notification = cls.objects.create(
            recipient=to_user,
            sender=from_user,
            notification_type='new_message',
            text=f'Нове повідомлення від {from_user.username}',
            link=f'/chat/conversation/{conversation_id}/'
        )
        return notification