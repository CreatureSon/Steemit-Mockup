from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Post(models.Model):
    # Local Participant Field
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="posts", 
        null=True,
        blank=True
    )

    resteemed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resteems'
    )

    original_post = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resteem_copies'
    )

    # Post Association Fields
    author = models.CharField(max_length=75)
    permlink = models.CharField(max_length=255, blank=True, null=True)

    # Author Associated Fields
    author_image = models.URLField(max_length=500, blank=True)
    author_reputation = models.IntegerField(default=25)

    # Post Data Fields
    title = models.CharField(max_length=150)
    body = models.TextField(max_length=50000)
    body_preview = models.TextField(max_length=10000)
    image_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=200, blank=True)
    category_name = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(default=timezone.now)
    votes = models.IntegerField(default=0)
    payout = models.CharField(max_length=30, default="0.00")

    def save(self, *args, **kwargs):
        self.payout = f"${self.votes * 0.4:,.2f}"
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('author', 'permlink')

    def __str__(self):
        return self.title
    
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True
    )
    
    # Comment Authentication Fields
    author = models.CharField(max_length=75)
    permlink = models.CharField(max_length=255, blank=True, null=True)

    # Author Comment Fields
    author_image = models.URLField(max_length=500, blank=True)
    author_reputation = models.IntegerField(default=25)

    # Comment Data Fields
    body = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    votes = models.IntegerField(default=0)
    payout = models.CharField(max_length=30, default="0.00")

    class Meta:
        unique_together = ('author', 'permlink')

    def save(self, *args, **kwargs):
        self.payout = f"${self.votes * 0.4:,.2f}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.body[:50]}..."
    
class Vote(models.Model):
    UPVOTE = 1
    DOWNVOTE = -1
    VOTE_CHOICES = [
        (UPVOTE, 'Upvote'),
        (DOWNVOTE, 'Downvote'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Generic relation to allow voting on both Posts and Comments
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    value = models.IntegerField(choices=VOTE_CHOICES)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')  # 1 User vote per Post/Comment
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_value_display()} on {self.post}"