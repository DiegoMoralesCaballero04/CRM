import requests

from django.conf import settings

def obtener_info_catastro(referencia_catastral):
    """
    Obtiene información del Catastro de España a partir de una referencia catastral.
    
    Args:
        referencia_catastral (str): La referencia catastral a consultar.
        
    Returns:
        dict: Un diccionario con los datos del catastro.
    """
    # URL base de la API del Catastro
    url_base = "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC"
    #url_base = "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadasRC"
    
    # Parámetros de la solicitud
    params = {
        "RefCat": referencia_catastral,
        "srs": "EPSG:4326"  # Sistema de coordenadas estándar
    }
    
    try:
        # Realizar la solicitud GET
        response = requests.get(url_base, params=params)
        
        # Comprobar si la solicitud fue exitosa
        if response.status_code == 200: 
            # Convertir la respuesta a un diccionario JSON
            datos = response.json()
            return datos
        else:
            # Manejar errores en la solicitud
            return {"error": f"Error al consultar el catastro. Código de estado: {response.status_code}"}
    
    except requests.RequestException as e:
        # Manejar excepciones de la solicitud
        return {"error": f"Excepción al realizar la consulta: {str(e)}"}

# Ejemplo de uso
# referencia = "7756002BE4375N0009FZ"
# info_catastro = obtener_info_catastro(referencia)
# print(info_catastro)


# from jinja2 import Template
def DameDatosCatastro(referencia_catastral):
    error=False
    datos=obtener_info_catastro(referencia_catastral)
    try:
        try:
            inmueble = datos['consulta_dnprcResult']['bico']['bi']
        except KeyError as e:
            return {"error":True, "literror":f"{e}"}
        referencia_catastral = (
            inmueble['idbi']['rc']['pc1'] +
            inmueble['idbi']['rc']['pc2'] +
            inmueble['idbi']['rc']['car'] +
            inmueble['idbi']['rc']['cc1'] +
            inmueble['idbi']['rc']['cc2']
        )
        localizacion = inmueble['ldt']
        clase = inmueble['idbi']['cn']
        uso_principal = inmueble['debi']['luso']
        try:
            superficie = inmueble['debi']['sfc']
        except:
            superficie=None
        try:
            anio_construccion = inmueble['debi']['ant']
        except:
            anio_construccion=None

        return {"error":False, "literror":"", "localizacion":localizacion,"clase":clase,"uso_principal":uso_principal,"superficie":superficie,"anio_construccion":anio_construccion}
    except KeyError as e:
        if settings.DEBUG:
            breakpoint()
        return {"error":True, "literror":f"Error al procesar los datos: Clave faltante {e}"}

def generar_card_inmueble_catastro(datos):
    """
    Genera una tarjeta HTML con la información del inmueble a partir de un diccionario.

    Args:
        datos (dict): Diccionario con los datos del inmueble.

    Returns:
        str: Una cadena de texto que contiene el HTML de la tarjeta.
    """
    # Extraer la información del diccionario
    try:
        inmueble = datos['consulta_dnprcResult']['bico']['bi']
        referencia_catastral = (
            inmueble['idbi']['rc']['pc1'] +
            inmueble['idbi']['rc']['pc2'] +
            inmueble['idbi']['rc']['car'] +
            inmueble['idbi']['rc']['cc1'] +
            inmueble['idbi']['rc']['cc2']
        )
        localizacion = inmueble['ldt']
        clase = inmueble['idbi']['cn']
        uso_principal = inmueble['debi']['luso']
        superficie = inmueble['debi']['sfc']
        anio_construccion = inmueble['debi']['ant']
    except KeyError as e:
        return f"Error al procesar los datos: Clave faltante {e}"
        breakpoint()

    # Plantilla HTML para la tarjeta
    html = f"""
    <div class="panel panel-sec">
        <div class="panel-heading amarillo">DATOS DESCRIPTIVOS DEL INMUEBLE</div>
        <div class="panel-body">
            <div id="ctl00_Contenido_tblInmueble" class="form-horizontal" name="tblInmueble">
                <div class="form-group">
                    <span class="col-md-4 control-label">Referencia catastral</span>
                    <div class="col-md-8">
                        <span class="control-label black">
                            <label class="control-label black text-left">{ referencia_catastral }</label>
                        </span>
                    </div>
                </div>
                <div class="form-group">
                    <span class="col-md-4 control-label">Localización</span>
                    <div class="col-md-8">
                        <span class="control-label black">
                            <label class="control-label black text-left">{ localizacion }</label>
                        </span>
                    </div>
                </div>
                <div class="form-group">
                    <span class="col-md-4 control-label">Clase</span>
                    <div class="col-md-8">
                        <span class="control-label black">
                            <label class="control-label black text-left">{ clase }</label>
                        </span>
                    </div>
                </div>
                <div class="form-group">
                    <span class="col-md-4 control-label">Uso principal</span>
                    <div class="col-md-8">
                        <span class="control-label black">
                            <label class="control-label black text-left">{ uso_principal }</label>
                        </span>
                    </div>
                </div>
                <div class="form-group">
                    <span class="col-md-4 control-label">Superficie construida</span>
                    <div class="col-md-8">
                        <span class="control-label black">
                            <label class="control-label black text-left">{ superficie } m<sup>2</sup></label>
                        </span>
                    </div>
                </div>
                <div class="form-group">
                    <span class="col-md-4 control-label">Año construcción</span>
                    <div class="col-md-8">
                        <span class="control-label black">
                            <label class="control-label black text-left">{ anio_construccion }</label>
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return html


#html_card = generar_card_inmueble(datos)
#print(html_card)
