# import xlwt
import xlsxwriter

from django.conf import settings
#from django.db.models.functions import Coalesce
from django.db.models import F, Case, When, Value, FloatField
from django.http import HttpResponse

from invest.utils import Importe2Cadena
from .models import Provincia, GrupoTipologia

def GenerarListaActivosExcel(empresa, campanya, lineas, clasif, grupo, tipo, poblacion, provincia, estado, nombrefichero="fichero.xlsx"):
    error=False
    literror=""
    output= settings.MEDIA_ROOT + '/' + nombrefichero



    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=mymodel.xlsx'

    workbook=DatosImprimirListado(output, empresa, campanya, lineas, clasif, grupo, tipo, poblacion, provincia, estado)

    workbook.close()


def DatosImprimirListado(output, empresa, campanya, lineas, clasif, grupo, tipo, poblacion, provincia, estado):
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()  

    formato_titulo = workbook.add_format({'size': '20'})    
    formato_titulo2 = workbook.add_format({'size': '12'})    
    formato = workbook.add_format({'size': '10'})    
    formato_rojo = workbook.add_format({'size': '10', 'font_color': 'red'})    
    bold = workbook.add_format({'bold': 1})
    gris = workbook.add_format({'font_color': 'gray'})
    rosa = workbook.add_format({'font_color': 'pink'})
    derecha = workbook.add_format({'align': 'right'})
    gris_derecha = workbook.add_format({'align': 'right', 'font_color': 'gray'})
    rosa_derecha = workbook.add_format({'align': 'right', 'font_color': 'pink'})
    numero = workbook.add_format({'num_format': '#,##0.00', 'size': '10'})
    gris_numero = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'gray', 'size': '10'})
    rosa_numero = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'pink', 'size': '10'})
    rojo_numero = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'red', 'size': '10'})

    row_num=3
    columnas = ["Nº", "Código","Fecha","Tipo","Ref UE", "ID", "Tipología", "Ref Cat", "Dirección", "Municipio", "Provincia", "Precio", "Comentarios", 
        'catastro_localizacion','catastro_clase','catastro_uso_principal','catastro_superficie','catastro_anyo_construccion',
        'google_maps' ]
        
    col_num=1
    for elemento in columnas: 
        worksheet.write(row_num, col_num, elemento, bold)
        col_num+=1
    row_num+=1

    num_activo=1
    lineas_activo = lineas.order_by(
            Case(
                When(tipo="NPL", then=Value(0)),
                When(tipo="CDR", then=Value(1)),
                When(tipo="REO", then=Value(2)),
                default=Value(3),
                output_field=FloatField()
            ),
            Case(
                    When(precio__isnull=True, then=Value(1000000000)),
                    When(precio=0, then=Value(1000000000)),
                    default=F('precio'),
                    output_field=FloatField()
                ),
            'activo__poblacion__provincia__nombre','activo__poblacion__nombre','activo__tipologia__grupo__orden','activo__tipologia__subgrupo__orden', 'pk')

    tipo_activo=""
    cambio_a_50k=False;cambio_a_75k=False;cambio_a_100k=False; cambio_a_mas100k=False; cambio_a_desconocidos=False
    for linea in lineas_activo:            
        if tipo_activo!=linea.tipo:
            cambio_a_50k=False;cambio_a_75k=False;cambio_a_100k=False; cambio_a_mas100k=False; cambio_a_desconocidos=False
            col_num=0        
            worksheet.write(row_num, col_num, linea.tipo, bold); col_num+=1
            row_num+=1
            tipo_activo=linea.tipo

        
        linea_campanya_fecha=linea.campanya.fecha.strftime("%d/%m/%Y")
        if linea.campanya.cartera:
            linea_campanya_cartera_codigo=linea.campanya.cartera.codigo
        else:
            linea_campanya_cartera_codigo=linea.campanya.proveedor.codigo

        linea_activo_direccion=linea.activo.direccion
        linea_activo_poblacion=linea.activo.poblacion.nombre
        #precio=Importe2Cadena(linea.precio)
        observ=""
        if linea.estado_ocupacional!='0': #si es desconocido lo obvio
            observ=linea.get_estado_ocupacional_display()
        if linea.estado_legal:
            observ+= f" {linea.estado_legal}"
        if not linea.precio and not cambio_a_desconocidos:
            cambio_a_desconocidos=True
            col_num=0        
            worksheet.write(row_num, col_num, "PRECIO A CONSULTAR"); col_num+=1
            row_num+=1
        elif linea.precio:
            if linea.precio<50000: 
                if not cambio_a_50k:
                    cambio_a_50k=True
                    col_num=0        
                    worksheet.write(row_num, col_num, "< 50k", gris_derecha); col_num+=1
            elif linea.precio<75000:
                if not cambio_a_75k:
                    cambio_a_75k=True
                    col_num=0
                    worksheet.write(row_num, col_num, "< 75k", gris_derecha); col_num+=1
            elif linea.precio<100000:
                if not cambio_a_100k:
                    cambio_a_100k=True
                    col_num=0
                    worksheet.write(row_num, col_num, "< 100k", gris_derecha); col_num+=1
            elif linea.precio>100000:
                if not cambio_a_mas100k:
                    cambio_a_mas100k=True; 
                    col_num=0
                    worksheet.write(row_num, col_num, "> 100k", gris_derecha); col_num+=1

        col_num=1        

        if linea.activo.no_disponible:
            tipo=formato_rojo
            tipo_numero=rojo_numero
        else:
            tipo=formato
            tipo_numero=numero

        subgrupo_nombre="---"
        if linea.activo.tipologia.subgrupo:
            subgrupo_nombre=linea.activo.tipologia.subgrupo.nombre
        
        worksheet.write(row_num, col_num, num_activo, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea_campanya_cartera_codigo, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea_campanya_fecha, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.tipo, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.activo.ref_ue, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.activo.id_proveedor, tipo); col_num+=1
        worksheet.write(row_num, col_num, subgrupo_nombre, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.activo.ref_catastral, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea_activo_direccion, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea_activo_poblacion, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.activo.poblacion.provincia.nombre, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.precio, tipo_numero); col_num+=1
        worksheet.write(row_num, col_num, observ, tipo); col_num+=1

        worksheet.write(row_num, col_num, linea.activo.catastro_localizacion, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.activo.catastro_clase, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.activo.catastro_uso_principal, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.activo.catastro_superficie, tipo); col_num+=1
        worksheet.write(row_num, col_num, linea.activo.catastro_anyo_construccion, tipo); col_num+=1
        worksheet.write_url(row_num, col_num, linea.activo.DameURLGoogleMaps(), tipo); col_num+=1
        
        row_num+=1
        num_activo+=1

    worksheet.write(1, 0, "Listado de activos", formato_titulo)
    worksheet.autofit()
    # fecha=""
    # if desde:
    #     desde=desde.strftime("%d/%m/%Y")
    #     fecha=f"Periodo del listado: {desde}"
    # if hasta:
    #     hasta=hasta.strftime("%d/%m/%Y")
    #     if fecha=="":
    #         fecha=f"Periodo del listado: {hasta}"
    #     else:
    #         fecha=f"{fecha}:{hasta}"
    # if fecha:
    #     worksheet.write(1, 0, fecha, formato_titulo2)
    # if cliente:
    #     worksheet.write(1, 4, cliente, formato_titulo2)
    # if factoria:
    #     worksheet.write(1, 6, factoria, formato_titulo2)
    # if tipo:
    #     worksheet.write(1, 8, tipo, formato_titulo2)
    # if estado:
    #     worksheet.write(1, 10, estado, formato_titulo2)
    return workbook


