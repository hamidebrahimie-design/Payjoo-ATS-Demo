from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import UserProfile

class PersianLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="نام کاربری",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام کاربری خود را وارد کنید',
            'id': 'username_field'
        })
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'id': 'password_field'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = "نام کاربری یا رمز عبور اشتباه است."
        self.error_messages['inactive'] = "این حساب کاربری غیرفعال شده است."


class UserCreationForm(forms.ModelForm):
    first_name = forms.CharField(label="نام", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="نام خانوادگی", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="ایمیل", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="رمز عبور", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    role = forms.ChoiceField(label="نقش", choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    is_external = forms.BooleanField(label="ارزیاب خارجی است؟", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    phone_number = forms.CharField(label="شماره تماس", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'نام کاربری',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            (role, label) for role, label in UserProfile.ROLE_CHOICES if role != UserProfile.ROLE_CANDIDATE
        ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("این نام کاربری قبلاً انتخاب شده است.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == UserProfile.ROLE_EXTERNAL_ASSESSOR:
            cleaned_data['is_external'] = True
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # The signal will auto-create the profile. We then retrieve it and update additional fields.
            profile = user.profile
            profile.role = self.cleaned_data['role']
            profile.is_external = self.cleaned_data['is_external']
            profile.phone_number = self.cleaned_data['phone_number']
            profile.save()
        return user


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(label="نام", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="نام خانوادگی", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="ایمیل", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    role = forms.ChoiceField(label="نقش", choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    is_external = forms.BooleanField(label="ارزیاب خارجی است؟", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    phone_number = forms.CharField(label="شماره تماس", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            (role, label) for role, label in UserProfile.ROLE_CHOICES if role != UserProfile.ROLE_CANDIDATE
        ]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == UserProfile.ROLE_EXTERNAL_ASSESSOR:
            cleaned_data['is_external'] = True
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=commit)
        profile = user.profile
        profile.role = self.cleaned_data['role']
        profile.is_external = self.cleaned_data['is_external']
        profile.phone_number = self.cleaned_data['phone_number']
        profile.save()
        return user
