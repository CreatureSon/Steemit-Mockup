from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts", default=1)
    title = models.CharField(max_length=75)
    text = models.CharField(max_length=200)
    image = models.ImageField(upload_to='images/')
    date = models.DateTimeField(auto_now_add=True)
    votes = models.IntegerField(default=0)
    commentCount = models.IntegerField(default=0)
    tokens = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        self.tokens = self.votes * 0.4
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
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.text[:50]}..."