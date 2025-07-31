import os
import re
from django.core.management.base import BaseCommand
from invest.models import Correo, RespuestaCorreo
from django.conf import settings
from imap_tools import MailBox, AND
from django.utils.timezone import make_aware
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = "Lee respuestas de correo IMAP y las almacena en la base de datos"

    def handle(self, *args, **kwargs):

        def extraer_tracking_id(texto):
            match = re.search(r"\[TRACKING_ID:(.*?)\]", texto)
            return match.group(1).strip() if match else None

        with MailBox(settings.EMAIL_HOST).login(
            settings.EMAIL_HOST_USER,
            settings.EMAIL_HOST_PASSWORD,
            initial_folder="INBOX",
        ) as mailbox:

            for msg in mailbox.fetch(AND(seen=False)):
                cuerpo_msg = msg.text or msg.html or ""
                tracking_id = extraer_tracking_id(cuerpo_msg)

                if tracking_id:
                    correo = Correo.objects.filter(tracking_id=tracking_id).first()
                    if correo and msg.from_ != "info@grupomss.com":
                        if not RespuestaCorreo.objects.filter(
                            correo=correo, cuerpo=msg.text
                        ).exists():
                            archivo = None

                            if msg.attachments:
                                adjuntos_con_extension = [
                                    att
                                    for att in msg.attachments
                                    if os.path.splitext(att.filename)[
                                        1
                                    ]  
                                ]

                                if adjuntos_con_extension:
                                    archivo = ContentFile(
                                        adjuntos_con_extension[0].payload,
                                        name=adjuntos_con_extension[0].filename,
                                    )

                            RespuestaCorreo.objects.create(
                                correo=correo,
                                remitente=msg.from_,
                                asunto=msg.subject,
                                cuerpo=msg.text,
                                fecha=(
                                    make_aware(msg.date)
                                    if msg.date.tzinfo is None
                                    else msg.date
                                ),
                                archivo=archivo,
                            )

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Respuesta guardada para tracking ID {tracking_id}"
                                )
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Tracking ID no encontrado: {tracking_id}"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING("No se encontró TRACKING_ID en el mensaje")
                    )
