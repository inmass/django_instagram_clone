import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Room, User, Message

"""
@channel_session, provides message.chanel_session
"""
class ChatConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
    
    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = text_data_json['user']
        sender = User.objects.get(username=user)

        
        # save message to db
        path = self.scope['path']
        room_label = path.replace('/chat/inbox/', '').replace('/', '')
        room = Room.objects.get(label=room_label)
        message_obj = Message(
            room=room,
            message_sender=sender,
            text=message
        )
        message_obj.save()

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': sender.username,
                'message_id': message_obj.id
            }
        )
        
    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        user = event['user']
        message_id = event['message_id']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'user': user,
            'message_id': message_id
        }))
