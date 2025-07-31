#encoding:utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from invest.importar import ImportarInversores

class Command(BaseCommand):

    def handle(self, *args, **options):
        ImportarInversores()
