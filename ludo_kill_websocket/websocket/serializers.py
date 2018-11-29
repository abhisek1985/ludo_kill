from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, required=True)
    password = serializers.CharField(max_length=200, required=True)
    first_name = serializers.CharField(max_length=255, required=False)
    last_name = serializers.CharField(max_length=255, required=False)


class DeleteUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, required=True)


class CreateRoomSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)


class JoinRoomSerializer(serializers.Serializer):
    room_name = serializers.CharField(max_length=255, required=True)

class ChatRoomSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()