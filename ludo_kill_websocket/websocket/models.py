from django.db import models
from django.contrib.auth.models import User


class Room(models.Model):
    """
    A room for people to chat in.
    """
    # Room title
    title = models.CharField(max_length=255)
    # If only "staff" users are allowed (is_staff on django's User)
    #staff_only = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    @property
    def group_name(self):
        """
        Returns the Channels Group name that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return "room-%s" % self.id


class UserRoom(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    room_id = models.IntegerField(verbose_name="RoomID for associated user")

    def __str__(self):
        return "User ID :{} from Room ID: {}".format(str(self.user.id), str(self.room_id))


