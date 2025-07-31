import django_filters

from .models import Activo, Campanya

class CampanyaFilter(django_filters.FilterSet):
    class Meta:
        model = Campanya
        fields = {
            'proveedor': ['exact'],
            'fecha': ['exact', 'year__gt', 'year__lt'],
            'estado': ['exact'],
        }

class ActivoFilter(django_filters.FilterSet):
    class Meta:
        model = Activo
        fields = {
            'poblacion': ['exact']
        }
