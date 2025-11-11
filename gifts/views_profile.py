from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import Profile

User = get_user_model()

@login_required
def view_profile(request, username_or_id):
    """View profile by username or ID"""
    try:
        # First try to find by ID
        if username_or_id.isdigit():
            user = get_object_or_404(User, id=username_or_id)
        else:
            # Then try username
            user = get_object_or_404(User, username=username_or_id)
            
        profile = get_object_or_404(Profile, user=user)
        # safely get requester's profile
        try:
            requester_profile, _ = Profile.objects.get_or_create(user=request.user)
        except Exception:
            requester_profile = None

        is_friend = requester_profile.is_friend_with(profile) if requester_profile else False
        
        saved = []
        if is_friend or user == request.user:
            saved = user.saved_items.select_related('gift').all()
        
        return render(request, 'gifts/view_profile.html', {
            'profile': profile,
            'is_friend': is_friend,
            'saved': saved,
            'hide_sidebar': True
        })
    except (Profile.DoesNotExist, User.DoesNotExist):
        return redirect('gifts:home')