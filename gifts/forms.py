from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль',
        min_length=8,
        help_text='Пароль мінімум 8 символів'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Повторіть пароль'
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ім'я користувача"}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Електронна пошта'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Користувач з таким ім\'ям вже існує')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Користувач з такою електронною поштою вже існує')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8:
                raise ValidationError('Пароль мінімум 8 символів')
            if password.isdigit():
                raise ValidationError('Пароль не повинен складатись лише з цифр')
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Паролі не співпадають')
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        from .models import Profile
        model = Profile
        fields = ('display_name', 'avatar', 'bio', 'location', 'birthday', 'interests')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Розкажіть про себе...'}),
            'birthday': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ваші інтереси та хобі...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше місто...'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ваше ім'я..."}),
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Validate file size (max 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError('Розмір файлу не повинен перевищувати 5MB')
        return avatar
