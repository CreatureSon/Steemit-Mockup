from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/', views.posts, name='posts'),
    path('posts/<int:post_id>/', views.post, name='post'),
    path('new_comment/<int:post_id>/', views.new_comment, name='new_comment')
    ]