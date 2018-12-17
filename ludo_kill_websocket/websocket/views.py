from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.parsers import JSONParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .serializers import UserSerializer, DeleteUserSerializer, CreateRoomSerializer, JoinRoomSerializer, \
    ChatRoomSerializer, PlayerBoardDetailSerializer, LiveGameRoomSerializer
import sys
from django.contrib.auth import authenticate, login, logout
from .models import Room, UserRoom, LiveGameRoom, PlayerBoardDetail
import websockets
import asyncio
import json
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from datetime import datetime
from random import randrange
from rest_framework.decorators import parser_classes, api_view
from .global_member import GlobalMember, KeepMeAlive
from django.core import serializers


def find_websocket_obj(content, user_id):
    r, flag = '', False
    for i in range(len(content)):
        content[i] = content[i].strip('\n')
        if content[i].find(str(user_id)):
            r = content[i]
            flag = True
            break
    if flag:
        websocket_str = r.split(' ', maxsplit=1)[1]
        websocket_obj = getattr(sys.modules[__name__], websocket_str)
        print(websocket_obj)
        return websocket_obj
    else:
        return None



# async def test_websocket(payload=None):
#     # Trying to connect an user to a given room name
#     async with websockets.connect('ws://127.0.0.1:8000/chat/' + payload["room"] +"/"+ payload["user_id"]+'/') as websocket:
#     #async with websockets.connect('ws://127.0.0.1:8000/webchat/') as websocket:
#         greeting = json.loads(await websocket.recv())["message"]
#         print("response received < {}".format(greeting))
#         await websocket.close(close_code=1000)
#         await websocket.send(data=json.dumps(payload))
#         print(">payload send :: {}".format(payload))
#         greeting = json.loads(await websocket.recv())["message"]
#         print("response received < {}".format(greeting))


async def join_websocket(payload=None):
    # Trying to connect an user to a given room name
    ws_url = 'ws://{}:{}/chat/{}/{}/'.format(payload["host"], payload["port"], payload["room"], payload["user_id"])
    print(ws_url)
    websocket = await websockets.connect(ws_url)
    response = json.loads(await websocket.recv())#["message"]
    if response.get("status") == status.HTTP_200_OK:
        UserRoom.objects.get_or_create(user=User.objects.get(username=response.get("username")),
                                room_name=response.get("room_name"))
        print("response received < {}".format(response))

        GlobalMember.uid_ws_dict[payload["user_id"]] = websocket
        print('join_websocket:', GlobalMember.uid_ws_dict)
        msg = {"username": response.get("username"), "user_id": payload["user_id"], "room_name": response.get("room_name")}
        kma = KeepMeAlive(websocket, msg, GlobalMember.uid_loop_dict[str(payload["user_id"])])
        kma.start()
        
    return response


async def get_current_state(user_id=None):
    ws = GlobalMember.uid_ws_dict.get(user_id, None)
    print('chat_websocket ws', GlobalMember.uid_ws_dict)
    print(str(ws))
    if ws is not None:
        response = json.loads(await ws.recv())
        print("response received < {}".format(response))
        return response
    else:
        return None

async def chat_websocket(payload=None):
    print('chat_websocket:', GlobalMember.uid_ws_dict)
    ws = GlobalMember.uid_ws_dict.get(str(payload['user_id']), None)
    print('chat_websocket ws',GlobalMember.uid_ws_dict)
    print(str(ws))
    if ws is not None:
        # payload = {"x": randrange(10, 20), "y": randrange(30, 40), "z": randrange(50,60)}
        await ws.send(data=json.dumps(payload))
        print(">payload send :: {}".format(json.dumps(payload)))
        response = json.loads(await ws.recv())
        print("response received < {}".format(response))
        return response
    else:
        return None


async def close_websocket(user_id=None):
    ws = GlobalMember.uid_ws_dict.get(str(user_id), None)
    if ws is not None:
        await ws.send(data=json.dumps({"message_type": "LEAVE", "user_id": user_id}))

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


def str_to_class(str):
    return getattr(sys.modules[__name__], str)


@csrf_exempt
def create_user(request):
    if request.method == 'POST' or request.method == 'OPTIONS':
        data = request.POST
        serializer = UserSerializer(data=data)

        if serializer.is_valid():
            info = serializer.validated_data
            try:
                User.objects.get(username=info['username'])
            except User.DoesNotExist:
                username = info['username']
                password = info['password']
                user_obj = User.objects.create_user(username=username, password=password)
                user_obj.first_name = info['first_name'] if 'first_name' in info.keys() else ""
                user_obj.last_name = info['last_name'] if 'last_name' in info.keys() else ""
                user_obj.save()

                response_dict = {"status": "created",
                                 "status_code": status.HTTP_201_CREATED,
                                 'username': user_obj.username,
                                 'id': user_obj.id,
                                 'first_name': user_obj.first_name,
                                 'last_name': user_obj.last_name
                                 }
                return JsonResponse(response_dict)
            else:
                return JsonResponse({"data": "User already exist with username: {}".format(info['username']),
                                     "status_code": status.HTTP_400_BAD_REQUEST, "status": "Fail"})
        else:
            return JsonResponse({"data": "Invalid Payload to create user..", "status_code": status.HTTP_400_BAD_REQUEST,
                                 "status": "Fail"})
    else:
        return JsonResponse({"status_code": status.HTTP_400_BAD_REQUEST, "data": "Invalid HTTP Method is selected",
                             "status": "Fail"})


@csrf_exempt
def delete_user(request):
    if request.method == 'POST' or request.method == 'OPTIONS':
        data = request.POST
        serializer = DeleteUserSerializer(data=data)
        if serializer.is_valid():
            info = serializer.validated_data
            try:
                user_obj = User.objects.get(username=info['username'])
            except User.DoesNotExist:
                return JsonResponse({"status_code": status.HTTP_400_BAD_REQUEST,
                                     "data": "User does not exist with username: {}".format(info['username']),
                                     "status": "Fail"})
            else:
                user_obj.delete()
                return JsonResponse({"status_code": status.HTTP_200_OK,
                                     "data": "User with username: {} is deleted successfully".format(info['username']),
                                     "status": "Success"})
        else:
            return JsonResponse({"data": "Invalid Payload to delete user..", "status_code": status.HTTP_400_BAD_REQUEST,
                                 "status": "Fail"})
    else:
        return JsonResponse({"status_code": status.HTTP_400_BAD_REQUEST, "data": "Invalid HTTP Method is selected",
                             "status": "Fail"})


@csrf_exempt
def login_user(request):
    if request.method == 'POST' or request.method == 'OPTIONS':
        data = request.POST
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            info = serializer.validated_data
            username = info['username']
            password = info['password']
            user = authenticate(request, username=username, password=password)
            print('user:', user)
            if user is not None:
                token_key, token = Token.objects.get_or_create(user=user)
                login(request, user)
                return JsonResponse({"username":username, "status_code": status.HTTP_200_OK,
                                     "user_type": user.is_authenticated, "token": token_key.key,
                                     "status": "Success"})
            else:
                return JsonResponse({"status_code": status.HTTP_400_BAD_REQUEST, "data": "Invalid username or password.",
                                     "status": "Fail"})
        else:
            return JsonResponse({"data": "Invalid Payload to authenticate user..",
                                 "status_code": status.HTTP_400_BAD_REQUEST,
                                 "status": "Fail"})

    else:
        return JsonResponse({"status_code": status.HTTP_400_BAD_REQUEST, "data": "Invalid HTTP Method is selected",
                             "status": "Fail"})


@csrf_exempt
def logout_user(request):
    logout(request)


@csrf_exempt
def create_room(request):
    if request.method == 'POST' or request.method == 'OPTIONS':

        data = request.POST
        serializer = CreateRoomSerializer(data=data)
        if serializer.is_valid():
            info = serializer.validated_data
            room_obj, state = Room.objects.get_or_create(title=info["title"])
            if state:
                return JsonResponse({"room_name": room_obj.title, "data": "Room is created with title: {}".format(info['title']),
                                     "status_code": status.HTTP_201_CREATED, "status": "Success"})
            else:
                return JsonResponse({"room_name": room_obj.title, "data": "Room is already exist with title: {}".format(info['title']),
                                     "status_code": status.HTTP_200_OK, "status": "Already exist"})
        else:
            return JsonResponse({"data": "Invalid Payload to create room..", "status_code": status.HTTP_400_BAD_REQUEST,
                                 "status": "Fail"})

    else:
        return JsonResponse({"status_code": status.HTTP_400_BAD_REQUEST, "data": "Invalid HTTP Method is selected",
                             "status": "Fail"})

# @csrf_exempt
# def join_room(request, room_name=None):
class JoinRoom(APIView):
    authentication_classes = (TokenAuthentication,)
    parser_classes = (FormParser,)
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer = JoinRoomSerializer(data=request.POST)
        if serializer.is_valid():
            info = serializer.validated_data
            if request.user.is_authenticated:
                socket_payload = {"command": "join", "room": info['room_name'], "user_id": str(request.user.id),
                                  "host": request.get_host().split(':')[0], "port": request.get_host().split(':')[1]}
                user_id = str(socket_payload["user_id"])
                loop = GlobalMember.uid_loop_dict.get(user_id, None)
                if not loop or (loop and loop.is_closed()):
                    coroutine = join_websocket(payload=socket_payload)
                    loop = asyncio.new_event_loop()
                    print(loop)
                    GlobalMember.uid_loop_dict[user_id] = loop
                    print('JoinRoom',GlobalMember.uid_loop_dict)
                    asyncio.set_event_loop(loop)
                    result = None
                    try:
                        result = loop.run_until_complete(coroutine)
                    except Exception as e:
                        print(e)
                    if result is None:
                        return JsonResponse(dict())
                    else:
                        # live_game_room, created = LiveGameRoom.objects.get_or_create(
                        #     live_room_name=info['room_name'])
                        # player_no = str(live_game_room.playerlist_details.all().count())
                        # if not live_game_room.playerlist_details.filter(user_id=int(user_id)):
                        #     player_board_details = PlayerBoardDetail.objects.create(
                        #         user=User.objects.get(pk=int(user_id)),
                        #         player_id=player_no, token_data=str(GlobalMember.TOKEN_DATA_PLAYER_DICT[player_no]))
                        #     live_game_room.playerlist_details.add(player_board_details)
                        # else:
                        #     player_board_details = live_game_room.playerlist_details.get(
                        #         user_id=int(user_id))
                        # player_board_details_serializer = PlayerBoardDetailSerializer(player_board_details)
                        # print(player_board_details_serializer.data)
                        return JsonResponse(result)
                else:
                    return JsonResponse({"message_type": "JOIN", "status": "{} is already connected".format(request.user.username)})


            else:
                user_obj = User.objects.create_user(username='guest_user_{}'.format(datetime.now().time()), password='pass123')
                socket_payload = {"command": "join", "room": info['room_name'], "user_id": str(user_obj.id),
                                  "host": request.get_host().split(':')[0], "port": request.get_host().split(':')[1]}
                coroutine = join_websocket(payload=socket_payload)
                loop = asyncio.new_event_loop()
                GlobalMember.uid_loop_dict[str(socket_payload["user_id"])] = loop
                print('JoinRoom else',GlobalMember.uid_loop_dict)
                asyncio.set_event_loop(loop)
                result = None
                try:
                    result = loop.run_until_complete(coroutine)
                except Exception as e:
                    print(e)
                if result is None:
                    return JsonResponse(dict())
                else:
                    return JsonResponse(result)

        else:
            return JsonResponse({"data": "Invalid Payload is supplied..",
                             "status_code": status.HTTP_400_BAD_REQUEST,
                             "status": "Fail"})


class ChatRoom(APIView):
    authentication_classes = (TokenAuthentication,)
    parser_classes = (FormParser,)
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ChatRoomSerializer(data=request.POST)
        if serializer.is_valid():
            info = serializer.validated_data
            print('ChatRoom user_id:',info["user_id"])
            if GlobalMember.uid_loop_dict.get(str(info["user_id"]), None):
                coroutine = chat_websocket(payload=info)
                print('chatroom',GlobalMember.uid_loop_dict)
                asyncio.set_event_loop(GlobalMember.uid_loop_dict[str(info["user_id"])])
                result = None
                try:
                    result = GlobalMember.uid_loop_dict[str(info["user_id"])].run_until_complete(coroutine)
                    print('chatroom result:',result)
                except Exception as e:
                    print(e)
                if result is None:
                    return JsonResponse(dict())
                else:
                    return JsonResponse(result)
            else:
                return JsonResponse({"data": "User with user id {} is not connected.".format(str(info["user_id"])),
                                     "status_code": status.HTTP_400_BAD_REQUEST,
                                     "status": "Fail"})
        else:
            return JsonResponse({"data": "Invalid Payload is supplied..",
                                 "status_code": status.HTTP_400_BAD_REQUEST,
                                 "status": "Fail"})


class UpdateResult(APIView):
    authentication_classes = (TokenAuthentication,)
    parser_classes = (FormParser,)
    permission_classes = (AllowAny,)

    def post(self, request):
        user_id = str(request.POST["user_id"])
        loop = GlobalMember.uid_loop_dict.get(user_id, None)
        if loop and not loop.is_closed():
            coroutine = get_current_state(user_id=user_id)
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coroutine)
            return JsonResponse(result)
        else:
            return JsonResponse({
                "data": "User with user_id {} is not connected.".format(user_id),
                "status_code": status.HTTP_200_OK,
                "status": "Success"
            })


class LeaveRoom(APIView):
    authentication_classes = (TokenAuthentication,)
    parser_classes = (FormParser,)
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ChatRoomSerializer(data=request.POST)
        if serializer.is_valid():
            info = serializer.validated_data
            print('ChatRoom user_id:',info["user_id"])
            loop = GlobalMember.uid_loop_dict.get(str(info["user_id"]), None)
            if loop and not loop.is_closed():
                coroutine = close_websocket(user_id=info["user_id"])
                asyncio.set_event_loop(loop)
                loop.run_until_complete(coroutine)
                loop.close()
                return JsonResponse({
                    "data": "User with user_id {} is disconnected.".format(str(info["user_id"])),
                    "status_code": status.HTTP_200_OK,
                    "status": "Success"
                })
            else:
                return JsonResponse({
                    "data": "User with user_id {} is not connected.".format(str(info["user_id"])),
                    "status_code": status.HTTP_200_OK,
                    "status": "Success"
                })
        else:
            return JsonResponse({"data": "Invalid Payload is supplied..",
                                 "status_code": status.HTTP_400_BAD_REQUEST,
                                 "status": "Fail"})