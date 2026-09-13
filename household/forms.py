from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class ShoppingForm(forms.Form):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'placeholder': 'Milk'}))
    section = forms.CharField(max_length=80, required=False, widget=forms.TextInput(attrs={'placeholder': 'Fridge'}))
    list_type = forms.ChoiceField(choices=[('groceries', 'Groceries'), ('other', 'Other shopping')])
    note = forms.CharField(max_length=260, required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional note'}))


class SignupForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    first_name = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise ValidationError('An account with that email already exists.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)
        return password
