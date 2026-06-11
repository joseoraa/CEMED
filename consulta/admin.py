from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


admin.site.register(SliderImagen)
admin.site.register(Especialidad)
admin.site.register(DetalleInsumoCita)
admin.site.register(BCV)
admin.site.register(HistoriaMedica)
admin.site.register(Factura)
admin.site.register(DetalleInsumoExamen)
admin.site.register(ExamenRealizado)
admin.site.register(RealizarExamen)
admin.site.register(Examen)
admin.site.register(InsumoMedico)
admin.site.register(Emergencia)
admin.site.register(TriajeEmergencia)
admin.site.register(EvaluacionEmergencia)
admin.site.register(EvolucionEmergencia)
admin.site.register(DetalleInsumoEmergencia)
admin.site.register(ProcedimientoEmergencia)
admin.site.register(SolicitudExamenEmergencia)
admin.site.register(AuditoriaEmergencia)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('cedula', 'nombre', 'apellido', 'rol', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('nombre', 'apellido', 'fecha_nacimiento', 'telefono', 'rol')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('nombre', 'apellido', 'fecha_nacimiento', 'telefono', 'rol')}),
    )

class HorarioInline(admin.TabularInline):
    model = HorarioDoctor
    extra = 1

@admin.register(Doctorperfil)
class DoctorAdmin(admin.ModelAdmin):
    inlines = [HorarioInline]


@admin.register(CitaMedica)
class CitaMedicaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'doctor', 'fecha', 'hora', 'estado', 'creado_por')
    list_filter = ('estado', 'fecha', 'doctor')
    search_fields = ('paciente__nombre', 'paciente__apellido', 'doctor__usuario__nombre', 'doctor__usuario__apellido')

@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        super().save_model(request, obj, form, change)

@admin.register(FamiliarPaciente)
class FamiliarPacienteAdmin(admin.ModelAdmin):
    list_display = ( 'nombre',  'apellido',  'parentesco', 'paciente_titular',   'activo' )
    search_fields = (  'nombre',   'apellido' )
    list_filter = (     'parentesco',     'activo' )

