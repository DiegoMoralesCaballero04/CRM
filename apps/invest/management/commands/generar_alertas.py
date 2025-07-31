from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from invest.models import PropuestaLinea, PropuestaComentario, PropuestaLineaEstado, AlertaPropuestaInactiva

class Command(BaseCommand):
    help = 'Genera alertas de inactividad en propuestas según estado y fechas.'

    def handle(self, *args, **kwargs):
        criterios_alerta = {
            '': 15,   # Propuesta enviada
            'I': 3,   # Interesado
            'E': 15,  # Esperando servicer
            'R': 1,   # Aceptada
        }

        alertas_creadas = []

        for estado, dias in criterios_alerta.items():
            fecha_limite = now() - timedelta(days=dias)
            lineas = PropuestaLinea.objects.filter(estado=estado, propuesta__anulado_en=None)

            for linea in lineas:
                tiene_comentarios = PropuestaComentario.objects.filter(linea=linea, creado_en__gte=fecha_limite).exists()
                tiene_estado = PropuestaLineaEstado.objects.filter(linea=linea, creado_en__gte=fecha_limite).exists()

                if not tiene_comentarios and not tiene_estado:
                    alerta, creada = AlertaPropuestaInactiva.objects.get_or_create(
                        linea=linea,
                        motivo=f"Sin actividad (estado '{estado or 'Enviada'}) en {dias} días",
                        defaults={'responsable': linea.propuesta.cliente.responsable}
                    )
                    if creada:
                        alertas_creadas.append(alerta)

        self.stdout.write(f"Se han creado {len(alertas_creadas)} alertas.")
        for alerta in alertas_creadas:
            self.stdout.write(f"- Línea {alerta.linea.id}, Cliente: {alerta.linea.propuesta.cliente.nombre}, Motivo: {alerta.motivo}")
