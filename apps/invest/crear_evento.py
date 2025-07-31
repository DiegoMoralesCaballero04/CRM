import json
from datetime import datetime
from django.utils.dateparse import parse_date, parse_time
from django.utils.timezone import make_aware
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from .models import Calendario 

@csrf_exempt
@login_required
def crear_evento(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            fecha_str = data.get("fecha")
            hora_str = data.get("hora")
            descripcion = data.get("descripcion", "").strip()

            if not (fecha_str and hora_str and descripcion):
                return JsonResponse({"success": False, "error": "Datos incompletos"})

            fecha = parse_date(fecha_str)
            hora = parse_time(hora_str)

            if not (fecha and hora):
                return JsonResponse(
                    {"success": False, "error": "Fecha u hora inválida"}
                )

            fecha_hora = make_aware(datetime.combine(fecha, hora))

            if Calendario.objects.filter(
                fecha=fecha_hora, descripcion=descripcion
            ).exists():
                return JsonResponse(
                    {"success": False, "error": "Este evento ya existe"}
                )

            evento = Calendario.objects.create(
                fecha=fecha_hora,
                descripcion=descripcion,
                content_type=ContentType.objects.get_for_model(Calendario),
                object_id=request.user.id,
                creado_por=request.user,
            )

            return JsonResponse({"success": True, "id": evento.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método no permitido"})
