from django.core.management.base import BaseCommand
from invest.models import Activo

class Command(BaseCommand):
    help = 'Actualiza los datos del catastro para los activos'

    def handle(self, *args, **kwargs):
        activos = Activo.objects.filter(fecha_peticion_catastro__isnull=False, catastro=False)
        if activos.count == 0:
            activos = Activo.objects.filter(catastro=True).order_by('-fecha_peticion_catastro')
        for activo in activos:
            activo.ActivoLocalizar()

        self.stdout.write(self.style.SUCCESS('Actualización de catastro completada'))
