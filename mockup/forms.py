from django import forms

from .models import *

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['user','text']
        labels = {
            'user':'Name:',
            'text':''
            }

        widgets = {'text':forms.Textarea(attrs={'cols':80})}