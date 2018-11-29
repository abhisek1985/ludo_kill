from django.contrib import admin
from .models import Room, UserRoom

# Register your models here.
admin.site.register(Room)
admin.site.register(UserRoom)