# chat/routing.py
from django.urls import re_path

from feeds import consumers

websocket_urlpatterns = [
    re_path(r"chat/inbox/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
]