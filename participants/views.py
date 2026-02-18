import os
import pandas as pd
from random import randint

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .decorators import study_time_required

from .models import Participant
from .forms import ParticipantLoginForm

def begin(request):

    if request.user.is_authenticated:
        return redirect('posts:posts')

    pid = request.GET.get('pid', None)

    assignment = request.GET.get('a', None)
    assignment = int(assignment) if assignment else randint(1, 2)

    if assignment == 1:
        steem_power = 10.00
        steem_dollars = 90.00
    else:
        steem_power = 90.00
        steem_dollars = 10.00

    if pid:
        participant, created = Participant.objects.get_or_create(
            participant_code=pid,
            defaults={
                'participant_image': 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y&s=128',
                'is_staff': False,
                'is_active': True,
                'steem_power': steem_power,
                'steem_dollars': steem_dollars,
            }
        )

        if created:
            # Set unusable password (required by AbstractBaseUser)
            participant.set_unusable_password()
            participant.save()

        request.session['participant_code'] = participant.participant_code
        request.session['joined_at'] = timezone.now().isoformat()

        # Log in the user manually (bypassing password)
        login(request, participant, backend='django.contrib.auth.backends.ModelBackend')

        return redirect('posts:posts')
    
    return render(request, "error.html", {"message": "Missing PID"})

@study_time_required
def participant_login(request):
    error = None
    next_url = request.GET.get('next', None)  # Get the original URL if any

    if request.method != 'POST':
        form = ParticipantLoginForm()
    else:
        form = ParticipantLoginForm(request.POST)
        if form.is_valid():
            participant_code = form.cleaned_data['participant_code']
            password = form.cleaned_data.get('password')

            try:
                user = Participant.objects.get(participant_code=participant_code)

                if user.is_superuser:
                    # Must authenticate with password
                    user_auth = authenticate(
                        request, participant_code=participant_code, password=password
                    )
                    if user_auth is not None:
                        login(request, user_auth)
                        return redirect(next_url or 'posts:posts')
                    else:
                        error = "Invalid password."
                else:
                    # Regular participant: log in manually without password
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    return redirect(next_url or 'posts:posts')

            except Participant.DoesNotExist:
                error = "Participant code does not exist."

    return render(request, 'registration/login.html', {'form': form, 'error': error})

@login_required
def end(request):

    user = request.user
    user_id = user.participant_code
    post_count = user.posts.count()
    comment_count = user.comment_set.count()
    vote_count = user.vote_set.count()
    steem_total = user.steem_power + user.steem_dollars

    new_row = {
        "ID": user_id,
        "Posts": post_count,
        "Comments": comment_count,
        "Votes": vote_count,
        "Steem": steem_total,
        "Steem Power Ratio": 0.00
    }

    file_path = os.path.join(settings.BASE_DIR, "Participant_Data.xlsx")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
    else:
        df = pd.DataFrame(columns=[
            "ID","Posts","Comments","Votes","Steem","Steem Power Ratio"
        ])

    # Appends new participant data
    df.loc[len(df)] = new_row

    # Save excelsheet
    df.to_excel(file_path, index=False)

    # Logout User
    logout(request)

    return render(request, 'participants/end.html')

@login_required
def wallet(request):
    return render(request, 'participants/wallet.html')