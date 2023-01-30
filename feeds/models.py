from datetime import datetime
from django.db import models
from django.contrib.auth.models import User

from imagekit.models import ProcessedImageField
from middlewares.middleware import RequestMiddleware

from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    followers = models.ManyToManyField('UserProfile',
                                        related_name="followers_profile",
                                        blank=True)
    following = models.ManyToManyField('UserProfile',
                                        related_name="following_profile",
                                        blank=True)
    profile_pic = ProcessedImageField(upload_to='profile_pics',
                                format='JPEG',
                                options={ 'quality': 100},
                                null=True,
                                blank=True)

    description = models.CharField(max_length=200, null=True, blank=True)

    def get_number_of_followers(self):
        print(self.followers.count())
        if self.followers.count():
            return self.followers.count()
        else:
            return 0

    def get_number_of_following(self):
        if self.following.count():
            return self.following.count()
        else:
            return 0

    def get_number_of_unseen_chats(self):
        count = 0
        request = RequestMiddleware(get_response=None)
        user = request.thread_local.current_request.user
        rooms = Room.objects.filter(sender=user) | Room.objects.filter(receiver=user)
        for room in rooms:
            if room.get_unseen_messages():
                count += 1
        return count

    def get_new_notifications(self):
        request = RequestMiddleware(get_response=None)
        user = request.thread_local.current_request.user
        notifications = Notification.objects.filter(notified_user= user, seen=False)
        return notifications.count()

    def __str__(self):
        return self.user.username

class IGPost(models.Model):
    user_profile = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    image = ProcessedImageField(upload_to='posts',
                                format='JPEG',
                                options={ 'quality': 100})
    posted_on = models.DateTimeField(auto_now_add=True)

    def get_number_of_likes(self):
        return self.like_set.count()

    def get_number_of_comments(self):
        return self.comment_set.count()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey('IGPost', on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.CharField(max_length=100)
    posted_on = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.comment


class Like(models.Model):
    post = models.ForeignKey('IGPost', on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return 'Like: ' + self.user.username + ' ' + self.post.title


class Room(models.Model):
    label = models.SlugField(unique=True)
    receiver = models.ForeignKey(User, related_name="receiver", on_delete=models.CASCADE, blank=True, null=True)
    sender = models.ForeignKey(User, related_name="sender", on_delete=models.CASCADE, blank=True, null=True)

    def get_last_message(self):
        message = Message.objects.filter(room=self).last()
        return message.text if message else ""

    def get_last_message_timestamp(self):
        message = Message.objects.filter(room=self).last()
        return message.timestamp if message else ""

    def get_unseen_messages(self):
        request = RequestMiddleware(get_response=None)
        user = request.thread_local.current_request.user
        return Message.objects.filter(room=self, message_receiver=user, seen=False).count()

    def __str__(self):
        return self.label


class Message(models.Model):
    room = models.ForeignKey(Room, related_name="messages", on_delete=models.CASCADE, blank=True, null=True)
    message_sender = models.ForeignKey(User, related_name="message_sender", on_delete=models.CASCADE, blank=True, null=True)
    message_receiver = models.ForeignKey(User, related_name="message_receiver", on_delete=models.CASCADE, blank=True, null=True)
    text = models.TextField()
    liked_by = models.ManyToManyField(User, related_name="liked_by", blank=True)
    seen = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=datetime.now, db_index=True)

    def save(self, *args, **kwargs):
        room_users = self.room.receiver, self.room.sender
        remaining_user = [user for user in room_users if user != self.message_sender][0]
        self.message_receiver = remaining_user
        super(Message, self).save(*args, **kwargs)


    def __str__(self):
        return self.text + " S:" + self.message_sender.username

NOTIFICATION_TYPE = (
    ('L', 'Like'),
    ('C', 'Comment'),
    ('F', 'Follow'),
)
class Notification(models.Model):
    notified_user = models.ForeignKey(User, related_name="notified_user", on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(max_length=1, choices=NOTIFICATION_TYPE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    post = models.ForeignKey('IGPost', on_delete=models.CASCADE, blank=True, null=True)
    seen = models.BooleanField(default=False)

    def get_notification_text(self):
        if self.type == 'L':
            return self.user.username + ' liked your post'
        elif self.type == 'C':
            return self.user.username + ' commented on your post'
        elif self.type == 'F':
            return self.user.username + ' started following you'


    def __str__(self):
        return self.type + " from " + self.user.username + " to " + self.notified_user.username


# notify the user when someone comments on his post
@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, **kwargs):

    if instance.post.user_profile.user != instance.user:
        Notification.objects.create(
            notified_user=instance.post.user_profile.user,
            type='C',
            user=instance.user,
            post=instance.post
        )

# notify the user when someone likes his post
@receiver(post_save, sender=Like)
def like_post_save(sender, instance, **kwargs):

    if instance.post.user_profile.user != instance.user:
        Notification.objects.create(
            notified_user=instance.post.user_profile.user,
            type='L',
            user=instance.user,
            post=instance.post
        )

