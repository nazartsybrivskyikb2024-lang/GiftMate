from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('new/', views.new_conversation, name='new'),
    path('conversation/<int:conv_id>/', views.conversation_view, name='conversation'),
    path('conversation/<int:conv_id>/send/', views.send_message, name='send_message'),
    path('conversation/<int:conv_id>/messages/', views.get_messages, name='get_messages'),
    path('forward/<int:conv_id>/', views.forward_saved, name='forward_saved'),
]
