from django.utils import timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow


@cache_page(20)
def index(request):
    posts = Post.objects.select_related('group').all()
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'index': True}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:10]
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'group': group, 'posts': posts, 'page_obj': page_obj}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated and Follow.objects.filter(
            user=request.user,
            author__username=username
        ).exists()
    )
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': page_obj,
            'paginator': paginator,
            'following': following,
        }
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    author_posts_count = Post.objects.filter(author_id=post.author_id).count()
    comments = Comment.objects.filter(post_id=post_id)
    context = {
        'year': timezone.now().year,
        'post': post,
        'author_posts_count': author_posts_count,
        'form': form,
        'comments': comments}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(request.POST or None, instance=post,)
    if not form.is_valid():
        return render(request, 'posts/update_post.html', {'form': form,
                                                          'post': post})
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'paginator': paginator,
               'follow': True}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follow_user = get_object_or_404(User, username=username)
    if request.user != follow_user:
        Follow.objects.get_or_create(user=request.user, author=follow_user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    unfollow_user = get_object_or_404(User, username=username)
    get_object_or_404(
        Follow,
        user=request.user,
        author=unfollow_user
    ).delete()
    return redirect('posts:profile', username=username)
