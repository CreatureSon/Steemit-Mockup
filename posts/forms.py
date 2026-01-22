from django import forms

from .models import *

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        labels = {
            'user':'Name:',
            'body':''
            }

        widgets = {'body':forms.Textarea(attrs={'cols':80})}

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body']
        labels = {
            'title':'Title:',
            'body':'Description:'
            }

        widgets = {
            'title':forms.TextInput(attrs={'size':80}),
            'body':forms.Textarea(attrs={'cols':80, 'rows':4}),
            }