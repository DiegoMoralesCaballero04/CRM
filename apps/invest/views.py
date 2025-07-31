import json
import os
from z3c.rml import rml2pdf
from PyPDF2 import PdfFileMerger, PdfFileReader
import gc

# Django
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.files import File
from django.core.files.base import ContentFile
from django.db.models import Q, Max, F, OuterRef, Subquery
from django.db.models import Value, IntegerField
from django.db.models import Case, When, Value, FloatField
from django.utils import timezone
from django.db.models.functions import TruncMonth
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from invest.models import Calendario
from django_filters.views import FilterView
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal
import platform
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, TemplateView, DeleteView
from django.views.generic import UpdateView, DetailView
from django.views.generic.base import View
from django.urls import resolve, reverse, reverse_lazy
from django.utils.timezone import now
from datetime import datetime, time
from django.utils.dateparse import parse_time

from datetime import datetime, timedelta
from django.core.files.storage import default_storage
from django.contrib.contenttypes.models import ContentType
from invest.forms import *
from invest.generarRML import GenerarListaActivosConCatastroRML, GenerarListadoEstados
from invest.generarExcel import GenerarListaActivosExcel
from invest.importar_activo import ImportarActivos
from invest.models import *
from invest.utils import DameFecha
from invest.catastro import obtener_info_catastro, generar_card_inmueble_catastro
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware


from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.chrome.service import Service
from django.db.models.functions import Greatest
from datetime import datetime, time

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from django.core.files import File
from django.conf import settings
import os
from django.contrib.admin.views.decorators import staff_member_required
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import ExpressionWrapper, FloatField, F
from django.db.models import ExpressionWrapper, FloatField, F, Func, Value
from django.http import FileResponse
from invest.generarFicha import generar_pdf_para_activo
from django.db.models.functions import Coalesce
import logging

logger = logging.getLogger("invest")
import re
from openai import OpenAI


class LoginRequiredMixin(object):
    @method_decorator(login_required(login_url="login"))
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        proxy = super(LoginRequiredMixin, self)
        return proxy.dispatch(request, *args, **kwargs)


class InitBaseMixin(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.request.session

        return context


class TienePermisosMixin(object):
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        vista_ = resolve(request.path_info).url_name
        if user.cliente and not vista_ in [
            "home",
            "misofertas",
            "detallelinea",
            "apiactivo",
            "listarpropuesta",
            "apipropuestas",
            "listaroferta",
            "listadopropuesta",
        ]:
            return HttpResponseForbidden()
        else:
            proxy = super(TienePermisosMixin, self)
            return proxy.dispatch(request, *args, **kwargs)


class Vista_Iniciar(
    LoginRequiredMixin, TienePermisosMixin, InitBaseMixin, TemplateView
):
    template_name = "inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user

        if not usuario.cliente:
            campanyas = Campanya.objects.filter(anulado_por=None)
            context["NumCampanyas"] = campanyas.count()

            id_activos = (
                CampanyaLinea.objects.filter(campanya__in=campanyas)
                .values_list("activo__pk", flat=True)
                .distinct()
            )

            activos = Activo.objects.filter(pk__in=id_activos)
            context["NumActivos"] = activos.count()

        propuestas = Propuesta.objects.filter(anulado_por=None)
        if usuario.cliente:
            propuestas = propuestas.filter(cliente=usuario.cliente)
        context["NumPropuestas"] = propuestas.count()

        propuestas_lineas = PropuestaLinea.objects.filter(anulado_por=None)
        if usuario.cliente:
            propuestas_lineas = propuestas_lineas.filter(
                propuesta__cliente=usuario.cliente
            )

        context["NumPropuestas_activos"] = propuestas_lineas.count()
        context["NumPropuestas_Interesadas"] = propuestas_lineas.filter(
            estado="I"
        ).count()
        context["NumPropuestas_InteresadasoEsperando"] = propuestas_lineas.filter(
            estado__in=["I", "E"]
        ).count()
        context["NumPropuestas_Esperando"] = propuestas_lineas.filter(
            estado="E"
        ).count()
        context["NumPropuestas_Preparadas"] = propuestas_lineas.filter(
            Q(estado="P") | Q(estado="R")
        ).count()
        context["NumPropuestas_No_Concretados"] = propuestas_lineas.filter(
            estado="X"
        ).count()
        context["NumPropuestas_Vendidos"] = propuestas_lineas.filter(estado="V").count()
        context["conversion_labels"] = json.dumps(
            [
                "Propuestos",
                "Interesados",
                "Esperando info",
                "Preparados",
                "No Concretado",
                "Aceptados",
            ]
        )
        context["conversion_datos"] = json.dumps(
            [
                context["NumPropuestas_activos"],
                context["NumPropuestas_Interesadas"],
                context["NumPropuestas_Esperando"],
                context["NumPropuestas_Preparadas"],
                context["NumPropuestas_No_Concretados"],
                context["NumPropuestas_Vendidos"],
            ]
        )
        tipos_activo = (
            Activo.objects.filter(tipologia__subgrupo__isnull=False)
            .values(nombre=F("tipologia__subgrupo__nombre"))
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        context["ActivoTiposLabels"] = json.dumps([x["nombre"] for x in tipos_activo])
        context["ActivoTiposDatos"] = json.dumps([x["total"] for x in tipos_activo])
        campanyas_estado = (
            Campanya.objects.values("estado")
            .annotate(total=Count("id"))
            .order_by("estado")
        )
        context["CampanyaEstadosLabels"] = json.dumps(
            [x["estado"] for x in campanyas_estado]
        )
        context["CampanyaEstadosDatos"] = json.dumps(
            [x["total"] for x in campanyas_estado]
        )

        clientes_zona = (
            Cliente.objects.exclude(zona="")
            .values("zona")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )
        context["ClientesZonaLabels"] = json.dumps([x["zona"] for x in clientes_zona])
        context["ClientesZonaDatos"] = json.dumps([x["total"] for x in clientes_zona])
        desde = now() - timedelta(days=180)
        propuestas_por_mes = (
            propuestas.filter(creado_en__gte=desde)
            .annotate(mes=TruncMonth("creado_en"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )

        base = OrderedDict()
        hoy = now()
        for i in range(5, -1, -1):
            fecha = (hoy - relativedelta(months=i)).replace(day=1)
            base[fecha.strftime("%b %Y")] = 0

        for p in propuestas_por_mes:
            clave = p["mes"].strftime("%b %Y")
            base[clave] = p["total"]

        context["labels_json"] = json.dumps(list(base.keys()))
        context["datos_json"] = json.dumps(list(base.values()))

        eventos = []
        for propuesta in propuestas[:10]:  
            eventos.append(
                {
                    "title": f"Propuesta #{propuesta.id}",
                    "start": propuesta.creado_en.date().isoformat(),
                }
            )
        context["eventos_json"] = json.dumps(eventos)

        campanyas_mes = (
            Campanya.objects.filter(anulado_por=None)
            .annotate(mes=TruncMonth("creado_en"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )

        base = OrderedDict()
        hoy = now()
        for i in range(5, -1, -1):
            fecha = (hoy - relativedelta(months=i)).replace(day=1)
            base[fecha.strftime("%b %Y")] = 0

        for c in campanyas_mes:
            clave = c["mes"].strftime("%b %Y")
            base[clave] = c["total"]

        context["CampanyasMesLabels"] = json.dumps(list(base.keys()))
        context["CampanyasMesDatos"] = json.dumps(list(base.values()))

        campanyas_mes = (
            Campanya.objects.filter(anulado_por=None)
            .annotate(mes=TruncMonth("creado_en"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )

        base = OrderedDict()
        hoy = now()
        for i in range(5, -1, -1):
            fecha = (hoy - relativedelta(months=i)).replace(day=1)
            base[fecha.strftime("%b %Y")] = 0

        for c in campanyas_mes:
            clave = c["mes"].strftime("%b %Y")
            base[clave] = c["total"]

        context["CampanyasMesLabels"] = json.dumps(list(base.keys()))
        context["CampanyasMesDatos"] = json.dumps(list(base.values()))

        activos_prov = (
            Activo.objects.values(nombre=F("poblacion__provincia__nombre"))
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        context["ActivosProvinciaLabels"] = json.dumps(
            [x["nombre"] for x in activos_prov]
        )
        context["ActivosProvinciaDatos"] = json.dumps(
            [x["total"] for x in activos_prov]
        )

        desde = now() - timedelta(days=180)
        meses = OrderedDict()
        for i in range(5, -1, -1):
            fecha = (now() - relativedelta(months=i)).replace(day=1)
            clave = fecha.strftime("%b %Y")
            meses[clave] = {"generadas": 0, "aceptadas": 0}

        generadas = (
            Propuesta.objects.filter(anulado_por=None, creado_en__gte=desde)
            .annotate(mes=TruncMonth("creado_en"))
            .values("mes")
            .annotate(total=Count("id"))
        )

        aceptadas = (
            PropuestaLinea.objects.filter(
                estado="R", anulado_por=None, creado_en__gte=desde
            )
            .annotate(mes=TruncMonth("creado_en"))
            .values("mes")
            .annotate(total=Count("id"))
        )

        for g in generadas:
            clave = g["mes"].strftime("%b %Y")
            meses[clave]["generadas"] = g["total"]
        for a in aceptadas:
            clave = a["mes"].strftime("%b %Y")
            meses[clave]["aceptadas"] = a["total"]

        context["PropuestasMesLabels"] = json.dumps(list(meses.keys()))
        context["PropuestasGeneradas"] = json.dumps(
            [x["generadas"] for x in meses.values()]
        )
        context["PropuestasAceptadas"] = json.dumps(
            [x["aceptadas"] for x in meses.values()]
        )
        return context


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        return reverse("home")


class CustomRegister(View):
    @method_decorator(csrf_exempt)
    @method_decorator(require_http_methods(["GET", "POST"]))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, "registration/register.html", {"form": form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            try:
                nombre_completo = form.cleaned_data["nombre_completo"]
                user = form.cleaned_data["username"]
                email = form.cleaned_data["email"]
                telefono = form.cleaned_data["telefono"]
                nombre = nombre_completo.split(" ")[0]
                apellido1 = (
                    nombre_completo.split(" ")[1]
                    if len(nombre_completo.split(" ")) > 1
                    else ""
                )
                apellido2 = (
                    nombre_completo.split(" ")[2]
                    if len(nombre_completo.split(" ")) > 2
                    else ""
                )
                cliente = Cliente.objects.create(
                    nombre=nombre,
                    apellidos=apellido1 + " " + apellido2,
                    telefono=telefono,
                    correo=email,
                    nombre_completo=nombre_completo,
                )

                user = User.objects.create_user(
                    email=email,
                    password=form.cleaned_data["password1"],
                    username=nombre_completo,
                    first_name=nombre,
                    last_name=apellido1 + " " + apellido2,
                    cliente_id=cliente.id,
                )
                messages.success(
                    request,
                    "¡Registro exitoso! Por favor inicia sesión con tus credenciales.",
                )
                return redirect("login")

            except Exception as e:
                print("Error: ")
                print(str(e))
                messages.error(
                    request, f"Ocurrió un error al crear tu cuenta: {str(e)}"
                )
                return render(request, "registration/register.html", {"form": form})

        return render(request, "registration/register.html", {"form": form})


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/password_reset.html"
    email_template_name = "registration/emails/password_reset.html"
    success_url = reverse_lazy("password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

    def form_valid(self, form):
        form.user.is_active = True
        response = super().form_valid(form)
        return response


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


class HerramientasView(LoginRequiredMixin, TienePermisosMixin, generic.TemplateView):
    template_name = "herramientas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subgrupos"] = SubGrupoTipologia.objects.filter().order_by(
            "grupo__orden", "orden", "nombre"
        )

        context["grupos"] = GrupoTipologia.objects.filter(anulado_por=None).order_by(
            "orden"
        )
        context["tipos"] = SubGrupoTipologia.objects.filter(anulado_por=None).order_by(
            "grupo__orden", "orden"
        )
        context["provincias"] = Provincia.objects.all().order_by("nombre")
        context["provincias_todas"] = Provincia.objects.all().order_by("nombre")
        context["poblaciones"] = Poblacion.objects.all().order_by("nombre")
        return context


class CampanyaView(LoginRequiredMixin, TienePermisosMixin, generic.TemplateView):
    template_name = "campanya.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proveedores"] = Proveedor.objects.filter(anulado_por=None).order_by(
            "codigo"
        )
        context["carteras"] = Cartera.objects.filter(anulado_por=None).order_by(
            "codigo"
        )
        return context


class Campanya_Detalle(LoginRequiredMixin, TienePermisosMixin, DetailView):
    model = Campanya
    template_name = "campanya_detalle.html"


class CampanyaCreateView(LoginRequiredMixin, TienePermisosMixin, generic.CreateView):
    model = Campanya
    form_class = CampanyaForm
    template_name = "campanya_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        fichero = self.request.FILES.get("fichero")
        campanya = form.save(commit=False)
        campanya.fichero = fichero
        campanya.save()
        ImportarActivos(campanya, self.request.user)
        return response

    def get_success_url(self):
        return reverse("detallecampanya", args=[self.object.pk])


class Campanya_Editar(LoginRequiredMixin, TienePermisosMixin, UpdateView):
    model = Campanya
    template_name = "campanya_form.html"
    form_class = CampanyaForm
    success_url = "/campanya/"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        fichero = self.request.FILES.get("fichero")
        if fichero:
            ruta_relativa = f"campanya//{fichero.name}"
            path_guardado = default_storage.save(
                ruta_relativa, ContentFile(fichero.read())
            )

            self.object.fichero.name = path_guardado

        CampanyaLinea.objects.filter(campanya=self.object).update(tipo=self.object.tipo)
        self.object.save()
        return super().form_valid(form)


class Campanya_Api(LoginRequiredMixin, TienePermisosMixin, View):
    def get(self, request, *args, **kwargs):
        accion = request.GET.get("accion")
        error = False
        literror = ""
        context_dict = []
        if accion == "actualiza_datos_catastro":
            campanya = request.GET["id_campanya"]
            activos_id = CampanyaLinea.objects.filter(campanya=campanya).values_list(
                "activo__pk", flat=True
            )
            activos = Activo.objects.filter(pk__in=activos_id)
            for activo in activos:
                activo.ActivoGuardaCatastro()
                activo.ActivoLocalizar()

        elif accion == "eliminar_campanya":
            campanya = request.GET["id_campanya"]
            campanya = Campanya.objects.get(pk=campanya)
            propuestas = PropuestaLinea.objects.filter(
                campanya_linea__campanya=campanya
            )
            if propuestas.first():
                campanya.anulado_en = datetime.now()
                campanya.anulado_por = self.request.user
                campanya.save()
            else:
                lineas = CampanyaLinea.objects.filter(campanya=campanya)
                id_activos = lineas.values_list("activo__pk", flat=True)
                id_activos_en_otras_campanyas = (
                    CampanyaLinea.objects.exclude(campanya=campanya)
                    .filter(activo__pk__in=id_activos)
                    .values_list("activo__pk", flat=True)
                )
                Activo.objects.filter(pk__in=id_activos).exclude(
                    pk__in=id_activos_en_otras_campanyas
                ).delete()
                lineas.delete()
                campanya.delete()
                tipologias_activas = (
                    Activo.objects.all().values_list("tipologia__pk").distinct()
                )
                Tipologia.objects.exclude(pk__in=tipologias_activas).delete()
        elif accion == "cargar_carteras_old":
            proveedor_id = request.GET.get("proveedor")
            if proveedor_id:
                carteras = Cartera.objects.filter(proveedor_id=proveedor_id).order_by(
                    "codigo"
                )
                return JsonResponse(
                    list(carteras.values("id", "codigo", "nombre")), safe=False
                )
            else:
                return None
        elif accion == "cargar_tipologias_old":
            grupo_id = request.GET.get("grupo")
            if grupo_id:
                tipologias = SubGrupoTipologia.objects.filter(
                    grupo__id=grupo_id
                ).order_by("grupo__orden", "orden")
                return JsonResponse(list(tipologias.values("id", "nombre")), safe=False)
            else:
                return None
        elif accion == "cargar_carteras":
            proveedor_id = request.GET.get("proveedor").split(",")
            if proveedor_id and proveedor_id != [] and proveedor_id != [""]:
                carteras = Cartera.objects.filter(
                    proveedor_id__in=proveedor_id
                ).order_by("codigo")
            else:
                carteras = Cartera.objects.all().order_by("codigo")
            html = []
            for cartera in carteras:
                html.append(
                    f"""
                    <div class="form-check cartera-item">
                        <input class="form-check-input" type="checkbox" name="cartera_bactivo" value="{cartera.pk}" id="cartera_{cartera.pk}">
                        <label class="form-check-label" for="cartera_{cartera.pk}">
                            {cartera.codigo}. {cartera.nombre}
                        </label>
                    </div>"""
                )
            context_dict = {"html": " ".join(html)}
            json_context = json.dumps(context_dict).encode("utf-8")
        elif accion == "cargar_subgrupos":
            grupo_id = request.GET.get("grupo").split(",")
            if grupo_id and grupo_id != [] and grupo_id != [""]:
                tipologias = SubGrupoTipologia.objects.filter(
                    grupo_id__in=grupo_id
                ).order_by("grupo__orden", "orden")
            else:
                tipologias = SubGrupoTipologia.objects.all().order_by(
                    "grupo__orden", "orden"
                )
            html = []
            for tipologia in tipologias:
                html.append(
                    f"""
                    <div class="form-check tipo-item">
                        <input class="form-check-input" type="checkbox" name="tipo_bactivo" value="{tipologia.pk}" id="cartera_{tipologia.pk}">
                        <label class="form-check-label" for="cartera_{tipologia.pk}">
                            {tipologia.nombre}
                        </label>
                    </div>"""
                )
            context_dict = {"html": " ".join(html)}
            json_context = json.dumps(context_dict).encode("utf-8")

        elif accion == "cargar_tipologias":
            grupo_id = request.GET.get("grupo").split(",")
            if grupo_id and grupo_id != [] and grupo_id != [""]:
                tipologias = SubGrupoTipologia.objects.filter(
                    grupo_id__in=grupo_id
                ).order_by("grupo__orden", "orden")
            else:
                tipologias = SubGrupoTipologia.objects.all().order_by(
                    "grupo__orden", "orden"
                )
            html = []
            for tipologia in tipologias:
                html.append(
                    f"""
                    <div class="form-check tipo-item">
                        <input class="form-check-input" type="checkbox" name="tipo_bactivo" value="{tipologia.pk}" id="cartera_{tipologia.pk}">
                        <label class="form-check-label" for="cartera_{tipologia.pk}">
                            {tipologia.nombre}
                        </label>
                    </div>"""
                )
            context_dict = {"html": " ".join(html)}
            json_context = json.dumps(context_dict).encode("utf-8")

        elif accion == "cargar_poblaciones_old":
            provincia_id = request.GET.get("provincia")
            if provincia_id:
                poblaciones = Poblacion.objects.filter(
                    provincia__id=provincia_id
                ).order_by("nombre")
                return JsonResponse(
                    list(poblaciones.values("id", "nombre")), safe=False
                )
            else:
                return None

        elif accion == "cargar_poblaciones":
            provincia_id = request.GET.get("provincia").split(",")
            if provincia_id and provincia_id != [] and provincia_id != [""]:
                poblaciones = Poblacion.objects.filter(
                    provincia__pk__in=provincia_id
                ).order_by("nombre")
            else:
                poblaciones = Poblacion.objects.all().order_by("nombre")
            html = []
            for poblacion in poblaciones:
                html.append(
                    f"""
                    <div class="form-check poblacion-item">
                        <input class="form-check-input" type="checkbox" name="poblacion_bactivo" value="{poblacion.pk}" id="poblacion_{poblacion.pk}">
                        <label class="form-check-label" for="poblacion_{poblacion.pk}">
                            {poblacion.nombre}
                        </label>
                    </div>"""
                )
            context_dict = {"html": " ".join(html)}
            json_context = json.dumps(context_dict).encode("utf-8")
            return HttpResponse(json_context, content_type="application/json")
        elif accion == "cargar_poblaciones_radio":
            provincia_id = request.GET.get("provincia").split(",")
            if provincia_id and provincia_id != [] and provincia_id != [""]:
                poblaciones = Poblacion.objects.filter(
                    provincia__pk__in=provincia_id
                ).order_by("nombre")
            else:
                poblaciones = Poblacion.objects.all().order_by("nombre")
            html = []

            id_name = request.GET.get("id_name", "poblacion_")
            name = request.GET.get("name", "poblacion_bactivo")
            for poblacion in poblaciones:
                html.append(
                    f"""
                    <div class="form-check poblacion-item">
                        <input class="form-check-input" type="radio" name="{name}" value="{poblacion.pk}" id="{id_name}{poblacion.pk}">
                        <label class="form-check-label" for="{id_name}{poblacion.pk}">
                            {poblacion.nombre}
                        </label>
                    </div>"""
                )
            context_dict = {"html": " ".join(html)}
            json_context = json.dumps(context_dict).encode("utf-8")
            return HttpResponse(json_context, content_type="application/json")
        elif accion == "activonodisponible":
            linea_id = request.GET.get("linea")
            activo_id = request.GET.get("activo")
            try:
                activo = CampanyaLinea.objects.get(
                    pk=linea_id, activo__pk=activo_id
                ).activo
                activo.no_disponible = datetime.now()
                activo.no_disponible_por = self.request.user
                activo.save()
            except:
                error = True
                literror = "Linea no enccontrada"
        elif accion == "activodisponible":
            linea_id = request.GET.get("linea")
            activo_id = request.GET.get("activo")
            try:
                activo = CampanyaLinea.objects.get(
                    pk=linea_id, activo__pk=activo_id
                ).activo
                activo.no_disponible = None
                activo.no_disponible_por = None
                activo.save()
            except:
                error = True
                literror = "Linea no encontrada"
        elif accion == "activoreservado" or accion == "activopreparado":
            propuestalinea_id = request.GET.get("propuestalinea_id")
            linea_id = request.GET.get("linea")
            activo_id = request.GET.get("activo")
            try:
                lineapropuesta = PropuestaLinea.objects.get(pk=propuestalinea_id)
                linea = CampanyaLinea.objects.get(pk=linea_id, activo__pk=activo_id)
                if accion == "activoreservado":
                    linea.reservado_en = datetime.now()
                    linea.reservado_por = self.request.user
                    lineapropuesta.estado = "R"

                if accion == "activopreparado":
                    linea.preparado_en = datetime.now()
                    linea.preparado_por = self.request.user
                    lineapropuesta.estado = "P"

                linea.save()
                lineapropuesta.save()
                PropuestaLineaEstado.objects.create(linea=lineapropuesta, estado="R")
            except:
                error = True
                literror = "Linea no enccontrada"
        elif accion == "pedir_info_catastro":
            linea_id = request.GET.get("linea")
            activo_id = request.GET.get("activo")
            try:
                linea = CampanyaLinea.objects.get(pk=linea_id, activo__pk=activo_id)
                if linea.activo.ref_catastral:

                    html = generar_card_inmueble_catastro(
                        obtener_info_catastro(linea.activo.ref_catastral)
                    )
                    context_dict = {"error": error, "literror": literror, "html": html}
                else:
                    error = True
                    literror = "Debe tener referencia catastral"
            except:
                error = True
                literror = "Linea no encontrada"
        elif accion == "actualizar_campanya_desde_excel":
            if self.request.user.pk == 1:
                campanya = Campanya.objects.get(pk=request.GET["id_campanya"])
                ImportarActivos(campanya, self.request.user, True)
        if context_dict == {}:
            context_dict = {"error": error, "literror": literror}
        json_context = json.dumps(context_dict).encode("utf-8")
        return HttpResponse(json_context, content_type="application/json")


class CampanyaListView(
    LoginRequiredMixin, TienePermisosMixin, generic.ListView
):  # TienePermisosMixin
    model = Campanya
    context_object_name = "campanyas"
    template_name = "campanya_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context["num_activos"] = (
            CampanyaLinea.objects.filter(
                campanya__pk__in=queryset.values_list("pk", flat=True)
            )
            .values_list("activo__pk")
            .distinct()
            .count()
        )
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(anulado_en=None)
        proveedor = self.request.GET.get("proveedor")
        if proveedor:
            queryset = queryset.filter(proveedor__pk=proveedor)
        cartera = self.request.GET.get("cartera")
        if cartera:
            queryset = queryset.filter(cartera__pk=cartera)
        tipo = self.request.GET.get("tipo")
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        estado = self.request.GET.get("estado")
        if estado:
            if estado == "1":
                queryset = queryset.exclude(finalizada_en=None)
        else:
            queryset = queryset.filter(finalizada_en=None)

        desde = DameFecha(self.request.GET.get("desde"))
        if desde:
            queryset = queryset.filter(fecha__gte=desde)
        hasta = DameFecha(self.request.GET.get("hasta"))
        if hasta:
            queryset = queryset.filter(fecha__lte=hasta)
        queryset = queryset.order_by("-fecha", "-pk")
        return queryset


class CampanyaListView(
    LoginRequiredMixin, TienePermisosMixin, generic.ListView
):  # TienePermisosMixin
    model = Campanya
    context_object_name = "campanyas"
    template_name = "campanya_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context["num_activos"] = (
            CampanyaLinea.objects.filter(
                campanya__pk__in=queryset.values_list("pk", flat=True)
            )
            .values_list("activo__pk")
            .distinct()
            .count()
        )
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(anulado_en=None)
        proveedor = self.request.GET.get("proveedor")
        if proveedor:
            queryset = queryset.filter(proveedor__pk=proveedor)
        cartera = self.request.GET.get("cartera")
        if cartera:
            queryset = queryset.filter(cartera__pk=cartera)
        tipo = self.request.GET.get("tipo")
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        estado = self.request.GET.get("estado")
        if estado:
            if estado == "1":
                queryset = queryset.exclude(finalizada_en=None)
        else:
            queryset = queryset.filter(finalizada_en=None)

        desde = DameFecha(self.request.GET.get("desde"))
        if desde:
            queryset = queryset.filter(fecha__gte=desde)
        hasta = DameFecha(self.request.GET.get("hasta"))
        if hasta:
            queryset = queryset.filter(fecha__lte=hasta)
        queryset = queryset.order_by("-fecha", "-pk")
        return queryset


class Proveedor_Listar(LoginRequiredMixin, TienePermisosMixin, ListView):
    model = Proveedor
    form = ProveedorForm
    template_name = "proveedor_list.html"

    def get_queryset(self):
        return super().get_queryset().filter(anulado_por=None).order_by("codigo")


class Proveedor_Detalle(LoginRequiredMixin, TienePermisosMixin, DetailView):
    model = Proveedor
    template_name = "proveedor_detalle.html"


class Proveedor_Crear(LoginRequiredMixin, TienePermisosMixin, CreateView):
    model = Proveedor
    template_name = "proveedor_form.html"
    fields = ["nombre", "codigo"]
    success_url = reverse_lazy("listarproveedor")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.creado_por = self.request.user
        self.object.creado_en = datetime.now()
        self.object.save()
        return response


class Proveedor_Editar(LoginRequiredMixin, TienePermisosMixin, UpdateView):
    model = Proveedor
    template_name = "proveedor_form.html"
    fields = ["nombre", "codigo"]
    success_url = reverse_lazy("listarproveedor")


class Proveedor_Eliminar(LoginRequiredMixin, TienePermisosMixin, DeleteView):
    model = Proveedor
    template_name = "proveedor_confirm_delete.html"
    success_url = reverse_lazy("listarproveedor")

    def form_valid(self, form):
        self.object.anulado_por = self.request.user
        self.object.anulado_en = datetime.now()
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        return super().get_queryset().filter(anulado_por=None)


class Cartera_Crear(LoginRequiredMixin, TienePermisosMixin, CreateView):
    model = Cartera
    template_name = "proveedor_cartera_form.html"
    fields = ["codigo", "nombre"]
    success_url = reverse_lazy("listarproveedor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        idservicer = self.kwargs["idservicer"]
        context["proveedor"] = Proveedor.objects.filter(pk=idservicer).first()
        return context

    def form_valid(self, form):
        idservicer = self.kwargs["idservicer"]
        proveedor = Proveedor.objects.get(pk=idservicer)
        form.instance.proveedor = proveedor
        form.instance.creado_por = self.request.user
        form.instance.creado_en = datetime.now()
        response = super().form_valid(form)
        return response



class Cartera_Editar(LoginRequiredMixin, TienePermisosMixin, UpdateView):
    model = Cartera
    template_name = "proveedor_cartera_form.html"
    fields = ["codigo", "nombre"]
    success_url = reverse_lazy("listarproveedor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        idservicer = self.kwargs["idservicer"]
        context["proveedor"] = Proveedor.objects.filter(pk=idservicer).first()
        return context


class Cartera_Eliminar(LoginRequiredMixin, TienePermisosMixin, DeleteView):
    model = Cartera
    template_name = "proveedor_cartera_confirm_delete.html"
    success_url = reverse_lazy("listarproveedor")

    def form_valid(self, form):
        self.object.anulado_por = self.request.user
        self.object.anulado_en = datetime.now()
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        return super().get_queryset().filter(anulado_por=None)

class Contacto_Crear(LoginRequiredMixin, TienePermisosMixin, CreateView):
    model = Contacto
    template_name = "proveedor_contacto_form.html"
    fields = ["nombre", "correo", "telefono", "cargo", "NPL", "CDR", "REO"]
    success_url = reverse_lazy("listarproveedor")

    def form_valid(self, form):
        idservicer = self.kwargs["idservicer"]
        proveedor = Proveedor.objects.get(pk=idservicer)
        form.instance.proveedor = proveedor
        form.instance.creado_por = self.request.user
        form.instance.creado_en = datetime.now()
        response = super().form_valid(form)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        idservicer = self.kwargs["idservicer"]
        context["proveedor"] = Proveedor.objects.filter(pk=idservicer).first()
        return context

class Contacto_Editar(LoginRequiredMixin, TienePermisosMixin, UpdateView):
    model = Contacto
    template_name = "proveedor_contacto_form.html"
    fields = ["nombre", "correo", "telefono", "cargo", "NPL", "CDR", "REO"]
    success_url = reverse_lazy("listarproveedor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        idservicer = self.kwargs["idservicer"]
        context["proveedor"] = Proveedor.objects.filter(pk=idservicer).first()
        return context


class Contacto_Eliminar(LoginRequiredMixin, TienePermisosMixin, DeleteView):
    model = Contacto
    template_name = "proveedor_contacto_confirm_delete.html"
    success_url = reverse_lazy("listarproveedor")

    def form_valid(self, form):
        self.object.anulado_por = self.request.user
        self.object.anulado_en = datetime.now()
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        return super().get_queryset().filter(anulado_por=None)



class Cliente_Api(LoginRequiredMixin, TienePermisosMixin, View):
    def get(self, request, *args, **kwargs):
        accion = request.GET.get("accion")
        if accion == "dame_telefono":
            cliente_id = request.GET.get("id")
            cliente = Cliente.objects.filter(pk=cliente_id).first()
            if cliente:
                return JsonResponse({"telefono": cliente.telefono or ""})
            else:
                return JsonResponse({"error": "Cliente no encontrado"}, status=404)

    def post(self, request, *args, **kwargs):
        accion = request.POST.get("accion")
        if not accion:
            data = json.loads(request.body)
            accion = data.get("accion")

        error = False
        literror = ""
        context_dict = {}
        if accion == "almacenar_nif":
            id_cliente = request.POST.get("id_cliente")
            cliente = Cliente.objects.get(pk=id_cliente)
            file = request.FILES["file"]
            ClienteDocumento.objects.create(cliente=cliente, tipo="0", documento=file)
            return JsonResponse({"mensaje": "Archivo subido correctamente"})
        elif accion == "eliminar_documento":
            id_cliente = data.get("id_cliente")
            id_elemento = data.get("id_elemento")
            ClienteDocumento.objects.filter(
                cliente__pk=id_cliente, pk=id_elemento
            ).delete()
            return JsonResponse({"mensaje": "Archivo eliminado correctamente"})

        return JsonResponse({"error": "Método no permitido"}, status=405)


class ClienteView(LoginRequiredMixin, TienePermisosMixin, generic.TemplateView):
    template_name = "cliente.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["responsables"] = Responsable.objects.filter(anulado_por=None).order_by(
            "nombre", "apellidos"
        )
        return context


class Cliente_Detalle(LoginRequiredMixin, TienePermisosMixin, DetailView):
    model = Cliente
    template_name = "cliente_detalle.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        objeto = self.get_object()
        context["NumCorreos"] = Correo.objects.filter(to_email=objeto.correo).count()
        context["NumCorreosRecibidos"] = RespuestaCorreo.objects.filter(
            remitente=objeto.correo
        ).count()
        ofertas = Propuesta.objects.filter(cliente=objeto)
        context["NumPropuestas"] = ofertas.count()
        context["NumPropuestasAceptadas"] = ofertas.filter(
            propuestalinea__estado="R"
        ).count()

        return context


class Cliente_Listar(LoginRequiredMixin, TienePermisosMixin, ListView):
    model = Cliente
    context_object_name = "clientes"
    form = ClienteForm
    template_name = "cliente_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id_activo = self.request.GET.get("activo")
        if id_activo:
            activo = Activo.objects.filter(pk=id_activo)
            context["activo"] = activo
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(anulado_en=None)
        nombre = self.request.GET.get("nombre")
        if nombre:
            queryset = queryset.filter(
                Q(nombre__icontains=nombre) | Q(apellidos__icontains=nombre)
            )
        responsable = self.request.GET.get("representante")
        if responsable:
            queryset = queryset.filter(responsable__pk=responsable)
        queryset = queryset.order_by("nombre", "apellidos")
        return queryset


class Cliente_Seleccion(LoginRequiredMixin, TienePermisosMixin, ListView):
    model = Cliente
    context_object_name = "clientes"
    form = ClienteForm
    template_name = "cliente_seleccion.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        responsable = self.request.user.responsable
        if responsable:
            queryset = queryset.filter(
                anulado_en=None, responsable=responsable
            ).order_by("nombre", "apellidos")
        else:
            queryset = queryset.filter(anulado_en=None).order_by("nombre", "apellidos")
        return queryset


class Cliente_Crear(LoginRequiredMixin, TienePermisosMixin, CreateView):
    model = Cliente
    template_name = "cliente_form.html"
    form_class = ClienteForm
    success_url = reverse_lazy("pantallacliente")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["responsables"] = Responsable.objects.filter(
            anulado_por=None, anulado_en=None
        ).order_by("nombre", "apellidos")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.nombre or self.object.apellidos:
            self.object.nombre_completo = (
                f"{self.object.nombre} {self.object.apellidos}"
            )
        self.object.creado_por = self.request.user
        self.object.creado_en = datetime.now()
        self.object.save()
        error, literror = self.object.CrearUsuario()
        if error:
            form.add_error(
                None, f"El usuario no ha sido creado correctamente. {literror}"
            )
            return self.form_invalid(form)
        return response


class Cliente_Editar(LoginRequiredMixin, TienePermisosMixin, UpdateView):
    model = Cliente
    template_name = "cliente_form.html"
    form_class = ClienteForm
    success_url = reverse_lazy("pantallacliente")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        objeto = self.get_object()
        context["responsables"] = Responsable.objects.filter(anulado_por=None).order_by(
            "nombre", "apellidos"
        )
        context["nifs"] = ClienteDocumento.objects.filter(cliente=objeto, tipo="0")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        cliente = form.save()
        cliente.ActualizaUsuario()
        error, literror = self.object.ActualizaUsuario()
        if error:
            form.add_error(
                None, f"El usuario no ha sido editado correctamente. {literror}"
            )
            return self.form_invalid(form)
        if cliente.nombre or cliente.apellidos:
            cliente.nombre_completo = f"{cliente.nombre} {cliente.apellidos}"
        cliente.save()
        return response

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class Cliente_Eliminar(LoginRequiredMixin, TienePermisosMixin, DeleteView):
    model = Cliente
    template_name = "cliente_confirm_delete.html"
    success_url = reverse_lazy("pantallacliente")

    def form_valid(self, form):
        self.object.anulado_por = self.request.user
        self.object.anulado_en = datetime.now()
        self.object.save()
        try:
            self.object.AnulaUsuario()
        except:
            pass
        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        return super().get_queryset().filter(anulado_por=None)


class PropuestaLineasListView(
    LoginRequiredMixin, TienePermisosMixin, generic.ListView
):  # TienePermisosMixin
    model = PropuestaLinea
    context_object_name = "ofertas"
    template_name = "oferta_cliente_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activo"] = Activo.objects.filter(pk=self.kwargs["pk"]).first()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        id_activo = self.kwargs["pk"]
        return queryset.filter(campanya_linea__activo__pk=id_activo).order_by("pk")


class PropuestaComentarioPartialView(LoginRequiredMixin, generic.ListView):
    model = PropuestaComentario
    template_name = "propuesta_comentario_list.html"
    context_object_name = "comentarios"

    def dispatch(self, request, *args, **kwargs):
        self.linea = get_object_or_404(PropuestaLinea, pk=self.kwargs["linea_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return PropuestaComentario.objects.filter(linea=self.linea).order_by(
            "-creado_en"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["linea"] = self.linea
        return context

    def post(self, request, *args, **kwargs):
        linea = get_object_or_404(
            PropuestaLinea, pk=self.kwargs["linea_id"]
        )  
        texto = request.POST.get("texto", "").strip()
        if texto:
            PropuestaComentario.objects.create(
                linea=linea, autor=request.user, texto=texto
            )
        return redirect("comentarios-modal", linea_id=linea.id)


class ActivoView(LoginRequiredMixin, TienePermisosMixin, generic.TemplateView):
    template_name = "activo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proveedores"] = Proveedor.objects.filter(anulado_por=None).order_by(
            "codigo"
        )
        context["carteras"] = Cartera.objects.filter(anulado_por=None).order_by(
            "codigo"
        )
        context["grupos"] = GrupoTipologia.objects.filter(anulado_por=None).order_by(
            "orden"
        )
        context["tipos"] = SubGrupoTipologia.objects.filter(anulado_por=None).order_by(
            "grupo__orden", "orden"
        )
        context["provincias"] = Provincia.objects.all().order_by("nombre")
        context["provincias_todas"] = Provincia.objects.all().order_by("nombre")
        context["poblaciones"] = Poblacion.objects.all().order_by("nombre")
        return context


class ActivoListView(
    LoginRequiredMixin, TienePermisosMixin, generic.ListView
):  # TienePermisosMixin
    model = CampanyaLinea
    context_object_name = "lineas"
    template_name = "activo_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id_campanya = self.request.GET.get("campanya")
        context["micampanya_id"] = id_campanya

        context["miclasif"] = self.request.GET.get("clasif", "")
        provincias_id = self.request.GET.getlist("provincia", [])
        if len(provincias_id) == 1: 
            provincias_id = provincias_id[0].split(",")
        context["miprovincia_id"] = ",".join(provincias_id)
        try:
            pnombre = Provincia.objects.filter(pk__in=provincias_id).values_list(
                "nombre", flat=True
            )
            if pnombre.count() > 0:
                context["miprovincia_nombre"] = ", ".join(pnombre)
            else:
                context["miprovincia_nombre"] = ""
        except:
            context["miprovincia_nombre"] = []
        context["provincias_todas"] = Provincia.objects.all().order_by("nombre")
        context["migrupo_id"] = self.request.GET.get("grupo", "")
        try:
            context["migrupo_nombre"] = GrupoTipologia.objects.get(
                pk=context["migrupo_id"]
            )
        except:
            context["migrupo_nombre"] = ""
        context["mitipo_id"] = self.request.GET.get("tipo", "")
        try:
            context["mitipo_nombre"] = SubGrupoTipologia.objects.get(
                pk=context["mitipo_id"]
            )
        except:
            context["mitipo_nombre"] = ""
        context["mipoblacion_id"] = self.request.GET.get("poblacion", "")
        try:
            context["mipoblacion_nombre"] = Poblacion.objects.get(
                pk=context["mipoblacion_id"]
            )
        except:
            context["mipoblacion_nombre"] = ""
        context["clasificaciones"] = ["NPL", "CDR", "REO"]

        qs = self.get_queryset()
        context["clientes"] = Cliente.objects.filter(anulado_en=None).order_by(
            "nombre_completo"
        )
        provincias = Provincia.objects.filter(
            pk__in=qs.values_list("activo__poblacion__provincia__pk", flat=True)
        ).order_by("nombre")
        context["provincias"] = provincias
        tipos = Tipologia.objects.filter(
            pk__in=qs.values_list("activo__tipologia__pk", flat=True)
        )
        context["grupos"] = GrupoTipologia.objects.filter(
            pk__in=tipos.values_list("grupo__pk")
        ).order_by("orden")
        context["tipos"] = SubGrupoTipologia.objects.filter(
            pk__in=tipos.values_list("subgrupo__pk")
        ).order_by("grupo__orden", "orden")

        poblaciones = Poblacion.objects.filter(
            pk__in=qs.values_list("activo__poblacion__pk", flat=True)
        ).order_by("nombre")
        context["poblaciones"] = poblaciones
        cantidad_total = qs.count()
        context["cantidad_total"] = cantidad_total
        context["campanya_id"] = id_campanya 
        try:
            context["num_activos"] = qs.count()
        except:
            context["num_activos"] = 0
        if id_campanya:
            campanya = Campanya.objects.get(pk=id_campanya)
            context["campanya"] = campanya
            if campanya.estado == "I":
                context["selected_iniciar"] = "checked"
            elif campanya.estado == "O":
                context["selected_ofrecer"] = "checked"
            elif campanya.estado == "A":
                context["selected_trabajar"] = "checked"
            else:
                context["selected_finalizar"] = "checked"

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        id_campanya = self.request.GET.get("campanya")
        if id_campanya:
            queryset = queryset.filter(campanya__pk=id_campanya)
        else:
            queryset = queryset.filter(campanya__anulado_en=None)

        proveedores_ids = self.request.GET.getlist("proveedor_bactivo", [])
        if proveedores_ids != []:
            queryset = queryset.filter(campanya__proveedor__pk__in=proveedores_ids)
        carteras_ids = self.request.GET.getlist("cartera_bactivo", [])
        if carteras_ids != []:
            queryset = queryset.filter(campanya__cartera__pk__in=carteras_ids)

        clasif = self.request.GET.get("clasif", "")
        if clasif:
            queryset = queryset.filter(tipo=clasif)
        clasif_ids = self.request.GET.getlist("categoria_bactivo", [])
        if clasif_ids != []:
            queryset = queryset.filter(tipo__in=clasif_ids)

        grupo = self.request.GET.get("grupo", "")
        if grupo:
            queryset = queryset.filter(activo__tipologia__grupo__pk=grupo)
        grupo_ids = self.request.GET.getlist("grupo_bactivo", [])
        if grupo_ids != []:
            queryset = queryset.filter(activo__tipologia__grupo__pk__in=grupo_ids)

        tipologia = self.request.GET.get("tipo", "")
        if tipologia and tipologia != "all":
            queryset = queryset.filter(activo__tipologia__subgrupo__id=tipologia)
        tipologia_ids = self.request.GET.getlist("tipo_bactivo", [])
        if tipologia_ids != []:
            queryset = queryset.filter(
                activo__tipologia__subgrupo__id__in=tipologia_ids
            )

        provincias_seleccionadas = self.request.GET.getlist("provincia")
        if (
            len(provincias_seleccionadas) == 1
        ):   
            provincias_seleccionadas = provincias_seleccionadas[0].split(",")

        if (
            len(provincias_seleccionadas) > 0
            and not provincias_seleccionadas == [""]
            and not "all" in provincias_seleccionadas
        ):
            queryset = queryset.filter(
                activo__poblacion__provincia__id__in=provincias_seleccionadas
            )

        provincia_ids = self.request.GET.getlist("provincia_bactivo", [])
        if provincia_ids != []:
            queryset = queryset.filter(
                activo__poblacion__provincia__id__in=provincia_ids
            )

        poblacion_id = self.request.GET.get("poblacion")
        if poblacion_id and poblacion_id != "all":
            queryset = queryset.filter(activo__poblacion__id=poblacion_id)
        poblacion_ids = self.request.GET.getlist("poblacion_bactivo", [])
        if poblacion_ids != []:
            queryset = queryset.filter(activo__poblacion__id__in=poblacion_ids)
        observaciones = self.request.GET.get("observaciones_bactivo", "")
        if observaciones:
            queryset = queryset.filter(observaciones__icontains=observaciones)
        radio_km = self.request.GET.get("radio_km", "")
        if poblacion_ids and len(poblacion_ids) == 1 and radio_km:
            try:
                poblacion = Poblacion.objects.get(pk=poblacion_ids[0])
                lat = poblacion.latitud
                lon = poblacion.longitud
                distancia_expr = ExpressionWrapper(
                    6371
                    * ACos(
                        Cos(Radians(Value(lat)))
                        * Cos(Radians(F("activo__latitud")))
                        * Cos(Radians(F("activo__longitud")) - Radians(Value(lon)))
                        + Sin(Radians(Value(lat))) * Sin(Radians(F("activo__latitud")))
                    ),
                    output_field=FloatField(),
                )

                queryset = queryset.annotate(distancia=distancia_expr).filter(
                    distancia__lte=float(radio_km)
                )
            except Exception as e:
                print(f"Error en filtro por radio: {e}")
        calle = self.request.GET.get("calle_bactivo", "")
        if calle:
            queryset = queryset.filter(activo__direccion__icontains=calle)
        idprov_activo = self.request.GET.get("id_bactivo", "")
        if idprov_activo:
            ids = [x.strip() for x in idprov_activo.split(",") if x.strip()]
            queryset = queryset.filter(activo__id_proveedor__in=ids)
        refue_activo = self.request.GET.get("refue_bactivo", "")
        if refue_activo:
            queryset = queryset.filter(activo__ref_ue=refue_activo)
        refcat_activo = self.request.GET.get("refcat_bactivo", "")
        if refcat_activo:
            cat_activo = [x.strip() for x in refcat_activo.split(",") if x.strip()]
            queryset = queryset.filter(activo__ref_catastral__in=cat_activo)

        fecha_desde = DameFecha(
            self.request.GET.get("campanya_fecha_desde_bactivo", "")
        )
        if fecha_desde:
            queryset = queryset.filter(campanya__fecha__gte=fecha_desde)
        fecha_hasta = DameFecha(
            self.request.GET.get("campanya_fecha_hasta_bactivo", "")
        )
        if fecha_hasta:
            queryset = queryset.filter(campanya__fecha__lte=fecha_hasta)
        precio_desde = self.request.GET.get("importe_desde_bactivo", "")
        cat = self.request.GET.getlist("categoria_bactivo", [])

        precio_desde = self.request.GET.get("importe_desde_bactivo", "")
        precio_hasta = self.request.GET.get("importe_hasta_bactivo", "")
        cat = self.request.GET.getlist("categoria_bactivo", [])

        queryset = queryset.annotate(
            valor_maximo_precio=Greatest(
                Coalesce("precio", Value(0.0), output_field=FloatField()),
                Coalesce("importe_deuda", Value(0.0), output_field=FloatField()),
                output_field=FloatField(),
            )
        )

        if precio_desde:
            queryset = queryset.filter(
                Q(tipo="NPL", valor_maximo_precio__gte=float(precio_desde))
                | Q(~Q(tipo="NPL"), precio__gte=float(precio_desde))
            )

        if precio_hasta:
            queryset = queryset.filter(
                Q(tipo="NPL", valor_maximo_precio__lte=float(precio_hasta))
                | Q(~Q(tipo="NPL"), precio__lte=float(precio_hasta))
            )

        disponible = self.request.GET.get("o_disponibles", "")
        if disponible == "Si":
            queryset = queryset.filter(activo__no_disponible=None)
        elif disponible == "No":
            queryset = queryset.exclude(activo__no_disponible=None)

        m2desde = self.request.GET.get("importe_desde_m2", "")
        if m2desde:
            queryset = queryset.filter(activo__m2__gte=m2desde)
        m2hasta = self.request.GET.get("importe_hasta_m2", "")
        if m2hasta:
            queryset = queryset.filter(activo__m2__lte=m2hasta)

        mostrar_reciente = self.request.GET.get("c_mostrar_reciente", "")
        if mostrar_reciente:
            subquery_fecha_maxima = (
                CampanyaLinea.objects.filter(activo=OuterRef("activo"))
                .order_by("-campanya__fecha")
                .values("campanya__fecha")[:1]
            )
            queryset = queryset.filter(campanya__fecha=Subquery(subquery_fecha_maxima))

        queryset = queryset.annotate(
            tipo_orden=Case(
                When(tipo="NPL", then=Value(0)),
                When(tipo="CDR", then=Value(1)),
                When(tipo="REO", then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            ),
            es_precio_consultar=Case(
                When(
                    tipo="NPL",
                    then=Case(
                        When(
                            (Q(precio__isnull=True) | Q(precio=0))
                            & (Q(importe_deuda__isnull=True) | Q(importe_deuda=0)),
                            then=Value(True),
                        ),
                        default=Value(False),
                    ),
                ),
                default=Case(
                    When(Q(precio__isnull=True) | Q(precio=0), then=Value(True)),
                    default=Value(False),
                ),
                output_field=BooleanField(),
            ),
        ).order_by(
            "tipo_orden",
            "valor_maximo_precio",
            "activo__poblacion__provincia__nombre",
            "activo__poblacion__nombre",
            "activo__tipologia__grupo__orden",
            "activo__tipologia__subgrupo__orden",
            "pk",
        )

        return queryset


class OfertaListView(LoginRequiredMixin, TienePermisosMixin, generic.ListView):
    model = PropuestaLinea
    context_object_name = "ofertas"
    template_name = "oferta_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        object_id = self.kwargs.get("pk")

        try:
            propuesta = Propuesta.objects.get(pk=object_id)
        except Propuesta.DoesNotExist:
            propuesta = None
        propuesta_lineas = (
            self.get_queryset().filter(propuesta=propuesta) if propuesta else []
        )
        context["propuestapendiente"] = True
        context["ofertas"] = propuesta_lineas

        id_campanya = self.request.GET.get("campanya")
        context["micampanya_id"] = id_campanya

        context["miclasif"] = self.request.GET.get("clasif", "")
        context["miprovincia_id"] = self.request.GET.get("provincia", "")
        try:
            context["miprovincia_nombre"] = Provincia.objects.get(
                pk=context["miprovincia_id"]
            )
        except:
            context["miprovincia_nombre"] = ""

        context["migrupo_id"] = self.request.GET.get("grupo", "")
        try:
            context["migrupo_nombre"] = GrupoTipologia.objects.get(
                pk=context["migrupo_id"]
            )
        except:
            context["migrupo_nombre"] = ""

        context["mitipo_id"] = self.request.GET.get("tipo", "")
        try:
            context["mitipo_nombre"] = Tipologia.objects.get(pk=context["mitipo_id"])
        except:
            context["mitipo_nombre"] = ""

        context["mipoblacion_id"] = self.request.GET.get("poblacion", "")
        try:
            context["mipoblacion_nombre"] = Poblacion.objects.get(
                pk=context["mipoblacion_id"]
            )
        except:
            context["mipoblacion_nombre"] = ""

        context["clasificaciones"] = ["NPL", "CDR", "REO"]

        context["clientes"] = Cliente.objects.filter(anulado_en=None).order_by(
            "nombre_completo"
        )

        provincias = Provincia.objects.filter(
            pk__in=propuesta_lineas.values_list(
                "campanya_linea__activo__poblacion__provincia__pk", flat=True
            )
        ).order_by("nombre")
        context["provincias"] = provincias

        tipos = Tipologia.objects.filter(
            pk__in=propuesta_lineas.values_list(
                "campanya_linea__activo__tipologia__pk", flat=True
            )
        )
        context["grupos"] = GrupoTipologia.objects.filter(
            pk__in=tipos.values_list("grupo__pk")
        ).order_by("orden")

        tipos = tipos.order_by("nombre")
        context["tipos"] = tipos

        poblaciones = Poblacion.objects.filter(
            pk__in=propuesta_lineas.values_list(
                "campanya_linea__activo__poblacion__pk", flat=True
            )
        ).order_by("nombre")
        context["poblaciones"] = poblaciones

        cantidad_total = propuesta_lineas.count()
        context["cantidad_total"] = cantidad_total

        context["campanya_id"] = id_campanya
        if id_campanya:
            campanya = Campanya.objects.get(pk=id_campanya)
            context["campanya"] = campanya
            if campanya.estado == "I":
                context["selected_iniciar"] = "checked"
            elif campanya.estado == "O":
                context["selected_ofrecer"] = "checked"
            elif campanya.estado == "A":
                context["selected_trabajar"] = "checked"
            else:
                context["selected_finalizar"] = "checked"

        context["nombreCompletoCliente"] = propuesta.cliente
        context["responsable"] = propuesta.cliente.responsable

        return context

    def get_queryset(self):
        object_id = self.kwargs.get("pk")

        try:
            propuesta = Propuesta.objects.get(pk=object_id)
        except Propuesta.DoesNotExist:
            propuesta = None
            return PropuestaLinea.objects.none()

        queryset = PropuestaLinea.objects.filter(propuesta=propuesta)

        usuario = self.request.GET.get("nombre_completo", "")
        if usuario:
            queryset = queryset.filter(propuesta__cliente=usuario)

        responsable = self.request.GET.get("responsable", "")

        if responsable:
            queryset = queryset.filter(
                propuesta__cliente__responsable_nombre=responsable
            )

        clasif = self.request.GET.get("clasif", "")
        if clasif:
            queryset = queryset.filter(campanya_linea__tipo=clasif)

        grupo = self.request.GET.get("grupo", "")
        if grupo:
            queryset = queryset.filter(
                campanya_linea__activo__tipologia__grupo__pk=grupo
            )

        tipologia = self.request.GET.get("tipo", "")
        if tipologia and tipologia != "all":
            queryset = queryset.filter(campanya_linea__activo__tipologia__id=tipologia)

        provincia_id = self.request.GET.get("provincia", "")
        if provincia_id:
            queryset = queryset.filter(
                campanya_linea__activo__poblacion__provincia__id=provincia_id
            )

        poblacion_id = self.request.GET.get("poblacion", "")
        if poblacion_id:
            queryset = queryset.filter(
                campanya_linea__activo__poblacion__id=poblacion_id
            )

        return queryset


class ActivoApiView(LoginRequiredMixin, TienePermisosMixin, View):
    def get(self, request, *args, **kwargs):
        accion = request.GET.get("accion")
        error = False
        literror = ""
        if (
            accion == "imprimir_activos"
            or accion == "obtener_catastro"
            or accion == "mapa_activos"
            or accion == "imprimir_estado"
        ):
            texto_filtro = ""
            empresa = Empresa.objects.all().first()
            campanya = request.GET.get("campanya", "")
            lineas_id = request.GET.get("lineas_id", "")

            if campanya:
                campanya = Campanya.objects.get(pk=campanya)
                if lineas_id:
                    ids = [int(x) for x in lineas_id.split(",") if x.strip().isdigit()]
                    lineas = CampanyaLinea.objects.filter(id__in=ids)
                else:
                    lineas = CampanyaLinea.objects.filter(campanya=campanya)
            else:
                campanya = Campanya.objects.filter(anulado_por=None)
                proveedor_id = request.GET.get("proveedor", "")
                if proveedor_id:
                    campanya = campanya.filter(proveedor_id__in=proveedor_id.split(","))
                cartera_id = request.GET.get("cartera", "")
                if cartera_id:
                    campanya = campanya.filter(cartera_id__in=cartera_id.split(","))

                fecha_desde = DameFecha(request.GET.get("fecha_desde", ""))
                if fecha_desde:
                    campanya = campanya.filter(fecha__gte=fecha_desde)
                fecha_hasta = DameFecha(request.GET.get("fecha_hasta", ""))
                if fecha_hasta:
                    campanya = campanya.filter(fecha__lte=fecha_hasta)

                if lineas_id:
                    ids = [int(x) for x in lineas_id.split(",") if x.strip().isdigit()]
                    lineas = CampanyaLinea.objects.filter(id__in=ids)
                else:
                    lineas = CampanyaLinea.objects.filter(
                        campanya__in=campanya.values_list("pk", flat=True)
                    )

            mitipo = None
            migrupo = None
            mipoblacion = None
            miprovincia = None
            miclasif = None
            miclasif = request.GET.get("clasif", "")
            if miclasif:
                miclasif_ = miclasif.split(",")
                lineas = lineas.filter(tipo__in=miclasif_)

                misclasif = ",".join(miclasif_)
                texto_filtro += f" Clasificación: {misclasif}"

            grupo = request.GET.get("grupo", "")
            if grupo:
                grupo_ = grupo.split(",")
                lineas = lineas.filter(activo__tipologia__grupo__pk__in=grupo_)
                migrupo = GrupoTipologia.objects.filter(pk__in=grupo_)

                misgrupos = ",".join(migrupo.values_list("nombre", flat=True))
                texto_filtro += f" Grupos: {misgrupos}"

            tipo = request.GET.get("tipo", "")
            if tipo:
                tipo = tipo.split(",")
                lineas = lineas.filter(activo__tipologia__subgrupo__pk__in=tipo)
                mitipo = Tipologia.objects.filter(pk__in=tipo)
                mistipos = ",".join(mitipo.values_list("nombre", flat=True))
                texto_filtro += f" Tipo: {mistipos}"

            poblacion = request.GET.get("poblacion", "")
            if poblacion:
                lineas = lineas.filter(activo__poblacion__pk__in=poblacion.split(","))
                mipoblacion = Poblacion.objects.filter(pk__in=poblacion.split(","))
                mispoblaciones = ",".join(mipoblacion.values_list("nombre", flat=True))
                texto_filtro += f" Poblaciones: {mispoblaciones}"

            provincia = request.GET.get("provincia", "")
            if provincia:
                lineas = lineas.filter(
                    activo__poblacion__provincia__pk__in=provincia.split(",")
                )
                miprovincia = Provincia.objects.filter(pk__in=provincia.split(","))
                misprovincias = ",".join(miprovincia.values_list("nombre", flat=True))
                texto_filtro += f" Provincias: {misprovincias}"
            calle = self.request.GET.get("calle", "")

            if calle:
                lineas = lineas.filter(
                    Q(activo__catastro_localizacion__icontains=calle)
                    | Q(activo__direccion__icontains=calle)
                )
            idprov = self.request.GET.get("idprov", "")
            if idprov:
                ids = [x.strip() for x in idprov.split(",") if x.strip()]
                lineas = lineas.filter(activo__id_proveedor__in=ids)
            refue = self.request.GET.get("refue", "")

            if refue:
                lineas = lineas.filter(activo__ref_ue=refue)
            refcat = self.request.GET.get("refcat", "")
            if refcat:
                cat = [x.strip() for x in refcat.split(",") if x.strip()]
                lineas = lineas.filter(activo__ref_catastral__in=cat)

            valor_mercado = request.GET.get("valor_mercado", "")
            if valor_mercado:
                lineas = lineas.filter(campanya_linea__valor_mercado=valor_mercado)
            valor_referencia = request.GET.get("valor_referencia", "")
            if valor_referencia:
                lineas = lineas.filter(
                    campanya_linea__valor_referencia=valor_referencia
                )
            valor_subasta = request.GET.get("valor_subasta", "")
            if valor_subasta:
                lineas = lineas.filter(campanya_linea__valor_subasta=valor_subasta)
            cat = request.GET.get("clasif", "")
            cat = cat.split(",") if cat else []
            precio_desde = request.GET.get("precio_desde", "")
            precio_hasta = request.GET.get("precio_hasta", "")

            lineas = lineas.annotate(
                valor_maximo_precio=Greatest(
                    Coalesce("precio", Value(0), output_field=FloatField()),
                    Coalesce("importe_deuda", Value(0), output_field=FloatField()),
                    output_field=FloatField(),
                )
            )

            if precio_desde:
                lineas = lineas.filter(
                    Q(tipo="NPL", valor_maximo_precio__gte=float(precio_desde))
                    | Q(~Q(tipo="NPL"), precio__gte=float(precio_desde))
                )

            if precio_hasta:
                lineas = lineas.filter(
                    Q(tipo="NPL", valor_maximo_precio__lte=float(precio_hasta))
                    | Q(~Q(tipo="NPL"), precio__lte=float(precio_hasta))
                )

            m2desde = request.GET.get("importe_desde_m2", "")
            if m2desde:
                lineas = lineas.filter(activo__m2__gte=m2desde)
            m2hasta = request.GET.get("importe_hasta_m2", "")
            if m2hasta:
                lineas = lineas.filter(activo__m2__lte=m2hasta)
            disponible = request.GET.get("disponible")
            if disponible == "No":
                lineas = lineas.exclude(activo__no_disponible=None)
            elif disponible == "Si":
                lineas = lineas.filter(activo__no_disponible=None)

            mostrar_reciente = (
                self.request.GET.get("mostrar_reciente", "false") == "true"
            )
            if mostrar_reciente:
                subquery_fecha_maxima = (
                    CampanyaLinea.objects.filter(activo=OuterRef("activo"))
                    .order_by("-campanya__fecha")
                    .values("campanya__fecha")[:1]
                )
                lineas = lineas.filter(campanya__fecha=Subquery(subquery_fecha_maxima))

            estado = request.GET.get("estado")
            if estado == "Ofrecer":
                activos = activos.filter(seleccionado=True)
            lineas = lineas.order_by(
                "activo__poblacion__provincia__nombre",
                "activo__tipologia__nombre",
                "activo__poblacion__nombre",
                "activo__direccion",
            )
            observaciones = request.GET.get("observaciones", "")
            if observaciones:
                lineas = lineas.filter(observaciones__icontains=observaciones)
            radio_km = request.GET.get("radio_km")
            poblacion_id = request.GET.get("poblacion")
            ids = poblacion_id.split(",") if poblacion_id else []
            if radio_km and len(ids) == 1:
                poblacion = Poblacion.objects.get(pk=ids[0])
                lat_centro = poblacion.latitud
                lon_centro = poblacion.longitud
                try:
                    distancia_expr = ExpressionWrapper(
                        6371
                        * ACos(
                            Cos(Radians(Value(lat_centro)))
                            * Cos(Radians(F("activo__latitud")))
                            * Cos(
                                Radians(F("activo__longitud"))
                                - Radians(Value(lon_centro))
                            )
                            + Sin(Radians(Value(lat_centro)))
                            * Sin(Radians(F("activo__latitud")))
                        ),
                        output_field=FloatField(),
                    )
                    lineas = lineas.annotate(distancia=distancia_expr).filter(
                        distancia__lte=radio_km
                    )

                except Exception as e:
                    print(f"Error al aplicar filtro de distancia: {e}")

            lineas = lineas.annotate(
                tipo_orden=Case(
                    When(tipo="NPL", then=Value(0)),
                    When(tipo="CDR", then=Value(1)),
                    When(tipo="REO", then=Value(2)),
                    default=Value(3),
                    output_field=FloatField(),
                ),
                es_precio_consultar=Case(
                    When(
                        tipo="NPL",
                        then=Case(
                            When(
                                (Q(precio__isnull=True) | Q(precio=0))
                                & (Q(importe_deuda__isnull=True) | Q(importe_deuda=0)),
                                then=Value(True),
                            ),
                            default=Value(False),
                            output_field=BooleanField(),
                        ),
                    ),
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
            )
            lineas = lineas.order_by(
                "tipo_orden",
                "valor_maximo_precio",
                "activo__poblacion__provincia__nombre",
                "activo__tipologia__nombre",
                "activo__poblacion__nombre",
                "activo__direccion",
            )
            if accion == "imprimir_activos" or accion == "imprimir_estado":
                es_excel = request.GET.get("es_excel", "false") == "true"
                if es_excel:
                    nombrefichero = "fichero.xlsx"
                    GenerarListaActivosExcel(
                        empresa,
                        campanya,
                        lineas,
                        miclasif,
                        migrupo,
                        mitipo,
                        mipoblacion,
                        miprovincia,
                        estado,
                        nombrefichero,
                    )
                else:
                    nombrefichero = "fichero.pdf"

                    if accion == "imprimir_estado":
                        estado = request.GET.get("estado", "")
                        estados = request.GET.getlist("estados")
                        idealista = request.GET.get("idealista", "")
                        fotocasa_pro = request.GET.get("fotocasa_pro", "")
                        web_invest = request.GET.get("web_invest", "")
                        if estados:
                            lineas = lineas.filter(activo__estado_activo__in=estados)
                        elif estado:
                            lineas = lineas.filter(activo__estado_activo=estado)
                        if fotocasa_pro is True:
                            lineas = lineas.filter(activo__fotocasa_pro=True)
                        if idealista is True:
                            lineas = lineas.filter(activo__idealista=True)
                        if web_invest is True:
                            lineas = lineas.filter(activo__web_invest=True)
                        nombrefichero = "listado_estados.pdf"
                    if lineas.count() >= 1000:
                        rml_parte = ""

                        rml_total_story = ""
                        rml_stylesheet = ""
                        rml_template = """
                        <template pagesize="(29.7cm, 21cm)">
                            <pageTemplate id="principal">
                                <frame id='first' x1='7mm' y1='10mm' width='280mm' height='185mm'/>
                            </pageTemplate>
                        </template>
                        """

                        from PyPDF2 import PdfMerger
                        import tempfile
                        import uuid

                        pdf_paths = []
                        rml_stylesheet = ""
                        for i in range(0, lineas.count(), 1000):
                            ids_bloque = list(
                                lineas[i : i + 1000].values_list("id", flat=True)
                            )
                            lineas_parte = lineas.filter(id__in=ids_bloque)
                            proveedores = lineas_parte.values_list(
                                "campanya__proveedor", flat=True
                            ).distinct()

                            if accion == "imprimir_estado":
                                rml_parte = GenerarListadoEstados(
                                    empresa,
                                    campanya,
                                    lineas_parte,
                                    miclasif,
                                    migrupo,
                                    mitipo,
                                    mipoblacion,
                                    miprovincia,
                                    estado,
                                    nombrefichero,
                                    texto_filtro,
                                    proveedores,
                                    numLinea=i,
                                    retornar_partes_rml=True,
                                )
                            else:

                                rml_parte = GenerarListaActivosConCatastroRML(
                                    empresa,
                                    campanya,
                                    lineas_parte,
                                    miclasif,
                                    migrupo,
                                    mitipo,
                                    mipoblacion,
                                    miprovincia,
                                    estado,
                                    nombrefichero,
                                    texto_filtro,
                                    proveedores,
                                    numLinea=i,
                                    retornar_partes_rml=True,
                                )

                            if not rml_parte:
                                logger.error(
                                    f"No se generó RML correctamente para bloque {i}-{i+1000}"
                                )
                                continue

                            rml_final = f"""<?xml version='1.0' encoding='UTF-8'?>
                                <document filename='archivo.pdf'>
                                {rml_parte["rml_template"]}
                                {rml_parte["rml_stylesheet"]}
                                <story>
                                {rml_parte["rml_story"].replace("<story>", "").replace("</story>", "").strip()}
                                </story>
                                </document>
                            """

                            temp_rml_path = tempfile.NamedTemporaryFile(
                                delete=False, suffix=".rml"
                            ).name
                            with open(temp_rml_path, "w", encoding="utf-8") as f:
                                f.write(rml_final)

                            temp_pdf_path = tempfile.NamedTemporaryFile(
                                delete=False, suffix=".pdf"
                            ).name
                            with open(temp_rml_path, "rb") as rml_file:
                                rml2pdf.go(rml_file, outputFileName=temp_pdf_path)

                            pdf_paths.append(temp_pdf_path)
                            os.unlink(temp_rml_path)

                        if not pdf_paths:
                            return JsonResponse(
                                {
                                    "status": "error",
                                    "message": "No se pudo generar ningún bloque de PDF.",
                                    "nombrefichero": nombrefichero,
                                }
                            )

                        output = os.path.join(settings.MEDIA_ROOT, nombrefichero)
                        merger = PdfMerger()
                        for path in pdf_paths:
                            merger.append(path)
                        merger.write(output)
                        merger.close()

                        for path in pdf_paths:
                            os.unlink(path)

                        return JsonResponse(
                            {
                                "status": "success",
                                "message": "PDF generado correctamente en bloques.",
                                "nombrefichero": nombrefichero,
                            }
                        )

                    else:
                        if accion == "imprimir_estado":
                            rml_cadena = GenerarListadoEstados(
                                empresa,
                                campanya,
                                lineas,
                                miclasif,
                                migrupo,
                                mitipo,
                                mipoblacion,
                                miprovincia,
                                estado,
                                nombrefichero,
                                texto_filtro,
                                idealista=request.GET.get("idealista", ""),
                                fotocasa_pro=request.GET.get("fotocasa_pro", ""),
                                web_invest=request.GET.get("web_invest", ""),
                            )
                        else:
                            rml_cadena = GenerarListaActivosConCatastroRML(
                                empresa,
                                campanya,
                                lineas,
                                miclasif,
                                migrupo,
                                mitipo,
                                mipoblacion,
                                miprovincia,
                                estado,
                                nombrefichero,
                                texto_filtro,
                            )
                        if not rml_cadena:
                            logger.error(
                                f"No se generó RML correctamente para {nombrefichero}"
                            )
                            return JsonResponse(
                                {
                                    "status": "error",
                                    "message": "No se pudo generar el documento PDF.",
                                    "nombrefichero": nombrefichero,
                                }
                            )
                        try:

                            file_path = os.path.join(settings.MEDIA_ROOT, "archivo.rml")
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
                                f.write(rml_cadena)

                            output = os.path.join(settings.MEDIA_ROOT, nombrefichero)
                            with open(file_path, "rb") as rml_file:
                                rml2pdf.go(rml_file, outputFileName=output)

                            del rml_cadena
                            gc.collect()

                        except Exception as e:
                            logger.exception("Error al generar el documento PDF")
                            return JsonResponse(
                                {
                                    "status": "error",
                                    "message": f"Error al generar el documento: {str(e)}",
                                    "fase": "FASE 99 - Error en generación de PDF",
                                    "nombrefichero": nombrefichero,
                                }
                            )

                return JsonResponse(
                    {
                        "status": "ok",
                        "message": "Archivo generado correctamente.",
                        "nombrefichero": nombrefichero,
                    }
                )

            elif accion == "obtener_catastro":
                for linea in lineas:
                    linea.activo.ActivoLocalizar()
                    linea.activo.ActivoGuardaCatastro()
                return JsonResponse({"status": "error", "message": "Invalid request"})
            elif accion == "mapa_activos":
                qs = lineas
                vistos = set()
                data = []
                for l in lineas:
                    a = l.activo
                    if a.latitud and a.longitud and a.id not in vistos:
                        data.append(
                            {
                                "id": a.id,
                                "direccion": a.catastro_localizacion or a.direccion,
                                "poblacion": a.poblacion.nombre,
                                "lat": a.latitud,
                                "lon": a.longitud,
                                "linea": l.id,
                            }
                        )
                        vistos.add(a.id)
                return JsonResponse({"activos": data})

        elif accion == "cliente":
            id_activo = request.GET["id"]
            estado = request.GET["estado"]
            oferta = PropuestaLinea.objects.filter(campanya_linea__activo=id_activo)
            if request.user.cliente:
                oferta = oferta.filter(propuesta__cliente=request.user.cliente)
            oferta = oferta.first()
            if not oferta:
                error = True
                literror = "Hay un fallo en la oferta"
            else:
                if estado == "interesa":
                    es_respuesta_cliente = True
                    PropuestaLineaEstado.objects.create(linea=oferta, estado="I")
                    oferta.estado = "I"
                    hay_correo = True
                elif estado == "nointeresa":
                    es_respuesta_cliente = True
                    PropuestaLineaEstado.objects.create(linea=oferta, estado="N")
                    oferta.estado = "N"
                    hay_correo = True
                elif estado == "confirma":  
                    es_respuesta_cliente = True
                    PropuestaLineaEstado.objects.create(linea=oferta, estado="R")
                    oferta.estado = "R"
                    hay_correo = True
                elif estado == "aceptarnointeresa":
                    es_respuesta_cliente = False
                    estado_oferta = (
                        PropuestaLineaEstado.objects.filter(linea=oferta, estado="N")
                        .order_by("pk")
                        .last()
                    )
                    estado_oferta.confirmado = datetime.now()
                    estado_oferta.confirmado_por = request.user
                    estado_oferta.save()
                    oferta.estado = "NA"
                    hay_correo = False
                elif estado == "preparado":
                    es_respuesta_cliente = False
                    PropuestaLineaEstado.objects.create(linea=oferta, estado="P")
                    oferta.estado = "P"
                    hay_correo = True
                oferta.save()
                if hay_correo:
                    oferta.EnviaCorreo()
                if es_respuesta_cliente:
                    texto_comunicacion = (
                        "<div>Comunicada su decisión a la empresa</div>"
                    )
                else:
                    if hay_correo:
                        texto_comunicacion = (
                            "<div>Comunicada su decisión al cliente</div>"
                        )
                    else:
                        texto_comunicacion = "<div>Ok</div>"
                return HttpResponse(texto_comunicacion)
        elif accion == "eliminar_imagen":
            id_activo = self.request.GET["id_activo"]
            id_imagen = self.request.GET["id_imagen"]
            imagen = ActivoImagen.objects.filter(
                activo__pk=id_activo, pk=id_imagen
            ).first()
            if imagen:
                imagen.delete()
            else:
                error = True
                literror = "No existe la imagen"
            return JsonResponse({"error": error, "literror": literror})
        elif accion == "ver_poblacion_activo":
            id_activo = self.request.GET["id_activo"]
            activo = Activo.objects.filter(pk=id_activo).first()
            if activo:
                return JsonResponse(
                    {
                        "poblacion": activo.poblacion.nombre,
                        "poblacion_id": activo.poblacion.id,
                    }
                )
        elif accion == "ver_tipologia_activo":
            id_activo = self.request.GET["id_activo"]
            activo = Activo.objects.filter(pk=id_activo).first()
            if activo:
                return JsonResponse(
                    {
                        "tipologia": activo.tipologia.nombre,
                        "tipologia_id": activo.tipologia.id,
                    }
                )
        elif accion == "modificar_poblacion_activo":
            error = False
            literror = ""
            idpoblacion_old = self.request.GET["id_poblacion_old"]
            idpoblacion_new = self.request.GET["id_poblacion_new"]
            poblacion_old = Poblacion.objects.filter(pk=idpoblacion_old).first()
            poblacion_new = Poblacion.objects.filter(pk=idpoblacion_new).first()
            if poblacion_old and poblacion_new:
                activos = Activo.objects.filter(poblacion=poblacion_old)
                for activo in activos:
                    activo.poblacion = poblacion_new
                    activo.save()
                Poblacion_Traduccion.objects.create(
                    nombre=poblacion_old.nombre, poblacion=poblacion_new
                )

                poblacion_old.delete()
            else:
                error = True
                literror = "Debe seleccionar una población"
            return JsonResponse({"error": error, "literror": literror})

        elif accion == "modificar_tipologia_activo":
            error = False
            literror = ""
            id_tipologia = self.request.GET["id_tipologia"]
            id_subgrupo = self.request.GET["id_subgrupo"]
            tipologia = Tipologia.objects.filter(
                pk=id_tipologia, grupo__es_varios=True
            ).first()
            subgrupo = SubGrupoTipologia.objects.filter(pk=id_subgrupo).first()
            if tipologia and subgrupo:
                tipologia.subgrupo = subgrupo
                tipologia.grupo = subgrupo.grupo
                tipologia.save()
            else:
                error = True
                literror = "Debe seleccionar una tipología y un tipo"
            return JsonResponse({"error": error, "literror": literror})

        return JsonResponse({"status": "error", "message": "Invalid request"})

    def post(self, request, *args, **kwargs):
        error = False
        literror = ""
        accion = request.POST.get("accion")
        if not accion:
            try:
                data = json.loads(request.body)
                accion = data.get("accion")
            except:
                accion = ""
        if accion == "editar":
            linea = data.get("linea")
            tipo = data.get("tipo")
            id_proveedor = data.get("id_proveedor")
            ref_ue = data.get("ref_ue")
            ref_catastral = data.get("ref_catastral")
            tipologia_nombre = data.get("tipologia")
            tipologia = data.get("subtipologia")
            direccion = data.get("direccion")
            cp = data.get("cp")
            poblacion_id = data.get("poblacion")
            try:
                poblacion = Poblacion.objects.get(pk=poblacion_id)
            except:
                problacion = None
            longitud = data.get("longitud")
            if not longitud:
                longitud = None
            latitud = data.get("latitud")
            if not latitud:
                latitud = None
            m2 = data.get("m2")
            if not m2:
                m2 = None
            fecha_construccion = data.get("fecha_construccion")
            num_habitaciones = data.get("num_habitaciones")
            num_banyos = data.get("num_banyos")
            precio_mercado = data.get("precio_mercado")
            importe_deuda = data.get("importe_deuda")
            valor_referencia = data.get("valor_referencia")
            estado_ocupacional = data.get("estado_ocupacional")
            estado_legal = data.get("estado_legal")
            observaciones = data.get("observaciones")
            disponible = data.get("disponible") == "true"
            judicializado = data.get("judicializado")
            deudor_localizado = data.get("deudor_localizado")
            deudor_ayuda = data.get("deudor_ayuda")
            valor_mercado = data.get("valor_mercado")
            valor_subasta = data.get("valor_subasta")
            valor_70 = data.get("valor_70")
            ultimo_hito = data.get("ultimo_hito")
            estado_activo = data.get("estado_activo")
            idealista = data.get("idealista")
            fotocasa_pro = data.get("fotocasa_pro")
            print(idealista)
            print(fotocasa_pro)
            web_invest = data.get("web_invest")
            print(web_invest)
            fecha_estudio_posicion = data.get("fecha_estudio_posicion") or now()
            comentarios = data.get("comentarios")
            respuesta_fondo = data.get("respuesta_fondo")
            if not m2:
                m2 = None
            if not fecha_construccion:
                fecha_construccion = None
            if not num_habitaciones:
                num_habitaciones = None
            if not num_banyos:
                num_banyos = None
            if not precio_mercado:
                precio_mercado = None
            if not importe_deuda:
                importe_deuda = None
            if not valor_referencia:
                valor_referencia = None
            clinea = CampanyaLinea.objects.get(pk=linea)
            clinea.tipo = tipo
            clinea.activo.id_proveedor = id_proveedor
            clinea.activo.ref_ue = ref_ue
            clinea.activo.ref_catastral = ref_catastral
            tipologia_obj = Tipologia.objects.filter(id=tipologia).first()
            subtipologia_obj = SubGrupoTipologia.objects.filter(
                id=tipologia_nombre
            ).first()
            clinea.activo.tipologia = tipologia_obj
            clinea.activo.tipologia.subgrupo = subtipologia_obj
            clinea.activo.direccion = direccion
            clinea.activo.cp = cp
            if poblacion:
                clinea.activo.poblacion = poblacion
            clinea.activo.longitud = longitud
            clinea.activo.latitud = latitud
            clinea.activo.m2 = m2
            clinea.activo.fecha_construccion = fecha_construccion
            clinea.activo.num_habitaciones = num_habitaciones
            clinea.activo.num_banyos = num_banyos
            clinea.precio = precio_mercado
            clinea.importe_deuda = importe_deuda
            clinea.valor_referencia = valor_referencia
            clinea.estado_ocupacional = estado_ocupacional
            clinea.estado_legal = estado_legal
            clinea.observaciones = observaciones
            clinea.disponible = disponible
            clinea.judicializado = judicializado
            clinea.deudor_localizado = deudor_localizado
            clinea.deudor_ayuda = deudor_ayuda
            clinea.valor_mercado = float(valor_mercado) if valor_mercado else 0
            clinea.valor_subasta = valor_subasta
            clinea.valor_mercado = valor_mercado
            clinea.valor_70 = float(valor_70) if valor_70 else 0
            clinea.activo.ultimo_hito = ultimo_hito
            clinea.activo.estado_activo = estado_activo
            print(estado_activo)
            if estado_activo == "reservado" or estado_activo == "publicado":
                print("dentro")
                clinea.activo.idealista = idealista
                clinea.activo.fotocasa_pro = fotocasa_pro
                clinea.activo.web_invest = web_invest
            elif estado_activo == "vendido":
                clinea.disponible = False
                clinea.activo.disponible = False
            clinea.activo.fecha_estudio_posicion = fecha_estudio_posicion
            clinea.activo.comentarios = comentarios
            clinea.activo.respuesta_fondo = respuesta_fondo

            try:
                clinea.save()
                clinea.activo.save()
            except Exception as e:
                error = True
                literror = f"Error al guardar la línea de la campaña: {e}"
            if not error:
                try:
                    clinea.activo.save()
                except Exception as e:
                    error = True
                    literror = f"Error al guardar el activo: {e}"
            if error:
                return JsonResponse({"status": "error", "message": literror})
            else:
                return JsonResponse({"status": "success"})

        elif accion == "crear":
            try:
                poblacion = (
                    Poblacion.objects.get(pk=data["poblacion"])
                    if data.get("poblacion")
                    else None
                )

                qs_activo = Activo.objects.filter(
                    id_proveedor=data.get("id_proveedor"),
                    ref_catastral=data.get("ref_catastral"),
                    campanyalinea__tipo=data.get("tipo"),
                    poblacion=poblacion,
                )
                if qs_activo.exists():
                    activo = qs_activo.first()
                    campanya_linea = CampanyaLinea.objects.filter(
                        activo_id=activo.pk
                    ).first()

                    return JsonResponse(
                        {"status": "exists", "id": campanya_linea.pk}, status=409
                    )

                tipologia = Tipologia.objects.filter(
                    nombre=data.get("tipologia")
                ).first()
                if not tipologia:
                    return JsonResponse(
                        {"status": "error", "message": "Tipología no encontrada"}
                    )
                cartera = Cartera.objects.filter(id=data.get("cartera")).first()
                campanya = Campanya.objects.create(
                    tipo=data.get("tipo"),
                    cartera=cartera,
                    proveedor=cartera.proveedor,
                    fecha=date.today(),
                    creado_por=request.user,
                )
                precio = Decimal(str(data.get("precio") or 0))
                deuda = Decimal(str(data.get("deuda") or 0))
                activo = Activo.objects.create(
                    id_proveedor=data.get("id_proveedor"),
                    ref_ue=data.get("ref_ue"),
                    ref_catastral=data.get("ref_catastral"),
                    tipologia=tipologia,
                    direccion=data.get("direccion"),
                    cp=data.get("cp"),
                    poblacion=poblacion,
                )
                campanyalinea = CampanyaLinea.objects.create(
                    campanya=campanya,
                    activo=activo,
                    tipo=data.get("tipo"),
                    creado_por=request.user,
                    precio=precio,
                    importe_deuda=deuda,
                    observaciones=data.get("observaciones", ""),
                )
                return JsonResponse({"status": "success", "id": campanyalinea.pk})
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})

        elif accion == "seleccionar_activo":
            id_activo = request.POST.get("id_activo")
            activo = get_object_or_404(Activo, id=id_activo)
            activo.seleccionado = not activo.seleccionado
            activo.save()
            return JsonResponse({"status": "success"})

        elif accion == "enviar_propuesta":
            clientes = data.get("clientes_id").split(",")
            lineas_id = data.get("lineas_id")
            for cliente_id in clientes:
                cliente = Cliente.objects.filter(pk=cliente_id).first()
                if cliente:
                    cliente.EnviarPropuesta(lineas_id, self.request.user)
            return JsonResponse({"status": "success"})

        elif accion == "aceptar_propuesta":
            lineas_id = data.get("propuestas_id").split(",")
            lineas = PropuestaLinea.objects.filter(pk__in=lineas_id)
            for linea in lineas:
                linea.estado = "I"
                linea.save()
                PropuestaLineaEstado.objects.create(linea=linea, estado="I")
            return JsonResponse({"status": "success"})

        elif accion == "pedir_info_servicers":
            empresa = Empresa.objects.all().first()
            lineas_id = data.get("lineas_id").split(",")
            lineas_propuestas = PropuestaLinea.objects.filter(pk__in=lineas_id)
            id_lineas_campanya = lineas_propuestas.values_list(
                "campanya_linea__pk", flat=True
            )
            lineas_campanya = CampanyaLinea.objects.filter(pk__in=id_lineas_campanya)
            id_proveedores = lineas_propuestas.values_list(
                "campanya_linea__campanya__proveedor__pk", flat=True
            )
            proveedores = Proveedor.objects.filter(pk__in=id_proveedores)
            for proveedor in proveedores:
                for tipo in ["NPL", "CDR", "REO"]:
                    contacto = Contacto.objects.filter(proveedor=proveedor)
                    if tipo == "NPL":
                        contacto = contacto.filter(NPL=True)
                    elif tipo == "CDR":
                        contacto = contacto.filter(CDR=True)
                    elif tipo == "REO":
                        contacto = contacto.filter(REO=True)
                    if contacto.first():
                        contacto = contacto.first()
                    else:
                        contacto = Contacto.objects.filter(proveedor=proveedor).last()

                    lineas = lineas_campanya.filter(
                        tipo=tipo, campanya__proveedor=proveedor
                    )
                    if lineas.first():
                        v_lineas = []
                        for linea in lineas:
                            v_lineas.append(linea.pk)
                        campanya_lineas = CampanyaLinea.objects.filter(pk__in=v_lineas)
                        parametros = {
                            "tipo": "peticion_informacion",
                            "tipologia": f"{tipo}",
                            "lineas": campanya_lineas,
                        }
                        EnviarCorreo(empresa, self.request.user, contacto, parametros)
                        for campanya_linea in campanya_lineas:
                            lineas_propuestas_ = lineas_propuestas.filter(
                                campanya_linea=campanya_linea
                            )
                            for linea_propuestas_ in lineas_propuestas_:
                                linea_propuestas_.estado = "E"
                                linea_propuestas_.save()
                                PropuestaLineaEstado.objects.create(
                                    linea=linea_propuestas_, estado="E"
                                )
            return JsonResponse({"status": "success"})
        elif accion == "enviar_info_clientes":
            empresa = Empresa.objects.all().first()
            lineas_id = data.get("lineas_id").split(",")
            lineas_propuestas = PropuestaLinea.objects.filter(pk__in=lineas_id)
            id_clientes = lineas_propuestas.values_list("propuesta__cliente__pk")
            clientes = Cliente.objects.filter(pk__in=id_clientes)
            for cliente in clientes:
                lineas = lineas_propuestas.filter(propuesta__cliente=cliente)
                parametros = {
                    "tipo": "enviar_info_clientes",
                    "cliente": cliente,
                    "lineas": lineas,
                }
                EnviarCorreo(empresa, self.request.user, cliente, parametros)
                for linea in lineas:
                    linea.estado = "P"
                    linea.save()
                    PropuestaLineaEstado.objects.create(linea=linea, estado="P")
            return JsonResponse({"status": "success"})

        elif accion == "NotaSimple":
            activo = Activo.objects.get(pk=self.request.POST["id_activo"])
            fichero = self.request.FILES.get("inputNotaSimple")
            ActivoDocumento.objects.create(activo=activo, documento=fichero, tipo="0")
            return JsonResponse({"status": "success"})
        elif accion == "Catastro":
            activo = Activo.objects.get(pk=self.request.POST["id_activo"])
            fichero = self.request.FILES.get("inputCatastro")
            ActivoDocumento.objects.create(activo=activo, documento=fichero, tipo="1")
            return JsonResponse({"status": "success"})
        elif accion == "Tasacion":
            activo = Activo.objects.get(pk=self.request.POST["id_activo"])
            fichero = self.request.FILES.get("inputTasacion")
            ActivoDocumento.objects.create(activo=activo, documento=fichero, tipo="2")
            return JsonResponse({"status": "success"})
        elif accion == "Prestamo":
            activo = Activo.objects.get(pk=self.request.POST["id_activo"])
            fichero = self.request.FILES.get("inputPrestamo")
            ActivoDocumento.objects.create(activo=activo, documento=fichero, tipo="3")
            return JsonResponse({"status": "success"})
        elif accion == "Judicial":
            activo = Activo.objects.get(pk=self.request.POST["id_activo"])
            fichero = self.request.FILES.get("inputJudicial")
            ActivoDocumento.objects.create(activo=activo, documento=fichero, tipo="4")
            return JsonResponse({"status": "success"})
        elif accion == "Deuda":
            activo = Activo.objects.get(pk=self.request.POST["id_activo"])
            fichero = self.request.FILES.get("inputDeuda")
            ActivoDocumento.objects.create(activo=activo, documento=fichero, tipo="5")
            return JsonResponse({"status": "success"})
        elif accion == "Doc":
            activo = Activo.objects.get(pk=self.request.POST["id_activo"])
            fichero = self.request.FILES.get("inputDoc")
            ActivoDocumento.objects.create(activo=activo, documento=fichero, tipo="V")
            return JsonResponse({"status": "success"})
        elif accion == "Imagenes":
            activo = Activo.objects.get(pk=self.request.POST["id_activo"])
            imagenes = self.request.FILES.getlist("inputImagenes")
            for imagen in imagenes:
                ActivoImagen.objects.create(activo=activo, imagen=imagen)
            return JsonResponse({"status": "success"})
        else:
            if "cod_activo" in self.request.POST:
                activo = Activo.objects.get(pk=self.request.POST["cod_activo"])
                fichero = self.request.FILES.get("fichero")
                ActivoImagen.objects.create(activo=activo, imagen=fichero)
                return JsonResponse({"status": "success"})

        return JsonResponse({"status": "error", "message": "Invalid request"})


class Linea_Detalle(LoginRequiredMixin, TienePermisosMixin, DetailView):
    model = CampanyaLinea

    def get_template_names(self):
        if self.request.user.cliente:
            return "linea_detalle_cliente.html"

        else:
            return "linea_detalle.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = Empresa.objects.all().first()
        objeto = self.get_object()
        if not objeto.activo.longitud:
            objeto.activo.ActivoLocalizar()
        if not objeto.activo.catastro:
            objeto.activo.ActivoGuardaCatastro()
        context["objeto"] = objeto
        context["imagenes"] = objeto.activo.DameImagenes()
        context["imagen1"] = objeto.activo.DameImagen()
        return context


class Activo_Detalle(LoginRequiredMixin, TienePermisosMixin, DetailView):
    model = Activo

    def get_template_names(self):
        if self.request.user.cliente:
            return ["activo_detalle_cliente.html"]
        else:
            return ["activo_detalle.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = Empresa.objects.all().first()
        objeto = self.get_object()
        if not objeto.longitud:
            objeto.ActivoLocalizar()
        context["objeto"] = objeto
        context["imagenes"] = objeto.DameImagenes()
        context["imagen1"] = objeto.DameImagen()
        return context


class Activo_DetalleCliente(LoginRequiredMixin, TienePermisosMixin, DetailView):
    model = Activo

    def get_template_names(self):
        return ["activo_detalle_cliente.html"]

    def capture_google_maps_screenshot(self, url):
        """
        Captura un screenshot de Google Maps usando Chromium y Selenium.
        Si hay reCAPTCHA y no se supera, no hace la captura.
        """
        options = Options()
        if platform.system() == "Linux":
            options.binary_location = "/usr/lib/chromium/chromium"
            service = Service("/home/crmgrupomss/bin/chromedriver")
        else:
            options.binary_location = "C:\\chrome-win\\chrome.exe"
            service = Service("C:\\chrome-win\\chromedriver.exe")

        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_window_size(1920, 1420)
            driver.get(url)
            time.sleep(2)

            try:
                accept_button = driver.find_element(
                    "xpath", "//button[.='Aceptar todo']"
                )
                accept_button.click()
                time.sleep(1)
            except NoSuchElementException:
                pass

            try:
                iframe = driver.find_element(
                    By.CSS_SELECTOR, "iframe[src*='recaptcha']"
                )
                driver.switch_to.frame(iframe)
                checkbox = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox")
                checkbox.click()
                time.sleep(2)
                driver.switch_to.default_content()

                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for f in iframes:
                    src = f.get_attribute("src")
                    if "bframe" in src:
                        print("reCAPTCHA con imágenes detectado. Abortando captura.")
                        return None

                print("reCAPTCHA clicado sin desafío adicional.")

            except NoSuchElementException:
                print("No se encontró reCAPTCHA, se continúa.")
            except Exception as e:
                print("Error al interactuar con reCAPTCHA:", e)
                return None

            screenshot_dir = os.path.join(settings.MEDIA_ROOT, "maps_screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            filename = f"map_{int(time.time())}.png"
            full_path = os.path.join(screenshot_dir, filename)

            if driver.save_screenshot(full_path):
                return full_path
            else:
                print("No se pudo guardar el screenshot.")
                return None

        except Exception as e:
            print(f"Error al capturar screenshot: {e}")
            return None

        finally:
            if "driver" in locals():
                driver.quit()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = Empresa.objects.first()
        objeto = self.get_object()

        if not objeto.longitud:
            objeto.ActivoLocalizar()

        context["objeto"] = objeto
        context["imagenes"] = objeto.DameImagenes()

        if context["imagenes"].count() == 0:
            maps_url = self.object.DameURLGoogleMaps()
            ruta_absoluta = self.capture_google_maps_screenshot(maps_url)

            if ruta_absoluta and os.path.exists(ruta_absoluta):
                with open(ruta_absoluta, "rb") as f:
                    nombre_archivo = os.path.basename(ruta_absoluta)
                    django_file = File(f, name=nombre_archivo)
                    ActivoImagen.objects.create(activo=self.object, imagen=django_file)

        context["imagenes"] = objeto.DameImagenes()
        context["imagen1"] = objeto.DameImagen()
        return context


class ActivoCrearView(LoginRequiredMixin, TienePermisosMixin, CreateView):
    model = Activo
    form_class = ActivoForm
    template_name = "crearactivo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["linea"] = None
        context["tipologias"] = SubGrupoTipologia.objects.all()
        context["provincias"] = Provincia.objects.all()
        context["carteras"] = Cartera.objects.filter(anulado_por__isnull=True)
        return context

    def get_success_url(self):
        return reverse("pantallacampanya")


class Activo_Editar(LoginRequiredMixin, TienePermisosMixin, UpdateView):
    model = Activo
    template_name = "activo_form.html"
    form_class = ActivoForm

    def get_success_url(self):
        referer = self.request.META.get("HTTP_REFERER")
        if referer:
            if "/campanya/" in referer:
                return reverse(
                    "detallecampanya", kwargs={"pk": self.object.campanya.pk}
                )
            else:
                return referer
        else:
            return reverse("pantallacampanya")


from collections import defaultdict


class Linea_Edito(LoginRequiredMixin, TienePermisosMixin, TemplateView):
    template_name = "linea_edito.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        linea = CampanyaLinea.objects.get(pk=self.kwargs["pk"])
        context["linea"] = linea
        context["activo"] = linea.activo
        context["provincias"] = Provincia.objects.all().order_by("nombre")
        context["poblaciones"] = Poblacion.objects.all().order_by("nombre")
        context["subtipologias"] = SubGrupoTipologia.objects.order_by(
            "nombre"
        ).distinct("nombre")

        context["tipologias"] = Tipologia.objects.filter(
            subgrupo_id=linea.activo.tipologia.subgrupo.id
        ).order_by("nombre")

        tipologias_por_subgrupo = defaultdict(list)
        for t in Tipologia.objects.all():
            tipologias_por_subgrupo[t.subgrupo_id].append(
                {"id": t.id, "nombre": t.nombre}
            )

        context["tipologias_por_subgrupo"] = dict(tipologias_por_subgrupo)
        return context


class PropuestaListadoView(LoginRequiredMixin, TienePermisosMixin, generic.ListView):
    model = Propuesta
    context_object_name = "propuestas"
    template_name = "propuesta_listado.html"

    def get_queryset(self):
        usuario = self.request.user
        if self.request.GET.get("cliente"):
            cliente = self.request.GET.get("cliente", "")
        else:
            cliente = self.request.user.cliente
        print(cliente)
        queryset = Propuesta.objects.filter(anulado_por=None, cliente=cliente)

        if hasattr(usuario, "cliente"):
            queryset = queryset.filter(cliente=cliente)

        tipo = self.request.GET.get("tipo")
        if tipo:
            tipo = tipo.strip("'\"")
            estados = [t.strip() for t in tipo.split(",")]
            queryset = queryset.filter(propuestalinea__estado__in=estados).distinct()

        return queryset.order_by("-creado_por")


class OfertaTemplateView(LoginRequiredMixin, TienePermisosMixin, TemplateView):
    template_name = "oferta_listar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["responsables"] = Responsable.objects.filter(anulado_por=None).order_by(
            "nombre"
        )
        id_clientes = Propuesta.objects.filter(anulado_por=None).values_list(
            "cliente__pk"
        )
        context["clientes"] = Cliente.objects.filter(pk__in=id_clientes).order_by(
            "nombre"
        )
        return context


class OfertaApiView(LoginRequiredMixin, TienePermisosMixin, View):
    def get(self, request, *args, **kwargs):
        accion = request.GET.get("accion")
        error = False
        literror = ""
        context_dict = {}
        usuario = self.request.user
        if accion == "dame_propuestas":
            tot_num_ofertas = 0
            tot_num_ofertas_nointeresado = 0
            tot_num_ofertas_interesado = 0
            tot_num_ofertas_esperando = 0
            tot_num_ofertas_preparado = 0
            tot_num_ofertas_reservado = 0
            tot_num_ofertas_noconcretado = 0
            tot_num_ofertas_vendidos = 0

            if not self.request.user.cliente:
                id_clientes = Propuesta.objects.filter(anulado_por=None).values_list(
                    "cliente__pk", flat=True
                )
                clientes = Cliente.objects.filter(
                    pk__in=id_clientes, anulado_por=None
                ).order_by("nombre", "apellidos", "nombre_completo")
            else:
                clientes = Cliente.objects.filter(
                    pk=self.request.user.cliente.pk
                ).order_by("nombre", "apellidos", "nombre_completo")

            html = []
            for cliente in clientes:
                propuestas = Propuesta.objects.filter(cliente=cliente, anulado_por=None)
                cant_propuestas = propuestas.count()
                id_propuestas = propuestas.values_list("pk")

                ofertas_campanya = PropuestaLinea.objects.filter(
                    anulado_por=None, propuesta__pk__in=id_propuestas
                )
                num_ofertas = ofertas_campanya.count()
                num_ofertas_nointeresado = ofertas_campanya.filter(estado="N").count()
                num_ofertas_interesado = ofertas_campanya.filter(estado="I").count()
                num_ofertas_esperando = ofertas_campanya.filter(estado="E").count()
                num_ofertas_preparado = ofertas_campanya.filter(estado="P").count()
                num_ofertas_reservado = ofertas_campanya.filter(estado="R").count()
                num_ofertas_noconcretado = ofertas_campanya.filter(estado="X").count()
                num_ofertas_vendidos = ofertas_campanya.filter(estado="V").count()

                if cliente.responsable:
                    cliente_responsable_nombre = cliente.responsable.nombre
                else:
                    cliente_responsable_nombre = ""

                html.append(
                    f"""
                    <tr>
                        <td>{cliente_responsable_nombre}</td>
                        <td>{cliente.DameNombre()}</td>
                        <td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, \'Ofertas\', )"><button class='btn btn-secondary'>{cant_propuestas}</button></td>
                        <td class="text-center">{num_ofertas}</td>"""
                )

                if num_ofertas_interesado:
                    html.append(
                        f"""
                        <td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, \'I\')"><button class='btn btn-secondary'>{num_ofertas_interesado}</button></td>"""
                    )
                else:
                    html.append("""<td class="text-center"> - </td>""")

                if num_ofertas_esperando:
                    html.append(
                        f"""
                        <td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, \'E\')"><button class='btn btn-secondary'>{num_ofertas_esperando}</button></td>"""
                    )
                else:
                    html.append("""<td class="text-center"> - </td>""")

                if num_ofertas_preparado:
                    html.append(
                        f"""
                        <td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, \'P\')"><button class='btn btn-secondary'>{num_ofertas_preparado}</button></td>"""
                    )
                else:
                    html.append("""<td class="text-center"> - </td>""")

                if num_ofertas_reservado:
                    html.append(
                        f"""
                        <td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, \'R\')"><button class='btn btn-secondary'>{num_ofertas_reservado}</button></td>"""
                    )
                else:
                    html.append("""<td class="text-center"> - </td>""")

                if num_ofertas_noconcretado:
                    html.append(
                        f"""
                        <td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, \'X\')"><button class='btn btn-secondary'>{num_ofertas_noconcretado}</button></td>"""
                    )
                else:
                    html.append("""<td class="text-center"> - </td>""")

                if num_ofertas_vendidos:
                    html.append(
                        f"""
                        <td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, \'V\')"><button class='btn btn-secondary'>{num_ofertas_vendidos}</button></td>"""
                    )
                else:
                    html.append("""<td class="text-center"> - </td>""")

                html.append(
                    """
                        <td></td>
                    </tr>"""
                )

            context_dict = {
                "error": error,
                "literror": literror,
                "html": " ".join(html),
            }

        elif accion == "dame_propuestas_detalle":
            if self.request.user.cliente:
                cliente = self.request.user.cliente
            else:
                id_cliente = self.request.GET.get("cliente", "")
                if id_cliente:
                    cliente = Cliente.objects.get(pk=id_cliente)
                else:
                    cliente = None

            estado = self.request.GET.get("estado", "")

            if estado == "Ofertas":
                print("hola")
                html_cabecera = []
                html = []
                propuestas = Propuesta.objects.filter(anulado_en=None)
                if cliente:
                    propuestas = propuestas.filter(cliente=cliente).order_by(
                        "creado_en"
                    )
                html_cabecera.append(
                    f"""
                    <tr>
                    <th>Fecha</th>
                    <th>Descripción</th>
                    <th class='text-center'>Activos Propuestos</th>
                    <th class='text-center'>Interesado</th>
                    <th class='text-center'>Esperando servicer</th>
                    <th class='text-center'>Preparado</th>
                    <th class='text-center'>Reservado</th>
                    <th class='text-center'>No Concretado</th>
                    <th class='text-center'>Vendidos</th>
                    <th colspan='10'></th>
                    </tr>"""
                )
                if not usuario.cliente:
                    html.append(f"<th></th>")
                html.append("</tr>")

                for propuesta in propuestas:
                    ofertas_campanya = PropuestaLinea.objects.filter(
                        anulado_por=None, propuesta=propuesta
                    )
                    num_ofertas = ofertas_campanya.count()
                    num_ofertas_interesado = ofertas_campanya.filter(estado="I").count()
                    num_ofertas_esperando = ofertas_campanya.filter(estado="E").count()
                    num_ofertas_preparado = ofertas_campanya.filter(estado="P").count()
                    num_ofertas_reservado = ofertas_campanya.filter(estado="R").count()
                    num_ofertas_noconcretado = ofertas_campanya.filter(
                        estado="X"
                    ).count()
                    num_ofertas_vendidos = ofertas_campanya.filter(estado="V").count()

                    vendidos = ofertas_campanya.filter(estado="V")

                    activos_vendidos = ", ".join(
                        [
                            v.campanya_linea.activo.direccion[:50]
                            for v in vendidos
                            if v.campanya_linea and v.campanya_linea.activo
                        ]
                    )

                    propuesta_fecha = propuesta.creado_en.strftime("%d-%m-%Y")
                    propuesta_descripcion = propuesta.DameNombreFichero()
                    html.append(
                        f"""
                        <tr>
                        <td>{propuesta_fecha}</td>
                        <td>{propuesta_descripcion}</td>
                        <td class='text-center'>{num_ofertas}</td>
                        <td class='text-center'>{num_ofertas_interesado}</td>
                        <td class='text-center'>{num_ofertas_esperando}</td>
                        <td class='text-center'>{num_ofertas_preparado}</td>
                        <td class='text-center'>{num_ofertas_reservado}</td>
                        <td class='text-center'>{num_ofertas_noconcretado}</td>
                        <td class='text-center'>{num_ofertas_vendidos}</td>
                        """
                    )
                    if not usuario.cliente:
                        html.append(
                            f"""
                            <td><button class='btn btn-info' onclick='ImprimirPropuesta({propuesta.pk})'>Imprimir</button></td>
                            <td><button class='btn btn-danger' onclick='AnularPropuesta({propuesta.pk})'>Eliminar</button></td>"""
                        )
                    html.append("</tr>")

                    if num_ofertas_vendidos > 0:
                        html.append(
                            f"""
                            <tr class='bg-success text-white'>
                                <td colspan='11'>Activos vendidos: {activos_vendidos}</td>
                            </tr>
                            """
                        )

                num_total = propuestas.count()
                html_titulo = "Propuestas realizadas"
                html_pie = f"{num_total} propuestas"

            else:
                print("hola2")
                html_cabecera = []
                html = []
                estado = estado.split(",")
                lineas = PropuestaLinea.objects.filter(
                    propuesta__anulado_en=None, estado__in=estado
                )
                print(lineas)
                filtro_cliente = request.GET.get("filtro_cliente", "").strip()
                responsable = request.GET.get("responsable", "").strip()
                id_proveedor = request.GET.get("proveedor", "").strip()
                ref_catastral = request.GET.get("ref_catastral", "").strip()
                direccion = request.GET.get("direccion", "").strip()
                if responsable:
                    lineas = lineas.filter(propuesta__cliente__pk=responsable.pk)
                if id_proveedor:
                    lineas = lineas.filter(
                        campanya_linea__activo__id_proveedor=id_proveedor
                    )
                if ref_catastral:
                    lineas = lineas.filter(
                        campanya_linea__activo__ref_catastral=ref_catastral
                    )
                if direccion:
                    lineas = lineas.filter(
                        campanya_linea__activo__direccion=ref_catastral
                    )
                if filtro_cliente:
                    lineas = lineas.filter(propuesta__cliente=filtro_cliente)
                estado = ",".join(estado)
                if cliente:
                    lineas = lineas.filter(propuesta__cliente=cliente)

                lineas = lineas.order_by("creado_en")
                html_cabecera.append(
                    f"""
                    <tr>"""
                )
                if estado == "I":
                    html_cabecera.append(
                        f"""
                    <th><input type="checkbox" id='c_sel_todos_activosI' onclick='SeleccionarTodosActivosI()'></th>"""
                    )
                elif estado == "E":
                    html_cabecera.append(
                        f"""
                    <th><input type="checkbox" id='c_sel_todos_activosE' onclick='SeleccionarTodosActivosE()'></th>"""
                    )
                if not usuario.cliente:
                    html_cabecera.append(
                        f"""
                        <th>Responsable</th>
                        <th>Cliente</th>"""
                    )
                if self.request.user.cliente:
                    html_cabecera.append(
                        f"""
                        <th>Fecha</th>
                        <th>Tipo</th>
                        <th>Ref Catastral</th>
                        <th>Tipología</th>
                        <th>Provincia</th>
                        <th>Población</th>
                        <th></th>
                        <th></th>
                        </tr>
                        """
                    )
                else:
                    html_cabecera.append(
                        f"""
                        <th>Fecha</th>
                        <th>Cartera</th>
                        <th>Tipo</th>
                        <th>Código prov</th>
                        <th>Ref Catastral</th>
                        <th>Tipología</th>
                        <th></th>
                        <th></th>
                        </tr>
                        """
                    )
                for linea in lineas:
                    try:
                        linea_fecha = linea.DameLineaEstado(estado).creado_en.strftime(
                            "%d-%m-%Y"
                        )
                    except:
                        linea_fecha = (
                            "" 
                        )
                    html.append(
                        f"""
                        <tr>"""
                    )
                    if estado == "I":
                        desc_activo = linea.DameDescActivo()
                        html.append(
                            f"""
                        <td>
                            <label for='c_sel_activoI{linea.pk}' class='d-none'>{desc_activo}</label>
                            <input type="checkbox" name="c_sel_activoI" value='{linea.pk}' id='c_sel_activoI{linea.pk}' onchange="actualizarResumenModalActivoI()">
                        </td>"""
                        )
                    elif estado == "E":
                        if linea.campanya_linea.preparado_en:
                            desc_activo = linea.DameDescActivo()
                            html.append(
                                f"""
                            <td>
                                <label for='c_sel_activoE{linea.pk}' class='d-none'>{desc_activo}</label>
                                <input type="checkbox" name="c_sel_activoE" value='{linea.pk}' id='c_sel_activoE{linea.pk}' onchange="actualizarResumenModalActivoE()">
                            </td>"""
                            )
                        else:
                            html.append("<td></td>")
                    if not usuario.cliente:
                        cliente_nombre = linea.propuesta.cliente.DameNombre()
                        responsable_nombre = ""
                        if linea.propuesta.cliente.responsable:
                            responsable_nombre = (
                                linea.propuesta.cliente.responsable.nombre
                            )
                        html.append(
                            f"""
                            <td>{responsable_nombre}</td>
                            <td>{cliente_nombre}</td>"""
                        )
                        html.append(
                            f"""
                            <td>{linea_fecha}</td>
                            <td>{linea.campanya_linea.campanya.cartera.codigo}</td>
                            <td>{linea.campanya_linea.get_tipo_display()}</td>
                            <td>{linea.campanya_linea.activo.id_proveedor}</td>
                            <td>{linea.campanya_linea.activo.ref_catastral}</td>
                            <td>{linea.campanya_linea.activo.tipologia.nombre}</td>
                            <td>"""
                        )
                    else:
                        html.append(
                            f"""
                            <td>{linea_fecha}</td>
                            <td>{linea.campanya_linea.get_tipo_display()}</td>
                            <td>{linea.campanya_linea.activo.ref_catastral}</td>
                            <td>{linea.campanya_linea.activo.tipologia.nombre}</td>
                            <td>{linea.campanya_linea.activo.poblacion.provincia.nombre}</td>
                            <td>{linea.campanya_linea.activo.poblacion.nombre}</td>
                            <td>"""
                        )
                    if not usuario.cliente:
                        html.append(
                            f"""
                            <a href="/linea/{linea.campanya_linea.id}/editar/">
                                <button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#activoModal" style="margin: 0px; padding:0px;">
                                🔎
                                </button>
                            </a>"""
                        )
                    else:
                        html.append(
                            f"""
                            <a href="/linea/{linea.campanya_linea.id}/">
                                <button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#activoModal" style="margin: 0px; padding:0px;">
                                🔎
                                </button>
                            </a>"""
                        )
                    html.append(
                        f"""
                        </td>
                        <td id='td_bot_preparado_{linea.pk}'>"""
                    )
                    if (
                        linea.estado == "I" or linea.estado == "E"
                    ) and not usuario.cliente:
                        if not linea.campanya_linea.preparado_en:
                            html.append(
                                f"""                            
                                <button class='btn btn-success' 
                                    onclick='Activo_Preparado2({linea.pk}, {linea.campanya_linea.pk}, {linea.campanya_linea.activo.pk})'>
                                    Dar como preparado
                                </button>
                                """
                            )
                        else:
                            html.append(
                                f"<label>Preparado desde {linea.campanya_linea.preparado_en}"
                            )

                    elif linea.estado == "P" and not usuario.cliente:
                        html.append(
                            f"""                            
                            <button class='btn btn-success' 
                                onclick='Activo_Reservado({linea.pk}, {linea.campanya_linea.pk}, {linea.campanya_linea.activo.pk})'>
                                Dar como reservado
                            </button>
                            """
                        )
                    elif linea.estado == "R" and not usuario.cliente:
                        html.append(
                            f"""                            
                            <label>Preparado desde {linea.campanya_linea.reservado_en}</label>
                            <button class='btn btn-warning mt-1 ms-2' 
                                onclick='CambiarEstado({linea.pk}, "X")'>
                                No Concretado
                            </button>
                            <button class='btn btn-success mt-1' 
                                onclick='CambiarEstado({linea.pk}, "V")'>
                                Vendido
                            </button>
                            """
                        )

                    html.append(
                        f"""
                        </td>
                        </tr>"""
                    )
                num_total = lineas.count()
                ESTADO = [
                    ("I", "Interesado"),
                    ("N", "No interesado"),
                    ("E", "Esperando información servicer"),
                    ("P", "Preparado"),
                    ("R", "Reservado"),
                    ("X", "No concretado"),
                    ("V", "Vendido"),
                ]
                if estado == "I":
                    estado_lit = "en la que desea más información"
                elif estado == "P":
                    estado_lit = "que hemos completado y pasado a"
                elif estado == "R":
                    estado_lit = "que ha reservado"
                elif estado == "X":
                    estado_lit = "que no ha concretado"
                elif estado == "V":
                    estado_lit = "vendido"
                else:
                    estado_lit = ""

                if cliente:
                    cliente_nombre = cliente.DameNombre()
                else:
                    cliente_nombre = ""
                html_titulo = f"Posiciones {estado_lit} {cliente_nombre}"
                html_pie = f"{num_total} posiciones"

            html_cabecera = " ".join(html_cabecera)
            html = " ".join(html)
            html_completo = [
                f"""
                        <h5 class="banner-reservas" id='h5_titulo_detalle'>
                            {html_titulo}
                        </h5>
                <div class="card-body">
                    <div id="propuestasSeleccionadas" class="alert alert-info" style="display: none;">
                        <strong>Posiciones seleccionadas:</strong>
                        <span id="resumenPropuestas"></span>"""
            ]
            texto_boton = ""
            if estado == "I":
                texto_boton = """<button type="button" class="btn btn-primary" onclick="pedirInformacionServicer()">Pedir Información servicer</button>"""
                html_completo.append(texto_boton)
            elif estado == "E":
                texto_boton = """<button type="button" class="btn btn-primary" onclick="enviarInformacionCliente()">Enviar confirmación al cliente</button>"""
                html_completo.append(texto_boton)
            html_completo.append(
                f"""                        
                    </div>
                    <table class="table table-striped table-hover col-12">
                        <thead class="table-dark" id='head_tabla_detalle'>
                            {html_cabecera}
                        </thead>
                        <tbody id='t_body_detalle'>
                            {html}
                        </tbody>
                    </table>
                  </div>
                  <div class="card-footer text-muted" id='div_footer_detalle'>
                        {html_pie}
                  </div>
                </div>"""
            )
            html_completo = " ".join(html_completo)
            context_dict = {
                "error": error,
                "literror": literror,
                "html_cabecera": html_cabecera,
                "html": html,
                "html_titulo": html_titulo,
                "html_pie": html_pie,
                "texto_boton": texto_boton,
                "html_completo": html_completo,
            }

        if accion == "filtrar_propuestas":
            estado = request.GET.get("estado", "").strip()
            responsable = request.GET.get("responsable", "").strip()
            cliente_nombre = request.GET.get("filtro_cliente", "").strip()
            id_proveedor = request.GET.get("proveedor", "").strip()
            ref_catastral = request.GET.get("ref_catastral", "").strip()
            direccion = request.GET.get("direccion", "").strip()

            if not self.request.user.cliente:
                id_clientes = Propuesta.objects.filter(anulado_por=None).values_list(
                    "cliente__pk", flat=True
                )
                clientes = Cliente.objects.filter(pk__in=id_clientes, anulado_por=None)

                if responsable:
                    clientes = clientes.filter(
                        responsable__nombre__icontains=responsable
                    )

                if cliente_nombre:
                    clientes = clientes.filter(
                        Q(nombre__icontains=cliente_nombre)
                        | Q(apellidos__icontains=cliente_nombre)
                    )

                clientes = clientes.order_by("nombre", "apellidos", "nombre_completo")
            else:
                clientes = Cliente.objects.filter(
                    pk=self.request.user.cliente.pk
                ).order_by("nombre", "apellidos", "nombre_completo")

            html = []
            for cliente in clientes:
                propuestas = Propuesta.objects.filter(cliente=cliente, anulado_por=None)

                if estado:
                    propuestas = propuestas.filter(propuestalinea__estado=estado)

                if id_proveedor or ref_catastral or direccion:
                    filtros = Q()
                    if id_proveedor:
                        filtros &= Q(
                            propuestalinea__campanya_linea__activo__id_proveedor__icontains=id_proveedor
                        )
                    if ref_catastral:
                        filtros &= Q(
                            propuestalinea__campanya_linea__activo__ref_catastral__icontains=ref_catastral
                        )
                    if direccion:
                        filtros &= Q(
                            propuestalinea__campanya_linea__activo__direccion__icontains=direccion
                        )
                    propuestas = propuestas.filter(filtros).distinct()

                cant_propuestas = propuestas.count()

                if cant_propuestas:
                    id_propuestas = propuestas.values_list("pk", flat=True)

                    ofertas_campanya = PropuestaLinea.objects.filter(
                        anulado_por=None, propuesta__pk__in=id_propuestas
                    )

                    if estado:
                        ofertas_campanya = ofertas_campanya.filter(estado=estado)

                    if id_proveedor or ref_catastral or direccion:
                        filtros = Q()
                        if id_proveedor:
                            filtros &= Q(
                                campanya_linea__activo__id_proveedor__icontains=id_proveedor
                            )
                        if ref_catastral:
                            filtros &= Q(
                                campanya_linea__activo__ref_catastral__icontains=ref_catastral
                            )
                        if direccion:
                            filtros &= Q(
                                campanya_linea__activo__direccion__icontains=direccion
                            )
                        ofertas_campanya = ofertas_campanya.filter(filtros).distinct()

                    num_ofertas = ofertas_campanya.count()
                    num_estados = {
                        "I": ofertas_campanya.filter(estado="I").count(),
                        "E": ofertas_campanya.filter(estado="E").count(),
                        "P": ofertas_campanya.filter(estado="P").count(),
                        "R": ofertas_campanya.filter(estado="R").count(),
                        "X": ofertas_campanya.filter(estado="X").count(),
                        "V": ofertas_campanya.filter(estado="V").count(),
                    }

                    responsable_nombre = (
                        cliente.responsable.nombre if cliente.responsable else ""
                    )

                    html.append(
                        f"""
                        <tr>
                            <td>{responsable_nombre}</td>
                            <td>{cliente.DameNombre()}</td>
                            <td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, 'Ofertas')">
                                <button class='btn btn-secondary'>{cant_propuestas}</button>
                            </td>
                            <td class="text-center">{num_ofertas}</td>
                        """
                    )

                    for est in ["I", "E", "P", "R", "X", "V"]:
                        num = num_estados[est]
                        if num:
                            html.append(
                                f"""<td class="text-center" style="cursor:pointer" onclick="SeleccionarLineas({cliente.pk}, '{est}')">
                                        <button class='btn btn-secondary'>{num}</button>
                                </td>"""
                            )
                        else:
                            html.append("<td class='text-center'> - </td>")

                    html.append("</tr>")

            context_dict = {
                "error": error,
                "literror": literror,
                "html": " ".join(html),
            }

        elif accion == "dame_propuestas_old":
            id_clientes = PropuestaLinea.objects.filter(anulado_por=None).values_list(
                "propuesta__cliente__pk"
            )
            clientes = Cliente.objects.filter(pk__in=id_clientes)
            tot_num_ofertas = 0
            tot_num_ofertas_nointeresado = 0
            tot_num_ofertas_interesado = 0
            tot_num_ofertas_preparado = 0
            tot_num_ofertas_reservado = 0
            tot_num_ofertas_noconcretado = 0
            html = []
            for cliente in clientes:
                id_campanyas = PropuestaLinea.objects.filter(
                    anulado_por=None, propuesta__cliente=cliente
                ).values_list("campanya_linea__campanya__pk")
                campanyas = Campanya.objects.filter(pk__in=id_campanyas).order_by(
                    "fecha"
                )
                for campanya in campanyas:
                    fecha = campanya.fecha.strftime("%d-%m-%Y")
                    ofertas_campanya = PropuestaLinea.objects.filter(
                        anulado_por=None,
                        propuesta__cliente=cliente,
                        campanya_linea__campanya=campanya,
                    )
                    num_ofertas = ofertas_campanya.count()
                    num_ofertas_nointeresado = ofertas_campanya.filter(
                        estado="N"
                    ).count()
                    num_ofertas_interesado = ofertas_campanya.filter(estado="I").count()
                    num_ofertas_preparado = ofertas_campanya.filter(estado="P").count()
                    num_ofertas_reservado = ofertas_campanya.filter(estado="R").count()
                    num_ofertas_noconcretado = ofertas_campanya.filter(
                        estado="X"
                    ).count()
                    num_ofertas_vendidos = ofertas_campanya.filter(estado="V").count()
                    if cliente.responsable:
                        cliente_responsable_nombre = cliente.responsable.nombre
                    else:
                        cliente_responsable_nombre = ""
                    html.append(
                        f"""
                        <tr>
                            <td>{cliente_responsable_nombre}</td>
                            <td>{cliente.DameNombre()}</td>
                            <td>{campanya.proveedor.nombre}</td>
                            <td>{fecha}</td>
                            <td class='text-end'>{num_ofertas}</td>
                            <td class='text-end'>{num_ofertas_nointeresado}</td>
                            <td class='text-end'>{num_ofertas_interesado}</td>
                            <td class='text-end'>{num_ofertas_preparado}</td>
                            <td class='text-end'>{num_ofertas_reservado}</td>
                            <td class='text-end'>{num_ofertas_noconcretado}</td>
                            <td class='text-end'>{num_ofertas_vendidos}</td>

                        </tr>"""
                    )
                    tot_num_ofertas += num_ofertas
                    tot_num_ofertas_nointeresado += num_ofertas_nointeresado
                    tot_num_ofertas_interesado += num_ofertas_interesado
                    tot_num_ofertas_preparado += num_ofertas_preparado
                    tot_num_ofertas_reservado += num_ofertas_reservado
                    tot_num_ofertas_noconcretado += num_ofertas_noconcretado
                    tot_num_ofertas_num_ofertas_vendidos += num_ofertas_vendidos

            html.append(
                f"""
                <tr>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td><b>Totales</b></td>
                    <td class='text-end'>{tot_num_ofertas}</td>
                    <td class='text-end'>{tot_num_ofertas_nointeresado}</td>
                    <td class='text-end'>{tot_num_ofertas_interesado}</td>
                    <td class='text-end'>{tot_num_ofertas_preparado}</td>
                    <td class='text-end'>{tot_num_ofertas_reservado}</td>
                    <td class='text-end'>{tot_num_ofertas_noconcretado}</td>
                    <td class='text-end'>{tot_num_ofertas_num_ofertas_vendidos}</td>

                </tr>"""
            )
            context_dict = {
                "error": error,
                "literror": literror,
                "html": " ".join(html),
            }
        if context_dict == {}:
            context_dict = {"error": error, "literror": literror}
        json_context = json.dumps(context_dict).encode("utf-8")
        return HttpResponse(json_context, content_type="application/json")

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        accion = data.get("accion")
        error = False
        literror = ""
        context_dict = {}
        usuario = self.request.user

        if accion == "anular_propuesta":
            usuario = self.request.user
            propuesta_id = data.get("propuesta_id")

            if not usuario.cliente:
                try:
                    lineas = PropuestaLinea.objects.filter(propuesta_id=propuesta_id)
                    for linea in lineas:
                        linea.anulado_en = now()
                        linea.anulado_por = usuario
                        linea.estado = ""
                        linea.save()
                        campanyaLinea = CampanyaLinea.objects.get(
                            pk=linea.campanya_linea_id
                        )
                        if campanyaLinea:
                            campanyaLinea.preparado_en = None
                            campanyaLinea.preparado_por_id = None
                            campanyaLinea.reservado_en = None
                            campanyaLinea.reservado_por_id = None
                            campanyaLinea.save()
                        try:
                            lineaEstado = PropuestaLineaEstado.objects.get(
                                linea=linea
                            ).first()
                        except:
                            lineaEstado = None
                        if lineaEstado:
                            lineaEstado.estado = ""
                            lineaEstado.anulado_en = now()
                            lineaEstado.anulado_por = usuario
                            lineaEstado.confirmado_por_id = usuario
                            lineaEstado.save()
                    propuesta = Propuesta.objects.get(pk=propuesta_id)
                    propuesta.anulado_en = now()
                    propuesta.anulado_por_id = usuario
                    propuesta.anulado_por = usuario
                    propuesta.anulado_en = now()
                    propuesta.save()

                    success = True
                    mensaje = "La propuesta y sus líneas fueron anuladas correctamente."
                except Exception as e:
                    error = True
                    literror = f"Error al anular la propuesta: {str(e)}"
            else:
                error = True
                literror = "No tiene permisos para realizar esta operación."

        elif accion == "imprimir_propuesta":
            propuesta = Propuesta.objects.filter(pk=data.get("propuesta_id"))
            if usuario.cliente:
                propuesta = propuesta.filter(cliente=usuario.cliente)
            propuesta = propuesta.first()
            if propuesta:
                nombrefichero = propuesta.ImprimirPropuesta()
                context_dict = {
                    "error": error,
                    "literror": literror,
                    "nombrefichero": nombrefichero,
                }

        elif accion == "cambiar_estado":
            linea_id = data.get("linea_id")
            nuevo_estado = data.get("nuevo_estado")
            try:
                linea = PropuestaLinea.objects.get(pk=linea_id)
                linea.estado = nuevo_estado
                linea.save()

                PropuestaLineaEstado.objects.create(
                    linea=linea,
                    estado=nuevo_estado,
                    creado_por=usuario,
                )

                context_dict = {"error": False, "literror": ""}
            except Exception as e:
                context_dict = {"error": True, "literror": str(e)}

        if context_dict == {}:
            context_dict = {"error": error, "literror": literror}
        json_context = json.dumps(context_dict).encode("utf-8")
        return HttpResponse(json_context, content_type="application/json")


class OfertaListView_NOuso(
    LoginRequiredMixin, TienePermisosMixin, generic.ListView
):  # TienePermisosMixin
    model = PropuestaLinea
    context_object_name = "ofertas"
    template_name = "oferta_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        campanya_id = self.request.GET.get("campanya")
        if campanya_id:
            id_activos = CampanyaLinea.objects.filter(
                campanya__pk=campanya_id
            ).values_list("activo__pk", flat=True)
            queryset = queryset.filter(
                anulado_en=None, campanya_linea__activo__pk__in=id_activos
            ).exclude(estado="NA")
        else:
            id_activos = CampanyaLinea.objects.filter(
                campanya__anulado_en=None
            ).values_list("activo__pk", flat=True)
            queryset = queryset.filter(
                anulado_en=None, campanya_linea__activo__pk__in=id_activos
            ).exclude(estado="NA")

        usuario = self.request.user
        cliente_id = ""
        if usuario.cliente:
            cliente_id = usuario.cliente.pk
        else:
            cliente_id = self.request.GET.get("cliente")
        if cliente_id and cliente_id != "all":
            queryset = queryset.filter(propuesta__cliente__id=cliente_id)
        tipo = self.request.GET.get("tipo")
        if tipo:
            queryset = queryset.filter(estado=tipo)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id_clientes = self.get_queryset().values_list(
            "propuesta__cliente__pk"
        )
        clientes = Cliente.objects.filter(pk__in=id_clientes).order_by(
            "nombre", "apellidos"
        )
        context["clientes"] = clientes
        context["micliente"] = self.request.GET.get("cliente")
        return context


class CorreoListView(LoginRequiredMixin, TienePermisosMixin, generic.ListView):
    model = Correo
    context_object_name = "correos"
    template_name = "correo_list.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(anulado_en=None)
        cliente_id = self.request.GET.get("cliente")
        representante_id = self.request.GET.get("representante")
        contacto_id = self.request.GET.get("contacto")

        if contacto_id:
            contacto = Contacto.objects.filter(pk=contacto_id).first()
            propuesta_id = self.request.GET.get("propuesta")
            propuesta = Propuesta.objects.filter(pk=propuesta_id).first()

            if contacto and propuesta:
                return RespuestaCorreo.objects.filter(correo_id=propuesta.correo_id)
            else:
                return RespuestaCorreo.objects.none()

        if representante_id:
            representante = Cliente.objects.filter(pk=representante_id).first()
            if representante:
                return RespuestaCorreo.objects.filter(remitente=representante.correo)
            else:
                return RespuestaCorreo.objects.none()

        if cliente_id and cliente_id != "all":
            cliente = Cliente.objects.filter(pk=cliente_id).first()
            if cliente:
                queryset = queryset.filter(to_email=cliente.correo)
            else:
                queryset = queryset.none()
        return queryset

    def get_template_names(self):
        if self.request.GET.get("representante"):
            return ["correo_representante.html"]

        if self.request.GET.get("contacto"):
            return ["correo_contacto.html"]

        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        correos = Correo.objects.filter(anulado_en=None)

        cliente_id = self.request.GET.get("cliente")
        representante_id = self.request.GET.get("representante")
        contacto_id = self.request.GET.get("contacto")
        propuesta_id = self.request.GET.get("propuesta")

        if contacto_id:
            contacto = Contacto.objects.filter(pk=contacto_id).first()
            propuesta = Propuesta.objects.filter(pk=propuesta_id).first()
            if contacto and propuesta:
                correos = Correo.objects.filter(pk=propuesta.correo_id)
            else:
                correos = Correo.objects.none()

        elif representante_id:
            representante = Cliente.objects.filter(pk=representante_id).first()
            if representante:
                correos = Correo.objects.filter(from_email=representante.correo)
            else:
                correos = Correo.objects.none()

        elif cliente_id and cliente_id != "all":
            cliente = Cliente.objects.filter(pk=cliente_id).first()
            if cliente:
                correos = Correo.objects.filter(to_email=cliente.correo)
            else:
                correos = Correo.objects.none()

        context["correo_responsables"] = correos.values_list("from_email", flat=True)
        context["micliente"] = cliente_id
        context["propuesta_linea"] = PropuestaLinea.objects.filter(
            propuesta=propuesta_id
        ).first()
        return context


class CorreoDetailView(LoginRequiredMixin, TienePermisosMixin, generic.DetailView):
    model = Correo
    context_object_name = "correo"
    template_name = "correo_detalle.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RespuestaDetailView(LoginRequiredMixin, TienePermisosMixin, generic.DetailView):
    model = RespuestaCorreo
    context_object_name = "respuestacorreo"
    template_name = "respuesta_detalle.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class Responsable_Listar(LoginRequiredMixin, TienePermisosMixin, ListView):
    model = Responsable
    form = ResponsableForm
    template_name = "responsable_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(anulado_en=None)
        return queryset


class Responsable_Crear(LoginRequiredMixin, TienePermisosMixin, CreateView):
    model = Responsable
    template_name = "responsable_form.html"
    fields = ["nombre", "apellidos", "correo_acceso", "correo_envio"]
    success_url = reverse_lazy("listarresponsable")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.creado_por = self.request.user
        self.object.creado_en = datetime.now()
        self.object.save()
        self.object.CrearUsuario()
        return response


class Responsable_Editar(LoginRequiredMixin, TienePermisosMixin, UpdateView):
    model = Responsable
    template_name = "responsable_form.html"
    fields = ["nombre", "apellidos", "correo_acceso", "correo_envio"]
    success_url = reverse_lazy("listarresponsable")

    def form_valid(self, form):
        response = super().form_valid(form)
        error, literror = self.object.ActualizaUsuario()
        if error:
            form.add_error(
                None, f"El usuario no ha sido creado correctamente. {literror}"
            )
            return self.form_invalid(form)
        return response


class Responsable_Eliminar(LoginRequiredMixin, TienePermisosMixin, DeleteView):
    model = Responsable
    template_name = "responsable_confirm_delete.html"
    success_url = reverse_lazy("listarresponsable")

    def form_valid(self, form):
        self.object.anulado_por = self.request.user
        self.object.anulado_en = datetime.now()
        self.object.save()
        self.object.AnulaUsuario()
        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        return super().get_queryset().filter(anulado_por=None)


class UsuarioDetalleView(LoginRequiredMixin, InitBaseMixin, DetailView):
    model = User
    template_name = "usuario_detalle.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        objeto = self.get_object()
        context["user"] = self.request.user
        context["usuario"] = self.request.user

        context["object"] = self.request.user

        return context

    def post(self, request, *args, **kwargs):
        error = False
        literror = ""
        context_dict = {}

        usuario = self.request.user 
        usuario_cambio_clave = usuario
        try:
            data = json.loads(request.body)
            if usuario.is_superuser or usuario.es_administrador:
                id_usuario = data.get("idusuario")
                if id_usuario:
                    usuario_cambio_clave = User.objects.get(pk=id_usuario)
            clave_new = data.get("clave_new")
            clave_new2 = data.get("clave_new2")
            clave_old = ""
        except:
            if usuario.is_superuser or usuario.es_administrador:
                id_usuario = self.request.POST.get("idusuario")
                if id_usuario:
                    usuario_cambio_clave = User.objects.get(pk=id_usuario)
            clave_new = self.request.POST["clave_new"]
            clave_new2 = self.request.POST["clave_new2"]
            clave_old = request.POST.get("clave_old", "")

        acceso = authenticate(username=usuario_cambio_clave.email, password=clave_old)
        if acceso is not None or usuario.is_superuser or usuario.es_administrador:
            if clave_new == clave_new2:
                if len(clave_new) < 6:
                    error = True
                    literror = "Las clave tiene que tener un mínimo de 6 dígitos"
                else:
                    user = usuario_cambio_clave
                    user.set_password(clave_new)
                    user.save()
            else:
                error = True
                literror = "Las claves nuevas no coinciden"
        else:
            error = True
            literror = "La contraseña no es correcta"
        context_dict = {"error": error, "literror": literror}
        json_context = json.dumps(context_dict).encode("utf-8")
        return HttpResponse(json_context, content_type="application/json")


class CalendarioView(LoginRequiredMixin, InitBaseMixin, TemplateView):
    template_name = "calendario.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        content_type = ContentType.objects.get_for_model(Propuesta)

        propuestas_existentes = Calendario.objects.filter(
            content_type=content_type
        ).values_list("object_id", flat=True)

        nuevas_propuestas = Propuesta.objects.filter(anulado_en__isnull=True).exclude(
            id__in=propuestas_existentes
        )

        for propuesta in nuevas_propuestas:
            Calendario.objects.create(
                fecha=propuesta.creado_en,
                descripcion=f"Propuesta {propuesta.id}",
                content_type=content_type,
                object_id=propuesta.id,
                creado_por=self.request.user,
            )

        eventos = Calendario.objects.filter(anulado_en__isnull=True).order_by("fecha")

        eventos_calendario = [
            {
                "title": e.descripcion or "Evento sin descripción",
                "start": e.fecha.isoformat(),
                "id": f"cal-{e.id}",
                "url": (
                    f"/propuesta/{e.object_id}/"
                    if e.content_type == content_type
                    else ""
                ),
                "className": (
                    "evento-propuesta"
                    if e.content_type == content_type
                    else "evento-general"
                ),
            }
            for e in eventos
        ]

        context["eventos_json"] = json.dumps(eventos_calendario, cls=DjangoJSONEncoder)
        return context


import openai
import requests
@method_decorator(staff_member_required, name="dispatch")
class AuditoriaView(LoginRequiredMixin, InitBaseMixin, TemplateView):
    template_name = "auditoria.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["auditorias"] = Auditoria.objects.select_related("usuario").all()[:200]
        return context


class AgendaView(LoginRequiredMixin, InitBaseMixin, ListView):
    model = Agenda
    template_name = "agenda.html"
    context_object_name = "agenda"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agendas"] = Agenda.objects.all()
        return context


class AgendaCrearView(LoginRequiredMixin, InitBaseMixin, CreateView):
    model = Agenda
    template_name = "agenda_crear.html"
    fields = [
        "nombre",
        "apellidos",
        "empresa",
        "telefono",
        "fijo",
        "email",
        "descripcion",
    ]
    success_url = reverse_lazy("agenda")

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        response = super().form_valid(form)

        if self.request.POST.get("crear_cliente") == "on":
            nombre = form.instance.nombre.strip()
            apellidos = form.instance.apellidos.strip()
            correo = form.instance.email.strip()

            cliente_existe = Cliente.objects.filter(correo=correo).exists()

            if cliente_existe:
                messages.warning(self.request, "⚠️ Ya existe un cliente con esos datos.")
            else:
                Cliente.objects.create(
                    nombre=nombre,
                    apellidos=apellidos,
                    correo=correo,
                    telefono=form.instance.telefono,
                    observaciones=form.instance.descripcion,
                    creado_por=self.request.user,
                    nombre_completo=f"{nombre} {apellidos}",
                )
                messages.success(self.request, "✅ Cliente creado correctamente.")

        return response


class AgendaEditarView(LoginRequiredMixin, InitBaseMixin, UpdateView):
    model = Agenda
    template_name = "agenda_editar.html"
    fields = [
        "nombre",
        "apellidos",
        "empresa",
        "telefono",
        "fijo",
        "email",
        "descripcion",
    ]
    success_url = reverse_lazy("agenda")

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.request.POST.get("crear_cliente") == "on":
            nombre = form.instance.nombre.strip()
            apellidos = form.instance.apellidos.strip()
            correo = form.instance.email.strip()

            if Cliente.objects.filter(correo=correo).exists():
                messages.warning(self.request, "⚠️ Ya existe un cliente con esos datos.")
            else:
                Cliente.objects.create(
                    nombre=nombre,
                    apellidos=apellidos,
                    correo=correo,
                    telefono=form.instance.telefono,
                    observaciones=form.instance.descripcion,
                    creado_por=self.request.user,
                    nombre_completo=f"{nombre} {apellidos}",
                )
                messages.success(self.request, "✅ Cliente creado correctamente.")

        return response


class AgendaEliminarView(LoginRequiredMixin, InitBaseMixin, DeleteView):
    model = Agenda
    template_name = "agenda_eliminar.html"
    success_url = reverse_lazy("agenda")


@method_decorator(csrf_exempt, name="dispatch")
class ComercialView(LoginRequiredMixin, InitBaseMixin, TemplateView):
    template_name = "comercial.html"

    def get_queryset(self):
        return Activo.objects.filter(no_disponible__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        orden_estados = ["publicado", "reservado", "vendido", "no publicado"]
        activos_por_estado = {}

        for estado in orden_estados:
            activos_estado = queryset.filter(estado_activo=estado).order_by(
                "-creado_en"
            )
            start = int(self.request.GET.get(f"start_{estado}", 0))
            total = activos_estado.count()

            activos_por_estado[estado] = {
                "activos": activos_estado[start : start + 250],
                "total": total,
                "start": start,
                "has_more": start + 500 < total,
            }

        context["activos_por_estado"] = activos_por_estado
        return context

    def post(self, request, *args, **kwargs):

        try:
            data = json.loads(request.body)
            activo_id = data.get("id")
            campo = data.get("campo")
            valor = data.get("valor")

            if campo not in ["idealista", "fotocasa_pro", "web_invest"]:
                return JsonResponse(
                    {"status": "error", "message": "Campo no permitido"}
                )

            activo = Activo.objects.get(id=activo_id)
            setattr(activo, campo, valor)
            activo.save()
            return JsonResponse({"status": "ok"})
        except Activo.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Activo no encontrado"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


def generar_ficha_pdf_view(request, linea_id):

    linea = CampanyaLinea.objects.select_related("activo").get(pk=linea_id)
    activo = linea.activo
    imagenes = ActivoImagen.objects.filter(activo=activo, anulado_en__isnull=True)
    documentacion = ActivoDocumento.objects.filter(
        activo=activo, anulado_en__isnull=True
    )
    buffer = generar_pdf_para_activo(activo, linea, imagenes, documentacion)
    return FileResponse(
        buffer, as_attachment=True, filename=f"ficha_linea_{linea.id}.pdf"
    )


@csrf_exempt
def chatbot(request):
    def es_pregunta_bbdd(pregunta):
        patrones = {
            "activo": [
                r"\bactivo\b",
                r"\bref(?:erencia)?\b",
                r"\bcatastral\b",
                r"\bdireccion\b",
                r"\bid\b",
            ],
            "cliente": [
                r"\bcliente\b",
                r"\bnif\b",
                r"\bnombre\b",
                r"\bapellidos\b",
                r"\bcorreo\b",
                r"\btelefono\b",
            ],
            "proveedor": [r"\bproveedor\b", r"\bnombre\b"],
        }

        pregunta_lower = pregunta.lower()

        for etiqueta, lista_patrones in patrones.items():
            for patron in lista_patrones:
                if re.search(patron, pregunta_lower):
                    return etiqueta 

        return None

    def extraer_fragmentos_utiles(pregunta):
        palabras = re.findall(r"\b[\w\-/]{3,}\b", pregunta.lower())
        return list(set(palabras))

    def buscar_info_en_bbdd(pregunta, etiqueta):
        fragmentos = extraer_fragmentos_utiles(pregunta)

        if etiqueta == "activo":
            for frag in fragmentos:
                activo = Activo.objects.filter(
                    Q(ref_catastral__icontains=frag)
                    | Q(catastro_localizacion__icontains=frag)
                    | Q(direccion__icontains=frag)
                    | Q(id_proveedor__icontains=frag)
                ).first()
                if activo:
                    linea = (
                        CampanyaLinea.objects.filter(activo_id=activo.id)
                        .order_by("-creado_en")
                        .first()
                    )
                    return f"Activo encontrado:</br>Dirección: {activo.direccion}</br>Referencia catastral: {activo.ref_catastral}</br>Id: {activo.id_proveedor}</br>Precio: {activo.DamePrecio()}</br>Importe Deuda: {activo.DameImporteDeuda()}</br><a href='/linea/{linea.id}/editar' target='_blank'>---Link al Activo---</a>"

        elif etiqueta == "cliente":
            for frag in fragmentos:
                cliente = Cliente.objects.filter(
                    Q(nombre__icontains=frag)
                    | Q(apellidos__icontains=frag)
                    | Q(nif__icontains=frag)
                    | Q(telefono__icontains=frag)
                    | Q(correo__icontains=frag)
                ).first()
                if cliente:
                    return f"Cliente encontrado:</br>Nombre: {cliente.nombre} {cliente.apellidos}</br>NIF: {cliente.nif}</br>Teléfono: {cliente.telefono}</br>Correo: {cliente.correo}</br><a href='/cliente/{cliente.id}' target='_blank'>---Link al Cliente---</a>"

        elif etiqueta == "proveedor":
            for frag in fragmentos:
                proveedor = Proveedor.objects.filter(Q(nombre__icontains=frag)).first()
                if proveedor:
                    return f"Proveedor encontrado:</br>Nombre: {proveedor.nombre}"

        return None

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            pregunta = data.get("question", "").strip()
            if not pregunta:
                return JsonResponse(
                    {"error": "No se recibió ninguna pregunta."}, status=400
                )

            etiqueta_bbdd = es_pregunta_bbdd(pregunta)
            if etiqueta_bbdd:
                respuesta_local = buscar_info_en_bbdd(pregunta, etiqueta_bbdd)
                if respuesta_local:
                    return JsonResponse(
                        {"answer": respuesta_local, "bbdd_keyword": etiqueta_bbdd}
                    )

            mensajes = [
                {
                    "role": "system",
                    "content": "Eres un asistente útil que trabaja para un vehículo de inversión.",
                },
                {"role": "user", "content": pregunta},
            ]
            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                respuesta_api = client.chat.completions.create(
                    model="gpt-4o",
                    messages=mensajes,
                    max_tokens=512,
                    temperature=0.7,
                )
                respuesta = respuesta_api.choices[0].message.content.strip()
                return JsonResponse({"answer": respuesta})
            except Exception as e:
                return JsonResponse(
                    {"error": f"Error al comunicarse con OpenAI: {str(e)}"}, status=500
                )

        except Exception as e:
            return JsonResponse({"error": f"Ocurrió un error: {str(e)}"}, status=500)
    else:
        return JsonResponse({"error": "Método no permitido."}, status=405)
