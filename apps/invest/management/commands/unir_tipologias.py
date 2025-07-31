#encoding:utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from invest.models import Tipologia, Activo, GrupoTipologia

class Command(BaseCommand):

    def handle(self, *args, **options):
        tipologias=Tipologia.objects.all().order_by("grupo", "nombre", "pk")
        nombre=None; grupo=None
        for tipologia in tipologias:
            if tipologia.nombre==nombre and tipologia.grupo==grupo:
                activos=Activo.objects.filter(tipologia=tipologia)
                for activo in activos:
                    activo.tipologia=tipologia_
                    activo.save()
                tipologia.delete()
            else:
                tipologia_=tipologia
                nombre=tipologia.nombre
                grupo=tipologia.grupo
        
        grupo=GrupoTipologia.objects.filter(es_varios=True).first()
        tipologias=Tipologia.objects.filter(grupo=None)
        for tipologia in tipologias:
            tipologia.grupo=grupo
            tipologia.save()
