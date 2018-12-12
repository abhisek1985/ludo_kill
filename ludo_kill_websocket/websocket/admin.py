from django.contrib import admin
from .models import Room, UserRoom, PlayerBoardDetail, LiveGameRoom

# Register your models here.
admin.site.register(Room)
admin.site.register(UserRoom)
admin.site.register(PlayerBoardDetail)
admin.site.register(LiveGameRoom)