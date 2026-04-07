from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('loaderio-eeb98a1782c3e4576ee0d135cfc64a81/', views.test, name= 'test'),
    path('', views.landing, name= 'landing'),
    path('login/', views.loginform, name = 'login'),
    path('reg/', views.reg, name = 'reg'),
    path('accounts/login/', views.fix_urls, name = 'fix'),
    path('logout/', auth_views.LogoutView.as_view(template_name='start/logout.html'), name='logout'),
]
