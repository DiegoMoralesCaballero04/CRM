import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Activo 
openai.api_key = settings.OPENAI_API_KEY
@csrf_exempt
def openai_chat(request):
    API_KEY = settings.OPENAI_API_KEY 
    API_URL = "https://api.openai.com/v1/chat/completions"

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            context = data.get("context", [])
            question = data.get("question")

            if not question:
                return JsonResponse({"error": "La pregunta es obligatoria"}, status=400)
            
            if isinstance(context, list) and len(context) >= 3:
                id_proveedor, ref_catastral, direccion = context[:3]
            else:
                return JsonResponse({"error": "Contexto incompleto. Se esperan id_proveedor, ref_catastral y direccion."}, status=400)

            try:
                activo = Activo.objects.filter(
                    id_proveedor=id_proveedor,
                    ref_catastral=ref_catastral,
                    direccion=direccion,
                ).first()

                if not activo:
                    return JsonResponse({"error": "Activo no encontrado con el contexto proporcionado."}, status=404)

            except Exception as e:
                return JsonResponse({"error": f"Error al buscar el activo en la base de datos: {str(e)}"}, status=500)

            context_text = (
                f"Referencia Catastral: {activo.ref_catastral or 'No disponible'}\n"
                f"Dirección: {activo.direccion or 'No disponible'}, CP {activo.cp or '---'}, "
                f"{getattr(activo.poblacion, 'nombre', '---')}, "
                f"{getattr(getattr(activo.poblacion, 'provincia', None), 'nombre', '---')}\n"
                f"Tipología: {getattr(activo.tipologia, 'nombre', 'No especificada')}\n"
                f"Superficie: {activo.m2 or 0} m²\n"
                f"Habitaciones: {activo.num_habitaciones or 0}, Baños: {activo.num_banyos or 0}\n"
                f"Año de construcción (registrado): {activo.fecha_construccion or '---'}\n"
                f"Catastro:\n"
                f"  - Clase: {activo.catastro_clase or '---'}\n"
                f"  - Uso principal: {activo.catastro_uso_principal or '---'}\n"
                f"  - Superficie: {activo.catastro_superficie or 0} m²\n"
                f"  - Localización: {activo.catastro_localizacion or '---'}\n"
                f"  - Año construcción (catastro): {activo.catastro_anyo_construccion or '---'}\n"
                f"Ubicación GPS: Lat {activo.latitud or '---'}, Lon {activo.longitud or '---'}\n"
            )

            payload = {
                "model": "gpt-4o", 
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente inmobiliario útil. Usa el contexto para responder a la pregunta del usuario.",
                    },
                    {
                        "role": "user",
                        "content": f"""Contexto del activo:
{context_text}

Pregunta: {question}
""",
                    },
                ],
                "max_tokens": 500,
                "temperature": 0.7,
            }

            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            }

            response = requests.post(API_URL, headers=headers, json=payload)

            if response.status_code != 200:
                return JsonResponse(
                    {"error": f"Error de OpenAI: {response.text}"},
                    status=response.status_code,
                )

            response_data = response.json()
            answer = response_data["choices"][0]["message"]["content"].strip()
            return JsonResponse({"answer": answer})

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "El cuerpo de la solicitud no tiene un formato JSON válido"},
                status=400,
            )

        except requests.RequestException as e:
            return JsonResponse({"error": f"Error de conexión con la API de OpenAI: {str(e)}"}, status=500)

        except Exception as e:
            return JsonResponse(
                {"error": f"Ocurrió un error inesperado: {str(e)}"}, status=500
            )

    return JsonResponse(
        {"error": "Método de solicitud no válido, usa POST"}, status=405
    )
```