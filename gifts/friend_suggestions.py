# Function to get suggested friends for a user
def get_suggested_friends(user):
    """
    Returns a list of suggested friends based on various criteria:
    1. Users who are not yet friends
    2. Users with similar interests
    3. Users in the same location
    4. Users who liked similar gifts
    5. Random selection if not enough suggestions
    """
    from django.db.models import Count, Q
    from random import sample
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Get user's current friends
    if hasattr(user, 'friends'):
        friends_ids = user.friends.values_list('id', flat=True)
    else:
        friends_ids = []
        
    # Base queryset - exclude current user and friends
    qs = User.objects.exclude(id=user.id).exclude(id__in=friends_ids).select_related('profile')
    
    suggestions = []
    
    # 1. Users in the same location (if user has location)
    if user.profile.location:
        location_users = qs.filter(profile__location=user.profile.location)[:5]
        suggestions.extend(list(location_users))
    
    # 2. Users with similar interests (if user has interests)
    if user.profile.interests:
        interests_users = qs.filter(profile__interests__icontains=user.profile.interests)[:5]
        suggestions.extend(list(interests_users))
    
    # 3. Users who liked similar gifts
    if hasattr(user, 'likes'):
        user_liked_gifts = user.likes.values_list('gift_id', flat=True)
        similar_users = qs.filter(likes__gift_id__in=user_liked_gifts).distinct()[:5]
        suggestions.extend(list(similar_users))
    
    # Remove duplicates while preserving order
    suggestions = list(dict.fromkeys(suggestions))
    
    # 4. If we don't have enough suggestions, add random users
    if len(suggestions) < 5:
        remaining_users = list(qs.exclude(id__in=[u.id for u in suggestions]))
        if remaining_users:
            random_users = sample(remaining_users, min(5 - len(suggestions), len(remaining_users)))
            suggestions.extend(random_users)
    
    # Return only first 5 suggestions
    return suggestions[:5]