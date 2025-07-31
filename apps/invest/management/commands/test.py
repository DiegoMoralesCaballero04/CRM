#encoding:utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from invest.models import PropuestaLinea

class Command(BaseCommand):

    def handle(self, *args, **options):
        linea=PropuestaLinea.objects.all().first()
        linea.ImprimirContrato()
