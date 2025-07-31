from django.contrib import admin

from invest.models import *

@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = ['id_proveedor', 'ref_ue', 'tipologia', 'ref_catastral', 'poblacion', 'no_disponible']
    list_filter = ['no_disponible']
@admin.register(ActivoDocumento)
class ActivoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['activo', 'documento', 'creado_en']
@admin.register(ActivoImagen)
class ActivoImagenAdmin(admin.ModelAdmin):
    list_display = ['activo', 'imagen', 'creado_en']
@admin.register(PropuestaLineaEstado)
class PropuestaLineaEstadoAdmin(admin.ModelAdmin):
    list_display = ['linea', 'estado', 'creado_en']
@admin.register(Campanya)
class CampanyaAdmin(admin.ModelAdmin):
    list_display = ['proveedor', 'fecha', 'fichero', 'anulado_por']
@admin.register(CampanyaLinea)
class CampanyaLineaAdmin(admin.ModelAdmin):
    raw_id_fields = ('campanya', 'activo')
    list_display = ['campanya', 'activo', 'no_disponible']
    list_filter = ['no_disponible']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nombre_completo', 'responsable', 'anulado_por']
@admin.register(ClienteDocumento)
class ClienteDocumentoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'documento', 'creado_en']

@admin.register(Correo)
class CorreoAdmin(admin.ModelAdmin):
    list_display = ['from_email', 'to_email', 'reply_to', 'subject']

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'razonsocial']

@admin.register(GrupoTipologia)
class GrupoTipologiaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'orden', 'anulado_por']

@admin.register(SubGrupoTipologia)
class GrupoTipologiaAdmin(admin.ModelAdmin):
    list_display = ['grupo', 'nombre', 'orden', 'anulado_por']

@admin.register(Propuesta)
class PropuestaAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'creado_en']
@admin.register(PropuestaLinea)
class PropuestaLineaAdmin(admin.ModelAdmin):
    raw_id_fields = ('propuesta', 'campanya_linea')
    list_display = ['propuesta', 'campanya_linea', 'estado', 'creado_en']
    list_filter = ['propuesta__cliente', 'estado']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'anulado_por']

@admin.register(Poblacion)
class PoblacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'provincia']

@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre']


@admin.register(Responsable)
class ResponsableAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'anulado_por']

@admin.register(Tipologia)
class TipologiaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'grupo', 'subgrupo', 'anulado_por']
    list_filter = ['grupo', 'subgrupo']

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username']
    