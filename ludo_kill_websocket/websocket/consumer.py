from channels.generic.websocket import AsyncJsonWebsocketConsumer, WebsocketConsumer

from .global_member import GlobalMember
from .serializers import PlayerBoardDetailSerializer, LiveGameRoomSerializer
from .utils import ClientError, get_room_or_error, user_count
from django.conf import settings
import requests
import datetime
from .models import UserRoom, PlayerBoardDetail, LiveGameRoom
import json
from channels.auth import login, logout
from django.contrib.auth.models import User
from rest_framework import status
from channels.db import database_sync_to_async

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
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = 'chat_%s' % self.room_name

        # login the new user before assign a channel with room_group
        await login(self.scope, User.objects.get(id=int(self.user_id)))
        # save the session (if the session backend does not access the db you can use `sync_to_async`)
        await database_sync_to_async(self.scope["session"].save)()

        if UserRoom.objects.filter(room_name=self.room_name).count() != 4:
            # Join current user to a room_group and associate a bi-direction channel for communication with other
            # users in same room_group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            # Trying to send JOINING message to other users in room_group
            user = self.scope["user"]
            message = {'username': user.username, "user_id": user.id, "room_name": self.room_name, "message_type": "JOIN",
                       "status":status.HTTP_200_OK}

            # Accepts an incoming socket request from user
            await self.accept()
            result = await self.join_operation(message)
            # await self.channel_layer.group_send(self.room_group_name, {'type': 'join.room', 'message': message})
            await self.send(text_data=json.dumps({**message, **result}))
        else:
            # Accept incoming socket request from user
            await self.accept()
            # Don't assign any channel to this user and add him in Room
            # Trying to send Not JOINING message as response
            user = self.scope["user"]
            message = {'user': user.username, "room_id": self.room_group_name, "message_type": "JOIN Failed Room Filled",
                       "status": status.HTTP_400_BAD_REQUEST}
            await self.send(text_data=json.dumps(message))
            # await self.channel_layer.group_send(self.room_group_name, {'type': 'join.room', 'message': message})

    async def join_room(self, event):
        message = event['message']
        # await self.send(text_data=json.dumps({'message': message}))
        await self.send(text_data=json.dumps(message))

    async def disconnect(self, close_code):
        print('close_code:', close_code)
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Trying to send LEAVE message to other users in room_group
        message = {'user': self.scope["user"].username, "room_id": self.room_group_name, "message_type": "LEAVE"}
        await self.send(text_data=json.dumps(message))
        # await self.channel_layer.group_send(self.room_group_name, {'type': 'leave.room', 'message': message})

    async def leave_room(self, event):
        message = event['message']
        # await self.send(text_data=json.dumps({'message': message}))
        await self.send(text_data=json.dumps(message))

    # Receive message from WebSocket
    async def receive_json(self, content, **kwargs):
        message = content
        print('receive_json:',content)
        if message.get('message_type', None) == 'PING':
            print('--')
        elif message.get('message_type', None) == 'UPDATE_BOARD':
            result = await self.update_board(message)
            await self.channel_layer.group_send(self.room_group_name, {'type': 'chat.message', 'message': result})
        elif message.get('message_type', None) == 'LEAVE':
            await logout(self.scope)
            await self.close()
        # Trying to broadcast chat message over room_group member
        # await self.channel_layer.group_send(self.room_group_name, {'type': 'chat.message', 'message': message})

    async def chat_message(self, event):
        message = event['message']
        # await self.send(text_data=json.dumps({'message': message}))
        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def join_operation(self, message=None):
        print('join_operation_message', message)
        live_game_room, created = LiveGameRoom.objects.get_or_create(live_room_name=self.room_name)
        player_no = str(live_game_room.playerlist_details.all().count())
        if not live_game_room.playerlist_details.filter(user_id=int(message['user_id'])):
            player_board_details = PlayerBoardDetail.objects.create(user=User.objects.get(pk=int(message['user_id'])),
                                                                    player_id=player_no,
                                                                    token_data=str(GlobalMember.TOKEN_DATA_PLAYER_DICT[player_no]))
            live_game_room.playerlist_details.add(player_board_details)
        else:
            player_board_details = live_game_room.playerlist_details.get(user_id=int(message['user_id']))
        player_board_details_serializer = PlayerBoardDetailSerializer(player_board_details)
        return player_board_details_serializer.data

    @database_sync_to_async
    def update_board(self, message=None):
        print('update_board', message)
        # TODO: Write the update code for database
        live_game_room = LiveGameRoom.objects.get(live_room_name=self.room_name)
        live_game_room_serializer = LiveGameRoomSerializer(live_game_room)
        return live_game_room_serializer.data
