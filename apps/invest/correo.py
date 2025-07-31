from django.core.mail import EmailMessage, EmailMultiAlternatives
from email.mime.image import MIMEImage
import uuid


def EnviarCorreo(empresa, enviado_por, enviado_a, parametros):
    # enviado_por es un responsable
    # enviado_por es un cliente
    from invest.models import Correo

    tipo = parametros["tipo"]
    activos = None
    if tipo == "propuesta":
        tipo_correo = "Propuesta de activos"
        lineas = parametros["lineas"]
    elif tipo == "peticion_informacion":
        lineas = parametros["lineas"]
        tipo_correo = "Petición de información"
    elif tipo == "oferta":
        oferta = parametros["oferta"]
        if oferta.estado == "R":
            tipo_correo = "Confirmación por parte del cliente"
        elif oferta.estado == "P":
            tipo_correo = "Preparada más información del activo"
        elif oferta.estado == "N":
            tipo_correo = "Desestimación por parte del cliente"
        elif oferta.estado == "I":
            tipo_correo = "Interés por parte del cliente"
        else:
            tipo_correo = "---"
    elif tipo == "enviar_info_clientes":
        tipo_correo = "Remisión de información de activos"
    else:
        tipo_correo = "---"
        activos = parametros["activos"]
    token = str(uuid.uuid4())

    # Información del remitente y destinatario
    # if enviado_por:
    #    from_address = enviado_por.email
    # else:
    from_address = "info@grupomss.com"
    if tipo == "oferta":
        to_address = "info@grupomss.com"
    else:
        to_address = enviado_a.correo
    reply_to = from_address
    subject = f"[Grupo MSS] {tipo_correo}"
    # pdf_path = ruta_adjunto  # Ruta al fichero PDF
    logo_path = empresa.logotipo_correos.path  # Ruta al logo de la empresa

    # Cuerpo del mensaje en HTML
    html = [
        f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .content {{
                font-family: Arial, sans-serif;
                color: #333;
            }}
            .header {{
                background-color: #f2f2f2;
                padding: 10px;
                text-align: center;
            }}
            .body {{
                margin: 20px;
            }}
            .footer {{
                background-color: #f2f2f2;
                padding: 10px;
                text-align: center;
            }}
            .signature {{
                display: flex;
                align-items: center;
                padding: 10px;
                border-top: 1px solid #e0e0e0;
                margin-top: 20px;
            }}
            .signature img {{
                margin-right: 10px;
                height: 50px;
            }}
            .signature div {{
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            <div class="header">
                <h1>{tipo_correo}</h1>
            </div>
            <div class="body">"""
    ]
    if tipo == "propuesta":
        tipos_activo = lineas.values_list("tipo", flat=True).distinct()
        cadena = ""
        inicio_bucle = True
        for tipo_ in tipos_activo:
            lineas_tipo_activo = lineas.filter(tipo=tipo_)
            cant_lineas_tipo_activo = lineas_tipo_activo.count()
            if inicio_bucle:
                inicio_bucle = False
                cadena = f"Se trata de {cant_lineas_tipo_activo} {tipo_} correspondientes a las provincias de "
            elif tipo_ == tipos_activo.last():
                cadena += f" y {cant_lineas_tipo_activo} {tipo_} correspondientes a las provincias de "
            else:
                cadena += f", {cant_lineas_tipo_activo} {tipo_} correspondientes a las provincias de "
            provs = lineas_tipo_activo.values_list(
                "activo__poblacion__provincia__nombre", flat=True
            ).distinct()
            for prov in provs:
                if prov == provs.first():
                    cadena += f" {prov}"
                elif prov == provs.last():
                    cadena += f" y {prov}"
                else:
                    cadena += f", {prov}"

        cliente_nombre = enviado_a.DameNombre()
        html.append(
            f"""
                <p>Hola {enviado_a.nombre}, 
                hemos seleccionado los siguientes activos que creemos le pueden ser interesantes. </p>
                <p>{cadena}.</p>
                <p>Le adjuntamos un documento pdf con la información disponible.</p>"""
        )

        responsable_nombre = ""
        responsable_correo = ""
        if enviado_a.responsable:
            responsable_nombre = enviado_a.responsable.DameNombre()
            if enviado_a.responsable.correo_envio:
                responsable_correo = enviado_a.responsable.correo_envio
            else:
                responsable_correo = "info@grupomss.com"

        html.append(
            f"""
                <p>También puede entrar en la aplicación que hemos desarrollado, <a href='https://crm.grupomss.com/'>Grupo MSS</a>, para hallar más información de cada activo.</p>
                <p>Saludos.</p>
                <p>{responsable_nombre}</p>
            </div>
            <div class="footer">
                <p></p>
            </div>
            <div class="signature">
                <img src="cid:logo_cid" alt="Logo de la Empresa">
                <div>
                    <table>
                    <tr><td style="color: gray;">{empresa.direccion}</td><td style="color: gray;">Teléfono {empresa.telefono}</td></tr>
                    <tr><td style="color: gray;">{empresa.cp} {empresa.poblacion}</td><td ><a href="mailto:{responsable_correo}">{responsable_correo}</a></td></tr>
                    </table>
                </div>
            </div>"""
        )
    elif tipo == "oferta":
        if oferta.estado == "R":
            tipo_correo = "Confirmación por parte del cliente"
            texto = (
                " pulsado la confirmación de su interés en la adquisición del activo"
            )
        elif oferta.estado == "N":
            tipo_correo = "Desestimación por parte del cliente"
            texto = " declarado que NO le interesa el activo"
        elif oferta.estado == "P":
            tipo_correo = "Preparada más información del activo"
            texto = " recibido la comnicación de que se ha introducido más información en el activo para su consideración"
        elif oferta.estado == "I":
            tipo_correo = "Interés por parte del cliente"
            texto = (
                " pedido que se aumente la información del activo porque le interesa"
            )
        cliente_nombre = oferta.propuesta.cliente.DameNombre()
        html.append(
            f"""
                <h1>{tipo_correo}</h1>
            </div>
            <div class="body">
                <p>El cliente {cliente_nombre} ha {texto}.</p>
            </div>"""
        )
    elif tipo == "peticion_informacion":
        responsable_nombre = ""
        responsable_correo = ""

        tipologia = parametros["tipologia"]
        html.append(
            f"""
            <div>
                <p>Buenos días/Buenas tardes,</p>
                <p>Tenemos un inversor interesado en esta(s) posición(es) por favor, facilítanos la siguiente información. </p>
                <p>Solicitamos información del activo {tipologia} descrito a continuación:</p>
            </div>
                """
        )

        # Iniciamos la tabla con encabezados
        html.append(
            """
            <table border="1" cellspacing="0" cellpadding="4" style="border-collapse: collapse; width: 100%;">
                <thead>
                    <tr style="background-color: #f2f2f2; text-align: left;">
                        <th>ID</th>
                        <th>Referencia Catastral</th>
                        <th>Referencia UE</th>
                        <th>Tipología</th>
                        <th>Dirección</th>
                        <th>Población</th>
                    </tr>
                </thead>
                <tbody>
            """
        )

        # Iteramos las líneas para generar las filas de datos
        for linea in parametros["lineas"]:
            html.append(
                f"""
                    <tr>
                        <td>{linea.activo.id_proveedor}</td>
                        <td>{linea.activo.ref_catastral or ''}</td>
                        <td>{linea.activo.ref_ue or ''}</td>
                        <td>{linea.activo.tipologia or ''}</td>
                        <td>{linea.activo.direccion or ''}</td>
                        <td>{linea.activo.poblacion.nombre if linea.activo.poblacion else ''}</td>
                    </tr>
                """
            )

        # Cerramos la tabla
        html.append(
            """
                </tbody>
            </table>
            """
        )

        if tipologia == "NPL":
            html.append(
                f"""
                <h3>Agradeceríamos que nos facilitarais los siguientes datos:</h3>
                <ol>
                <li>Importe de Deuda</li>
                <li>Precio de compra/referencia</li>
                <li>Colabora o no colabora.</li>
                <li>Situación judicial</li>
                <li>Situación posesoria</li>
                <li>Documentación: Nota simple, demanda…etc</li>
                </ol>"""
            )
        elif tipologia == "CDR":
            html.append(
                f"""
                <ol>
                <li>Precio de compra/referencia</li>
                <li>Situación judicial: último hito judicial</li>
                <li>Situación posesoria</li>
                <li>Documentación: Nota simple, demanda…etc</li>
                </ol>"""
            )
        elif tipologia == "REO":
            html.append(
                f"""
                <ol>
                <li>Precio de compra/referencia</li>
                <li>Situación posesoria: Ocupación</li>
                <li>Título de la ocupación.</li>
                <li>Situación posesoria: Ocupación</li>
                </ol>"""
            )
        html.append(
            f"""
                <p>Quedamos a la espera de vuestras noticias.</p>
                <p>Un cordial saludo,</p>
                <p>Gestión de Activos Bancarios</p>
                <p>Teléfono  +34 628 627 915</p>
                <p><a href='https://investmss.com/'>www.investmss.com</a></p>
              
            </div>
            <table>
            """
        )
        # maider ha dicho de quitarlo 28/8/25
        # html.append(f"""<tr><td>{enviado_por}</td></tr>""")
        html.append(
            f"""
            </table>"""
        )
        html.append(
            f"""
            <div class="signature">
                <img src="cid:logo_cid" alt="Logo de la Empresa">
                <div>
                    <table>
                    <tr><td style="color: gray;">{empresa.direccion}</td><td style="color: gray;">Teléfono {empresa.telefono}</td></tr>
                    <tr><td style="color: gray; ">{empresa.cp} {empresa.poblacion}</td><td ><a href="mailto:{responsable_correo}">{responsable_correo}</a></td></tr>
                    </table>
                </div>
            </div>"""
        )
    elif tipo == "enviar_info_clientes":
        html.append(
            f"""
            <div>
                <p>Estimado {enviado_a.nombre}.
Te remitimos información de la posición solicitada en la que podrás
constatar la contestación del fondo, la información catastral y la
información del mercado.
En el supuesto estuvieses interesado en adquirir la posición, es necesario
cumplir los siguientes requisitos:</p>
<ol>
<li>.- Remitir email de confirmación en el plazo de 5 días.</li>
<li>.- Adjuntar contrato de mandato debidamente firmado, contrato que
consta como documento incorporado al presente email.<br/>
En el supuesto deseases modificar o cambiar los datos del contrato, por
favor comunícanoslo.
<li>.- Prueba de fondos; simple pantallazo de cuenta corriente del titular
del mandante.</li>
<li>.- Justificación de haber ingresado en la cuenta que a continuación se
designa el 5% del importe de compra en concepto de señal – depósito.</li>
<br/>
<br/>
<br/>
<p>
La cuenta bancaria es la siguiente:
<b>Titular Invest MSS SL</b>
Cuenta: ES95 0081 5237 5000 0134 0838
</p>
<p>
Este importe será reembolsable hasta el momento que se sancione la
operación por parte del fondo/banco. A partir de ese momento, la señal-
depósito tendrá la naturaleza de garantía de la operación, no teniendo
derecho a reembolso en el supuesto no se materializase la compra –
adquisición de la posición por causa imputable al mandante.
El email de ratificación deberá remitirse en el plazo de 5 días desde la
recepción de la información facilitada en relación a la posición.
</p>
<p>
A partir de la recepción del contrato y de la documentación reseñada, se
iniciará el proceso de presentación de oferta al fondo y ratificación del
precio de compra, los precios serán orientativos hasta el momento de la
sanción por el fondo/banco.
</p>
<p>
En el momento se nos comunique la sanción de la oferta por el fondo, se
aperturará una ventana de 48 horas para confirmar definitivamente la
voluntad de compra.
</p>
<p>
Un cordial saludo.
</p>"""
        )

    html.append(f"""<div style="display:none;">[TRACKING_ID:{token}]</div>""")

    html.append(
        f"""
        </div>
    </body>
    </html>
    """
    )
    html = "".join(html)
    cc_address = "donosti@grupomss.com"

    email = EmailMultiAlternatives(
        from_email=from_address,
        to=[to_address],
        cc=[cc_address],
        reply_to=[reply_to],
        subject=subject,
        body=html,
    )

    # Adjuntar el cuerpo HTML al mensaje
    email.attach_alternative(html, "text/html")

    # Adjuntar la imagen del logo
    with open(logo_path, "rb") as img_file:
        logo = MIMEImage(img_file.read())
        logo.add_header("Content-ID", "<logo_cid>")
        email.attach(logo)

    # Adjuntar el archivo PDF
    if "nombrefichero" in parametros and parametros["nombrefichero"]:
        if parametros["nombrefichero_destino"]:
            nombrefichero_destino = parametros["nombrefichero_destino"]
        else:
            nombrefichero_destino = activos_investmss.pdf
        with open(parametros["nombrefichero"], "rb") as pdf_file:
            email.attach(
                nombrefichero_destino,  # Nombre del archivo adjunto
                pdf_file.read(),  # Contenido del archivo
                "application/pdf",  # Tipo MIME del archivo
            )

    try:
        email.send()
    except Exception as e:
        print(f"Error inesperado al enviar el correo: {e}")
    correo = Correo.objects.create(
        from_email=from_address,
        to_email=to_address,
        reply_to=reply_to,
        subject=subject,
        body=html,
        tracking_id=token,
    )
    if tipo == "propuesta":
        propuesta = parametros["propuesta"]
        propuesta.correo = correo
        propuesta.save()
