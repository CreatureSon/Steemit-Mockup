from django.urls import path

from . import views

app_name = 'participants'

urlpatterns = [
    path('', views.begin, name='begin'),
    path('login/', views.participant_login, name='login'),
    path('end/', views.end, name='end'),
    path('wallet/', views.wallet, name='wallet'),
    ]