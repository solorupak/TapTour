from django import forms
from django.contrib.auth.forms import AuthenticationForm


class SignInForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "username", "placeholder": "you@organization.com", "class": "form-input"}),
    )
    password = forms.CharField(
        label="Password", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Enter your password", "class": "form-input"}),
    )
    remember_me = forms.BooleanField(required=False, label="Remember me for 14 days")
