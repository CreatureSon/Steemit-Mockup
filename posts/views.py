from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from bs4 import BeautifulSoup
from .models import *
from .forms import *

from participants.decorators import study_time_required

def index(request):
    return render(request, 'posts/index.html')

@login_required
@study_time_required
def posts(request):
    participant = request.user

    if participant.is_staff:
        posts = Post.objects.all()
    else:
        posts = Post.objects.filter(user=None) | Post.objects.filter(user=participant)

    context = {
        'posts': posts,
        'participant': participant
        }

    return render(request, "posts/posts.html", context)

@login_required
@study_time_required
def post(request, post_id):
    participant = request.user
    post = Post.objects.get(id=post_id)

    if participant.is_staff:
        # Only get top-level comments (no parent)
        comments = Comment.objects.filter(post=post, parent__isnull=True)
    else:
        # Only get top-level comments that are visible to this user
        comments = (Comment.objects.filter(post=post, user=None, parent__isnull=True) | 
                   Comment.objects.filter(post=post, user=participant, parent__isnull=True))

    context = {
        'post': post,
        'comments': comments,
        'participant': request.user
        }

    return render(request, "posts/post.html", context)

@login_required
@study_time_required
def new_comment(request, post_id, parent_id=None):
    post = Post.objects.get(id=post_id)
    parent = Comment.objects.get(id=parent_id) if parent_id else None

    if request.method != 'POST':
        form = CommentForm()
    else:
        form = CommentForm(data=request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.user = request.user
            new_comment.post = post
            new_comment.parent = parent
            new_comment.author = request.user.participant_code
            new_comment.author_image = request.user.participant_image
            new_comment.save()
            return redirect('posts:post', post_id=post_id)

    context = {'form': form, 'post': post, 'parent': parent}

    return render(request, "posts/new_comment.html", context)

@login_required
@study_time_required
def new_post(request):
    if request.method != 'POST':
        form = PostForm()
    else:
        form = PostForm(data=request.POST)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.user = request.user
            new_post.author = request.user.participant_code
            new_post.author_image = request.user.participant_image
            new_post.permlink = slugify(new_post.title)

            # New Post Preview
            soup = BeautifulSoup(new_post.body, 'html.parser')
            for img in soup.find_all('img'):
                img.decompose()
            
            new_post.body_preview = soup.get_text(
                separator=' ',
                strip=True
            )

            new_post.save()
            return redirect('posts:posts')

    context = {'form': form}

    return render(request, "posts/new_post.html", context)