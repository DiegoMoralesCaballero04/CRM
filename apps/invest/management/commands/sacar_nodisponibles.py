#encoding:utf-8
import csv 

from django.core.management.base import BaseCommand, CommandError

from invest.models import CampanyaLinea, Activo
from invest.utils import NormalizarCadena

class Command(BaseCommand):

    def handle(self, *args, **options):
        archivo_salida = "salida.csv"
        lineas=CampanyaLinea.objects.exclude(no_disponible=None)
        with open(archivo_salida, mode="w", encoding="utf-8", newline="") as outfile:
            escritor = csv.writer(outfile)
            escritor.writerow(["ref_catastral", "id_proveedor", "direccion"])
            for linea in lineas:
                print(f"{linea.activo.ref_catastral} - {linea.activo.id_proveedor}")
                escritor.writerow([linea.activo.ref_catastral, linea.activo.id_proveedor, linea.activo.direccion])
