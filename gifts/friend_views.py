from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .friends import Friend
from .models import Profile

User = get_user_model()


@login_required
def find_users(request):
    """Пошук користувачів для додавання в друзі"""
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

    try:
        requester_profile, _ = Profile.objects.get_or_create(user=request.user)
        friends = requester_profile.get_friends().select_related('user')
        friend_usernames = {p.user.username for p in friends}
        pending_usernames = set(
            Friend.objects.filter(sender=requester_profile, status='pending')
            .values_list('receiver__user__username', flat=True)
        )
    except Exception:
        friend_usernames = set()
        pending_usernames = set()

    return render(request, 'gifts/find_users.html', {
        'users': users,
        'query': q,
        'hide_sidebar': True,
        'friend_usernames': friend_usernames,
        'pending_usernames': pending_usernames,
    })


@login_required
def view_profile(request, username):
    """Перегляд профілю користувача"""
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)

    try:
        requester_profile, _ = Profile.objects.get_or_create(user=request.user)
    except Exception:
        requester_profile = None

    is_friend = requester_profile.is_friend_with(profile) if requester_profile else False
    has_pending = requester_profile.has_pending_request_with(profile) if requester_profile else False

    saved = []
    if is_friend:
        saved = profile.user.saved_items.select_related('gift').all()

    return render(request, 'gifts/view_profile.html', {
        'profile': profile,
        'is_friend': is_friend,
        'has_pending': has_pending,
        'saved': saved,
        'hide_sidebar': True
    })


@login_required
def friend_list(request):
    """Список друзів"""
    try:
        requester_profile, _ = Profile.objects.get_or_create(user=request.user)
        friends = requester_profile.get_friends().select_related('user')
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
@require_POST
def add_friend(request, username):
    """Надіслати запит у друзі або прийняти зустрічний"""
    user_to_add = get_object_or_404(User, username=username)
    if user_to_add == request.user:
        return JsonResponse({'status': 'error'}, status=400)

    try:
        requester_profile, _ = Profile.objects.get_or_create(user=request.user)
    except Exception:
        return JsonResponse({'status': 'error'}, status=400)

    target_profile = getattr(user_to_add, 'profile', None)
    if not target_profile:
        return JsonResponse({'status': 'error'}, status=400)

    if requester_profile.is_friend_with(target_profile):
        return JsonResponse({'status': 'friends'})

    # Якщо є зустрічний запит – приймаємо його
    inverse_request = Friend.objects.filter(
        sender=target_profile,
        receiver=requester_profile,
        status='pending'
    ).first()
    if inverse_request:
        inverse_request.status = 'accepted'
        inverse_request.save(update_fields=['status'])
        requester_profile.add_friend(target_profile)
        return JsonResponse({'status': 'accepted'})

    friend_request, created = Friend.objects.get_or_create(
        sender=requester_profile,
        receiver=target_profile,
        defaults={'status': 'pending'}
    )

    if not created:
        if friend_request.status == 'pending':
            return JsonResponse({'status': 'pending'})
        friend_request.status = 'pending'
        friend_request.save(update_fields=['status'])

    if created:
        try:
            from chat.models import Notification
            Notification.create_friend_request(request.user, user_to_add)
        except Exception:
            pass
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{user_to_add.id}',
                {
                    'type': 'notification_message',
                    'message': {
                        'type': 'friend_request',
                        'from': request.user.username,
                    }
                }
            )
        except Exception:
            pass

    return JsonResponse({'status': 'sent'})


@login_required
@require_POST
def remove_friend(request, username):
    """Видалити друга та всі пов'язані запити"""
    user_to_remove = get_object_or_404(User, username=username)
    try:
        requester_profile, _ = Profile.objects.get_or_create(user=request.user)
        target_profile = user_to_remove.profile
    except Exception:
        return JsonResponse({'status': 'error'}, status=400)

    if requester_profile.is_friend_with(target_profile):
        requester_profile.remove_friend(target_profile)

    Friend.objects.filter(
        Q(sender=requester_profile, receiver=target_profile) |
        Q(sender=target_profile, receiver=requester_profile)
    ).delete()

    return JsonResponse({'status': 'removed'})


@login_required
@require_POST
def accept_friend_request(request, request_id):
    """Підтвердити запит у друзі"""
    friend_request = get_object_or_404(
        Friend,
        id=request_id,
        receiver=request.user.profile,
        status='pending'
    )
    friend_request.status = 'accepted'
    friend_request.save(update_fields=['status'])
    request.user.profile.add_friend(friend_request.sender)
    return JsonResponse({'status': 'accepted'})


@login_required
@require_POST
def decline_friend_request(request, request_id):
    """Відхилити запит у друзі"""
    friend_request = get_object_or_404(
        Friend,
        id=request_id,
        receiver=request.user.profile,
        status='pending'
    )
    friend_request.delete()
    return JsonResponse({'status': 'declined'})
