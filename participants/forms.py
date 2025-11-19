from django import forms

from .models import *

class ParticipantLoginForm(forms.Form):
    participant_code = forms.CharField(
        required = True,
        max_length=20,
        label="Participant Code"
    )
    
    password = forms.CharField(
        required = False,
        widget = forms.PasswordInput,
        label='Password'
    )