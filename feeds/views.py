import datetime
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic.edit import CreateView

from imagekit.models import ProcessedImageField
from annoying.decorators import ajax_request

from . forms import UserCreateForm, PostPictureForm, ProfileEditForm, CommentForm
from . models import UserProfile, IGPost, Comment, Like, Message, Room, Notification

@login_required(login_url='login')
def index(request):

    users_followed = request.user.userprofile.following.all()
    posts = IGPost.objects.filter(
                user_profile__in=users_followed).order_by('-posted_on')

    return render(request, 'feeds/index.html', {
        'posts': posts
    })

@login_required(login_url='login')
def explore(request):
    random_posts = IGPost.objects.all().order_by('?')[:40]
    profiles = []

    context = {
        'posts': random_posts,
    }
    return render(request, 'feeds/explore.html', context)

@login_required(login_url='login')
def search(request, username):
    
    users = User.objects.filter(username__icontains=username)
    profiles = UserProfile.objects.filter(user__in=users)

    # convert to list of dictionaries
    data = []
    for profile in profiles:
        data.append({
            'username': profile.user.username,
            'profile_pic': profile.profile_pic.url if profile.profile_pic else '',
        })

    return JsonResponse({'profiles': data})

@login_required(login_url='login')
def notifications(request):
    user = request.user
    notifications = Notification.objects.filter(notified_user=user).order_by('-id')
    for notification in notifications:
        if not notification.seen:
            notification.seen = True
            notification.save()

    context = {
        'notifications': notifications
    }
    return render(request, 'feeds/notifications.html', context)

@login_required(login_url='login')
def inbox(request):
    user = request.user
    rooms = Room.objects.filter(Q(receiver=user) | Q(sender=user))
    context = {
        'rooms': rooms
    }
    return render(request, 'feeds/inbox.html', context)

@login_required(login_url='login')
def chat(request, label):
    user = request.user
    room = Room.objects.get(label=label)
    messages = room.messages.order_by('-timestamp')

    for message in messages:
        if message.message_sender != user and not message.seen:
            message.seen = True
            message.save()

    context = {
        'room': room,
        'messages': messages[::-1]
    }
    return render(request, 'feeds/chat.html', context)

@login_required(login_url='login')
def like_message(request, id):
    user = request.user
    message = Message.objects.get(id=id)

    if user in message.liked_by.all():
        message.liked_by.remove(user)
    else:
        message.liked_by.add(user)

    return JsonResponse({'likes': message.liked_by.count()})

@login_required(login_url='login')
def new_chat(request):
    profiles = request.user.userprofile.following.all()
    context = {
        'profiles': profiles
    }
    return render(request, 'feeds/new_chat.html', context)

@login_required(login_url='login')
def new_chat_create(request, username):
    user_to_message = User.objects.get(username=username)
    room_label = request.user.username + '_' + user_to_message.username

    try:
        does_room_exist = Room.objects.get(label=room_label)
    except:
        room = Room(label=room_label, receiver=user_to_message,
                    sender=request.user)
        room.save()

    return redirect('chat', label=room_label)

def signup(request):
    form = UserCreateForm()

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            user = User.objects.get(username=request.POST['username'])
            profile = UserProfile(user=user)
            profile.save()

            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect('index')

    return render(request, 'feeds/signup.html', {
        'form': form
    })

def login_user(request):
    form = AuthenticationForm()

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')

    return render(request, 'feeds/login.html', {
        'form': form
    })

@login_required(login_url='login')
def signout(request):
    logout(request)
    return redirect('index')

@login_required(login_url='login')
def profile(request, username):
    user = User.objects.get(username=username)
    if not user:
        return redirect('index')

    profile = UserProfile.objects.get(user=user)
    context = {
        'username': username,
        'user': user,
        'profile': profile
    }
    return render(request, 'feeds/profile.html', context)

@login_required(login_url='login')
def profile_settings(request, username):
    user = User.objects.get(username=username)
    if request.user != user:
        return redirect('index')

    if request.method == 'POST':
        print(request.POST)
        form = ProfileEditForm(request.POST, instance=user.userprofile, files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect(reverse('profile', kwargs={'username': user.username}))
    else:
        form = ProfileEditForm(instance=user.userprofile)

    context = {
        'user': user,
        'form': form
    }
    return render(request, 'feeds/profile_settings.html', context)

@login_required(login_url='login')
def followers(request, username):
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)
    profiles = user_profile.followers.all

    context = {
        'header': 'Followers',
        'profiles': profiles,
    }

    return render(request, 'feeds/follow_list.html', context)

@login_required(login_url='login')
def following(request, username):
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)
    profiles = user_profile.following.all

    context = {
        'header': 'Following',
        'profiles': profiles
    }
    return render(request, 'feeds/follow_list.html', context)

@login_required(login_url='login')
def post_picture(request):
    if request.method == 'POST':
        form = PostPictureForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            post = IGPost(user_profile=request.user.userprofile,
                          title=request.POST['title'],
                          image=request.FILES['image'],
                          posted_on=datetime.datetime.now())
            post.save()
            return redirect(reverse('profile', kwargs={'username': request.user.username}))
    else:
        form = PostPictureForm()

    context = {
        'form': form
    }
    return render(request, 'feeds/post_picture.html', context)

@login_required(login_url='login')
def post(request, pk):
    post = IGPost.objects.get(pk=pk)
    try:
        like = Like.objects.get(post=post, user=request.user)
        liked = 1
    except:
        like = None
        liked = 0

    context = {
        'post': post,
        'liked': liked
    }
    return render(request, 'feeds/post.html', context)

@login_required(login_url='login')
def likes(request, pk):
    #likes = IGPost.objects.get(pk=pk).like_set.all()
    #profiles = [like.user.userprofile for like in likes]

    post = IGPost.objects.get(pk=pk)
    profiles = Like.objects.filter(post=post)

    context = {
        'header': 'Likes',
        'profiles': profiles
    }
    return render(request, 'feeds/follow_list.html', context)

@login_required(login_url='login')
@ajax_request
def add_like(request):
    post_pk = request.POST.get('post_pk')
    post = IGPost.objects.get(pk=post_pk)
    try:
        like = Like(post=post, user=request.user)
        like.save()
        result = 1
    except Exception as e:
        like = Like.objects.get(post=post, user=request.user)
        like.delete()
        result = 0

    return {
        'result': result,
        'post_pk': post_pk
    }

@login_required(login_url='login')
@ajax_request
def add_comment(request):
    comment_text = request.POST.get('comment_text')
    post_pk = request.POST.get('post_pk')
    post = IGPost.objects.get(pk=post_pk)
    commenter_info = {}

    try:
        comment = Comment(comment=comment_text, user=request.user, post=post)
        comment.save()

        username = request.user.username
        profile_url = reverse('profile', kwargs={'username': request.user})

        commenter_info = {
            'username': username,
            'profile_url': profile_url,
            'comment_text': comment_text
        }


        result = 1
    except Exception as e:
        print(e)
        result = 0

    return {
        'result': result,
        'post_pk': post_pk,
        'commenter_info': commenter_info
    }

@ajax_request
@login_required(login_url='login')
def follow_toggle(request):
    user_profile = UserProfile.objects.get(user=request.user)
    follow_profile_pk = request.POST.get('follow_profile_pk')
    follow_profile = UserProfile.objects.get(pk=follow_profile_pk)

    try:
        if user_profile != follow_profile:
            if request.POST.get('type') == 'follow':
                user_profile.following.add(follow_profile)
                follow_profile.followers.add(user_profile)
            elif request.POST.get('type') == 'unfollow':
                user_profile.following.remove(follow_profile)
                follow_profile.followers.remove(user_profile)
            user_profile.save()
            result = 1
        else:
            result = 0
    except Exception as e:
        print(e)
        result = 0

    return {
        'result': result,
        'type': request.POST.get('type'),
        'follow_profile_pk': follow_profile_pk
    }
