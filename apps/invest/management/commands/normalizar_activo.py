#encoding:utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


from invest.models import CampanyaLinea, Activo
from invest.utils import NormalizarCadena

class Command(BaseCommand):

    def handle(self, *args, **options):
        breakpoint()
        activos=Activo.objects.exclude(id_proveedor="", ref_catastral="").order_by("pk")
        for activo in activos:
            activos_=Activo.objects.filter(
                id_proveedor=activo.id_proveedor, 
                ref_ue=activo.ref_ue,
                tipologia=activo.tipologia,
                ref_catastral=activo.ref_catastral,
                direccion=activo.direccion,
                poblacion=activo.poblacion,
                pk__gt=activo.pk)
            for activo_ in activos_:
                lineas=CampanyaLinea.objects.filter(activo=activo_)
                for linea in lineas:
                    linea.activo=activo
                    linea.save()
                print(f"{activo_.direccion} -> {activo.id_proveedor} -> {activo.ref_catastral}")
            activos_.delete()
