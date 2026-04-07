from django.urls import path, include
from . import views

urlpatterns = [
    path('editor/practical/', views.practical_editor, name = 'practical_editor'),
    path('editor/lection/', views.editor_course, name = 'editor'),
    path('editor/lection/create/', views.create, name = 'create'),
    path('editor/lection/<slug:slug>/', views.content_edit, name = 'edit'),
    path('editor/lection/edit/<slug:slug>/', views.edit_course, name='edit_course'),
    path('api/tests/<int:test_id>/questions/', views.get_test_questions, name='get_test_questions'),
    path('editor/practical/create/', views.practical_create, name = 'practical_create'),
    path('editor/practical/<slug:slug>/', views.practical_edit, name = 'practical_edit'),
    path('editor/practical/edit/<slug:slug>/', views.edit_practical_more, name='more_practical_edit'),
]