from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Group
from django import forms
from django.contrib.auth import password_validation

class SignUpForm(UserCreationForm):
    error_messages = {
        'password_mismatch': "Пароли не совпадают.",
    }

    username = forms.CharField(
        label="Имя пользователя",
        max_length=150,
        help_text="Только буквы, цифры и @/./+/-/_",
        error_messages={
            'unique': "Пользователь с таким именем уже существует.",
            'required': "Пожалуйста, введите имя пользователя.",
        }
    )

    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput,
        min_length=8,  # Установите минимальную длину 8 символов
        error_messages={
            'min_length': "Пароль слишком короткий. Минимальная длина — 8 символов.",
        },
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Введите тот же пароль, что и выше, для подтверждения.",
    )

    class Meta:
        model = CustomUser
        fields = ('username',)

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

