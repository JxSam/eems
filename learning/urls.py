from django.urls import path, include
from . import views

urlpatterns = [
    path('message/', views.message, name = 'message'),
    path('check_practical/', views.check_practical, name = 'check_practical'),
    path('update-practical-score/', views.update_practical_score, name='update_practical_score'),
    path('docs/', views.docs, name='docs'),
    path('home/', views.dash, name = 'home'),
    path('settings/', views.settings_page, name = 'settings'),
    path('information/', views.information, name = 'info'),
    path('lection/', views.learn, name = 'learn'),
    path('practical/', views.practical, name = 'practical'),
    path('lection/<slug:slug>/', views.step_redirect, name='preview'),
    path('lection/<slug:slug>/page<int:step>/', views.preview, name='preview'),
    path('check_test/<int:test_id>/', views.check_test, name='check_test'),
    path('error403/', views.zapret, name='zapret'),
    path('practical/<slug:slug>/', views.practical_step_redirect, name='practical_step_preview'),
    path('practical/<slug:slug>/page<int:step>/', views.practical_step_preview, name='practical_step_preview'),
    path('upload/<slug:slug>/<int:step>/', views.upload_practical_file, name='upload_practical_file'),
]