from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import ParticipantManager

class Participant(AbstractBaseUser, PermissionsMixin):
    # Unique Login code for participants
    participant_code = models.CharField(max_length=100, unique=True)
    
    # Participant Steemit Balances
    steem_dollars = models.DecimalField(max_digits=20, decimal_places=3, default=0)
    steem_power = models.DecimalField(max_digits=20, decimal_places=3, default=0)

    # Required Fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Date the User was Created
    date_joined = models.DateTimeField(default=timezone.now)

    # Login Fields
    USERNAME_FIELD = 'participant_code'
    REQUIRED_FIELDS = [] # For createsuperuser

    objects = ParticipantManager()

    def __str__(self):
        return self.participant_code
