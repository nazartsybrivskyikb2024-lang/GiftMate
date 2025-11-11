from django.db import models
from django.conf import settings

class Friend(models.Model):
    sender = models.ForeignKey('Profile', related_name='friends_sent', on_delete=models.CASCADE)
    receiver = models.ForeignKey('Profile', related_name='friends_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')
        
    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"