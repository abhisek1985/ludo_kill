from channels.db import database_sync_to_async
from .models import Room, UserRoom


class ClientError(Exception):
    """
    Custom exception class that is caught by the websocket receive()
    handler and translated into a send back to the client.
    """
    def __init__(self, code):
        super().__init__(code)
        self.code = code


# This decorator turns this function from a synchronous function into an async one
# we can call from our async consumers, that handles Django DBs correctly.
# For more, see http://channels.readthedocs.io/en/latest/topics/databases.html
@database_sync_to_async
def get_room_or_error(room_id, user):
    """
    Tries to fetch a room for the user, checking permissions along the way.
    """
    # Check if the user is logged in
    if not user.is_authenticated:
        raise ClientError("USER_HAS_TO_LOGIN")
    # Find the room they requested (by ID)
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        raise ClientError("ROOM_INVALID")
    # Check permissions
    # if room.staff_only and not user.is_staff:
    #     raise ClientError("ROOM_ACCESS_DENIED")
    return room


@database_sync_to_async
def user_count(room_id):
    return UserRoom.objects.filter(room_id=room_id).count()







