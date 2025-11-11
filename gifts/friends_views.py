from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Profile
from .friends import Friend
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator

User = get_user_model()

@login_required
def find_users(request):
    q = request.GET.get('q', '').strip()
    users = []
    if q:
        users = Profile.objects.filter(
            Q(user__username__icontains=q) |
            Q(display_name__icontains=q)
        ).exclude(user=request.user)
        
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    return render(request, 'gifts/find_users.html', {
        'users': users,
        'query': q,
        'hide_sidebar': True
    })

@login_required
def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    try:
        requester_profile, _ = Profile.objects.get_or_create(user=request.user)
    except Exception:
        requester_profile = None

    is_friend = requester_profile.is_friend_with(profile) if requester_profile else False
    has_pending = requester_profile.has_friend_request_from(profile) if requester_profile else False
    
    saved = profile.user.saved_items.select_related('gift').all() if is_friend else []
    
    return render(request, 'gifts/view_profile.html', {
        'profile': profile,
        'is_friend': is_friend,
        'has_pending': has_pending,
        'saved': saved,
        'hide_sidebar': True
    })

@login_required
def friend_list(request):
    try:
        requester_profile, _ = Profile.objects.get_or_create(user=request.user)
        friends = requester_profile.get_friends()
        pending = requester_profile.get_pending_friend_requests()
    except Exception:
        friends = []
        pending = []
    
    return render(request, 'gifts/friends.html', {
        'friends': friends,
        'pending': pending,
        'hide_sidebar': True
    })

@login_required
def send_friend_request(request, username):
    if request.method == 'POST':
        receiver = get_object_or_404(User, username=username)
        friend_request, created = Friend.objects.get_or_create(
            sender=request.user.profile,
            receiver=receiver.profile,
            defaults={'status': 'pending'}
        )

        # Create notification if new request
        if created:
            from chat.models import Notification
            Notification.create_friend_request(request.user, receiver)

            # Send real-time notification via WebSocket
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'notifications_{receiver.id}',
                    {
                        'type': 'notification_message',
                        'message': {
                            'type': 'friend_request',
                            'from': request.user.username,
                        }
                    }
                )
            except Exception as e:
                print(f"Failed to send real-time notification: {e}")

        return JsonResponse({'status': 'sent'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def accept_friend_request(request, request_id):
    if request.method == 'POST':
        friend_request = get_object_or_404(
            Friend,
            id=request_id,
            receiver=Profile.objects.get(user=request.user),
            status='pending'
        )
        friend_request.status = 'accepted'
        friend_request.save()
        return JsonResponse({'status': 'accepted'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def decline_friend_request(request, request_id):
    if request.method == 'POST':
        friend_request = get_object_or_404(
            Friend,
            id=request_id,
            receiver=Profile.objects.get(user=request.user),
            status='pending'
        )
        friend_request.delete()
        return JsonResponse({'status': 'declined'})
    return JsonResponse({'status': 'error'}, status=400)