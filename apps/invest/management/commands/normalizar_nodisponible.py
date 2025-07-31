#encoding:utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


from invest.models import CampanyaLinea, Activo
from invest.utils import NormalizarCadena

class Command(BaseCommand):

    def handle(self, *args, **options):
        breakpoint()
        lineas=CampanyaLinea.objects.exclude(no_disponible=None)
        for linea in lineas:
            print(linea.no_disponible_por.username)
            activo=linea.activo
            activo.no_disponible=linea.no_disponible
            activo.no_disponible_por=linea.no_disponible_por
            activo.save()
