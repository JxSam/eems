from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Group


admin.site.register(CustomUser)
admin.site.register(Group)
# Register your models here.
