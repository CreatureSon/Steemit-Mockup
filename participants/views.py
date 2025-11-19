import os
import pandas as pd

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import Participant
from .forms import ParticipantLoginForm

def begin(request):
    if request.user.is_authenticated:
        return redirect('posts:posts')
    elif request.method == 'POST':
        consent_given = request.POST.get('consent_checkbox')  # checkbox name in form
        if consent_given:
            # Generate unique participant code
            prefix = 'Participant_'
            existing_participants = Participant.objects.filter(is_npc=False).count()
            participant_code = f"{prefix}{existing_participants + 1:03d}"

            # Create new participant
            participant = Participant.objects.create_user(
                participant_code=participant_code,
                password=None,
                is_npc=False,
                is_staff=False,
                is_active=True,
                steem_power=100.00,
                steem_dollars=20.00
            )

            # Log in the user manually (bypassing password)
            participant.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, participant)

            # Store participant_code in session
            request.session['participant_code'] = participant.participant_code

            # Redirect to posts page
            return redirect('posts:posts')

        else:
            # Consent not checked, maybe show an error
            return render(request, 'participants/begin.html', {
                'error': 'You must agree to the consent to continue.'
            })

    return render(request, 'participants/begin.html')

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

                #TODO
                # Add these lines before releasing so no one can login as NPCs
                # Will also just be removing the whole logic to login in the end.
                #if user.is_npc:
                #    error = "Cannot login to this account."
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