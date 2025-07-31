from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse
from django.urls import path, re_path
from django.views.generic import RedirectView

from boot.views import SendfileView
from invest.views import *
from invest.openai_chat
from invest.actualizar_mapeo_columnas
from invest.crear_evento



def ping(request):
    return HttpResponse("pong", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("favicon.ico", RedirectView.as_view(url="/static/img/favicon.ico")),
    path("ping", ping),  # Do not remove
    re_path(r"^sendfile/(?P<path>.*)$", SendfileView.as_view(), name="sendfile"),
    path("", Vista_Iniciar.as_view(), name="home"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("register/", CustomRegister.as_view(), name="register"),
    path("salir/", LogoutView.as_view(next_page="/"), name="logout"),
    path("password_reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password_reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password_reset/complete/",
        PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("herramientas/", HerramientasView.as_view(), name="pantallaherramientas"),
    path("campanya/", CampanyaView.as_view(), name="pantallacampanya"),
    path("campanya/<int:pk>/", Campanya_Detalle.as_view(), name="detallecampanya"),
    path("campanya/listar/", CampanyaListView.as_view(), name="listarcampanya"),
    path("campanya/crear/", CampanyaCreateView.as_view(), name="crearcampanya"),
    path("campanya/<int:pk>/update/", Campanya_Editar.as_view(), name="editarcampanya"),
    path("campanya/api/", Campanya_Api.as_view(), name="apicampanya"),
    path("servicer/", Proveedor_Listar.as_view(), name="listarproveedor"),
    path("servicer/crear/", Proveedor_Crear.as_view(), name="crearproveedor"),
    path("servicer/<int:pk>/", Proveedor_Detalle.as_view(), name="detalleproveedor"),
    path(
        "servicer/<int:pk>/update/", Proveedor_Editar.as_view(), name="editarproveedor"
    ),
    path(
        "servicer/<int:pk>/eliminar/",
        Proveedor_Eliminar.as_view(),
        name="eliminarproveedor",
    ),
    path(
        "servicer/<int:idservicer>/cartera/crear/",
        Cartera_Crear.as_view(),
        name="crearcartera",
    ),
    path(
        "servicer/<int:idservicer>/cartera/<int:pk>/update/",
        Cartera_Editar.as_view(),
        name="editarcartera",
    ),
    path(
        "servicer/<int:idservicer>/cartera/<int:pk>/eliminar/",
        Cartera_Eliminar.as_view(),
        name="eliminarcartera",
    ),
    path(
        "servicer/<int:idservicer>/contacto/crear/",
        Contacto_Crear.as_view(),
        name="crearcontacto",
    ),
    path(
        "servicer/<int:idservicer>/contacto/<int:pk>/update/",
        Contacto_Editar.as_view(),
        name="editarcontacto",
    ),
    path(
        "servicer/<int:idservicer>/contacto/<int:pk>/eliminar/",
        Contacto_Eliminar.as_view(),
        name="eliminarcontacto",
    ),
    path("activo/", ActivoView.as_view(), name="pantallaactivo"),
    path("activo/crear/", ActivoCrearView.as_view(), name="crearactivo"),
    path(
        "activo/listar/", ActivoListView.as_view(), name="listaractivo"
    ),  # <int:id_campanya>/
    path("listar/", ActivoListView.as_view(), name="listaractivo"),
    path("activo/api/", ActivoApiView.as_view(), name="apiactivo"),
    path("linea/<int:pk>/", Linea_Detalle.as_view(), name="detallelinea"),
    path("activo/<int:pk>/", Activo_Detalle.as_view(), name="detalleactivo"),
    path(
        "activo/<int:pk>/detalle/",
        Activo_DetalleCliente.as_view(),
        name="detalleclienteactivo",
    ),
    path(
        "activo/<int:pk>/ofertas/",
        PropuestaLineasListView.as_view(),
        name="listarofertasactivo",
    ),
    path("activo/<int:pk>/update/", Activo_Editar.as_view(), name="editaractivo"),
    path("linea/<int:pk>/editar/", Linea_Edito.as_view(), name="editoactivo"),
    path("propuestas/", OfertaTemplateView.as_view(), name="listarpropuesta"),
    path("propuestas/api/", OfertaApiView.as_view(), name="apipropuestas"),
    path("correo/listar/", CorreoListView.as_view(), name="listarcorreo"),
    # solucion lupa cliente 8/4/25
    path("correo/<int:pk>/", CorreoDetailView.as_view(), name="detallecorreo"),
    path("respuesta/<int:pk>/", RespuestaDetailView.as_view(), name="detallerespuesta"),
    path(
        "propuestas/listado/", PropuestaListadoView.as_view(), name="listadopropuesta"
    ),
    path("propuesta/<int:pk>/", OfertaListView.as_view(), name="listaroferta"),
    path("misofertas/<int:pk>/", OfertaListView.as_view(), name="oferta_misofertas"),
    # path('propuesta/<int:pk>/', Propuesta_ClienteListView.as_view(), name='misofertas'),
    path("cliente/", ClienteView.as_view(), name="pantallacliente"),
    path("cliente/<int:pk>/", Cliente_Detalle.as_view(), name="detallecliente"),
    path("cliente/listar/", Cliente_Listar.as_view(), name="listarcliente"),
    path("cliente/crear/", Cliente_Crear.as_view(), name="crearcliente"),
    path("cliente/<int:pk>/update/", Cliente_Editar.as_view(), name="editarcliente"),
    path(
        "cliente/<int:pk>/eliminar/", Cliente_Eliminar.as_view(), name="eliminarcliente"
    ),
    path("cliente/api/", Cliente_Api.as_view(), name="apicliente"),
    path("misclientes/", Cliente_Seleccion.as_view(), name="seleccioncliente"),
    path("responsable/", Responsable_Listar.as_view(), name="listarresponsable"),
    path("responsable/crear/", Responsable_Crear.as_view(), name="crearresponsable"),
    path(
        "responsable/<int:pk>/update/",
        Responsable_Editar.as_view(),
        name="editarresponsable",
    ),
    path(
        "responsable/<int:pk>/eliminar/",
        Responsable_Eliminar.as_view(),
        name="eliminarresponsable",
    ),
    path("usuario/<int:pk>/", UsuarioDetalleView.as_view(), name="usuariodetalle"),
    path("openai/chat/", openai_chat, name="openai_chat"),
    path(
        "propuesta_linea/<int:linea_id>/comentarios/",
        PropuestaComentarioPartialView.as_view(),
        name="comentarios-modal",
    ),
    path(
        "calendario/",
        CalendarioView.as_view(),
        name="calendario",
    ),
    path("calendario/crear/", crear_evento, name="crear_evento"),
    path("auditoria/", AuditoriaView.as_view(), name="auditoria"),
    path("agenda/", AgendaView.as_view(), name="agenda"),
    path("agenda/crear/", AgendaCrearView.as_view(), name="agenda_crear"),
    path("agenda/editar/<int:pk>/", AgendaEditarView.as_view(), name="agenda_editar"),
    path(
        "agenda/eliminar/<int:pk>/",
        AgendaEliminarView.as_view(),
        name="agenda_eliminar",
    ),
    path(
        "herramientas/api/actualizar_mapeo/",
        actualizar_mapeo_columnas,
        name="actualizar_mapeo_columnas",
    ),
    path(
        "linea/<int:linea_id>/ficha/", generar_ficha_pdf_view, name="generar_ficha_pdf"
    ),
    path("comercial/", ComercialView.as_view(), name="comercial"),
    path("chatbot/", chatbot, name="chatbot"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
