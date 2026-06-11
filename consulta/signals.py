from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Usuario, Doctorperfil


def crear_grupos(sender, **kwargs):
    grupos = ['Paciente', 'Enfermera', 'Doctor', 'Administración']
    for nombre in grupos:
        Group.objects.get_or_create(name=nombre)


@receiver(post_save, sender=Usuario)
def crear_perfil_doctor(sender, instance, created, **kwargs):
    if created and instance.rol == Usuario.DOCTOR:
        Doctorperfil.objects.get_or_create(usuario=instance)
