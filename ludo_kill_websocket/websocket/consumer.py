from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .utils import ClientError, get_room_or_error, user_count
from django.conf import settings
import requests
import datetime
from .models import UserRoom
import json


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    This chat consumer handles websocket connections for chat clients.
    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    ##### WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Are they logged in?
        if self.scope["user"].is_anonymous:
            # # Reject the connection
            # await self.close()

            # Create guest user with timestamp
            url = 'http://{}:{}/create_user/'.format('127.0.0.1', '8000')
            payload = {"username": 'guest_user_{}'.format(datetime.datetime.now()), "password": "pass123"}
            response = requests.post(url=url, data=payload).json()
            print("response:: ", response)
            # Login the guest user
            url = 'http://{}:{}/login_user/'.format('127.0.0.1', '8000')
            payload = {"username": response.get('username'), "password": response.get('password')}
            response = requests.post(url=url, data=payload).json()
            print("response:: ", response)
            if response.get('status') == "Success":
                # Accept connection from guest user
                await self.accept()
            else:
                print("Invalid user details are given at login time")
                # Reject the connection
                await self.close()
        else:
            # Accept the connection
            print(self.scope["user"].username)
            await self.accept()
        # Store which rooms the user has joined on this connection
        self.rooms = set()

    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        command = content.get("command", None)
        print("command", command)
        try:
            if command == "join":
                # Make them join the room
                await self.join_room(content["room"])
            elif command == "leave":
                # Leave the room
                await self.leave_room(content["room"])
            elif command == "send":
                await self.send_room(content["room"], content["message"])
        except ClientError as e:
            # Catch any errors and send it back
            await self.send_json({"error": e.code})

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        for room_id in list(self.rooms):
            try:
                await self.leave_room(room_id)
            except ClientError:
                pass

    ##### Command helper methods called by receive_json

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        print(self.scope["user"])
        room = await get_room_or_error(room_id, self.scope["user"])
        users = user_count(room_id=room.id)
        if users < 4:
            # update UserRoom model
            UserRoom.objects.get_or_create(user=self.scope["user"].username, room_id=room_id)

            # Send a join message if it's turned on
            if settings.NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
                await self.channel_layer.group_send(
                    room.group_name,
                    {
                        "type": "chat.join",
                        "room_id": room_id,
                        "username": self.scope["user"].username,
                    }
                )
            # Store that we're in the room
            self.rooms.add(room_id)
            # Add them to the group so they get room messages
            await self.channel_layer.group_add(
                room.group_name,
                self.channel_name,
            )
            # Instruct their client to finish opening the room
            await self.send_json({
                "join_room_ID": str(room.id),
                "title": room.title,
                "user_count": users,
                "status": "Success"
            })
        else:
            await self.send_json({
                "join_room_ID": str(room.id),
                "title": room.title,
                "user_count": users,
                "status": "Fail"
            })

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        room = await get_room_or_error(room_id, self.scope["user"])
        # Send a leave message if it's turned on
        if settings.NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "chat.leave",
                    "room_id": room_id,
                    "username": self.scope["user"].username,
                }
            )
        # Remove that we're in the room
        self.rooms.discard(room_id)
        # Remove them from the group so they no longer get room messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )
        # Instruct their client to finish closing the room
        await self.send_json({
            "leave": str(room.id),
        })

    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone sends a message to a room.
        """
        # Check they are in this room
        if room_id not in self.rooms:
            raise ClientError("ROOM_ACCESS_DENIED")
        # Get the room and send to the group about it
        room = await get_room_or_error(room_id, self.scope["user"])
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "room_id": room_id,
                "username": self.scope["user"].username,
                "message": message,
            }
        )

    ##### Handlers for messages sent over the channel layer

    # These helper methods are named by the types we send - so chat.join becomes chat_join
    async def chat_join(self, event):
        """
        Called when someone has joined our chat.
        """
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_ENTER,
                "room": event["room_id"],
                "username": event["username"],
            },
        )

    async def chat_leave(self, event):
        """
        Called when someone has left our chat.
        """
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_LEAVE,
                "room": event["room_id"],
                "username": event["username"],
            },
        )

    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        """
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_MESSAGE,
                "room": event["room_id"],
                "username": event["username"],
                "message": event["message"],
            },
        )


class SimpleChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        print(self.scope["user"])
        print("room_name, room_group_name")
        print(self.room_name, self.room_group_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        message = {'user': self.scope["user"].username, "room_id": self.room_group_name}
        await self.accept()
        await self.channel_layer.group_send(self.room_group_name, {'type': 'chat_message', 'message': message})

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive_json(self, content, **kwargs):
        message = content
        print("##### from async def receive_json", message)
        # Send message to room group
        await self.channel_layer.group_send(self.room_group_name, {'type': 'chat_message', 'message': message})

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))