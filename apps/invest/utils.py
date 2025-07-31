import random
import re
import string
from unicodedata import normalize
from datetime import datetime


def DameGeneradorNombres(size=6, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def Importe2Cadena(importe):
    if importe is not None:
        if importe == "":
            importe = 0
        cadena = (
            "{:,.2f}".format(importe)
            .replace(",", "_")
            .replace(".", ",")
            .replace("_", ".")
        )
    else:
        cadena = ""
    return cadena


def DameFecha(date_str):
    if date_str:
        formats = [
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d:%m:%Y",
            "%Y:%m:%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
    return ""


def NormalizarCadena(s):
    s = s.strip()
    s = re.sub(
        r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+",
        r"\1",
        normalize("NFD", s),
        0,
        re.I,
    )

    return normalize("NFC", s)


def registrar_accion(usuario, instancia, accion, descripcion=None):
    from invest.models import Auditoria

    Auditoria.objects.create(
        modelo=instancia.__class__.__name__,
        objeto_id=instancia.pk,
        accion=accion,
        descripcion=descripcion or str(instancia),
        usuario=usuario,
    )
