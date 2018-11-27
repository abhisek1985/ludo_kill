from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.parsers import JSONParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .serializers import UserSerializer, DeleteUserSerializer, CreateRoomSerializer
import json
import sys
from django.contrib.auth import authenticate, login, logout
from .models import Room


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
                login(request, user)
                return JsonResponse({"status_code": status.HTTP_200_OK, "user_type": user.is_authenticated,
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
                return JsonResponse({"data": "Room is created with title: {}".format(info['title']),
                                     "status_code": status.HTTP_201_CREATED, "status": "Success"})
            else:
                return JsonResponse({"data": "Room is already exist with title: {}".format(info['title']),
                                     "status_code": status.HTTP_200_OK, "status": "Already exist"})
        else:
            return JsonResponse({"data": "Invalid Payload to create room..", "status_code": status.HTTP_400_BAD_REQUEST,
                                 "status": "Fail"})

    else:
        return JsonResponse({"status_code": status.HTTP_400_BAD_REQUEST, "data": "Invalid HTTP Method is selected",
                             "status": "Fail"})

