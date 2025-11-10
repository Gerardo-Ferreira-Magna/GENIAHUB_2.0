from django import forms
from django.contrib.auth.forms import UserCreationForm, authenticate
from .models import Usuario
from .models import RegistroEmpresa

# --------------------------
# FORMULARIO DE REGISTRO
# --------------------------
class RegistroForm(UserCreationForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Cree una contraseña'}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita la contraseña'}),
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'rut', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su nombre'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido paterno'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido materno'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        }

    # Validación de email único
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("⚠️ Este correo ya está registrado.")
        return email

    # Validación de rut único
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if Usuario.objects.filter(rut=rut).exists():
            raise forms.ValidationError("⚠️ Este RUT ya está registrado.")
        return rut


# --------------------------
# FORMULARIO DE LOGIN
# --------------------------
class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su correo',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError("❌ Correo o contraseña incorrectos.")
        return cleaned_data


# --------------------------
class RegistroEmpresaForm(forms.ModelForm):
    class Meta:
        model = RegistroEmpresa
        fields = [
            'nombre_empresa',
            'direccion_fiscal',
            'nif_cif',
            'telefono_contacto',
            'correo_contacto',
            'documento_adjunto',
        ]
        widgets = {
            'nombre_empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Introduce el nombre legal de tu empresa'
            }),
            'direccion_fiscal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa, ciudad y código postal'
            }),
            'nif_cif': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: B12345678'
            }),
            'telefono_contacto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678'
            }),
            'correo_contacto': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contacto@tuempresa.com'
            }),
            'documento_adjunto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = [
            "sobre_mi",
            "habilidades",
            "experiencia",
            "industrias_interes",
            "tecnologias_preferidas",
        ]
        widgets = {
            "sobre_mi": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "habilidades": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "experiencia": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "industrias_interes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "tecnologias_preferidas": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
        labels = {
            "sobre_mi": "Sobre mí",
            "habilidades": "Habilidades (separadas por comas)",
            "experiencia": "Experiencia laboral / académica",
            "industrias_interes": "Industrias de interés (separadas por comas)",
            "tecnologias_preferidas": "Tecnologías preferidas (separadas por comas)",
        }