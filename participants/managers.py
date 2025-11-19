import string, random
from django.contrib.auth.base_user import BaseUserManager

class ParticipantManager(BaseUserManager):

    def create_user(self, participant_code, password=None, **extra_fields):
        if not participant_code:
            raise ValueError('Participants must have a participant code')
        user = self.model(participant_code=participant_code, **extra_fields)
        if user.is_npc:
            user.set_unusable_password()
        else:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, participant_code, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_npc', False)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_npc') is not False:
            raise ValueError('Superuser cannot be an NPC account.')

        return self.create_user(participant_code, password, **extra_fields)
    
    @staticmethod
    def generate_random_password(length=12):
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(chars) for _ in range(length))