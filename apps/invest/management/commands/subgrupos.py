#encoding:utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from invest.models import Tipologia, SubGrupoTipologia, GrupoTipologia

class Command(BaseCommand):

    def handle(self, *args, **options):
        tipologias=Tipologia.objects.filter(subgrupo=None)
        for tipologia in tipologias:
            subgrupo=SubGrupoTipologia.objects.filter(grupo=tipologia.grupo).order_by("orden").first()
            if subgrupo:
                tipologia.subgrupo=subgrupo
                tipologia.save()
