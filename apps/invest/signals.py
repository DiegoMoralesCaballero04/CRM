from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from invest.models import Auditoria, Activo, Campanya, Cliente, Propuesta
from threading import local

_user = local()


def set_user(user):
    _user.value = user


def get_user():
    return getattr(_user, "value", None)


@receiver(post_save)
def registrar_creacion_o_edicion(sender, instance, created, **kwargs):

    if sender not in [Auditoria]:
        if hasattr(instance, "_meta") and instance._meta.app_label != "invest":
            return
        accion = "CREAR" if created else "EDITAR"
        usuario = get_user()

        Auditoria.objects.create(
            modelo=sender.__name__,
            objeto_id=instance.pk,
            accion=accion,
            descripcion=str(instance),
            usuario=usuario,
        )


@receiver(post_delete)
def registrar_eliminacion(sender, instance, **kwargs):
    if sender not in [Auditoria]:
        if hasattr(instance, "_meta") and instance._meta.app_label != "invest":
            return
        usuario = get_user()
        Auditoria.objects.create(
            modelo=sender.__name__,
            objeto_id=instance.pk,
            accion="ELIMINAR",
            descripcion=str(instance),
            usuario=usuario,
        )
