from datetime import date

from django import forms
from .models import Activo, Campanya, Cliente, Proveedor, Responsable

from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import User

User = get_user_model()


class ActivoForm(forms.ModelForm):
    class Meta:
        model = Activo
        fields = ['tipologia', 'ref_catastral', 'direccion', 'cp', 'poblacion', 'longitud', 'latitud'] #'precio', 'estado_ocupacional', 'estado_legal', 'url'

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'codigo']

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['responsable', 'codigo', 'tipo', 'nombre', 'apellidos', 'nombre_completo', 'contacto',
            'nif', 'direccion', 'cp', 'poblacion','provincia', 'correo', 'correo_2', 'correo_3', 'telefono', 'zona', 'observaciones']

class ResponsableForm(forms.ModelForm):
    class Meta:
        model = Responsable
        fields = ['nombre']

class CampanyaForm(forms.ModelForm):
    class Meta:
        model = Campanya
        fields = ['proveedor', 'cartera', 'fecha', 'tipo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].initial = date.today()
        self.fields['proveedor'].queryset = Proveedor.objects.filter(anulado_por=None).order_by("codigo")

class CustomUserCreationForm(UserCreationForm):
    nombre_completo = forms.CharField(label="Nombre completo", max_length=150, required=True)
    telefono = forms.CharField(label="Teléfono", max_length=20, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "nombre_completo", "telefono", "password1", "password2")


from django import forms
from .models import Agenda

class AgendaForm(forms.ModelForm):
    crear_cliente = forms.BooleanField(
        required=False,
        label="Crear también como cliente"
    )

    class Meta:
        model = Agenda
        fields = ['nombre', 'apellidos', 'descripcion', 'telefono', 'fijo', 'email']
