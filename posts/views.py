from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *

def index(request):
    return render(request, 'posts/index.html')

@login_required
def posts(request):
    posts = Post.objects.all()

    context = {
        'posts': posts,
        'icons': posts, #ICONS
        'participant': posts #participant
        }

    return render(request, "posts/posts.html", context)

@login_required
def post(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = Comment.objects.filter(post=post)

    context = {
        'post': post, 
        'comments': comments,
        'icons': comments, #ICONS
        'participant': post, #participant
        }

    return render(request, "posts/post.html", context)

@login_required
def new_comment(request, post_id):
    post = Post.objects.get(id=post_id)

    if request.method != 'POST':
        form = CommentForm()
    else:
        form = CommentForm(data=request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.user = request.user
            new_comment.post = post
            new_comment.save()
            return redirect('posts:post', post_id=post_id)

    context = {'form': form, 'post': post}

    return render(request, "posts/new_comment.html", context)

@login_required
def new_post(request):
    if request.method != 'POST':
        form = PostForm()
    else:
        form = PostForm(data=request.POST)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.user = request.user
            new_post.save()
            return redirect('posts:posts')

    context = {'form': form}

    return render(request, "posts/new_post.html", context)