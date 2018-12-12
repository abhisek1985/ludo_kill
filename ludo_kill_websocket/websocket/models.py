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
    room_name = models.CharField(verbose_name="Room name for associated user", max_length=255, default="")

    def __str__(self):
        return "User ID :{} from Room ID: {}".format(str(self.user.id), self.room_name)


class PlayerBoardDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    player_id = models.CharField(max_length=1, help_text="player id will be 0 or 1 or 2 or 3")
    is_online = models.CharField(max_length=1, help_text='1=online, 0=offline')
    token_data = models.TextField(default='')

    def __str__(self):
        return "player_id: {}, user_name: {}".format(self.player_id, str(self.user.username))


class LiveGameRoom(models.Model):
    live_room_name = models.CharField(max_length=100, unique=True)
    playerlist_details = models.ManyToManyField(PlayerBoardDetail)

    def __str__(self):
        return 'live_room_name: {}'.format(self.live_room_name)
