from django.urls import path
from .views import create_user, delete_user, login_user, logout_user, create_room, JoinRoom

urlpatterns = [
    path('create_user/', create_user),
    path('delete_user/', delete_user),
    path('login_user/', login_user),
    path('logout_user/', logout_user),
    path('create_room/', create_room),
    path('ws/join_room/', JoinRoom.as_view())
]