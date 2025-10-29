from django.db import models

class Post(models.Model):
    post_name = models.CharField(max_length=200)
    post_image = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.post_name

""" class Topping(models.Model):
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    topping_name = models.CharField(max_length=200)

    def __str__(self):
        return self.topping_name """
    
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()
    user = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.text[:50]}..."