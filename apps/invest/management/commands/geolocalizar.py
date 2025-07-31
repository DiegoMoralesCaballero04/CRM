#encoding:utf-8
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from invest.models import Activo
from invest.utils_geoloc import Geolocaliza
from invest.catastro import DameDatosCatastro
class Command(BaseCommand):

    def handle(self, *args, **options):
        activos=Activo.objects.filter(Q(longitud=None)|Q(longitud=0)|Q(catastro=False)).filter(fecha_peticion_catastro=None).order_by("-pk")
        i=0; tot_activos=activos.count()
        for activo in activos:
            print (f"{i}/{tot_activos}")
            if not activo.longitud or activo.longitud==0:
                activo.ActivoLocalizar()
                if settings.DEBUG:
                    print ("geolocalizado")

            if not activo.catastro and activo.ref_catastral:
                activo.ActivoGuardaCatastro()
                if settings.DEBUG:
                    print ("catastro")
            i+=1

