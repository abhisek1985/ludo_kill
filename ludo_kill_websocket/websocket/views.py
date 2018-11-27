from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.parsers import JSONParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .serializers import UserSerializer, DeleteUserSerializer, CreateRoomSerializer, JoinRoomSerializer
import sys
from django.contrib.auth import authenticate, login, logout
from .models import Room, UserRoom
import websockets
import asyncio
import json
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser
from datetime import datetime

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


async def test_websocket(payload=None):
    # Trying to connect an user to a given room name
    ws_url = 'ws://{}:{}/chat/{}/{}/'.format(payload["host"], payload["port"], payload["room"], payload["user_id"])
    async with websockets.connect(ws_url) as websocket:
        print(websocket, type(websocket))
        response = json.loads(await websocket.recv())["message"]
        if response.get("status") == status.HTTP_200_OK:
            UserRoom.objects.create(user=User.objects.get(username=response.get("username")),
                                    room_name=response.get("room_name"))

            #print("response received < {}".format(response))
        return response

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
    if (request.method == 'POST' or request.method == 'OPTIONS') and \
            request.content_type == 'application/json' and \
            (not request.body.decode('utf-8') or is_json(request.body.decode('utf-8'))):
        data = {}
        if request.body.decode('utf-8'):
            data = JSONParser().parse(request)
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
    if (request.method == 'POST' or request.method == 'OPTIONS') and \
            request.content_type == 'application/json' and \
            (not request.body.decode('utf-8') or is_json(request.body.decode('utf-8'))):
        data = {}
        if request.body.decode('utf-8'):
            data = JSONParser().parse(request)
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
    if (request.method == 'POST' or request.method == 'OPTIONS') and \
            request.content_type == 'application/json' and \
            (not request.body.decode('utf-8') or is_json(request.body.decode('utf-8'))):
        data = {}
        if request.body.decode('utf-8'):
            data = JSONParser().parse(request)
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            info = serializer.validated_data
            username = info['username']
            password = info['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                token_key, token = Token.objects.get_or_create(user=user)
                login(request, user)
                return JsonResponse({"username":username, "status_code": status.HTTP_200_OK,
                                     "user_type": user.is_authenticated, "token": token_key.key,
                                     "status": "Success"})
            else:
                return JsonResponse({"status_code": status.HTTP_400_BAD_REQUEST, "user_type": user.is_authenticated,
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
    if (request.method == 'POST' or request.method == 'OPTIONS') and \
        request.content_type == 'application/json' and (not request.body.decode('utf-8') or
                                                        is_json(request.body.decode('utf-8'))):
        data = {}
        if request.body.decode('utf-8'):
            data = JSONParser().parse(request)
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
    parser_classes = (JSONParser,)
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer = JoinRoomSerializer(data=request.data)
        if serializer.is_valid():
            info = serializer.validated_data
            if request.user.is_authenticated:
                socket_payload = {"command": "join", "room": info['room_name'], "user_id": str(request.user.id),
                                  "host": request.get_host().split(':')[0], "port": request.get_host().split(':')[1]}
                print(socket_payload)
                coroutine = test_websocket(payload=socket_payload)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = None
                try:
                    result = loop.run_until_complete(coroutine)
                except Exception as e:
                    print(e)
                if result is None:
                    loop.close()
                    return JsonResponse(dict())
                else:
                    loop.close()
                    return JsonResponse(result)

                #return JsonResponse({"username": request.user.username, "room_name": info['room_name']})

            else:
                user_obj = User.objects.create_user(username='guest_user_{}'.format(datetime.now().time()), password='pass123')
                socket_payload = {"command": "join", "room": info['room_name'], "user_id": str(user_obj.id),
                                  "host": request.get_host().split(':')[0], "port": request.get_host().split(':')[1]}
                coroutine = test_websocket(payload=socket_payload)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = None
                try:
                    result = loop.run_until_complete(coroutine)
                except Exception as e:
                    print(e)
                if result is None:
                    loop.close()
                    return JsonResponse(dict())
                else:
                    loop.close()
                    return JsonResponse(result)

                #return JsonResponse({"username": user_obj.username, "room_name": info['room_name']})
        else:
            return JsonResponse({"data": "Invalid Payload is supplied..",
                             "status_code": status.HTTP_400_BAD_REQUEST,
                             "status": "Fail"})
