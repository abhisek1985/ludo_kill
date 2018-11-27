from django.urls import path
from .consumer import ChatConsumer

websocket_urlpatterns = [
    # path('chat/<int:room_name>/',ChatConsumer),
    # path('ws/heartbeat/<int:clinic_id>/', HeartbeatConsumer)
    path('', ChatConsumer)
]