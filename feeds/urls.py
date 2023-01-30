from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_user, name='login'),
    path('signout/', views.signout, name='signout'),

    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/edit/', views.profile_settings, name='profile_settings'),
    path('profile/<str:username>/followers/', views.followers, name='followers'),
    path('profile/<str:username>/following/', views.following, name='following'),

    path('post/<int:pk>/', views.post, name='post'),
    path('post/', views.post_picture, name='post_picture'),

    path('explore/', views.explore, name='explore'),

    path('search/<str:username>/', views.search, name='search'),

    path('notifications/', views.notifications, name='notifications'),

    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<str:label>/', views.chat, name='chat'),
    path('message/like/<int:id>/', views.like_message, name='like_message'),
    path('new_chat/', views.new_chat, name='new_chat'),
    path('new_chat/<str:username>/', views.new_chat_create, name='new_chat_create'),
    
    path('post/<int:pk>/likes/', views.likes, name='likes'),
    path('like/', views.add_like, name='like'),
    path('comment/', views.add_comment, name='comment'),
    path('follow_toggle/', views.follow_toggle, name='follow_toggle'),
]
