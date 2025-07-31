from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.conf import settings
import os
from reportlab.lib.colors import black, gray

def generar_pdf_para_activo(activo, linea, imagenes=[], documentacion=[]):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- ENCABEZADO ---
    logo_path = os.path.join(settings.BASE_DIR, 'project', 'static', 'img', 'grupo_mss_invest.png')
    try:
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            p.drawImage(logo, 50, height - 80, width=100, height=50, preserveAspectRatio=True)
        p.setFont("Helvetica-Bold", 13)
        p.drawRightString(width - 50, height - 60, "www.investmss.com")
    except Exception as e:
        print(f"[PDF] Error cargando logo: {e}")

    # --- TÍTULO PRINCIPAL ---
    tipo = linea.tipo or "Tipo no definido"
    if linea.tipo != "REO":
        tipo += " (" + (linea.estado_legal or "Sin estado legal") + ")"
    direccion = linea.activo.catastro_localizacion or linea.activo.direccion or "Sin dirección"
    ref_catastral = f"Ref. Catastral: {activo.ref_catastral or 'N/A'}"

    caja_top = height - 90
    caja_height = 60
    caja_x = 50
    caja_width = width - 100
    caja_y = caja_top - caja_height

    p.setLineWidth(1)
    p.rect(caja_x, caja_y, caja_width, caja_height)

    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, caja_y + caja_height - 20, tipo)
    p.setFont("Helvetica", 13)
    p.drawCentredString(width / 2, caja_y + caja_height - 35, direccion)
    p.drawCentredString(width / 2, caja_y + 15, ref_catastral)

    # --- IMÁGENES ---
    y_pos = caja_y - 160
    img_width = 180 
    img_height = 150  # Cuadradas forzadas
    max_per_row = 2
    spacing_x = 5
    spacing_y = 5
    x_start = (width - (max_per_row * img_width + (max_per_row - 1) * spacing_x)) / 2
    row_count = 0

    for idx, imagen in enumerate(imagenes[:4]):  # Máximo 4 imágenes (2x2)
        try:
            path = os.path.join(settings.MEDIA_ROOT, imagen.imagen.name)
            if os.path.exists(path):
                img = ImageReader(path)

                col = idx % max_per_row
                row = idx // max_per_row
                x = x_start + col * (img_width + spacing_x)
                y_img = y_pos - row * (img_height + spacing_y)

                # Forzar tamaño fijo sin preservar proporción
                p.drawImage(img, x, y_img, width=img_width, height=img_height, preserveAspectRatio=False)
                row_count = row + 1
        except Exception as e:
            print(f"[PDF] No se pudo cargar imagen {imagen.id}: {e}")




    # --- CARACTERÍSTICAS ---
    y = y_pos - row_count * (img_height + spacing_y) + 120

    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "CARACTERÍSTICAS")
    p.setFont("Helvetica", 11)
    y -= 20
    descripcion = f"► {activo.tipologia.nombre} de {activo.catastro_superficie or activo.m2 or '-'} m². {activo.num_habitaciones or '-'} habitaciones, {activo.num_banyos or '-'} baños."
    observaciones = f"► {linea.observaciones or ''}"
    p.drawString(50, y, descripcion)
    p.drawString(50, y-15, observaciones)

    y -= 40
    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "SITUACIÓN ECONÓMICA")
    p.setFont("Helvetica", 11)
    y -= 20

    # --- RECUADROS ECONÓMICOS ---
    y_base = y_pos - row_count * (img_height + 10) -30
    caja_width = 115
    caja_height = 60
    spacing = 20

    recuadros = []

    if linea.tipo == "NPL":
        deuda_str = f"{linea.importe_deuda:,.0f} €" if linea.importe_deuda else "---"
        comentario_str = "+ 5%" if linea.importe_deuda else ""
        recuadros.append(("IMPORTE DEUDA", (deuda_str, comentario_str)))

    precio_str = f"{linea.precio:,.0f} €" if linea.precio else "---"

    if linea.tipo == "CDR":
        comentario_str2 = "+ 10%" if linea.importe_deuda else ""
        recuadros.append(("IMPORTE COMPRA", (precio_str, comentario_str2)))
    else:
        recuadros.append(("IMPORTE COMPRA", precio_str))

    if linea.tipo == "NPL":
        valor_subasta = f"{linea.valor_referencia:,.0f} €" if linea.valor_referencia else "---"
        recuadros.append(("VALOR SUBASTA", valor_subasta))

    valor_mercado_str = f"{linea.valor_mercado:,.0f} €" if linea.valor_mercado else "---"
    recuadros.append(("VALOR MERCADO", valor_mercado_str))

    if linea.tipo == "NPL" and linea.importe_deuda:
        valor_70 = f"{linea.valor_70:,.0f} €" if linea.valor_70 else "---"
        recuadros.append(("(70%)", valor_70))

    num_recuadros = len(recuadros)

    # Centrado condicional
    if linea.tipo != "NPL":
        total_ancho = num_recuadros * caja_width + (num_recuadros - 1) * spacing
        x_start = (width - total_ancho) / 2
    else:
        x_start = 50

    for i, (titulo, valor) in enumerate(recuadros):
        if linea.tipo == "NPL" and titulo == "VALOR SUBASTA":
            y = y_base + 15
        elif linea.tipo == "NPL" and titulo == "(70%)":
            idx_subasta = [i for i, (t, _) in enumerate(recuadros) if t == "VALOR SUBASTA"]
            if idx_subasta:
                subasta_x = x_start + idx_subasta[0] * (caja_width + spacing)
                y_objetivo = y_base - 50
                x = subasta_x
                p.setLineWidth(1.5)
                p.rect(x, y_objetivo, caja_width, caja_height)
                p.setFont("Helvetica-Bold", 10)
                p.drawCentredString(x + caja_width / 2, y_objetivo + caja_height - 15, titulo)
                p.setFont("Helvetica-Bold", 13)
                p.drawCentredString(x + caja_width / 2, y_objetivo + 20, str(valor))
            continue
        else:
            y = y_base

        x = x_start + i * (caja_width + spacing)
        p.setLineWidth(1.5)
        p.rect(x, y, caja_width, caja_height)

        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(x + caja_width / 2, y + caja_height - 15, titulo)

        if isinstance(valor, tuple):
            valor_principal, comentario = valor
            p.setFont("Helvetica-Bold", 13)
            p.drawCentredString(x + caja_width / 2, y + 30, str(valor_principal))
            p.setFont("Helvetica-Oblique", 9)
            p.setFillColor(gray)
            p.drawCentredString(x + caja_width / 2, y + 15, str(comentario))
            p.setFillColor(black)
        else:
            p.setFont("Helvetica-Bold", 13)
            p.drawCentredString(x + caja_width / 2, y + 20, str(valor))

    # --- DOCUMENTACIÓN ---
    y = y_base - 80
    p.setFont("Helvetica", 11)
    documentacionString = "► Documentación disponible: "
    if documentacion:
        for doc in documentacion:
            documentacionString += f"{doc.get_tipo_display()}, "
        documentacionString = documentacionString[:-2]
    else:
        documentacionString += "No hay documentación disponible."
    p.drawString(50, y, documentacionString)

    y -= 20
    p.drawString(50, y, "► Valor de mercado obtenido a través de Chat GPT.")

    # --- PIE DE PÁGINA ---
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, 50, "INVEST MSS REAL ESTATE S.L.")
    p.setFont("Helvetica", 10)
    p.drawString(50, 35, "C/Colón, 12 - 1º-1ª - 46004 - Valencia")
    p.drawRightString(width - 50, 50, "info@grupomss.com")
    p.drawRightString(width - 50, 35, "Tel. 96 380 96 77")

    p.save()
    buffer.seek(0)
    return buffer
