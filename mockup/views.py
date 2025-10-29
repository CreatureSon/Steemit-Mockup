from django.shortcuts import render, redirect
from .models import *
from .forms import *

def index(request):
    return render(request, 'mockup/index.html')

def posts(request):
    posts = Post.objects.all()

    context = {'posts': posts}

    return render(request, "mockup/posts.html", context)

def post(request, post_id):
    post = Post.objects.get(id=post_id)

    comments = Comment.objects.filter(post=post)

    context = {'post': post, 'comments': comments}

    return render(request, "mockup/post.html", context)

def new_comment(request, post_id):
    post = Post.objects.get(id=post_id)

    if request.method != 'POST':
        form = CommentForm()
    else:
        form = CommentForm(data=request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.post = post
            new_comment.save()
            return redirect('posts:post', post_id=post_id)

    context = {'form': form, 'post': post}

    return render(request, "mockup/new_comment.html", context)