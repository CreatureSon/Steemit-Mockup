from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import ParticipantManager

class Participant(AbstractBaseUser, PermissionsMixin):
    # Unique Login code for participants
    participant_code = models.CharField(max_length=30, unique=True)
    
    # Participant Steemit Balances
    steem_dollars = models.DecimalField(max_digits=20, decimal_places=3, default=0)
    steem_power = models.DecimalField(max_digits=20, decimal_places=3, default=0)
    
    # NPC Account Flag
    is_npc = models.BooleanField(default=True)

    # Required Fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Login Fields
    USERNAME_FIELD = 'participant_code'
    REQUIRED_FIELDS = [] # For createsuperuser

    objects = ParticipantManager()

    def __str__(self):
        return self.participant_code
