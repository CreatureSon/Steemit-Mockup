from django.db import models
from django.conf import settings
from django.utils import timezone

class Post(models.Model):
    # Local Participant Field
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="posts", 
        null=True,
        blank=True
    )

    # Post Association Fields
    author = models.CharField(max_length=75)
    permlink = models.CharField(max_length=255, blank=True, null=True)

    # Post Data Fields
    title = models.CharField(max_length=150)
    body = models.TextField(max_length=50000)
    body_preview = models.TextField(max_length=10000)
    image_url = models.URLField(blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)
    votes = models.IntegerField(default=0)
    payout = models.CharField(max_length=30, default="0.00")

    def save(self, *args, **kwargs):
        self.payout = f"${self.votes * 0.4:,.2f}"
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('author', 'permlink')

    #//TODO
    # Future method for tokens possibly
    # from django.db.models import F

    # tokens = models.GeneratedField(
    #    expression=F('votes') * 0.4,
    #    output_field=models.FloatField(),
    #    db_persist=True,
    # )

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
    
    author = models.CharField(max_length=75)
    body = models.TextField()
    date = models.DateTimeField(default=timezone.now)

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
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="user_vote")
    value = models.IntegerField(choices=VOTE_CHOICES)

    class Meta:
        unique_together = ('user', 'post')  # 1 User vote per Post