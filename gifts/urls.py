from django.urls import path
from . import views
from . import friend_views
from . import views_profile

app_name = 'gifts'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('gift/<int:gift_id>/like/', views.toggle_like, name='toggle_like'),
    path('gift/<int:gift_id>/save/', views.toggle_save, name='toggle_save'),
    path('gift/<int:gift_id>/', views.gift_detail, name='gift_detail'),
    path('gift/<int:gift_id>/comment/', views.add_comment, name='add_comment'),
    
    # Friend system URLs
    path('find/', friend_views.find_users, name='find_users'),
    path('friends/', friend_views.friend_list, name='friend_list'),
    path('profile/<str:username_or_id>/', views_profile.view_profile, name='view_profile'),
    path('friends/add/<str:username>/', friend_views.add_friend, name='add_friend'),
    path('friends/remove/<str:username>/', friend_views.remove_friend, name='remove_friend'),
    path('friends/accept/<int:request_id>/', friend_views.accept_friend_request, name='accept_friend_request'),
    path('friends/decline/<int:request_id>/', friend_views.decline_friend_request, name='decline_friend_request'),
]
