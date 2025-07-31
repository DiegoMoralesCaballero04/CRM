from boot.storage import sendfile_storage
from datetime import datetime
from z3c.rml import rml2pdf

import time
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.db.models import Model
from django.db.models import BooleanField, CharField, EmailField, FloatField
from django.db.models import ImageField, IntegerField, CharField, FileField, TextField
from django.db.models import DateField, TimeField, DateTimeField
from django.db.models import ForeignKey, ManyToManyField, OneToOneField
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Q, Max, Min, Sum, Count

from invest.utils import DameGeneradorNombres

# if not settings.DEBUG:
# from invest.utils_geoloc import Geolocaliza
from invest.catastro import DameDatosCatastro

from invest.correo import EnviarCorreo
from . import managers
from django.utils import timezone
from invest.utils_geoloc import Geolocaliza


class BaseModel(Model):

    class Meta:
        abstract = True

    creado_en = DateTimeField(auto_now_add=True)
    actualizado_en = DateTimeField(auto_now=True)
    anulado_en = DateTimeField(null=True, blank=True)

    creado_por = models.ForeignKey(
        "invest.User",
        models.RESTRICT,
        null=True,
        editable=False,
        related_name="+",
    )
    anulado_por = models.ForeignKey(
        "invest.User",
        models.RESTRICT,
        null=True,
        editable=False,
        related_name="++",
    )


class User(AbstractUser):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower("email"),
                name="main_user_email_unique_lower",
                violation_error_message="Ya existe un usuario con este e-mail",
            ),
        ]

    objects = managers.UserManager()

    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(_("username"), max_length=150, unique=False)
    responsable = models.ForeignKey(
        "Responsable",
        models.CASCADE,
        null=True,
        blank=True,
        related_name="Usuario_responsable",
    )
    cliente = models.ForeignKey(
        "Cliente", models.CASCADE, null=True, blank=True, related_name="Usuario_cliente"
    )
    es_administrador = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        if self.first_name or self.last_name:
            cadena = f"{self.first_name} {self.last_name}"
        else:
            cadena = self.email
        return cadena


class Empresa(BaseModel):
    nombre = CharField(max_length=200, verbose_name="Nombre:", blank=True)
    razonsocial = CharField(max_length=200, verbose_name="Razón social:", blank=True)
    nif = CharField(max_length=20, verbose_name="CIF:", blank=True)
    direccion = CharField(max_length=400, verbose_name="Dirección:", blank=True)
    cp = CharField(max_length=5, verbose_name="C.P.:", blank=True)
    poblacion = CharField(max_length=400, verbose_name="Población:", blank=True)
    provincia = CharField(max_length=400, verbose_name="Provincia:", blank=True)
    telefono = CharField(max_length=50, verbose_name="Teléfono:", blank=True)
    email = EmailField(max_length=250, verbose_name="Email:", blank=True)
    logotipo = ImageField(
        storage=sendfile_storage, upload_to="logos", null=True, blank=True
    )
    logotipo_correos = ImageField(
        storage=sendfile_storage, upload_to="logos", null=True, blank=True
    )

    def __str__(self):
        return self.nombre


class Provincia(Model):
    codigo = IntegerField(verbose_name="Código")
    nombre = CharField(max_length=250, verbose_name="Nombre:")
    es_varios = BooleanField(default=False)

    def __str__(self):
        return self.nombre

    @classmethod
    def create(cls, codigo, nombre):
        provincia = cls(codigo=codigo, nombre=nombre)
        provincia.save()
        return provincia


class Comarca(Model):
    provincia = ForeignKey(Provincia, on_delete=models.CASCADE)
    nombre = CharField(max_length=250, verbose_name="Nombre:")

    def __str__(self):
        return self.nombre


class Poblacion(Model):
    provincia = ForeignKey(Provincia, on_delete=models.CASCADE)
    comarca = ForeignKey(Comarca, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = CharField(max_length=250, verbose_name="Nombre:")
    cp = CharField(max_length=5, verbose_name="CP:")
    longitud = FloatField(default=0)
    latitud = FloatField(default=0)

    def __str__(self):
        return self.nombre

    @classmethod
    def create(cls, provincia, nombre):
        poblacion = cls(provincia=provincia, nombre=nombre)
        poblacion.save()
        return poblacion


class Poblacion_Traduccion(BaseModel):
    nombre = CharField(max_length=250, verbose_name="Nombre:")
    poblacion = ForeignKey(Poblacion, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Proveedor(BaseModel):
    nombre = CharField(max_length=200, verbose_name="Nombre:")
    codigo = CharField(max_length=50, verbose_name="Código:")

    def __str__(self):
        return f"{self.codigo}. {self.nombre}"

    def DameCarteras(self):
        return Cartera.objects.filter(proveedor=self, anulado_en=None).order_by(
            "codigo"
        )

    def DameContactos(self):
        return Contacto.objects.filter(proveedor=self, anulado_en=None).order_by(
            "cargo"
        )


class Cartera(BaseModel):
    proveedor = ForeignKey(Proveedor, on_delete=models.CASCADE, verbose_name="Servicer")
    codigo = CharField(max_length=50, verbose_name="Código:")
    nombre = CharField(max_length=200, verbose_name="Nombre:")

    def __str__(self):
        return f"{self.codigo}. {self.nombre}"


class Contacto(BaseModel):
    proveedor = ForeignKey(Proveedor, on_delete=models.CASCADE, verbose_name="Servicer")
    nombre = CharField(max_length=200, verbose_name="Nombre:")
    correo = EmailField(max_length=200, verbose_name="Correo:", blank=True)
    telefono = CharField(max_length=20, verbose_name="Teléfono:", blank=True)
    cargo = CharField(max_length=100, verbose_name="Cargo:", blank=True)
    NPL = BooleanField(default=False)
    CDR = BooleanField(default=False)
    REO = BooleanField(default=False)

    def __str__(self):
        return self.nombre

    def DameNombre(self):
        return self.nombre


class Campanya(BaseModel):
    proveedor = ForeignKey(Proveedor, on_delete=models.CASCADE, verbose_name="Servicer")
    cartera = ForeignKey(Cartera, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = DateField()
    fichero = FileField(
        # storage=sendfile_storage,
        upload_to="campanya",
        null=True,
        blank=True,
    )
    ESTADO = [("A", "Activa"), ("F", "Finalizada")]
    estado = CharField(max_length=1, choices=ESTADO, default="I")
    TIPO = [
        ("NPL", "NPL-Cesión de crédito"),
        ("CDR", "CDR-Cesión de remate"),
        ("REO", "REO-Compra de activo"),
    ]
    tipo = CharField(max_length=3, choices=TIPO, default="NPL")
    finalizada_en = DateTimeField(null=True, blank=True)
    finalizada_por = models.ForeignKey(
        "invest.User",
        models.RESTRICT,
        null=True,
        editable=False,
        related_name="usuario_finaliza_campanya",
    )

    def __str__(self):
        return self.proveedor.nombre

    def DameActivos(self):
        return Activo.objects.filter(campanya=self)

    def DameBadge(self):
        badge = ""
        if self.estado == "I":
            badge = "badge bg-primary"
        elif self.estado == "O":
            badge = "badge bg-warning"
        elif self.estado == "A":
            badge = "badge bg-success"
        elif self.estado == "F":
            badge = "badge bg-dark"
        return badge

    def ActivosTotales(self):
        return self.campanyalinea_set.count()

    def PropuestasEnviadas(self):
        id_activos = (
            CampanyaLinea.objects.filter(campanya=self)
            .values_list("activo__pk", flat=True)
            .distinct()
        )
        return PropuestaLinea.objects.filter(
            campanya_linea__activo__pk__in=id_activos, anulado_por=None
        ).count()

    def PropuestasInteresadas(self):
        id_activos = (
            CampanyaLinea.objects.filter(campanya=self)
            .values_list("activo__pk", flat=True)
            .distinct()
        )
        return (
            PropuestaLinea.objects.filter(
                campanya_linea__activo__pk__in=id_activos, anulado_por=None
            )
            .filter(estado="I")
            .count()
        )

    def PropuestasEsperando(self):
        id_activos = (
            CampanyaLinea.objects.filter(campanya=self)
            .values_list("activo__pk", flat=True)
            .distinct()
        )
        return (
            PropuestaLinea.objects.filter(
                campanya_linea__activo__pk__in=id_activos, anulado_por=None
            )
            .filter(estado="E")
            .count()
        )

    def PropuestasTrabajadas(self):
        id_activos = (
            CampanyaLinea.objects.filter(campanya=self)
            .values_list("activo__pk", flat=True)
            .distinct()
        )
        return (
            PropuestaLinea.objects.filter(
                campanya_linea__activo__pk__in=id_activos, anulado_por=None
            )
            .exclude(estado="P")
            .count()
        )  # interesa_cliente=None

    def PropuestasAceptadas(self):
        id_activos = (
            CampanyaLinea.objects.filter(campanya=self)
            .values_list("activo__pk", flat=True)
            .distinct()
        )
        return (
            PropuestaLinea.objects.filter(
                campanya_linea__activo__pk__in=id_activos, anulado_por=None
            )
            .filter(estado="R")
            .count()
        )  # confirma_cliente=None


class CampanyaLinea(BaseModel):
    campanya = ForeignKey(Campanya, on_delete=models.CASCADE)
    TIPO = [
        ("NPL", "NPL-Cesión de crédito"),
        ("CDR", "CDR-Cesión de remate"),
        ("REO", "REO-Compra de activo"),
    ]
    tipo = CharField(max_length=3, choices=TIPO, default="NPL")
    activo = ForeignKey("Activo", on_delete=models.CASCADE)
    precio = FloatField(null=True, blank=True)
    ESTADO_OCUPACIONAL = [
        ("0", "Desconocido"),
        ("1", "Vacío"),
        ("2", "Ocupado"),
        ("3", "Alquilado"),
        ("4", "Ocupado por propietario"),
    ]
    estado_ocupacional = CharField(
        max_length=1, choices=ESTADO_OCUPACIONAL, default="0"
    )
    estado_legal = CharField(max_length=1024, blank=True)
    observaciones = TextField(null=True, blank=True)
    no_disponible = DateTimeField(null=True, blank=True)
    no_disponible_por = models.ForeignKey(
        "invest.User",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="disponible_creador",
    )
    importe_deuda = FloatField(null=True, blank=True)
    valor_referencia = FloatField(null=True, blank=True)
    valor_mercado = FloatField(null=True, blank=True)
    valor_70 = FloatField(null=True, blank=True)

    responsabilidad_hipotecaria = FloatField(null=True, blank=True)
    ESTADO = [("0", "Desconocido"), ("1", "Sí"), ("2", "No")]
    judicializado = CharField(max_length=1, choices=ESTADO, default="0")
    deudor_localizado = CharField(max_length=1, choices=ESTADO, default="0")
    deudor_ayuda = CharField(max_length=1, choices=ESTADO, default="0")
    url = CharField(max_length=1024, blank=True, verbose_name="Dirección web")
    preparado_en = DateField(null=True, blank=True)
    preparado_por = ForeignKey(
        "invest.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preparado_creador",
    )
    reservado_en = DateField(null=True, blank=True)
    reservado_por = ForeignKey(
        "invest.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservado_creador",
    )

    def __str__(self):
        return f"{self.activo.pk}"

    def DameObservaciones(self):
        observ = self.observaciones
        if int(self.estado_ocupacional) != 0:
            observ += " " + self.get_estado_ocupacional_display()
        if self.estado_legal:
            observ += f" {self.estado_legal}"
        return observ


class CampanyaLinea_Documentacion(BaseModel):
    campanya_linea = ForeignKey(CampanyaLinea, on_delete=models.CASCADE)
    TIPO = [
        (0, "Nota simple"),
        (1, "Catastro"),
        (2, "Tasación"),
        (3, "Escritura préstamos hipitecario"),
        (4, "Documentación judicial"),
        (5, "Certificado deuda"),
        (6, "Otros"),
    ]
    documento = FileField(
        storage=sendfile_storage, upload_to="docs_activo", null=True, blank=True
    )
    fecha = DateField(null=True, blank=True)
    descripcion = TextField(blank=True)

    def __str__(self):
        return f"{self.campanya_linea.activo.pk}"


class GrupoTipologia(BaseModel):
    nombre = CharField(max_length=200, verbose_name="Nombre:")
    orden = IntegerField(default=1)
    es_varios = BooleanField(default=False)

    def __str__(self):
        return self.nombre

    @classmethod
    def create(cls, nombre, usuario):
        tipo = cls(nombre=nombre, creado_por=usuario, creado_en=datetime.now())
        tipo.save()
        return tipo


class SubGrupoTipologia(BaseModel):
    grupo = ForeignKey(GrupoTipologia, on_delete=models.CASCADE)
    nombre = CharField(max_length=200, verbose_name="Nombre:")
    orden = IntegerField(default=1)

    def __str__(self):
        return self.nombre


class Tipologia(BaseModel):
    nombre = CharField(max_length=200, verbose_name="Nombre:")
    grupo = ForeignKey(GrupoTipologia, on_delete=models.SET_NULL, null=True, blank=True)
    subgrupo = ForeignKey(
        SubGrupoTipologia, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.nombre

    @classmethod
    def create(cls, nombre, usuario, grupo=None, subgrupo=None):
        if not grupo:
            grupo = GrupoTipologia.objects.filter(es_varios=True).first()
        if not subgrupo:
            subgrupo = SubGrupoTipologia.objects.filter(grupo=grupo).first()
        tipo = cls(
            nombre=nombre,
            grupo=grupo,
            subgrupo=subgrupo,
            creado_por=usuario,
            creado_en=datetime.now(),
        )
        tipo.save()
        return tipo


class Activo(BaseModel):
    id_proveedor = CharField(max_length=200, blank=True)
    ref_ue = CharField(max_length=200, blank=True)
    tipologia = ForeignKey(Tipologia, on_delete=models.CASCADE)
    ref_catastral = CharField(max_length=500, blank=True)
    cp = CharField(max_length=20, blank=True)
    direccion = TextField()
    poblacion = ForeignKey(Poblacion, on_delete=models.CASCADE)
    longitud = FloatField(null=True, blank=True)
    latitud = FloatField(null=True, blank=True)
    m2 = FloatField(null=True, blank=True)
    fecha_construccion = IntegerField(null=True, blank=True)
    num_habitaciones = IntegerField(null=True, blank=True)
    num_banyos = IntegerField(null=True, blank=True)
    seleccionado = BooleanField(default=False)
    catastro = BooleanField(default=False)
    fecha_peticion_catastro = DateField(null=True, blank=True)
    catastro_localizacion = CharField(max_length=250, blank=True)
    catastro_clase = CharField(max_length=75, blank=True)
    catastro_uso_principal = CharField(max_length=75, blank=True)
    catastro_superficie = FloatField(null=True, blank=True)
    catastro_anyo_construccion = IntegerField(null=True, blank=True)
    no_disponible = DateTimeField(null=True, blank=True)
    no_disponible_por = models.ForeignKey(
        "invest.User",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="sindisponibilidad_creador",
    )
    ultimo_hito = models.CharField(max_length=100, blank=True, null=True)
    estado_activo = models.CharField(
        max_length=20,
        choices=[
            ("publicado", "Publicado"),
            ("no publicado", "NO publicado"),
            ("reservado", "Reservado"),
            ("vendido", "Vendido"),
        ],
        default="no publicado",
    )

    # Publicación en portales (True o False)
    idealista = models.BooleanField(default=False)
    fotocasa_pro = models.BooleanField(default=False)
    web_invest = models.BooleanField(default=False)
    fecha_estudio_posicion = models.DateField(null=True, blank=True)
    comentarios = models.TextField(blank=True)
    respuesta_fondo = models.TextField(blank=True)

    def __str__(self):
        if self.ref_ue:
            return self.ref_ue
        elif self.ref_catastral:
            return self.ref_catastral
        else:
            return f"{self.pk}"

    def ActivoLocalizar(self):
        direccion = f"{self.direccion}. {self.cp}. {self.poblacion}.SPAIN"
        longitud = 0
        latitud = 0
        self.ActivoGuardaCatastro()
        #        if not settings.DEBUG:
        latitud, longitud = Geolocaliza(
            self.catastro_localizacion or direccion[:199], self.poblacion.nombre
        )

        if longitud != 0 or latitud != 0:
            print(f"longitud: {longitud}, latitud: {latitud}")
            self.latitud = latitud
            self.longitud = longitud
            self.save()

    def DameLocalizacion(self):
        latitud = str(self.latitud).replace(",", ".")
        longitud = str(self.longitud).replace(",", ".")
        return f"{latitud},{longitud}"

    def DameURLGoogleMaps(self):
        def remove_accents(input_str):
            import unicodedata

            nfkd_form = unicodedata.normalize("NFKD", input_str)
            return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

        if self.latitud and self.longitud:
            return f"https://www.google.com/maps?q={self.latitud},{self.longitud}"

        if self.catastro_localizacion:
            dire = self.catastro_localizacion.split()
            pob_obj = Poblacion.objects.filter(nombre__iexact=dire[-2]).first()
            pob = (
                str(pob_obj).replace("(", "").replace(")", "")
                if pob_obj
                else str(self.poblacion)
            )
            pob = remove_accents(pob)

            palabras = self.catastro_localizacion.split()
            partes_direccion = []
            encontro_numero = False

            for palabra in palabras:
                if any(c.isdigit() for c in palabra):
                    partes_direccion.append(palabra)
                    encontro_numero = True
                    break
                partes_direccion.append(palabra)

            loca = " ".join(partes_direccion).replace(" ", "+")
            loca = remove_accents(loca)
            return f"https://www.google.com/maps?q={loca},{pob.replace(' ', '+')}"

        direccion_limpia = ""
        if self.direccion:
            palabras = self.direccion.split()

            partes_direccion = []
            encontro_numero = False
            for palabra in palabras:
                if any(c.isdigit() for c in palabra):
                    partes_direccion.append(palabra)
                    encontro_numero = True
                    break
                partes_direccion.append(palabra)

            direccion_limpia = " ".join(partes_direccion).replace(" ", "+")
            direccion_limpia = direccion_limpia.replace('"', "")
            direccion_limpia = direccion_limpia.replace(",", "")
            direccion_limpia = remove_accents(direccion_limpia)

        poblacion_limpia = ""
        if self.poblacion and hasattr(self.poblacion, "nombre"):
            poblacion_limpia = remove_accents(self.poblacion.nombre).replace(" ", "+")

        if direccion_limpia and poblacion_limpia:
            return (
                f"https://www.google.com/maps?q={direccion_limpia},{poblacion_limpia}"
            )
        elif direccion_limpia:
            return f"https://www.google.com/maps?q={direccion_limpia}"
        else:
            return ""

    def ActivoGuardaCatastro(self):
        if self.ref_catastral and len(self.ref_catastral) == 20:
            self.fecha_peticion_catastro = datetime.now().date()
            self.save()
            result = DameDatosCatastro(self.ref_catastral)

            print("Referencia: " + self.ref_catastral)
            print(result.get("literror").lower())
            if not result["error"]:
                self.catastro = True
                self.catastro_localizacion = result["localizacion"]
                self.catastro_clase = result["clase"]
                self.catastro_uso_principal = result["uso_principal"]
                self.catastro_superficie = result["superficie"]
                self.catastro_anyo_construccion = result["anio_construccion"]
                self.save()
            elif "'consulta_dnprcresult'" in result.get("literror").lower():
                encontrado = False
                intentos = 0
                while not encontrado and intentos < 5:
                    print("dentro")
                    time.sleep(5400)
                    print("dentro2")
                    result2 = DameDatosCatastro(self.ref_catastral)
                    self.fecha_peticion_catastro = datetime.now().date()
                    self.save()

                    print("intento")
                    if not result2["error"]:
                        self.catastro = True
                        self.catastro_localizacion = result2["localizacion"]
                        self.catastro_clase = result2["clase"]
                        self.catastro_uso_principal = result2["uso_principal"]
                        self.catastro_superficie = result2["superficie"]
                        self.catastro_anyo_construccion = result2["anio_construccion"]
                        self.save()
                        encontrado = True
                    elif "'consulta_dnprcresult'" in result2.get("literror").lower():
                        intentos = intentos + 1
                    else:
                        break

    def DameOfertasNombre(self):
        ofertas = PropuestaLinea.objects.filter(
            campanya_linea__activo=self, anulado_por=None
        )
        num_ofertas = ofertas.count()
        if num_ofertas == 0:
            num_ofertas = ""
        return num_ofertas

    def DameImagenes(self):
        return ActivoImagen.objects.filter(activo=self).order_by("pk")

    def DameImagen(self):
        return ActivoImagen.objects.filter(activo=self).first()

    def DameNotasSimple(self):
        return ActivoDocumento.objects.filter(activo=self, tipo="0").order_by("pk")

    def DameCatastros(self):
        return ActivoDocumento.objects.filter(activo=self, tipo="1").order_by("pk")

    def DameTasaciones(self):
        return ActivoDocumento.objects.filter(activo=self, tipo="2").order_by("pk")

    def DamePrestamos(self):
        return ActivoDocumento.objects.filter(activo=self, tipo="3").order_by("pk")

    def DameJudiciales(self):
        return ActivoDocumento.objects.filter(activo=self, tipo="4").order_by("pk")

    def DameDeudas(self):
        return ActivoDocumento.objects.filter(activo=self, tipo="5").order_by("pk")

    def DameDocs(self):
        return ActivoDocumento.objects.filter(activo=self, tipo="V").order_by("pk")

    def DameUltLinea(self):
        return (
            CampanyaLinea.objects.filter(activo=self).order_by("campanya__fecha").last()
        )

    def DameTipo(self):
        tipo = ""
        linea = self.DameUltLinea()
        if linea:
            tipo = linea.tipo
        return tipo

    def DamePrecio(self):
        precio = 0
        linea = self.DameUltLinea()
        if linea:
            precio = linea.precio
        return precio

    def DameImporteDeuda(self):
        importe_deuda = 0
        linea = self.DameUltLinea()
        if linea:
            importe_deuda = linea.importe_deuda
        print(f"Importe deuda {importe_deuda}")
        return importe_deuda

    def DameValorSubasta(self):
        valor_referencia = 0
        linea = self.DameUltLinea()
        if linea:
            valor_referencia = linea.valor_referencia
        return valor_referencia

    def DameEstadoOcupacional():
        estado_ocupacional = ""
        linea = self.DameUltLinea()
        if linea:
            estado_ocupacional = linea.get_estado_ocupacional_display()
        return estado_ocupacional

    def DameEstadoLegal():
        estado_legal = ""
        linea = self.DameUltLinea()
        if linea:
            estado_legal = linea.estado_legal
        return estado_ocupacional

    def DameUrl():
        url = ""
        linea = self.DameUltLinea()
        if linea:
            url = linea.url
        return url


class ActivoImagen(BaseModel):
    activo = ForeignKey(Activo, on_delete=models.CASCADE)
    imagen = ImageField(storage=sendfile_storage, upload_to="imagenes_activos")

    def __str__(self):
        return f"{self.activo.pk}"


class ActivoDocumento(BaseModel):
    activo = ForeignKey(Activo, on_delete=models.CASCADE)
    documento = FileField(storage=sendfile_storage, upload_to="activos_documentos")
    TIPO = [
        ("V", "Varios"),
        ("0", "Nota Simple"),
        ("1", "Catastro"),
        ("2", "Tasación"),
        ("3", "Escritura de préstamos hipotecario"),
        ("4", "Documentación judicial"),
        ("5", "Certificado de deuda"),
    ]
    tipo = CharField(max_length=1, choices=TIPO, default="V")
    caducidad = DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.activo.pk}"


class Responsable(BaseModel):
    nombre = CharField(max_length=200)
    apellidos = CharField(max_length=500, blank=True)
    correo_acceso = EmailField(max_length=250)
    correo_envio = EmailField(max_length=250, blank=True, default="info@grupomss.com")

    def __str__(self):
        return self.DameNombre()

    def DameUsuario(self):
        return User.objects.filter(responsable=self).first()

    def DameUsuarioPK(self):
        usuario = self.DameUsuario()
        if usuario:
            return usuario.pk
        else:
            return None

    def DameNombre(self):
        return f"{self.nombre} {self.apellidos}"

    def CrearUsuario(self):
        nombre = self.nombre
        cont = 1
        while User.objects.filter(username__iexact=nombre).first():
            nombre = f"{self.nombre}{cont}"
            cont += 1
        user = User.objects.create_user(
            email=self.correo_acceso, password=DameGeneradorNombres(), username=nombre
        )
        user.first_name = self.nombre
        user.last_name = self.apellidos
        user.responsable = self
        user.save()

    def ActualizaUsuario(self):
        error = False
        literror = ""
        modif = False
        user = User.objects.get(responsable=self)
        if user.first_name != self.nombre:
            user.first_name = self.nombre
            modif = True
        if user.last_name != self.apellidos:
            user.last_name = self.apellidos
            modif = True
        if user.email != self.correo_acceso:
            user.email = self.correo_acceso
            modif = True
        if modif:
            try:
                user.save()
            except Exception as e:
                error = True
                literror = f"{e}"
        return error, literror

    def AnulaUsuario(self):
        try:
            user = User.objects.get(responsable=self)
        except:
            user = None
        if user:
            user.is_active = False
            user.save()


class Cliente(BaseModel):
    codigo = CharField(max_length=10, blank=True)
    responsable = ForeignKey(
        Responsable, on_delete=models.SET_NULL, null=True, blank=True
    )
    TIPO = [("F", "Persona física"), ("J", "P. Jurídica")]
    tipo = CharField(max_length=1, choices=TIPO, default="F")
    nombre = CharField(max_length=200, blank=True)
    apellidos = CharField(max_length=500, blank=True)
    nombre_completo = CharField(max_length=500, blank=True)
    contacto = CharField(max_length=500, blank=True)
    nif = CharField(max_length=20, verbose_name="NIF:", blank=True)
    direccion = CharField(max_length=400, verbose_name="Dirección:", blank=True)
    cp = CharField(max_length=5, verbose_name="C.P.:", blank=True)
    poblacion = CharField(max_length=400, verbose_name="Población:", blank=True)
    provincia = CharField(max_length=400, verbose_name="Provincia:", blank=True)
    telefono = CharField(max_length=255, blank=True)
    zona = CharField(max_length=250, blank=True)
    observaciones = TextField(blank=True)
    correo = EmailField(max_length=250, blank=True, null=True)
    correo_2 = EmailField(max_length=250, blank=True, null=True)
    correo_3 = EmailField(max_length=250, blank=True, null=True)

    def __str__(self):
        return self.DameNombre()

    def DameNombre(self):
        if self.nombre_completo:
            return f"{self.nombre_completo}"
        else:
            return f"{self.nombre} {self.apellidos}"

    def DameUsuario(self):
        return User.objects.filter(cliente=self).first()

    def CrearUsuario(self):
        error = False
        literror = ""
        nombre = self.nombre
        cont = 1
        while User.objects.filter(username__iexact=nombre).first():
            nombre = f"{self.nombre}{cont}"
            cont += 1
        try:
            user = User.objects.create_user(
                email=self.correo, password=DameGeneradorNombres(), username=nombre
            )
        except Exception as e:
            error = True
            literror = f"{e}"
        if not error:
            user.first_name = self.nombre
            user.last_name = self.apellidos
            user.cliente = self
            user.save()
        return error, literror

    def ActualizaUsuario(self):
        modif = False
        error = False
        literror = ""
        user = User.objects.filter(cliente=self).first()
        if user:
            if user.first_name != self.nombre:
                user.first_name = self.nombre
                modif = True
            if user.last_name != self.apellidos:
                user.last_name = self.apellidos
                modif = True
            if user.email != self.correo:
                user.email = self.correo
                modif = True
            if modif:
                user.save()
        else:
            error, literror = self.CrearUsuario()
        return error, literror

    def AnulaUsuario(self):
        user = User.objects.get(cliente=self)
        user.is_active = False
        user.save()

    def PropuestasEnviadas(self):
        return Propuesta.objects.filter(cliente=self, anulado_por=None)

    def NumPropuestasEnviadas(self):
        return self.PropuestasEnviadas().count()

    def PropuestasInteresadas(self):
        return PropuestaLinea.objects.filter(
            propuesta__cliente=self, propuesta__anulado_por=None, estado="I"
        )

    def NumPropuestasInteresadas(self):
        return self.PropuestasInteresadas().count()

    def PropuestasInteresadasoEsperando(self):
        return PropuestaLinea.objects.filter(
            propuesta__cliente=self, propuesta__anulado_por=None
        ).filter(Q(estado="I") | Q(estado="E"))

    def NumPropuestasInteresadasoEsperando(self):
        return self.PropuestasInteresadasoEsperando().count()

    def PropuestasTrabajadas(self):
        return PropuestaLinea.objects.filter(
            propuesta__cliente=self, propuesta__anulado_por=None, estado="P"
        )

    def NumPropuestasTrabajadas(self):
        return self.PropuestasTrabajadas().count()

    def PropuestasAceptadas(self):
        return PropuestaLinea.objects.filter(
            propuesta__cliente=self, propuesta__anulado_por=None, estado="R"
        )

    def NumPropuestasAceptadas(self):
        return self.PropuestasAceptadas().count()

    def EnviarPropuesta(self, lineas_id, usuario):
        from invest.generarRML import GenerarListaActivosConCatastroRML

        empresa = Empresa.objects.all().first()
        lineas = CampanyaLinea.objects.filter(pk__in=lineas_id.split(","))

        hoy = datetime.now().strftime("%Y%m%d")
        nombrefichero = f"relacion_activos_mssinvest_{self.nombre}_{hoy}.pdf"
        rml_cadena = GenerarListaActivosConCatastroRML(
            empresa, None, lineas, "", "", "", "", "", "", nombrefichero
        )
        f = open(settings.MEDIA_ROOT + "/archivo.rml", "w", encoding="utf-8")
        f.write(rml_cadena)
        f.close()
        output = settings.MEDIA_ROOT + "/" + nombrefichero
        rml2pdf.go(settings.MEDIA_ROOT + "/archivo.rml", outputFileName=output)

        propuesta = Propuesta.objects.create(cliente=self)
        for linea in lineas:
            PropuestaLinea.objects.create(propuesta=propuesta, campanya_linea=linea)
        nombrefichero_destino = propuesta.DameNombreFichero()

        parametros = {
            "tipo": "propuesta",
            "lineas": lineas,
            "propuesta": propuesta,
            "nombrefichero": output,
            "nombrefichero_destino": nombrefichero_destino,
        }
        EnviarCorreo(empresa, usuario, self, parametros)


class ClienteDocumento(BaseModel):
    cliente = ForeignKey(Cliente, on_delete=models.CASCADE)
    documento = FileField(storage=sendfile_storage, upload_to="activos_documentos")
    TIPO = [("V", "Varios"), ("0", "NIF")]
    tipo = CharField(max_length=1, choices=TIPO, default="V")
    caducidad = DateField(null=True, blank=True)

    def __str__(self):
        return self.cliente.nombre


class ClientePreferencia(BaseModel):
    cliente = ForeignKey(Cliente, on_delete=models.CASCADE)
    tipologia = ManyToManyField(Tipologia, blank=True)
    provincia = ManyToManyField(Provincia, blank=True)
    poblacion = ManyToManyField(Poblacion, blank=True)

    def __str__(self):
        return self.cliente.nombre


class Correo(BaseModel):
    from_email = CharField(max_length=255, blank=True)
    to_email = CharField(max_length=1024, blank=True)
    reply_to = CharField(max_length=255, blank=True)
    subject = CharField(max_length=255, blank=True)
    body = TextField(blank=True)
    tracking_id = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.to_email


class RespuestaCorreo(models.Model):
    correo = models.ForeignKey(
        "Correo", on_delete=models.CASCADE, related_name="respuestas"
    )
    remitente = models.EmailField()
    asunto = models.CharField(max_length=255)
    cuerpo = models.TextField()
    fecha = models.DateTimeField()
    archivo = models.FileField(upload_to="respuestas_correo", null=True, blank=True)


class Propuesta(BaseModel):
    cliente = ForeignKey(Cliente, on_delete=models.CASCADE)
    correo = ForeignKey(Correo, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.cliente.nombre

    def DameNombreFichero(
        self, pdf=False
    ):  
        nombrefichero = []
        tipos = PropuestaLinea.objects.filter(propuesta=self).values_list(
            "campanya_linea__tipo", flat=True
        )
        if pdf:
            separador = "_"
        else:
            separador = " "
        if "NPL" in tipos:
            nombrefichero.append(f"NPL{separador}")
        if "CDR" in tipos:
            nombrefichero.append(f"CDR{separador}")
        if "REO" in tipos:
            nombrefichero.append(f"REO{separador}")
            TIPO = [
                ("NPL", "NPL-Cesión de crédito"),
                ("CDR", "CDR-Cesión de remate"),
                ("REO", "REO-Compra de activo"),
            ]

        id_provincias = PropuestaLinea.objects.filter(propuesta=self).values_list(
            "campanya_linea__activo__poblacion__provincia__id", flat=True
        )
        provincias = Provincia.objects.filter(pk__in=id_provincias).order_by("nombre")
        for provincia in provincias:
            nombrefichero.append(f"{provincia.nombre}{separador}")
        nombrefichero = "".join(nombrefichero)
        fecha = self.creado_en.strftime("%d_%m_%Y")
        if pdf:
            return f"investmss_activos_{nombrefichero}{fecha}.pdf"
        else:
            return f"{nombrefichero}"

    def EstaPendiente(self):
        return (
            PropuestaLinea.objects.filter(propuesta=self).exclude(estado="").first()
            == None
        )

    def PropuestasEnviadas(self):
        return PropuestaLinea.objects.filter(
            propuesta=self, propuesta__anulado_por=None
        )

    def NumPropuestasEnviadas(self):
        return self.PropuestasEnviadas().count()

    def PropuestasInteresadas(self):
        return PropuestaLinea.objects.filter(
            propuesta=self, propuesta__anulado_por=None, estado="I"
        )

    def NumPropuestasInteresadas(self):
        return self.PropuestasInteresadas().count()

    def PropuestasInteresadasoEsperando(self):
        return PropuestaLinea.objects.filter(
            propuesta=self, propuesta__anulado_por=None
        ).filter(Q(estado="I") | Q(estado="E"))

    def NumPropuestasInteresadasoEsperando(self):
        return self.PropuestasInteresadasoEsperando().count()

    def PropuestasTrabajadas(self):
        return PropuestaLinea.objects.filter(
            propuesta=self, propuesta__anulado_por=None, estado="P"
        )

    def NumPropuestasTrabajadas(self):
        return self.PropuestasTrabajadas().count()

    def PropuestasAceptadas(self):
        return PropuestaLinea.objects.filter(
            propuesta=self, propuesta__anulado_por=None, estado="R"
        )

    def NumPropuestasAceptadas(self):
        return self.PropuestasAceptadas().count()

    def ImprimirPropuesta(self):
        from invest.generarRML import GenerarListaActivosConCatastroRML

        empresa = Empresa.objects.all().first()
        lineas_id = PropuestaLinea.objects.filter(propuesta=self).values_list(
            "campanya_linea", flat=True
        )
        lineas = CampanyaLinea.objects.filter(pk__in=lineas_id)

        fecha = self.creado_en.strftime("%Y%m%d")
        nombrefichero = f"relacion_activos_mssinvest_{self.cliente.nombre}_{fecha}.pdf"
        rml_cadena = GenerarListaActivosConCatastroRML(
            empresa, None, lineas, "", "", "", "", "", "", nombrefichero
        )
        rml_path = settings.MEDIA_ROOT + "/archivo.rml"
        with open(rml_path, "w", encoding="utf-8") as f:
            f.write(rml_cadena)

        output = settings.MEDIA_ROOT + "/" + nombrefichero
        rml2pdf.go(rml_path, outputFileName=output)

        return nombrefichero


class PropuestaLinea(BaseModel):
    propuesta = ForeignKey(Propuesta, on_delete=models.CASCADE)
    campanya_linea = ForeignKey(CampanyaLinea, on_delete=models.CASCADE)

    ESTADO = [
        ("", "Propuesto"),
        ("I", "Interesado"),
        ("N", "No interesado"),
        ("NA", "No interesado ACEPTADO"),
        ("E", "Esperando información servicer"),
        ("P", "Preparado"),
        ("R", "Reservado"),
        ("RA", "Reservado ACEPTADO"),
        ("X", "No concretado"),
    ]
    estado = CharField(max_length=2, choices=ESTADO, default="", blank=True)

    def __str__(self):
        return self.propuesta.cliente.nombre

    def ImprimirContrato(self):
        from invest.generarRML import GenerarContratoRML

        empresa = Empresa.objects.all().first()
        nombrefichero = "Propuesta.pdf"
        rml_cadena = GenerarContratoRML(empresa, self, nombrefichero)
        f = open(settings.MEDIA_ROOT + "/archivo.rml", "w")
        f.write(rml_cadena)
        f.close()
        output = settings.MEDIA_ROOT + "/" + nombrefichero
        rml2pdf.go(settings.MEDIA_ROOT + "/archivo.rml", outputFileName=output)
        return nombrefichero

    def DameDescActivo(self):
        if self.campanya_linea.activo.id_proveedor:
            return self.campanya_linea.activo.id_proveedor
        else:
            return self.campanya_linea.activo.ref_catastral

    def DameLineaEstado(self, estado=""):
        if estado:
            estado = estado.split(",")
            linea = (
                PropuestaLineaEstado.objects.filter(linea=self, estado__in=estado)
                .order_by("-creado_en")
                .first()
            )
        else:
            linea = (
                PropuestaLineaEstado.objects.filter(linea=self)
                .order_by("-creado_en")
                .first()
            )
        return linea

    def EnviaCorreo(self):
        parametros = {"tipo": "oferta", "oferta": self}
        empresa = Empresa.objects.all().first()
        EnviarCorreo(empresa, None, self.propuesta.cliente.responsable, parametros)

    def DameEstado(self):
        oferta = PropuestaLineaEstado.objects.filter(linea=self).order_by("pk").last()
        estado = ""
        if not oferta:
            estado = f"Esperando al cliente"
        else:
            fecha = self.creado_en.strftime("%d-%m-%Y %H:%M")
            if self.estado == "X":
                estado = f"Reserva no concretada {fecha} "
            elif self.estado == "R":
                estado = f"Reservada {fecha}"
            elif self.estado == "P":
                estado = f"Esperando reserva {fecha}"
            elif self.estado == "E":
                estado = f"Esperando información del servicer {fecha}"
            elif self.estado == "N":
                estado = f"No interesa al cliente {fecha}"
            elif self.estado == "I":
                estado = f"Interesa al cliente {fecha}"
        return estado


class AlertaPropuestaInactiva(BaseModel):
    linea = models.ForeignKey("PropuestaLinea", on_delete=models.CASCADE)
    responsable = models.ForeignKey(
        "Responsable", null=True, blank=True, on_delete=models.SET_NULL
    )
    motivo = models.CharField(max_length=255)
    resuelta = models.BooleanField(default=False)
    pospuesto_en = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alerta: {self.linea} ({self.motivo})"


class PropuestaComentario(models.Model):
    linea = models.ForeignKey(
        "PropuestaLinea", on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    texto = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Comentario de {self.autor} en {self.linea}"


class PropuestaLineaEstado(BaseModel):
    linea = ForeignKey(PropuestaLinea, on_delete=models.CASCADE)
    ESTADO = [
        ("I", "Interesado"),
        ("N", "No interesado"),
        ("E", "Esperando información servicer"),
        ("P", "Preparado"),
        ("R", "Reservado"),
        ("X", "No concretado"),
        ("V", "Vendido"),
    ]
    estado = CharField(max_length=1, choices=ESTADO, default="")
    confirmado_responsable = DateTimeField(null=True, blank=True)
    confirmado_por = models.ForeignKey(
        "invest.User",
        models.RESTRICT,
        null=True,
        editable=False,
        related_name="usuario_confirmado",
    )


class Calendario(BaseModel):
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.contenttypes.fields import GenericForeignKey

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    objeto = GenericForeignKey("content_type", "object_id")

    fecha = models.DateTimeField()
    descripcion = models.TextField(blank=True, null=True)  

    class Meta:
        verbose_name = "Evento de calendario"
        verbose_name_plural = "Eventos de calendario"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.objeto} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"


class Auditoria(
    models.Model,
):

    def user(request):
        return request.user.username

    ACCIONES = [
        ("CREAR", "Creación"),
        ("EDITAR", "Edición"),
        ("ELIMINAR", "Eliminación"),
    ]

    modelo = models.CharField(max_length=100)
    objeto_id = models.BigIntegerField()
    accion = models.CharField(max_length=20, choices=ACCIONES)
    descripcion = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invest_auditoria"
        ordering = ["-creado_en"]


class Agenda(BaseModel):
    nombre = CharField(max_length=255)
    apellidos = CharField(max_length=255, blank=True, null=True)
    empresa = CharField(max_length=255, blank=True, null=True)
    descripcion = TextField(blank=True, null=True)
    telefono = CharField(max_length=15, blank=True, null=True)
    fijo = CharField(max_length=15, blank=True, null=True)
    email = EmailField(max_length=100, blank=True, null=True)
    creado_por = models.ForeignKey(
        "invest.User",
        models.RESTRICT,
        null=True,
        editable=False,
        related_name="usuario_creado",
    )

    def __str__(self):
        return f"{self.nombre} - {self.descripcion} - {self.email} - {self.telefono} - {self.fijo}"
