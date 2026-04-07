from django.contrib import admin
from .models import Practical, Practical_text, Practical_work, PracticalFile, PracticalFileStorage


class PracticalAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'visible')

admin.site.register(Practical, PracticalAdmin)
admin.site.register(Practical_text)
admin.site.register(Practical_work)
admin.site.register(PracticalFile)