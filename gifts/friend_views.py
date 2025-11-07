from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from .models import Profile

User = get_user_model()

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
    # prepare friend usernames for template checks (safe for anonymous users)
    friend_usernames = set()
    if request.user.is_authenticated:
        try:
            friends = request.user.profile.get_friends()
            friend_usernames = {p.user.username for p in friends}
        except Exception:
            friend_usernames = set()

    return render(request, 'gifts/find_users.html', {
        'users': users,
        'query': q,
        'hide_sidebar': True,
        'friend_usernames': friend_usernames,
    })

@login_required
def view_profile(request, username):
    """Перегляд профілю користувача"""
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    is_friend = request.user.profile.is_friend_with(profile)
    
    saved = []
    if is_friend:
        saved = profile.user.saved_items.select_related('gift').all()
    
    return render(request, 'gifts/view_profile.html', {
        'profile': profile,
        'is_friend': is_friend,
        'saved': saved,
        'hide_sidebar': True
    })

@login_required
def friend_list(request):
    """Список друзів"""
    friends = request.user.profile.get_friends()
    
    return render(request, 'gifts/friends.html', {
        'friends': friends,
        'hide_sidebar': True
    })

@login_required
def add_friend(request, username):
    """Додати в друзі"""
    if request.method == 'POST':
        user_to_add = get_object_or_404(User, username=username)
        if request.user.profile.add_friend(user_to_add.profile):
            return JsonResponse({'status': 'added'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def remove_friend(request, username):
    """Видалити з друзів"""
    if request.method == 'POST':
        user_to_remove = get_object_or_404(User, username=username)
        request.user.profile.remove_friend(user_to_remove.profile)
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'error'}, status=400)