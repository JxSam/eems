from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import get_user_model
from landing.models import CustomUser

User = get_user_model()


class UserUpdateForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'username', 'phone_number', 'telegram')
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
            'telegram': forms.TextInput(attrs={'placeholder': '@username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget = forms.HiddenInput()
