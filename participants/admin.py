from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, ReadOnlyPasswordHashField
from .managers import ParticipantManager
from .models import Participant
from django import forms

class ParticipantAdminAddForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Participant
        fields = ('participant_code', 'participant_image', 'is_staff', 'is_active', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Always set NPC for admin-created users
        self.fields['is_staff'].initial = False
        self.fields['is_staff'].widget = forms.HiddenInput()
        # Password fields are not required
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].widget = forms.HiddenInput()
        self.fields['password2'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
    
class ParticipantAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text="Raw passwords are not stored, so there is no way to see this user's password, but you can change it using the form below."
    )

    class Meta:
        model = Participant
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.is_npc:
            self.fields['password'].widget = forms.HiddenInput()
            self.fields['groups'].widget = forms.HiddenInput()
            self.fields['user_permissions'].widget = forms.HiddenInput()
            self.fields['is_staff'].widget = forms.HiddenInput()

class ParticipantAdmin(UserAdmin):
    model = Participant
    form = ParticipantAdminChangeForm
    add_form = ParticipantAdminAddForm

    # Fields to show in the admin list
    list_display = ('participant_code', 'participant_image', 'steem_dollars', 'steem_power', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ['participant_code']
    ordering = ['participant_code']

    fieldsets = (
        (None, {'fields': ('participant_code', 'password', 'participant_image')}),
        ('Balances', {'fields': ('steem_dollars', 'steem_power')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('participant_code', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    def get_fieldsets(self, request, obj=None):
        fsets = super().get_fieldsets(request, obj)
        if obj:
            # Filter out the 'Balances' section
            fsets = [fs for fs in fsets if fs[0] != 'Balances']
        return fsets

    def save_model(self, request, obj, form, change):
        obj.set_unusable_password()
        super().save_model(request, obj, form, change)

admin.site.register(Participant, ParticipantAdmin)
