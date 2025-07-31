#encoding:utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


from invest.models import Poblacion, Activo
from invest.utils import NormalizarCadena

class Command(BaseCommand):

    def handle(self, *args, **options):
        poblaciones=Poblacion.objects.filter().order_by("pk")
        breakpoint()
        for poblacion in poblaciones:
            nombre=NormalizarCadena(poblacion.nombre)
            poblaciones=Poblacion.objects.filter(nombre__iexact=nombre, provincia=poblacion.provincia, pk__gt=poblacion.pk)
            if poblaciones.first():
                id_poblaciones=poblaciones.values_list("pk", flat=True)
                activos=Activo.objects.filter(poblacion__pk__in=id_poblaciones)
                for activo in activos:
                    print (f"{activo.poblacion} -> {poblacion}")
                    activo.poblacion=poblacion
                    activo.save()
                poblaciones.delete()
