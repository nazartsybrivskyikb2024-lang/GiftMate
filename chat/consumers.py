import json
import base64
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile

from .models import Message, Conversation, Notification
from gifts.models import Gift


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.notification_group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial unread count
        unread_count = await self.get_unread_notifications_count()
        await self.send(json.dumps({
            'type': 'notification_count',
            'count': unread_count
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    @database_sync_to_async
    def get_unread_notifications_count(self):
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'mark_read':
                await self.mark_notifications_read()
                unread_count = await self.get_unread_notifications_count()
                await self.send(json.dumps({
                    'type': 'notification_count',
                    'count': unread_count
                }))
        except Exception as e:
            print(f"Error processing notification command: {str(e)}")

    @database_sync_to_async
    def mark_notifications_read(self):
        Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).update(is_read=True)

    async def notification_message(self, event):
        # Ensure we have the correct notification data structure
        message_data = event.get('message', {})
        
        # Add message link if it's from chat
        if message_data.get('type') == 'new_message' and message_data.get('conversation_id'):
            message_data['link'] = f'/chat/conversation/{message_data["conversation_id"]}/'
        
        await self.send(text_data=json.dumps(message_data))



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"[WS CONNECT] room={self.room_name} user={self.user.username}")

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Receive message from WebSocket, save to DB and broadcast to the group.
        """
        try:
            data = json.loads(text_data)
        except Exception as e:
            print(f"[WS PARSE ERROR] {e}; text={text_data[:200]}")
            return

        message_type = data.get('type', 'text')
        
        if message_type == 'mark_read':
            return

        message = (data.get('message') or '').strip()
        fwd_id = data.get('forwarded_gift_id')
        photo_data = data.get('photo') if message_type == 'photo' else None

        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            return

        try:
            print(f"[WS RECEIVE] from={user.username} room={self.room_name} type={message_type}")
        except Exception:
            print(f"[WS RECEIVE] type={message_type}")

        if not (message or photo_data or fwd_id):
            print(f"[WS SKIP] Empty message from {user.username}")
            return

        # Try to resolve forwarded gift (if any)
        forwarded = None
        if fwd_id:
            try:
                forwarded = await database_sync_to_async(Gift.objects.get)(id=int(fwd_id))
            except Exception:
                forwarded = None

        # Persist message to database
        try:
            msg = Message(
                conversation_id=int(self.room_name),
                sender=user,
                text=message,
                forwarded_gift=forwarded,
            )
            
            if photo_data:
                try:
                    if ';base64,' in photo_data:
                        _, photo_data = photo_data.split(';base64,', 1)
                    
                    photo_content = base64.b64decode(photo_data)
                    unique_filename = f'chat_photo_{user.id}_{uuid.uuid4()}.jpg'
                    msg.photo.save(unique_filename, ContentFile(photo_content), save=False)
                    print(f"[PHOTO SAVE] Successfully saved photo {unique_filename}")
                except Exception as e:
                    print(f"[PHOTO ERROR] Failed to save photo: {str(e)}")
                    msg.photo = None
            
            await database_sync_to_async(msg.save)()
            print(f"[MESSAGE SAVED] id={msg.id} photo={bool(msg.photo)}")
        except Exception as e:
            print(f"[MESSAGE ERROR] Failed to save message: {str(e)}")
            msg = None

        forwarded_payload = None
        if forwarded:
            try:
                image = getattr(forwarded, 'image', None)
                forwarded_payload = {
                    'id': forwarded.id,
                    'title': getattr(forwarded, 'title', None),
                    'image': image.url if image and getattr(image, 'name', '') else None,
                }
            except Exception:
                forwarded_payload = None

        # Broadcast to group so all clients receive
        response_data = {
            'type': 'chat_message',
            'message': message,
            'username': user.username,
            'message_id': getattr(msg, 'id', None),
            'forwarded': forwarded_payload,
        }

        if msg and msg.photo:
            response_data['photo_url'] = msg.photo.url

        await self.channel_layer.group_send(self.room_group_name, response_data)

        # Send a lightweight notification to other participants so their
        # notification bell / UI can update in real time.
        try:
            # Load conversation and create notifications for other members
            conv = await database_sync_to_async(Conversation.objects.get)(id=int(self.room_name))
            
            # First create notification records
            recipient_ids = await database_sync_to_async(list)(
                conv.participants.exclude(id=user.id).values_list('id', flat=True)
            )
            
            if msg and recipient_ids:
                from django.contrib.auth import get_user_model
                User = get_user_model()

                for rid in recipient_ids:
                    recipient = await database_sync_to_async(User.objects.get)(id=rid)
                    await database_sync_to_async(Notification.objects.create)(
                        recipient=recipient,
                        sender=user,
                        notification_type='new_message',
                        text=f'Нове повідомлення від {user.username}',
                        link=f'/chat/conversation/{conv.id}/'
                    )
            
            # Then send real-time notifications to connected users
            for rid in recipient_ids:
                notification_payload = {
                    'type': 'notification',
                    'from': user.username,
                    'conversation_id': conv.id,
                    'message_preview': (message or '')[:120],
                    'photo_included': bool(photo_data),
                    'message_id': getattr(msg, 'id', None),
                }
                await self.channel_layer.group_send(
                    f'notifications_{rid}',
                    {
                        'type': 'notification_message',
                        'message': notification_payload,
                    }
                )
        except Exception as e:
            print(f"[NOTIFICATION ERROR] Failed to send notifications: {str(e)}")
            # Continue execution - notifications are non-critical

    async def chat_message(self, event):
        message = event.get('message')
        username = event.get('username')
        message_id = event.get('message_id')
        forwarded = event.get('forwarded')
        photo_url = event.get('photo_url')

        response_data = {
            'message': message,
            'username': username,
            'id': message_id,
        }

        if forwarded:
            response_data['forwarded'] = forwarded

        if photo_url:
            response_data['photo_url'] = photo_url

        await self.send(text_data=json.dumps(response_data))
