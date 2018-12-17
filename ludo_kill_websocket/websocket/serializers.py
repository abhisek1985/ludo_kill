from rest_framework import serializers
from .models import PlayerBoardDetail, LiveGameRoom


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
    message_type = serializers.CharField(max_length=255, required=True)  # massage_type: CURRENT_STATE, UPDATE_BOARD
    token_data = serializers.CharField(required=False)


class PlayerBoardDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerBoardDetail
        fields = ('user', 'player_id', 'token_data')

class LiveGameRoomSerializer(serializers.ModelSerializer):
    playerlist_details = PlayerBoardDetailSerializer(many=True)
    class Meta:
        model = LiveGameRoom
        fields = ('playerlist_details',)