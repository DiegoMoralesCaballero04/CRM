from django.core.management.base import BaseCommand
from invest.models import Poblacion
import requests
import time
import unicodedata
import re

def normalizar(texto):
    texto = texto.strip()
    texto = re.sub(r'[\u2018\u2019\u201A\u201B\u2032\u2035]', "'", texto)
    texto = re.sub(r'[\u201C\u201D\u201E\u201F\u2033\u2036]', '"', texto)
    texto = texto.replace('´', "'").replace("`", "'")
    texto = re.sub(r'\s+', ' ', texto)
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')

class Command(BaseCommand):
    help = 'Actualiza latitud y longitud de los municipios con lat=0 y lon=0 usando OpenStreetMap (Nominatim)'

    def handle(self, *args, **kwargs):
        poblaciones = Poblacion.objects.filter(latitud=0, longitud=0)
        headers = {'User-Agent': 'Django CRM MSS'}

        for pob in poblaciones:
            nombre = normalizar(pob.nombre)
            provincia = normalizar(pob.provincia.nombre)

            if provincia.lower() in ["varios", "", "desconocida"]:
                self.stdout.write(self.style.WARNING(f"⚠ Provincia indefinida: {nombre}, {provincia}, España"))
                continue

            direccion = f"{nombre}, {provincia}, España"
            url = f"https://nominatim.openstreetmap.org/search?q={direccion}&format=json&limit=1"

            try:
                response = requests.get(url, headers=headers)
                data = response.json()

                # Segundo intento sin provincia si el primero falla
                if not data:
                    direccion_simple = f"{nombre}, España"
                    url_simple = f"https://nominatim.openstreetmap.org/search?q={direccion_simple}&format=json&limit=1"
                    response = requests.get(url_simple, headers=headers)
                    data = response.json()

                if data:
                    pob.latitud = float(data[0]['lat'])
                    pob.longitud = float(data[0]['lon'])
                    pob.save()
                    self.stdout.write(self.style.SUCCESS(f"✔ {pob.nombre}: {pob.latitud}, {pob.longitud}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ No encontrado: {direccion}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✖ Error con {nombre}: {e}"))

            time.sleep(1.1)
