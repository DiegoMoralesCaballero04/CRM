import json
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def actualizar_mapeo_columnas(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            tabla = data.get("tabla")
            campo = data.get("campo")
            nuevo_valor = data.get("nuevoValor").upper()

            ruta_json = os.path.join(settings.BASE_DIR, "invest", "MAPEO_COLUMNAS.json")

            with open(ruta_json, "r", encoding="utf-8") as f:
                mapeo = json.load(f)

            if tabla not in mapeo:
                mapeo[tabla] = {}
            if campo not in mapeo[tabla]:
                mapeo[tabla][campo] = []

            if nuevo_valor in mapeo[tabla][campo]:
                mapeo[tabla][campo].remove(nuevo_valor)
                mensaje = "Valor reordenado al final"
            else:
                mensaje = "Valor añadido"

            mapeo[tabla][campo].append(nuevo_valor)

            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(mapeo, f, ensure_ascii=False, indent=4)

            return JsonResponse({"ok": True, "mensaje": mensaje})
        except Exception as e:
            return JsonResponse({"ok": False, "mensaje": str(e)})
    return JsonResponse({"ok": False, "mensaje": "Método no permitido, solo se acepta POST."}, status=405)