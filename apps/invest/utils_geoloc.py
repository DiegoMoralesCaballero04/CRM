from geopy.geocoders import Nominatim
import time
import re
#from opencage.geocoder import OpenCageGeocode
# \venv\Scripts\python.exe -m pip install geopy
import re
from geopy.geocoders import Nominatim

def Geolocaliza(direccion, municipio):
    from django.apps import apps

    latitud = 0
    longitud = 0
    if municipio:
        Poblacion = apps.get_model('invest', 'Poblacion')  
        poblacion = Poblacion.objects.filter(nombre=municipio).first()
        if poblacion:
            provincia = poblacion.provincia.nombre.strip().title()
    try:
        geolocator = Nominatim(user_agent="FRASOR_INVEST", timeout=10)

        # 🧹 LIMPIEZA INICIAL
        direccion = re.sub(r'Es:.*?Pt:.*?\d+', '', direccion)  # quitar "Es:1 Pl:01 Pt:B"
        direccion = re.sub(r'\([^)]*\)', '', direccion)        # quitar paréntesis
        direccion = re.sub(r'Bl:.*?(?=\s|$)', '', direccion)   # quitar "Bl:I"
        direccion = re.sub(r'Edificio.*?(?=\d{5}|\s|$)', '', direccion)  # quitar "Edificio PORTAL DE CASTALIA"
        direccion = re.sub(r'N2-\d+', '', direccion)           # quitar "N2-9"
        direccion = re.sub(r'SECTOR.*?(?=\d{5}|\s|$)', '', direccion)  # quitar "SECTOR 6"
        direccion = re.sub(r'Suelo', '', direccion)            # quitar "Suelo"
        direccion = re.sub(r'EDIF.*?(?=\d{5}|\s|$)', '', direccion)  # quitar "EDIF BAHIA DEL SEGURA"
        direccion = re.sub(r'URB.*?(?=\d{5}|\s|$)', '', direccion)  # quitar "URB 125"
        direccion = direccion.replace('.', ' ')                # reemplazar puntos por espacios
        direccion = direccion.replace('/', ' ')                # reemplazar barras por espacios
        direccion = direccion.replace('-', ' ')                # reemplazar guiones por espacios
        direccion = re.sub(r'\s+', ' ', direccion)            # normalizar espacios
        
        # Procesar formato especial "Tipo vía: CALLE; Nombre vía: ..."
        if "Tipo vía:" in direccion:
            match = re.search(r'Tipo vía:\s*([^;]+);\s*Nombre vía:\s*([^;]+);\s*Numero:\s*(\d+)?', direccion)
            if match:
                tipo_via = match.group(1).strip()
                nombre_via = match.group(2).strip()
                numero = match.group(3) if match.group(3) else ''
                direccion = f"{tipo_via} {nombre_via} {numero}".strip()
        
        direccion = ' '.join(direccion.split())               # quitar espacios duplicados

        # 🧾 MAPA DE ABREVIATURAS (Catastro → Forma expandida)
        # Sustituciones en castellano
        sustituciones_castellano = {
            "AC ": "Acceso ",
            "AL ": "Alameda ",
            "AV ": "Avenida ",
            "BJ ": "Bajo ",
            "BL ": "Bloque ",
            "BO ": "Barrio ",
            "CA ": "Calleja ",
            "CG ": "Colegio ",
            "CL ": "Calle ",
            "CM ": "Camino ",
            "CN ": "Centro ",
            "CR ": "Carretera ",
            "CT ": "Callejón ",
            "CU ": "Cuesta ",
            "DEP ": "Deportista ",
            "DR ": "Doctor ",
            "ED ": "Edificio ",
            "EN ": "Entresuelo ",
            "ES ": "Escalera ",
            "EX ": "Extrarradio ",
            "FC ": "Ferrocarril ",
            "GL ": "Glorieta ",
            "GR ": "Gran Vía ",
            "JR ": "Jardines ",
            "LG ": "Lugar ",
            "MC ": "Mercado ",
            "MUSI ": "Músico ",
            "MZ ": "Manzana ",
            "PA ": "Paraje ",
            "PB ": "Pabellón ",
            "PD ": "Partida ",
            "PG ": "Polígono ",
            "PJ ": "Pasaje ",
            "PL ": "Planta ",
            "PO ": "Poblado ",
            "PQ ": "Parque ",
            "PR ": "Prolongación ",
            "PS ": "Paseo ",
            "PT ": "Puerta ",
            "PZ ": "Plaza ",
            "RB ": "Rambla ",
            "RD ": "Ronda ",
            "S ": "Sant ",
            "SC ": "Sector ",
            "SL ": "Solar ",
            "SN ": "Senda ",
            "SU ": "Subida ",
            "TR ": "Travesía ",
            "UR ": "Urbanización ",
            "VR ": "Vereda ",
            "ZC ": "Zona común ",
            "POL ": "Polígono ",
            "POL. ": "Polígono ",
            "IND ": "Industrial ",
            "IND. ": "Industrial ",
            "POLIG ": "Polígono ",
            "POLIG. ": "Polígono ",
        }

        # Sustituciones en valenciano/catalán
        sustituciones_valenciano = {
            "CL ": "Carrer ",
            "AV ": "Avinguda ",
            "PL ": "Planta ",
            "PZ ": "Plaça ",
            "BJ ": "Baix ",
            "ED ": "Edifici ",
            "UR ": "Urbanització ",
            "TR ": "Travessera ",
            "PS ": "Passeig ",
            "DR ": "Doctor ",
            "S ": "Sant ",
            "PG ": "Polígon ",
            "POL ": "Polígon ",
            "POL. ": "Polígon ",
            "POLIG ": "Polígon ",
            "POLIG. ": "Polígon ",
            "IND ": "Industrial ",
            "IND. ": "Industrial ",
        }

        PROVINCIAS_CATALANAS = [
            "Valencia", "Alicante", "Castellón",      # Comunidad Valenciana
            "Barcelona", "Tarragona", "Lleida", "Girona",  # Cataluña
            "Baleares", "Illes Balears"               # Islas Baleares
        ]
        # Aplicar sustituciones
        direccion_upper = direccion.upper()
        poblacion = Poblacion.objects.get(nombre=municipio)
        provincia_nombre = poblacion.provincia.nombre.strip().title()

        if provincia_nombre in PROVINCIAS_CATALANAS:
            sustituciones = sustituciones_valenciano
        else:
            sustituciones = sustituciones_castellano
        for abrev, extendido in sustituciones.items():
            if direccion_upper.startswith(abrev):
                direccion = extendido + direccion[len(abrev):]
            espacio_abrev = f" {abrev}"
            if espacio_abrev in direccion_upper:
                direccion = direccion.replace(direccion_upper[direccion_upper.index(espacio_abrev):direccion_upper.index(espacio_abrev)+len(espacio_abrev)], f" {extendido}")
        
        # Normalizar nombres de municipios compuestos
        municipios_compuestos = {
            r'CASTELLO DE LA PLANA': 'CASTELLON',
            r'MORA D\'EBRE': 'MORA DE EBRO',
            r'RODA DE BERA': 'RODA DE BARA',
            r'ELCHE/ELX': 'ELCHE',
            r'VILANOVA I LA GELTRU': 'VILLANUEVA Y GELTRU',
            r'SANT HILARI SACALM': 'SAN HILARIO SACALM',
            r'SANTA PERPETUA DE MOGODA': 'SANTA PERPETUA',
            r'LLOCNOU DE SANT JERONI': 'LUGAR NUEVO DE SAN JERONIMO',
            r'GUARDAMAR DEL SEGURA': 'GUARDAMAR',
            r'RIBA-ROJA DE TURIA': 'RIBARROJA',
            r'CANET DE MAR': 'CANET',
        }

        print(f"Buscando dirección: {direccion}")
        location = geolocator.geocode(direccion, exactly_one=True, country_codes=['es'])

        if location:
            latitud = location.latitude
            longitud = location.longitude
            print(f"Encontrado - Longitud: {longitud}, Latitud: {latitud}")
        else:
            match = re.search(r'^(.+?\s\d+)', direccion)
            if match:
                direccion_limpia = match.group(1).strip()
            else:
                direccion_limpia = direccion 
            direccion_limpia = re.sub(r'\s+\d{5}\s+', ' ', direccion_limpia)  # quitar códigos postales
            direccion_limpia = re.sub(r'\s+[A-Z]\'[A-Z]+\s*$', '', direccion_limpia)  # quitar L'ALCUDIA al final
            direccion_limpia = direccion_limpia + f" {municipio} ESPAÑA"
            print(f"Reintentando sin número/CP: {direccion_limpia}")
            location = geolocator.geocode(direccion_limpia, exactly_one=True, country_codes=['es'])
            
            if location:
                latitud = location.latitude
                longitud = location.longitude
                print(f"Encontrado sin número - Longitud: {longitud}, Latitud: {latitud}")
            else:
                if provincia_nombre in PROVINCIAS_CATALANAS and sustituciones != sustituciones_castellano:
                    direccion_original = direccion
                    for abrev, extendido in sustituciones_valenciano.items():
                        direccion = direccion.replace(extendido, abrev)  # revertir valenciano
                    for abrev, extendido in sustituciones_castellano.items():
                        if direccion.upper().startswith(abrev):
                            direccion = extendido + direccion[len(abrev):]
                        espacio_abrev = f" {abrev}"
                        if espacio_abrev in direccion.upper():
                            direccion = direccion.replace(direccion.upper()[direccion.upper().index(espacio_abrev):direccion.upper().index(espacio_abrev)+len(espacio_abrev)], f" {extendido}")
                    print(f"Reintentando con dirección en castellano: {direccion}")
                    location = geolocator.geocode(direccion, exactly_one=True, country_codes=['es'])
                    if location:
                        latitud = location.latitude
                        longitud = location.longitude
                        print(f"Encontrado con castellano - Longitud: {longitud}, Latitud: {latitud}")
                        return latitud, longitud
                    else:
                        print("Tampoco se encontró en castellano.")
                
                    # Último intento con dirección recortada (sin número ni CP)
                    match = re.search(r'^(.+?\s\d+)', direccion)
                    if match:
                        direccion_limpia = match.group(1).strip()
                    else:
                        direccion_limpia = direccion 
                    direccion_limpia = re.sub(r'\s+\d{5}\s+', ' ', direccion_limpia)
                    direccion_limpia = re.sub(r'\s+[A-Z]\'[A-Z]+\s*$', '', direccion_limpia)
                    direccion_limpia = direccion_limpia + f" {municipio} ESPAÑA"
                    print(f"Reintentando sin número/CP: {direccion_limpia}")
                    location = geolocator.geocode(direccion_limpia, exactly_one=True, country_codes=['es'])

                    if location:
                        latitud = location.latitude
                        longitud = location.longitude
                        print(f"Encontrado sin número - Longitud: {longitud}, Latitud: {latitud}")
                    else:
                        print("No se encontró la ubicación final.")





    except Exception as e:
        print(f"Error en geocodificación: {e}")
        
    return latitud, longitud
