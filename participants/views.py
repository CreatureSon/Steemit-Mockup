from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from .models import Participant
from .forms import ParticipantLoginForm

def begin(request):
    if request.method == 'POST':
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
                is_active=True
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

    if request.method != 'POST':
        form = ParticipantLoginForm()
    else:
        form = ParticipantLoginForm(request.POST)
        if form.is_valid():
            participant_code = form.cleaned_data['participant_code']
            password = form.cleaned_data.get('password')

            try:
                user = Participant.objects.get(participant_code=participant_code)

                if user.is_npc:
                    error = "Cannot login to this account."
                elif user.is_superuser:
                    # Must authenticate with password
                    user_auth = authenticate(
                        request, participant_code=participant_code, password=password
                    )
                    if user_auth is not None:
                        login(request, user_auth)
                        return redirect('posts:posts')
                    else:
                        error = "Invalid password."
                else:
                    # Regular participant: log in manually without password
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    return redirect('posts:posts')

            except Participant.DoesNotExist:
                error = "code does not exist."

    return render(request, 'registration/login.html', {'form': form, 'error': error})

def end(request):
    # Logout User
    logout(request)

    return render(request, 'participants/end.html')