#encoding:utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from invest.models import Campanya
from invest.importar_activo import ImportarActivos

class Command(BaseCommand):

    def handle(self, *args, **options):

        campanyas=Campanya.objects.exclude(fichero="")
        for campanya in campanyas:
            ImportarActivos(campanya, User.objects.all().first())
