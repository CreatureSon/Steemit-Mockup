from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .decorators import study_time_required

from .models import Participant
from posts.models import Vote
from .forms import ParticipantLoginForm

def begin(request):

    if request.user.is_authenticated:
        return redirect('posts:posts')

    pid = request.GET.get('pid', '')
    vestingness = request.GET.get('vestingness', '')
    return_url = request.GET.get('return_url', '')

    if vestingness == 2:
        steem = 10.00
        steem_power = 90.00
    else:
        steem = 90.00
        steem_power = 10.00

    if pid:
        participant, created = Participant.objects.get_or_create(
            participant_code=pid,
            defaults={
                'participant_image': 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y&s=128',
                'is_staff': False,
                'is_active': True,
                'steem_power': steem_power,
                'steem': steem,
                'return_url': return_url,
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
    return_url = user.return_url
    post_count = user.posts.count()
    comment_count = user.comment_set.count()
    vote_count = Vote.objects.filter(user=user).count()
    steem_total = user.steem_power + user.steem

    user.post_count_final = post_count
    user.comment_count_final = comment_count
    user.vote_count_final = vote_count
    user.steem_total_final = steem_total
    user.completed = True
    user.save()

    if return_url:
        params = urlencode({
            'posts': post_count,
            'comments': comment_count,
            'votes': vote_count,
            'steem': float(steem_total),
        })
        return_url = f"{return_url}&{params}"

    # Logout User
    logout(request)

    return render(request, 'participants/end.html', {'return_url': return_url})

@login_required
def wallet(request):
    return render(request, 'participants/wallet.html')