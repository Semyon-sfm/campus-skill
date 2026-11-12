from django import forms
from django.contrib.auth import authenticate

from .models import User


class RegisterForm(forms.ModelForm):
    """Регистрация: email + пароль. Валидации пароля нет — по требованию заказчика."""

    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Любой пароль"}),
    )

    class Meta:
        model = User
        fields = ["full_name", "email", "study_group"]
        labels = {
            "full_name": "Имя и фамилия",
            "email": "Email",
            "study_group": "Учебная группа",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Анна Павлова"}),
            "email": forms.EmailInput(attrs={"placeholder": "anna@campus.ru"}),
            "study_group": forms.TextInput(attrs={"placeholder": "ПИ-301"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже зарегистрирован.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"placeholder": "anna@campusskill.ru"})
    )
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        password = cleaned.get("password")
        if email and password:
            self.user = authenticate(self.request, username=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Неверный email или пароль.")
        return cleaned
