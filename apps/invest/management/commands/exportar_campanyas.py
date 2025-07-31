#encoding:utf-8
from z3c.rml import rml2pdf

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from invest.models import Empresa, Campanya, CampanyaLinea
from invest.generarExcel import *
from invest.generarRML import *
from invest.utils import DameGeneradorNombres

class Command(BaseCommand):

    def handle(self, *args, **options):
        empresa=Empresa.objects.all().first()
        campanyas=Campanya.objects.all()
        for campanya in campanyas:
            print (f"{campanya.proveedor.nombre} - {campanya.cartera.codigo } - " + campanya.fecha.strftime("%Y-%m-%d"))
            lineas=CampanyaLinea.objects.filter(campanya=campanya)

            nombrefichero_="mss" + DameGeneradorNombres()
            nombrefichero=f"{nombrefichero_}.xlsx"
            GenerarListaActivosExcel(empresa, campanya, lineas, "", "", "", "", "", "", nombrefichero)                
            
            nombrefichero=f"{nombrefichero_}.pdf"
            rml_cadena=GenerarListaActivosRML (empresa, campanya, lineas, "", "", "", "", "", "", nombrefichero)
            f=open(settings.MEDIA_ROOT + "/archivo.rml","w")
            f.write(rml_cadena)
            f.close()
            output= settings.MEDIA_ROOT + '/' + nombrefichero
            rml2pdf.go(settings.MEDIA_ROOT + "/archivo.rml", outputFileName=output)
