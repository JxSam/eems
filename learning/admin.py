from django.contrib import admin
from .models import Content, Subcontent, MatchingPair, Test, Question, Answer, UserContentProgress, UserTestProgress, \
    UserAnswer, Video, Competency


class ContentAdmin(admin.ModelAdmin):

    list_display = ('number', 'title', 'visible')

class SubcontentAdmin(admin.ModelAdmin):

    list_display = ('content', 'step')

class TestAdmin(admin.ModelAdmin):

    list_display = ('content', 'step')

admin.site.register(Content, ContentAdmin)
admin.site.register(Subcontent, SubcontentAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(MatchingPair)
admin.site.register(Question)
admin.site.register(Competency)
admin.site.register(Answer)
# admin.site.register(Text)
class UserContentProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'is_completed')
    list_filter = ('is_completed', 'content')
    search_fields = ('user__username', 'content__title')
    raw_id_fields = ('user', 'content')

class UserTestProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'attempts', 'is_passed', 'last_attempt')
    list_filter = ('is_passed', 'test__content')
    search_fields = ('user__username', 'test__title')
    raw_id_fields = ('user', 'test')

class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'answer', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'question__test')
    search_fields = ('user__username', 'question__text')
    raw_id_fields = ('user', 'question', 'answer')

admin.site.register(UserContentProgress, UserContentProgressAdmin)
admin.site.register(UserTestProgress, UserTestProgressAdmin)
admin.site.register(UserAnswer, UserAnswerAdmin)
admin.site.register(Video)

# Register your models here.
