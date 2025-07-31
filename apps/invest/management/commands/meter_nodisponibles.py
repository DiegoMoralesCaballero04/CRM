#encoding:utf-8
import csv 
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from invest.models import CampanyaLinea, Activo, User
from invest.utils import NormalizarCadena

class Command(BaseCommand):

    def handle(self, *args, **options):
        breakpoint()
        archivo_entrada = "salida.csv"
        with open(archivo_entrada, mode="r", encoding="utf-8") as infile:
            lector = csv.DictReader(infile)
            for fila in lector:
                ref_catastral = fila.get("ref_catastral", "").strip()  
                id_proveedor = fila.get("id_proveedor", "").strip()
                direccion = fila.get("direccion", "").strip()

                print(f"{ref_catastral} - {id_proveedor} - {direccion}")
                activos=Activo.objects.filter(ref_catastral=ref_catastral, id_proveedor=id_proveedor)
                for activo in activos:
                    activo.no_disponible=datetime.now()
                    activo.no_disponible_por=User.objects.all().first()
                    activo.save()

