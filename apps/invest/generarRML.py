from datetime import datetime

from django.db.models import Q
from django.db.models import F, Value, IntegerField
from django.db.models import Case, When, Value, FloatField
from django.db.models import Max
from django.db.models import BooleanField
import re
from django.db.models.functions import Greatest
from invest.utils import Importe2Cadena
import logging

logger = logging.getLogger("invest")
from invest.models import CampanyaLinea


def GenerarListaActivosConCatastroRML(
    empresa,
    campanya,
    lineas,
    clasif,
    grupo,
    tipo,
    poblacion,
    provincia,
    estado,
    nombrefichero="fichero.pdf",
    texto_filtro="",
    proveedores=None,
    numLinea=None,
    retornar_partes_rml=False,
):
    try:
        from .models import Provincia, GrupoTipologia

        texto_filtro = re.sub(r"\s*Desde:\s*Hasta:\s*", "", texto_filtro).strip()
        hoy = datetime.now().strftime("%d-%m-%Y")
        if proveedores is None:
            proveedores = lineas.values_list(
                "campanya__proveedor", flat=True
            ).distinct()
        carteras = lineas.values_list("campanya__cartera", flat=True).distinct()
        tipos = lineas.values_list("tipo", flat=True).distinct()
        varias_campanyas = True
        cartera_nombre = ""
        nombre_campanya = ""
        if campanya:

            if hasattr(campanya, "count"):  # Es un queryset
                tam = campanya.count()
                if tam == 1:
                    camp = campanya.first()
                else:
                    camp = None
            else:  # Es una instancia única
                tam = 1
                camp = campanya

            if camp:
                cartera_nombre = camp.cartera.nombre
                nombre_campanya = f"{camp.cartera.codigo}"
                varias_campanyas = False

        filtro = ""
        if provincia and provincia.first():
            provincia_nombre = provincia.values_list("nombre", flat=True)
            provincia_nombre = ",".join(provincia_nombre).upper()
            filtro = f"PROVINCIA: {provincia_nombre}"
        else:
            filtro = "TODAS LAS PROVINCIAS"
        if grupo:
            try:
                grupo_nombre = grupo.nombre.upper()
            except Exception:
                grupo_nombre = "".join(g.nombre.upper() for g in grupo)
            filtro = f"{filtro} - TIPOLOGÍA: {grupo_nombre}"
        else:
            filtro = f"{filtro} - TODAS LAS TIPOLOGÍAS"
        if poblacion and poblacion.first():
            poblacion_nombre = poblacion.values_list("nombre", flat=True)
            poblacion_nombre = ",".join(poblacion_nombre).upper()
            filtro = f"{filtro} - POBLACIÓN: {poblacion_nombre}"
        if not filtro:
            filtro = texto_filtro
        filtro_clasif = ""
        tam_observ = 95
        columnas_alineamiento_derecha = []
        pos_precios = 7
        if varias_campanyas:
            tam_campanya = "15mm,"
            tam_fecha = "10mm,"
            tam_observ -= 25
            pos_precios += 2
        else:
            tam_campanya = ""
            tam_fecha = ""
        if tipos.count() == 1:
            tipos_diferentes = False
            tipo = tipos.first()
            tam_tipo = ""
        else:
            tipos_diferentes = True
            tipo = "--"
            tam_tipo = "10mm,"
            tam_observ -= 10
            pos_precios += 1
        precios = lineas.exclude(Q(precio=None) | Q(precio=0)).first()
        if precios:
            hay_precios = True
            tam_precios = "15mm,"
            tam_observ -= 15
            columnas_alineamiento_derecha.append(pos_precios)
            pos_precios += 1
        else:
            hay_precios = False
            tam_precios = ""
        importe_deuda = lineas.exclude(
            Q(importe_deuda=None) | Q(importe_deuda=0)
        ).first()
        if importe_deuda:
            hay_importe_deuda = True
            tam_importe_deuda = "15mm,"
            tam_observ -= 15
            columnas_alineamiento_derecha.append(pos_precios)
            pos_precios += 1
        else:
            hay_importe_deuda = False
            tam_importe_deuda = ""
        valor_referencia = lineas.exclude(
            Q(valor_referencia=None) | Q(valor_referencia=0)
        ).first()
        if valor_referencia:
            hay_valor_referencia = True
            tam_valor_referencia = "15mm,"
            tam_observ -= 15
            columnas_alineamiento_derecha.append(pos_precios)
            pos_precios += 1
        else:
            hay_valor_referencia = False
            tam_valor_referencia = ""
        rml_cadena = [
            f"""
            <!DOCTYPE document SYSTEM \"rml.dtd\">
            <document filename='{nombrefichero}'>
            <template pagesize=\"(29.7cm, 21cm)\">
                <pageTemplate id=\"principal\">
                    <pageGraphics>
                        <setFont name=\"Times-Roman\" size=\"8\"/>
                        <drawString x='5mm' y='206mm'>INVEST MSS</drawString>
                        <drawString x='140mm' y='206mm'>{nombre_campanya}</drawString>
                        <setFont name=\"Times-Roman\" size=\"8\"/>
                        <drawCentredString x=\"148.5mm\" y=\"203mm\">{filtro}</drawCentredString>
                        <drawCentredString x=\"148.5mm\" y=\"200mm\">{filtro_clasif}</drawCentredString>
                        <setFont name=\"Times-Roman\" size=\"8\"/>
                        <drawString x='270mm' y='206mm'>{hoy}</drawString>
                        <setFont name=\"Times-Roman\" size=\"8\"/>
                        <drawString x='250mm' y='8mm'>Pág. <pageNumber />  <getName id=\"lastPage\" /></drawString>
                    </pageGraphics>
                    <frame id='first' x1='7mm' y1='10mm' width='280mm' height='185mm'/>
                 </pageTemplate>             
            </template>"""
        ]

        colWidths = "(10mm,20mm,15mm,25mm,25mm,25mm,50mm,25mm,20mm,20mm,50mm)"

        rml_story = [
            """
            <story>            
                    """
        ]
        rml_stylesheet = [
            """
            <stylesheet>
                    """
        ]

        rml_story.append(
            f"""<blockTable style=\"tablalinea\" repeatRows=\"0\" colWidths='{colWidths}'>"""
        )

        cabecera = f"""
            <tr>
                <td><para style=\"paralinea2\">Nº</para></td>
                <td><para style=\"paralinea2\">Fecha</para></td>
                <td><para style=\"paralinea2\">Clasif</para></td>
                <td><para style=\"paralinea2\">Código</para></td>
                <td><para style=\"paralinea2\">ID</para></td>
                <td><para style=\"paralinea2\">Tipología</para></td>
                <td><para style=\"paralinea2\">Dirección</para></td>
                <td><para style=\"paralinea2\">Municipio</para></td>
                <td><para style=\"paralinea2\">Provincia</para></td>
                <td><para style=\"paralinea2\">Deuda</para></td>
                <td><para style=\"paralinea2\">Comentarios</para></td>
            </tr>
        """

        cabecera2 = f"""
            <tr>
                <td><para style="paralinea2">Nº</para></td>
                <td><para style="paralinea2">Fecha</para></td>
                <td><para style="paralinea2">Clasif</para></td>
                <td><para style="paralinea2">Código</para></td>
                <td><para style="paralinea2">ID</para></td>
                <td><para style="paralinea2">Tipología</para></td>
                <td><para style="paralinea2">Dirección</para></td>
                <td><para style="paralinea2">Municipio</para></td>
                <td><para style="paralinea2">Provincia</para></td>
                <td><para style="paralinea2">Precio</para></td>
                <td><para style="paralinea2">Comentarios</para></td>
            </tr>
        """

        # activos=campanya.DameActivos()
        lineas_cabeceras = []
        lineas_catastro = []
        numlinea = 0

        i = 0
        if numLinea is not None:
            i = numLinea
        inicio_bucle = True
        separacion = False
        cambio_a_50k = False
        cambio_a_75k = False
        cambio_a_100k = False
        cambio_a_mas100k = False
        cambio_a_desconocidos = False
        # solucion duplicados 9/4/25
        ids_lineas_unicas = (
            lineas.values(
                "activo__id",
                "activo__ref_catastral",
                "activo__direccion",
            )
            .annotate(ultimo_id=Max("id"))
            .values_list("ultimo_id", flat=True)
        )

        lineas = lineas.filter(id__in=ids_lineas_unicas)

        lineas = lineas.annotate(
            tipo_orden=Case(
                When(tipo="NPL", then=Value(0)),
                When(tipo="CDR", then=Value(1)),
                When(tipo="REO", then=Value(2)),
                default=Value(3),
                output_field=FloatField(),
            ),
            es_precio_consultar=Case(
                # Si es NPL, mirar tanto precio como importe_deuda
                When(
                    tipo="NPL",
                    then=Case(
                        When(
                            (Q(precio__isnull=True) | Q(precio=0))
                            and (Q(importe_deuda__isnull=True) | Q(importe_deuda=0)),
                            then=Value(True),
                        ),
                        default=Value(False),
                        output_field=BooleanField(),
                    ),
                ),
                # Si no es NPL, solo mirar precio
                default=Case(
                    When(Q(precio__isnull=True) | Q(precio=0), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
                output_field=BooleanField(),
            ),
            valor_orden=Case(
                When(tipo="NPL", then=Greatest(F("precio"), F("importe_deuda"))),
                default=F("precio"),
                output_field=FloatField(),
            ),
        ).order_by("tipo_orden", "es_precio_consultar", "valor_orden")

        tipo = ""
        for linea in lineas:
            if "NPL" in linea.tipo:
                num_columnas = 11
                cabecera_a_usar = cabecera
            else:
                num_columnas = 11
                cabecera_a_usar = cabecera2

            # cambio_a_desconocidos = True

            no_disponible = ""
            if linea.activo.no_disponible:
                no_disponible = "no_disponible"
            i += 1
            if tipo != linea.tipo:
                tipo = linea.tipo
                cambio_a_50k = False
                cambio_a_75k = False
                cambio_a_100k = False
                cambio_a_mas100k = False
                cambio_a_desconocidos = False
                # Cierra tabla actual

                rml_story.append(
                    f"""
                    <tr><td colspan='{num_columnas}'><para style="lineaprecio">{tipo}</para></td></tr>"""
                )
                lineas_cabeceras.append(numlinea)
                numlinea += 1
            if (
                (tipo == "NPL" and not linea.precio and not linea.importe_deuda)
                or (tipo != "NPL" and not linea.precio)
            ) and not cambio_a_desconocidos:
                rml_story.append(
                    f"""
                    <tr><td colspan='{num_columnas}'><para style="lineaprecio">PRECIO A CONSULTAR</para></td></tr>{cabecera_a_usar}"""
                )
                lineas_cabeceras.append(numlinea)
                numlinea += 2
                cambio_a_desconocidos = True

            elif linea.precio or linea.importe_deuda:
                if tipo == "NPL":
                    if max(linea.precio or 0, linea.importe_deuda or 0) < 50000:
                        if not cambio_a_50k:
                            cambio_a_50k = True
                            rml_story.append(
                                f"""
                                <tr><td colspan='{num_columnas}'><para style="lineaprecio">&lt; 50k</para></td></tr>{cabecera_a_usar}"""
                            )
                            lineas_cabeceras.append(numlinea)
                            numlinea += 2
                    elif max(linea.precio or 0, linea.importe_deuda or 0) < 75000:
                        if not cambio_a_75k:
                            cambio_a_75k = True
                            rml_story.append(
                                f"""
                                <tr><td colspan='{num_columnas}'><para style="lineaprecio">&lt; 75k</para></td></tr>{cabecera_a_usar}"""
                            )
                            lineas_cabeceras.append(numlinea)
                            numlinea += 2
                    elif max(linea.precio or 0, linea.importe_deuda or 0) < 100000:
                        if not cambio_a_100k:
                            cambio_a_100k = True
                            rml_story.append(
                                f"""
                                <tr><td colspan='{num_columnas}'><para style="lineaprecio">&lt; 100k</para></td></tr>{cabecera_a_usar}"""
                            )
                            lineas_cabeceras.append(numlinea)
                            numlinea += 2
                    elif max(linea.precio or 0, linea.importe_deuda or 0) > 100000:
                        if not cambio_a_mas100k:
                            cambio_a_mas100k = True
                            rml_story.append(
                                f"""
                                <tr><td colspan='{num_columnas}'><para style="lineaprecio">&gt; 100k</para></td></tr>{cabecera_a_usar}"""
                            )
                            lineas_cabeceras.append(numlinea)
                            numlinea += 2
                else:
                    if (linea.precio or 0) < 50000:
                        if not cambio_a_50k:
                            cambio_a_50k = True
                            rml_story.append(
                                f"""
                                <tr><td colspan='{num_columnas}'><para style="lineaprecio">&lt; 50k</para></td></tr>{cabecera_a_usar}"""
                            )
                            lineas_cabeceras.append(numlinea)
                            numlinea += 2
                    elif linea.precio < 75000:
                        if not cambio_a_75k:
                            cambio_a_75k = True
                            rml_story.append(
                                f"""
                                <tr><td colspan='{num_columnas}'><para style="lineaprecio">&lt; 75k</para></td></tr>{cabecera_a_usar}"""
                            )
                            lineas_cabeceras.append(numlinea)
                            numlinea += 2
                    elif linea.precio < 100000:
                        if not cambio_a_100k:
                            cambio_a_100k = True
                            rml_story.append(
                                f"""
                                <tr><td colspan='{num_columnas}'><para style="lineaprecio">&lt; 100k</para></td></tr>{cabecera_a_usar}"""
                            )
                            lineas_cabeceras.append(numlinea)
                            numlinea += 2
                    elif linea.precio > 100000:
                        if not cambio_a_mas100k:
                            cambio_a_mas100k = True
                            rml_story.append(
                                f"""
                                <tr><td colspan='{num_columnas}'><para style="lineaprecio">&gt; 100k</para></td></tr>{cabecera_a_usar}"""
                            )
                            lineas_cabeceras.append(numlinea)
                            numlinea += 2

            linea_campanya_cartera_codigo = linea.campanya.proveedor.codigo
            if linea.campanya.cartera:
                linea_campanya_cartera_codigo = linea.campanya.cartera.codigo
            linea_campanya_fecha = linea.campanya.fecha.strftime("%d/%m/%Y")
            precio = ""
            deuda = ""
            subasta = ""
            if linea.precio or linea.importe_deuda:
                if tipo == "NPL":
                    precio = Importe2Cadena(
                        max(linea.precio or 0, linea.importe_deuda or 0)
                    )
                else:
                    precio = Importe2Cadena(linea.precio or None)

            if linea.valor_referencia:
                subasta = Importe2Cadena(linea.valor_referencia)
            if linea.activo.ref_ue:
                linea_activo_ref_ue = linea.activo.ref_ue
            else:
                linea_activo_ref_ue = ""
            linea_activo_direccion = linea.activo.direccion
            linea_activo_poblacion = linea.activo.poblacion.nombre
            observ = ""
            if linea.estado_ocupacional != "0":  # si es desconocido lo obvio
                observ = linea.get_estado_ocupacional_display()
            if linea.estado_legal:
                observ += f" {linea.estado_legal}"
            subgrupo_nombre = "---"
            if linea.activo.tipologia:
                subgrupo_nombre = linea.activo.tipologia

            if observ == "":
                observ = linea.observaciones

            # rml_story.append(f"""
            # <tr><td>{i}</td>
            # <td><para style="paralinea{no_disponible}">{linea_campanya_cartera_codigo}</para></td>
            # <td><para style="paralinea{no_disponible}">{linea_campanya_fecha}</para></td>
            # <td><para style="paralinea{no_disponible}">{linea.tipo}</para></td>
            # <td><para style="paralinea{no_disponible}">{linea.activo.ref_ue}</para></td>
            # <td><para style="paralinea{no_disponible}">{linea.activo.id_proveedor}</para></td>
            # <td><para style="paralinea{no_disponible}">{subgrupo_nombre}</para></td>
            # <td><para style="paralinea{no_disponible}">{linea.activo.ref_catastral}</para></td>
            # <td><para style="paralinea{no_disponible}_direccion">{linea_activo_direccion}</para></td>
            # <td><para style="paralinea{no_disponible}">{linea_activo_poblacion}</para></td>
            # <td><para style="paralinea{no_disponible}">{linea.activo.poblacion.provincia.nombre}</para></td>
            # <td><para style="paralinea{no_disponible}_precio">{precio}</para></td>
            # <td><para style="paralinea{no_disponible}_direccion">{observ}</para></td></tr>
            # """)

            rml_story.append(
                f"""
                <tr><td>{i}</td>
                <td><para style="paralinea{no_disponible}">{QuitaCaracteres(linea_campanya_fecha)}</para></td>
                <td><para style="paralinea{no_disponible}">{QuitaCaracteres(tipo)}</para></td>
                <td><para style="paralinea{no_disponible}">{QuitaCaracteres(linea_campanya_cartera_codigo)}</para></td>
                <td><para style="paralinea{no_disponible}">{QuitaCaracteres(linea.activo.id_proveedor)}</para></td>
                <td><para style="paralinea{no_disponible}_direccion">{QuitaCaracteres(subgrupo_nombre)}</para></td>
                <td><para style="paralinea{no_disponible}_direccion">{QuitaCaracteres(linea_activo_direccion)}</para></td>
                <td><para style="paralinea{no_disponible}">{QuitaCaracteres(linea_activo_poblacion)}</para></td>
                <td><para style="paralinea{no_disponible}">{QuitaCaracteres(linea.activo.poblacion.provincia.nombre)}</para></td>
                <td><para style="paralinea{no_disponible}_precio">{QuitaCaracteres(precio)}</para></td>
                <td><para style="paralinea{no_disponible}_direccion">{QuitaCaracteres(observ)}</para></td></tr>
            """
            )
            numlinea += 1
            url_google = linea.activo.DameURLGoogleMaps().replace('"', "")
            url_google = QuitaCaracteres(url_google)
            # rml_story.append(f"""
            # <tr><td></td>
            # <td><para style="paralinea{no_disponible}">Catastro: Dirección: </para><para style="paralinea{no_disponible}_direccion">{linea.activo.catastro_localizacion}</para></td>
            # <td></td>
            # <td></td>
            # <td></td>
            # <td><para style="paralinea{no_disponible}">Clase: {linea.activo.catastro_clase}</para></td>
            # <td><para style="paralinea{no_disponible}">Uso: {linea.activo.catastro_uso_principal}</para></td>
            # <td><para style="paralinea{no_disponible}">Superficie:{linea.activo.catastro_superficie}</para></td>
            # <td><para style="paralinea{no_disponible}">Año:{linea.activo.catastro_anyo_construccion}</para></td>
            # <td><para style="paralinea{no_disponible}_direccion">Localización: <link href="{url_google}">{url_google}</link></para></td>
            # <td></td>
            # <td></td>
            # </tr>""")

            # cambio 25/3/25
            inf = ""
            if linea.activo.catastro_superficie:
                inf = f"Superficie: {linea.activo.catastro_superficie} m², Uso principal: {linea.activo.catastro_uso_principal}, Año construcción: {linea.activo.catastro_anyo_construccion}"

            rml_story.append(
                f"""
                <tr><td></td>
                    <td><para style="paralinea{no_disponible}">Catastro: {linea.activo.ref_catastral}</para>
                    <para style="paralinea{no_disponible}">Dirección: {linea.activo.catastro_localizacion}</para></td>
                    <td></td>
                    <td></td>
                    <td><para style="paralinea{no_disponible}_direccion">Localización: <link href="{url_google}">{url_google}</link></para></td>
                    <td></td>
                    <td></td>
                    <td><para style="paralinea{no_disponible}">{inf}</para></td>
                    <td></td>
                    
                </tr>"""
            )

            lineas_catastro.append(numlinea)
            numlinea += 1

        rml_story.append(
            f"""
                </blockTable>"""
        )

        rml_stylesheet.append(
            f"""        
                <blockTableStyle id="tablalinea">
                    <blockFont name="Times-Roman" size="8" start="0,1" stop="-1,-1" />
                    <lineStyle kind="GRID" colorName="black" thickness="1" start="0,0" stop="-1,-1"/>
                    <blockAlignment value="CENTER" start="0,0" stop="0,-1" />"""
        )
        for num_columna in columnas_alineamiento_derecha:
            rml_stylesheet.append(
                f"""
                    <blockAlignment value="RIGHT" start="{num_columna},0" stop="{num_columna},-1" />"""
            )
        for linea_cabecera in lineas_cabeceras:
            linea_cabecera_1 = linea_cabecera + 1
            rml_stylesheet.append(
                f"""
                    <blockSpan start='0,{linea_cabecera}' stop='-1,{linea_cabecera}'/>
                    <blockFont name="Courier-Bold" size="6" start="0,{linea_cabecera_1}" stop="-1,{linea_cabecera_1}" />
                """
            )
        for linea_catastro in lineas_catastro:
            rml_stylesheet.append(
                f"""
                <blockSpan start='1,{linea_catastro}' stop='3,{linea_catastro}'/>
                <blockSpan start='4,{linea_catastro}' stop='6,{linea_catastro}'/>
                <blockSpan start='7,{linea_catastro}' stop='10,{linea_catastro}'/>
            """
            )
        rml_stylesheet.append(
            f"""
            </blockTableStyle>"""
        )
        rml_stylesheet.append(
            f"""
                <paraStyle name="paralinea_direccion"
                            fontName='Times-Roman'
                            fontSize='8'
                            leading='8'
                />
                <paraStyle name="paralinea_precio"
                            fontName='Times-Roman'
                            fontSize='8'
                            leading='8'
                            alignment="RIGHT"
                />

                <paraStyle name="paralinea"
                            fontName='Times-Roman'
                            fontSize='8'
                            leading='8'
                />
                <paraStyle name="paralinea2"
                            fontName='Times-Roman'
                            fontSize='9'
                            leading='12'
                            alignment='CENTER'

                />
                <paraStyle name="lineaprecio"
                            fontName='Times-Roman'
                            fontSize='12'
                            alignment='CENTER'
                />
                <paraStyle name="paralineano_disponible_direccion"
                            fontName='Times-Roman'
                            fontSize='6'
                            leading='6'
                            textColor='red'
                />
                <paraStyle name="paralineano_disponible_precio"
                            fontName='Times-Roman'
                            fontSize='8'
                            leading='8'
                            textColor='red'
                            alignment="RIGHT"
                />

                <paraStyle name="paralineano_disponible"
                            fontName='Times-Roman'
                            fontSize='8'
                            leading='8'
                            textColor='red'
                />
                <paraStyle name="lineapreciono_disponible"
                            fontName='Times-Roman'
                            fontSize='12'
                            alignment='CENTER'
                            textColor='red'
                />"""
        )
        # for linea_cabecera in lineas_cabeceras:
        #     linea_cabecera_1=linea_cabecera+1
        #     rml_stylesheet.append(f"""
        #             <blockSpan start='0,{linea_cabecera}' stop='-1,{linea_cabecera}'/>
        #             <blockFont name="Courier-Bold" size="6" start="0,{linea_cabecera_1}" stop="-1,{linea_cabecera_1}" />
        #         """)
        # for linea_catastro in lineas_catastro:
        #     rml_stylesheet.append(f"""
        #             <blockSpan start='1,{linea_catastro}' stop='4,{linea_catastro}'/>
        #             <blockSpan start='9,{linea_catastro}' stop='11,{linea_catastro}'/>
        #         """)
        rml_stylesheet.append(
            f"""
            </stylesheet>"""
        )

        rml_story.append(
            """

            </story>"""
        )

        rml_cadena += rml_stylesheet + rml_story
        rml_cadena.append("</document>")

        rml_cadena = "".join(rml_cadena)
        if retornar_partes_rml:
            cabecera_footer = f"""
            <template pagesize=\"(29.7cm, 21cm)\">
                <pageTemplate id=\"principal\">
                    <pageGraphics>
                        <setFont name=\"Times-Roman\" size=\"8\"/>
                        <drawString x='5mm' y='206mm'>INVEST MSS</drawString>
                        <drawString x='140mm' y='206mm'>{nombre_campanya}</drawString>
                        <setFont name=\"Times-Roman\" size=\"8\"/>
                        <drawCentredString x=\"148.5mm\" y=\"203mm\">{filtro}</drawCentredString>
                        <drawCentredString x=\"148.5mm\" y=\"200mm\">{filtro_clasif}</drawCentredString>
                        <setFont name=\"Times-Roman\" size=\"8\"/>
                        <drawString x='270mm' y='206mm'>{hoy}</drawString>
                        <setFont name=\"Times-Roman\" size=\"8\"/>
                        <drawString x='250mm' y='8mm'>Pág. <pageNumber />  <getName id=\"lastPage\" /></drawString>
                    </pageGraphics>
                    <frame id='first' x1='7mm' y1='10mm' width='280mm' height='185mm'/>
                </pageTemplate>             
            </template>
            """

            return {
                "rml_completo": "".join(rml_cadena),
                "rml_stylesheet": "".join(rml_stylesheet),
                "rml_story": "".join(rml_story),
                "rml_template": cabecera_footer,
            }

        return rml_cadena
    except Exception as e:
        logger.error(f"Error en GenerarListaActivosConCatastroRML: {e}", exc_info=True)
        return f"Error generando el RML: {e}"


def GenerarContratoRML(empresa, lineapropuesta, nombrefichero="fichero.pdf"):

    rml_cadena = [
        f"""
        <!DOCTYPE document SYSTEM "rml.dtd">
        <document filename='{nombrefichero}'>
        <template pagesize="(21cm, 29.7cm, 21cm)">
            <pageTemplate id="principal">
                <pageGraphics>
                    <image file='{empresa.logotipo_correos.path}' x='20mm' y='255mm' height='15mm' width='45mm'/>
                    <setFont name="Times-Bold" size="8"/>                    
                    <drawString x='155mm' y='268mm'>{empresa.direccion} {empresa.cp} {empresa.poblacion}</drawString>
                    <drawString x='155mm' y='265mm'>Telf {empresa.telefono} CIF {empresa.nif}</drawString>
                    <setFont name="Courier" size="8"/>
                    <drawString x='250mm' y='8mm'>Pág. <pageNumber />  <getName id="lastPage" /></drawString>


                </pageGraphics>
                <frame id='first' x1='20mm' y1='20mm' width='175mm' height='210mm'/>
             </pageTemplate>             
        </template>
        <stylesheet>
            
            <paraStyle name="estilotitulo" 
                        fontName='Times-Roman'
                        fontSize='14'
                        leading='14'
                        alignment="CENTER"
                        spaceAfter="1cm"
                        leftIndent="50"
                        rightIndent="50"
            />
            <paraStyle name="estiloderecha" 
                        fontName='Times-Roman'
                        fontSize='12'
                        alignment="RIGHT"
            />
            <paraStyle name="estiloresaltado" 
                        fontName='Times-Bold'
                        fontSize='12'
                        alignment="CENTER"
                        spaceBefore="1cm"
                        spaceAfter="1cm"
            />
            <paraStyle name="estilonormal" 
                        fontName='Times-Roman'
                        fontSize='12'
                        leading='14'
                        alignment="justify"
                        firstLineIndent="50"
                        spaceAfter="0.5cm"
            />
            <paraStyle name="estiloactivo" 
                        fontName='Times-Roman'
                        fontSize='12'
                        leading='14'
                        alignment="justify"
                        leftIndent="75"
                        spaceAfter="0.5cm"
            />
            <listStyle name="listItemStyle" 
                        fontName='Times-Roman'
                        fontSize='12'
                        bulletColor="black"
                        bulletFontName="Courier"
                        bulletFontsize="13" 
            />
            <blockTableStyle id="estilofirma">
                <blockFont name='Times-Roman' size="12"/>
                <blockAlignment value="RIGHT" start="1,0" stop="1,-1"/>
                leftIndent="50"
            </blockTableStyle>

        </stylesheet>
        <story>
            <para style='estilotitulo'>CONTRATO DE MANDATO DE COMPRA Y PRESTACIÓN DE SERVICIOS PROFESIONALES</para>
            <para style='estiloderecha'>En Valencia, a ……</para>
            <para style='estiloresaltado'>REUNIDOS</para>
            <para style='estilonormal'>De una parte, <b>{lineapropuesta.propuesta.cliente.nombre}</b>, mayor de edad, con DNI {lineapropuesta.propuesta.cliente.nif}, en calidad de Administrador único de ………. con CIF ......, con domicilio social en………………, en adelante MANDANTE.</para>
            <para style='estilonormal'>Y, de otra parte, <b>D. José Ramón Albiñana Bengoechea</b>, mayor de edad, provisto con D.N.I.: 25.386.422-B actuando en su calidad de Administrador único de la entidad Mercantil INVEST MSS S.L. con CIF B-98844442, con domicilio social en calle Colón, nº12, 1º 1ª y en adelante MANDATARIO.</para>
            <para style='estiloresaltado'>MANIFIESTAN</para>
            <para style='estilonormal'>I.- Que la mercantil…………. está interesada en adquirir la siguiente</para>
            <para style='estiloactivo'><b>•</b> {lineapropuesta.campanya_linea.activo.tipologia.subgrupo.nombre} {lineapropuesta.campanya_linea.activo.direccion} {lineapropuesta.campanya_linea.activo.poblacion}</para>
            <para style='estiloactivo'><b>•</b> </para>
            <para style='estiloactivo'><b>•</b> Referencia catastral {lineapropuesta.campanya_linea.activo.ref_catastral}</para>
            <para style='estilonormal'>II.- Que ………….. (MANDANTE) en este acto confiere mandato expreso a la entidad mercantil INVEST MSS S.L. (MANDATARIO), facultándola para que en su nombre realice las gestiones necesarias para adquirir la deuda anteriormente reseñada y descrita.</para>
            <para style='estilonormal'>Reconociéndose ambas partes la capacidad legal necesaria para la celebración y suscripción del presente contrato de mandato se someten al cumplimiento de los siguientes acuerdos:</para>
            <para style='estiloresaltado'>ACUERDOS</para>
            <para style='estiloresaltado' underline="true">PRIMERO.- OBJETO DE MANDATO</para>
            <para style='estilonormal'>El objeto de mandato es la adquisición de la deuda que grava el inmueble descrito anteriormente en el manifestando primero, deuda que se adquirirá por el importe total de ………. € (…………….), más gastos e impuestos, que soportará el mandante.</para>
            <para style='estilonormal'>La referida deuda se adquirirá en virtud de escritura pública de compraventa de crédito, subrogándose el mandante en la posición del acreedor hipotecario, previo cumplimiento de la obligación de pago anteriormente reseñada.</para>
            <para style='estiloresaltado' underline="true">SEGUNDO.- PAGO DEL PRECIO DE ADQUISICIÓN</para>
            <para style='estilonormal'>El MANDATARIO informará al MANDANTE de los cheques bancarios y el importe de los mismos que debe entregar en el momento de la formalización de la escritura pública de compraventa y adquisición de la deuda, momento en el que se subrogará en posición del acreedor hipotecante.</para>
            <para style='estiloresaltado' underline="true">TERCERO.- RETRIBUCIÓN DEL MANDATARIO</para>
            <para style='estilonormal'>El mandatario percibirá en concepto de retribución por el cumplimiento del mandato el 5% del importe de adquisición más el IVA correspondiente, cantidad que pagará el mandante en el instante que se otorgue la escritura pública de adquisición del crédito, objeto de contrato.</para>
            <para style='estiloresaltado' underline="true">CUARTO.- PLAZO DEL MANDATO Y VENTANA DE SALIDA</para>
            <para style='estilonormal'>Ambas partes acuerdan que el presente mandato tenga una vigencia temporal de 30 (treinta) días, pudiéndose prorrogar por 30 (treinta) días más a voluntad de ambas partes, debiéndose otorgar la escritura pública de compraventa del crédito-deuda y subrogación del mandante en la posición del acreedor hipotecante en dicho plazo.</para>
            <para style='estiloresaltado' underline="true">QUINTO.- OBLIGACIONES MUTUAS</para>
            <para style='estilonormal'>EL MANDANTE se compromete a facilitar a la mayor brevedad posible cuanta documentación sea requerida por parte del MANDATARIO con la finalidad de cumplir el objeto de mandato, en concreto, la documentación necesaria relativa al PBC o Blanqueo de Capitales que sea requerida para el buen fin del cumplimiento del mandato y cualquier otra documentación preceptiva.</para>
            <para style='estilonormal'>Ambas partes acuerdan que toda documentación facilitada deberá remitirse por e-mail – correos electrónicos- al objeto que quede debida constancia, siendo el correo del MANDATARIO: info@grupomss.com</para>
            <para style='estilonormal'>El MANDATARIO no divulgará, difundirá o hará uso de la documentación e información facilitada por el MANDANTE salvo para los fines del cumplimiento de este contrato.</para>
            <para style='estiloresaltado' underline="true">SEXTO.- SEÑAL ACEPTACIÓN MANDATO</para>
            <para style='estilonormal'>El MANDANTE se compromete y obliga a ingresar a la firma del presente contrato la cantidad de …….. € (………….) en concepto de aceptación del mandato en la cuenta bancaria de la que es titular el MANDATARIO y que a continuación se reseña:</para>
            <para style='estiloresaltado'>ES95 0081 5237 5000 0134 0838</para>
            <para style='estilonormal'>En el supuesto no pudiese materializarse el objeto de este contrato por no cumplir el mandante con su obligación de pago, así como, el desistimiento voluntario después de la sanción por parte del fondo, éste perderá la cantidad entregada y, en el resto de posibles supuestos éste tendrá derecho a la devolución de la cantidad entregada, debiendo reintegrar el mandatario la misma en un plazo de 15 a 30 días desde el requerimiento.</para>
            <para style='estilonormal'>La cantidad entregada por el MANDANTE, al margen de lo reseñado, se entrega en concepto de pago parcial del precio de compra en el supuesto ésta llegase a buen fin.</para>
            <para style='estiloresaltado' underline="true">SÉPTIMO.- SUMISIÓN AL FUERO PROPIO</para>
            <para style='estilonormal'>Ambas partes con renuncia expresa a su fuero propio se someten a la jurisdicción de los Juzgados y Tribunales de la ciudad de Valencia para resolver cuantas dudas y divergencias pudiesen derivarse de la interpretación, alcance y contenido de este contrato.</para>
            <para style='estilonormal'>En prueba de su conformidad firman por duplicado y a un solo efecto en el lugar y el encabezamiento ut supra.</para>
            <blockTable style="estilofirma" colWidths='(80mm, 80mm)'>
                <tr><td>El Mandante</td><td>El Mandatario</td></tr>
                <tr><td></td><td></td></tr>
                <tr><td></td><td></td></tr>
                <tr><td>...................</td><td>D. José Ramón Albiñana Bengoechea.</td></tr>
                <tr><td></td><td>INVEST MSS S.L.</td></tr>
            </blockTable>

            <namedString id="lastPage"><pageNumber/></namedString>
        </story>
        </document>
        """
    ]

    rml_cadena = " ".join(rml_cadena)
    return rml_cadena


def GenerarListadoEstados(
    empresa,
    campanya,
    lineas,
    clasif,
    grupo,
    tipo,
    poblacion,
    provincia,
    estado,
    nombrefichero="fichero.pdf",
    texto_filtro="",
    proveedores=None,
    numLinea=None,
    retornar_partes_rml=False,
    idealista=False,
    fotocasa_pro=False,
    web_invest=False,
):
    try:
        texto_filtro = re.sub(r"\s*Desde:\s*Hasta:\s*", "", texto_filtro).strip()
        hoy = datetime.now().strftime("%d-%m-%Y")

        if proveedores is None:
            proveedores = lineas.values_list(
                "campanya__proveedor", flat=True
            ).distinct()

        nombre_campanya = ""
        if campanya and hasattr(campanya, "cartera"):
            nombre_campanya = f"{campanya.cartera.codigo}"

        filtro = ""
        if provincia and provincia.first():
            provincia_nombre = provincia.values_list("nombre", flat=True)
            provincia_nombre = ",".join(provincia_nombre).upper()
            filtro = f"PROVINCIA: {provincia_nombre}"
        else:
            filtro = "TODAS LAS PROVINCIAS"

        if grupo:
            try:
                grupo_nombre = grupo.nombre.upper()
            except Exception:
                grupo_nombre = "".join(g.nombre.upper() for g in grupo)
            filtro += f" - TIPOLOGÍA: {grupo_nombre}"
        else:
            filtro += f" - TODAS LAS TIPOLOGÍAS"

        if poblacion and poblacion.first():
            poblacion_nombre = poblacion.values_list("nombre", flat=True)
            poblacion_nombre = ",".join(poblacion_nombre).upper()
            filtro += f" - POBLACIÓN: {poblacion_nombre}"

        filtro_clasif = ""

        rml = [
            f"""
            <!DOCTYPE document SYSTEM "rml.dtd">
            <document filename="{nombrefichero}">
                <template pagesize="(29.7cm, 21cm)">
                    <pageTemplate id="principal">
                        <pageGraphics>
                            <setFont name="Times-Roman" size="8"/>
                            <drawString x="5mm" y="206mm">INVEST MSS</drawString>
                            <drawString x="140mm" y="206mm">{nombre_campanya}</drawString>
                            <drawCentredString x="148.5mm" y="203mm">{filtro}</drawCentredString>
                            <drawCentredString x="148.5mm" y="200mm">{filtro_clasif}</drawCentredString>
                            <drawString x="270mm" y="206mm">{hoy}</drawString>
                            <drawString x="250mm" y="8mm">Pág. <pageNumber />  <getName id="lastPage" /></drawString>
                        </pageGraphics>
                        <frame id="first" x1="7mm" y1="10mm" width="280mm" height="185mm"/>
                    </pageTemplate>
                </template>

                <stylesheet>
                    <paraStyle name="default" fontName="Times-Roman" fontSize="9" leading="10" alignment="CENTER"/>
                    <paraStyle name="linea" fontName="Times-Bold" fontSize="8" textColor="#444444"/>
                    <paraStyle name="titulo" fontName="Times-Bold" fontSize="11" alignment="CENTER"/>

                    <blockTableStyle id="tabla_estados">
                        <blockAlignment value="LEFT"/>
                        <blockValign value="TOP"/>
                        <lineStyle kind="GRID" colorName="black" thickness="0.5"/>
                        <lineStyle kind="INNERGRID" colorName="black" thickness="0.25"/>
                        <lineStyle kind="OUTLINE" colorName="black" thickness="0.5"/>
                        <blockFont name="Times-Roman" size="8"/>
                        <blockBackground colorName="white"/>
                    </blockTableStyle>

                    <blockTableStyle id="tabla_titulo">
                        <blockValign value="MIDDLE"/>
                        <blockAlignment value="CENTER"/>
                        <blockBackground colorName="whitesmoke"/>
                        <lineStyle kind="GRID" colorName="black" thickness="0.5"/>
                        <lineStyle kind="INNERGRID" colorName="black" thickness="0.25"/>
                        <lineStyle kind="OUTLINE" colorName="black" thickness="0.5"/>
                        <blockFont name="Times-Bold" size="9" textColor="black"/>
                    </blockTableStyle>
                </stylesheet>



                <story>
            """
        ]

        current_estado = None
        i = 1
        # lineas = lineas.annotate(
        #    portal_orden=Case(
        #        When(idealista=True, then=Value(0)),
        #        When(fotocasa_pro=True, then=Value(1)),
        #        When(web_invest=True, then=Value(2)),
        #        default=Value(3),
        #        output_field=IntegerField()
        #    ),
        #    estado_orden=Case(
        #        When(activo__estado_activo=None, then=Value("Sin Portal")),  # Para que los nulos vayan al final
        #        default=F("activo__estado_activo"),
        #    )
        # ).order_by("estado_orden", "portal_orden")

        lineas = lineas.annotate(
            portal_orden=Case(
                When(activo__idealista=True, then=Value(0)),
                When(activo__fotocasa_pro=True, then=Value(1)),
                When(activo__web_invest=True, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            ),
            estado_orden=F("activo__estado_activo"),
        ).order_by("estado_orden", "portal_orden")

        ids_lineas_unicas = (
            lineas.values(
                "activo__id",
                "activo__ref_catastral",
                "activo__direccion",
            )
            .annotate(ultimo_id=Max("id"))
            .values_list("ultimo_id", flat=True)
        )

        lineas = lineas.filter(id__in=ids_lineas_unicas)

        current_estado = None
        current_portal = None
        i = 1
        # rml.append(
        #    """
        #    <blockTable style="tabla_titulo" colWidths="(290mm)">
        #        <tr>
        #            <td><para alignment="CENTER">POSICIONES ESTUDIADAS - POSIBLES ANUNCIOS DEPARTAMENTO COMERCIAL</para></td>
        #        </tr>
        #    </blockTable>
        # """
        # )
        for linea in lineas:
            estado_actual = getattr(linea.activo, "estado_activo", "SIN ESTADO")
            portal_actual = (
                "IDEALISTA"
                if getattr(linea.activo, "idealista", False)
                else (
                    "FOTOCASA_PRO"
                    if getattr(linea.activo, "fotocasa_pro", False)
                    else (
                        "WEB_INVEST"
                        if getattr(linea.activo, "web_invest", False)
                        else "SIN PORTAL"
                    )
                )
            )

            # Cambio de estado
            if estado_actual != current_estado:
                if current_estado is not None:
                    rml.append("</blockTable>")
                current_estado = estado_actual
                current_portal = None
                rml.append("<spacer length='3mm'/>")
                rml.append(
                    f"""
                    <blockTable style="tabla_titulo" colWidths="(290mm)">
                        <tr>
                            <td><para alignment="CENTER"><b>POSICIONES EN ESTADO {current_estado.upper()}</b></para></td>
                        </tr>
                    </blockTable>
                """
                )

            # Cambio de portal dentro del mismo estado
            if portal_actual != current_portal:
                if current_portal is not None:
                    rml.append("</blockTable>")  # Cierra tabla anterior del portal
                current_portal = portal_actual
                rml.append(
                    f"""
                    <blockTable style="tabla_titulo" colWidths="(290mm)">
                        <tr>
                            <td><para alignment="CENTER"><b>PORTAL: {current_portal}</b></para></td>
                        </tr>
                    </blockTable>
                    <blockTable style="tabla_titulo"
                    colWidths="(6mm,20mm,10mm,23mm,18mm,22mm,28mm,19.31mm,19.31mm,19.16mm, 19.17mm, 19.17mm,23mm,26.33mm,17.55mm)">
                        <tr>
                            <td><para style="default"><b>Nº</b></para></td>
                            <td><para style="default"><b>Fecha <br/>Perímetro</b></para></td>
                            <td><para style="default"><b>Tipo</b></para></td>
                            <td><para style="default"><b>Código</b></para></td>
                            <td><para style="default"><b>ID</b></para></td>
                            <td><para style="default"><b>Clasificación</b></para></td>
                            <td><para style="default"><b>Dirección</b></para></td>
                            <td><para style="default"><b>Municipio</b></para></td>
                            <td><para style="default"><b>Provincia</b></para></td>
                            <td><para style="default"><b>Importe Deuda</b></para></td>
                            <td><para style="default"><b>Precio Compra</b></para></td>
                            <td><para style="default"><b>Valor Mercado</b></para></td>
                            <td><para style="default"><b>Comentarios</b></para></td>
                            <td><para style="default"><b>Respuesta Fondo</b></para></td>
                            <td><para style="default"><b>Fecha Estudio</b></para></td>
                        </tr>
                    </blockTable>
                    <blockTable style="tabla_estados"
                    colWidths="(6mm,20mm,10mm,23mm,18mm,22mm,28mm,19.31mm,19.31mm,19.31mm,19.31mm,19.31mm,23mm,26.33mm,17.55mm)">
                """
                )

            # Fila de datos
            rml.append(
                f"""
                <tr>
                    <td><para style="linea">{i}</para></td>
                    <td><para style="linea">{linea.campanya.fecha.strftime('%d/%m/%Y')}</para></td>
                    <td><para style="linea">{linea.tipo}</para></td>
                    <td><para style="linea">{getattr(linea.campanya.proveedor, "nombre", "")}</para></td>
                    <td><para style="linea">{linea.activo.id_proveedor}</para></td>
                    <td><para style="linea">{getattr(linea.activo.tipologia, "nombre", "")}</para></td>
                    <td><para style="linea">{linea.activo.catastro_localizacion or linea.activo.direccion}</para></td>
                    <td><para style="linea">{linea.activo.poblacion.nombre}</para></td>
                    <td><para style="linea">{linea.activo.poblacion.provincia.nombre}</para></td>
                    <td><para style="linea" noWrap="1">{FormateaEuros(linea.importe_deuda)}</para></td>
                    <td><para style="linea" noWrap="1">{FormateaEuros(linea.precio)}</para></td>
                    <td><para style="linea" noWrap="1">{FormateaEuros(getattr(linea, 'valor_mercado', ''))}</para></td>
                    <td><para style="linea">{QuitaCaracteres(linea.activo.comentarios or '')}</para></td>
                    <td><para style="linea">{QuitaCaracteres(getattr(linea.activo, "respuesta_fondo", ""))}</para></td>
                    <td><para style="linea">{QuitaCaracteres(getattr(linea.activo, "fecha_estudio_posicion", "").strftime('%d/%m/%Y') if getattr(linea.activo, "fecha_estudio_posicion", None) else '')}</para></td>

                </tr>
            """
            )
            i += 1

        # Cierre de la última tabla
        if i > 1:
            rml.append("</blockTable>")

        rml.append("</story></document>")

        if retornar_partes_rml:
            rml_template = f"""
            <template pagesize="(29.7cm, 21cm)">
                <pageTemplate id="principal">
                    <pageGraphics>
                        <setFont name="TimesNewRoman" size="8"/>
                        <drawString x="5mm" y="206mm">INVEST MSS</drawString>
                        <drawString x="140mm" y="206mm">{nombre_campanya}</drawString>
                        <drawCentredString x="148.5mm" y="203mm">{filtro}</drawCentredString>
                        <drawCentredString x="148.5mm" y="200mm">{filtro_clasif}</drawCentredString>
                        <drawString x="270mm" y="206mm">{hoy}</drawString>
                        <drawString x="250mm" y="8mm">Pág. <pageNumber />  <getName id="lastPage" /></drawString>
                    </pageGraphics>
                    <frame id="first" x1="7mm" y1="10mm" width="280mm" height="185mm"/>
                </pageTemplate>
            </template>
            """

            rml_stylesheet = """
           <stylesheet>
                <paraStyle name="default" fontName="Times-Roman" fontSize="9" leading="10" alignment="CENTER"/>
                <paraStyle name="linea" fontName="Times-Bold" fontSize="8" textColor="#444444"/>
                <paraStyle name="titulo" fontName="Times-Bold" fontSize="11" alignment="CENTER"/>

                <blockTableStyle id="tabla_estados">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                    <lineStyle kind="GRID" colorName="black" thickness="0.5"/>
                    <lineStyle kind="INNERGRID" colorName="black" thickness="0.25"/>
                    <lineStyle kind="OUTLINE" colorName="black" thickness="0.5"/>
                    <blockFont name="Times-Roman" size="8"/>
                    <blockBackground colorName="white"/>
                </blockTableStyle>

                <blockTableStyle id="tabla_titulo">
                    <blockValign value="MIDDLE"/>
                    <blockAlignment value="CENTER"/>
                    <blockBackground colorName="whitesmoke"/>
                    <lineStyle kind="GRID" colorName="black" thickness="0.5"/>
                    <lineStyle kind="INNERGRID" colorName="black" thickness="0.25"/>
                    <lineStyle kind="OUTLINE" colorName="black" thickness="0.5"/>
                    <blockFont name="Times-Bold" size="9" textColor="black"/>
                </blockTableStyle>
            </stylesheet>

            """

            rml_story = "".join(rml[1:-1])  # Excluye el <document> inicial y final
            rml_completo = f"""<!DOCTYPE document SYSTEM "rml.dtd">
        <document filename="{nombrefichero}">
            {rml_template}
            {rml_stylesheet}
            <story>
                {rml_story}
            </story>
        </document>
        """

            return {
                "rml_completo": rml_completo,
                "rml_stylesheet": rml_stylesheet,
                "rml_story": rml_story,
                "rml_template": rml_template,
            }

        # Si no se pide por partes:
        return "".join(rml)

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error en GenerarListadoEstados: {e}", exc_info=True)
        return f"Error generando el RML: {e}"


def QuitaCaracteres(cadena):
    if not cadena:
        return ""
    import unicodedata
    import re

    cadena = str(cadena)
    cadena = cadena.replace("&", "&amp;")
    cadena = cadena.replace("<", "&lt;")
    cadena = cadena.replace(">", "&gt;")
    cadena = cadena.replace('"', "&quot;")
    cadena = cadena.replace("'", "&apos;")

    cadena = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cadena)

    cadena = unicodedata.normalize("NFC", cadena)

    # Elimina cualquier carácter que no sea imprimible
    cadena = "".join(c for c in cadena if c.isprintable())

    return cadena


def FormateaEuros(valor):
    if not valor:
        return ""
    try:
        valor = float(valor)
        return (
            f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + "€"
        )
    except (ValueError, TypeError):
        return str(valor)
