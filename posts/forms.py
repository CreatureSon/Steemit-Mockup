from django import forms

from .models import *

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'user':'Name:',
            'text':''
            }

        widgets = {'text':forms.Textarea(attrs={'cols':80})}

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text']
        labels = {
            'title':'Title:',
            'text':'Description:'
            }

        widgets = {
            'title':forms.TextInput(attrs={'size':80}),
            'text':forms.Textarea(attrs={'cols':80, 'rows':4}),
            }