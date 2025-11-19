from django.db import models
from django.conf import settings

class Post(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="posts", 
        default=2
    )
    title = models.CharField(max_length=75)
    text = models.CharField(max_length=200)
    image = models.ImageField(upload_to='images/')
    date = models.DateTimeField(auto_now_add=True)
    votes = models.IntegerField(default=0)
    tokens = models.CharField(max_length=30, default="0.00")

    def save(self, *args, **kwargs):
        self.tokens = f"${self.votes * 0.4:,.2f}"
        super().save(*args, **kwargs)

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.text[:50]}..."
    
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