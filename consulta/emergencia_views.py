import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from .decoradores import rol_requerido
from .forms import *
from .models import *



def _auditoria_emergencia(emergencia, usuario, accion):
    AuditoriaEmergencia.objects.create(
        emergencia=emergencia,
        usuario=usuario,
        accion=accion,
    )


@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
@transaction.atomic
def registrar_emergencia(request):

    if request.method == 'POST':
        form = EmergenciaForm(request.POST)

        if form.is_valid():
            emergencia = form.save(commit=False)
            emergencia.creado_por = request.user
            emergencia.numero = f'EM-{timezone.now().strftime("%Y%m%d%H%M%S")}'

            tipo_persona = form.cleaned_data['tipo_persona']
            id_persona = form.cleaned_data.get('id_persona')

            if tipo_persona == 'EXISTENTE':

                if not id_persona:
                    form.add_error('id_persona', 'Debe seleccionar una persona.')
                    return render(request, 'Emergencia/registrar_emergencia.html', {'form': form})

                tipo, pk = id_persona.split('_')

                if tipo == 'U':
                    paciente = Usuario.objects.get(id=pk)
                    emergencia.paciente = paciente
                    emergencia.nombre_paciente = paciente.nombre
                    emergencia.apellido_paciente = paciente.apellido
                    emergencia.fecha_nacimiento = paciente.fecha_nacimiento
                    emergencia.sexo = paciente.sexo
                    emergencia.cedula = paciente.cedula
                    emergencia.telefono = paciente.telefono

                elif tipo == 'F':
                    familiar = FamiliarPaciente.objects.get(id=pk)
                    emergencia.familiar = familiar
                    emergencia.nombre_paciente = familiar.nombre
                    emergencia.apellido_paciente = familiar.apellido
                    emergencia.fecha_nacimiento = familiar.fecha_nacimiento
                    emergencia.sexo = familiar.sexo
                    emergencia.telefono = familiar.telefono

            elif tipo_persona == 'NUEVO_PACIENTE':

                paciente = Usuario.objects.create_user(
                    cedula=form.cleaned_data.get('cedula', ''),
                    email=f"{form.cleaned_data.get('cedula', 'temp')}@hospital.com",
                    password=secrets.token_urlsafe(10),
                    nombre=form.cleaned_data['nombre_paciente'],
                    apellido=form.cleaned_data['apellido_paciente'],
                    sexo=form.cleaned_data['sexo'],
                    fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
                    telefono=form.cleaned_data['telefono'],
                    rol=Usuario.PACIENTE
                )

                emergencia.paciente = paciente
                emergencia.nombre_paciente = paciente.nombre
                emergencia.apellido_paciente = paciente.apellido
                emergencia.fecha_nacimiento = paciente.fecha_nacimiento
                emergencia.sexo = paciente.sexo
                emergencia.cedula = paciente.cedula
                emergencia.telefono = paciente.telefono

            elif tipo_persona == 'NUEVO':

                familiar = FamiliarPaciente.objects.create(
                    paciente_titular=None,
                    nombre=form.cleaned_data['nombre_paciente'],
                    apellido=form.cleaned_data['apellido_paciente'],
                    sexo=form.cleaned_data['sexo'],
                    fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
                    telefono=form.cleaned_data['telefono'],
                    parentesco=FamiliarPaciente.OTRO
                )

                emergencia.familiar = familiar
                emergencia.nombre_paciente = familiar.nombre
                emergencia.apellido_paciente = familiar.apellido
                emergencia.fecha_nacimiento = familiar.fecha_nacimiento
                emergencia.sexo = familiar.sexo
                emergencia.telefono = familiar.telefono

            emergencia.save()
            _auditoria_emergencia(emergencia, request.user, 'Registro de emergencia')

            messages.success(request, 'Emergencia registrada correctamente.')
            return redirect('detalle_emergencia', emergencia_id=emergencia.id)

    else:
        form = EmergenciaForm()

    return render(request, 'Emergencia/registrar_emergencia.html', {'form': form})



@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
def lista_emergencias(request):

    buscar = request.GET.get('buscar', '')
    estado = request.GET.get('estado', '')

    emergencias = Emergencia.objects.select_related(
        'paciente',
        'familiar'
    )

    if buscar:

        emergencias = emergencias.filter(

            Q(numero__icontains=buscar) |

            Q(paciente__nombre__icontains=buscar) |

            Q(paciente__apellido__icontains=buscar) |

            Q(familiar__nombre__icontains=buscar) |

            Q(familiar__apellido__icontains=buscar) |

            Q(nombre_paciente__icontains=buscar) |

            Q(apellido_paciente__icontains=buscar)

        )
    if estado:
        emergencias = emergencias.filter(
            estado=estado
        )

    emergencias = emergencias.order_by(
        '-fecha_ingreso'
    )

    paginator = Paginator(
        emergencias,
        10
    )

    page_number = request.GET.get('page')

    emergencias_paginadas = paginator.get_page(
        page_number
    )

    return render(
        request,
        'Emergencia/lista_emergencias.html',
        {
            'emergencias': emergencias_paginadas,
            'buscar': buscar,
            'estado': estado,
        }
    )



@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
def detalle_emergencia(request, emergencia_id):
    emergencia = get_object_or_404(
        Emergencia.objects.select_related('paciente', 'familiar', 'creado_por'),
        pk=emergencia_id
    )

    triaje = emergencia.triajes.order_by('-fecha').first()
    evaluacion = emergencia.evaluaciones.select_related('doctor__usuario').first()
    evoluciones = emergencia.evoluciones.select_related('doctor__usuario').order_by('-fecha')
    insumos_usados = emergencia.insumos.select_related('insumo').order_by('-fecha')
    procedimientos = ProcedimientoEmergencia.objects.filter(
        emergencia=emergencia
    ).order_by('-fecha')
    solicitudes = emergencia.solicitudes_examen.select_related(
        'realizar_examen__examen'
    ).order_by('-fecha')
    auditoria = AuditoriaEmergencia.objects.filter(
        emergencia=emergencia
    ).select_related('usuario').order_by('-fecha')[:20]

    doctor_perfil = None
    if request.user.rol == 'DOCTOR':
        doctor_perfil = getattr(request.user, 'doctor_perfil', None)

    context = {
        'emergencia': emergencia,
        'triaje': triaje,
        'evaluacion': evaluacion,
        'evoluciones': evoluciones,
        'insumos_usados': insumos_usados,
        'procedimientos': procedimientos,
        'solicitudes': solicitudes,
        'auditoria': auditoria,
        'estado_form': EmergenciaEstadoForm(instance=emergencia),
        'evaluacion_form': EvaluacionEmergenciaForm(instance=evaluacion),
        'evolucion_form': EvolucionEmergenciaForm(),
        'insumo_form': DetalleInsumoEmergenciaForm(),
        'procedimiento_form': ProcedimientoEmergenciaForm(),
        'examenes_disponibles': Examen.objects.all().order_by('nom_exa'),
        'doctor_perfil': doctor_perfil,
    }

    return render(request, 'Emergencia/detalle_emergencia.html', context)


@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
@require_POST
def cambiar_estado_emergencia(request, emergencia_id):
    emergencia = get_object_or_404(Emergencia, pk=emergencia_id)
    form = EmergenciaEstadoForm(request.POST, instance=emergencia)

    if form.is_valid():
        emergencia = form.save()
        _auditoria_emergencia(
            emergencia,
            request.user,
            f'Estado cambiado a {emergencia.get_estado_display()}'
        )
        messages.success(request, 'Estado actualizado correctamente.')
    else:
        messages.error(request, 'No se pudo actualizar el estado.')

    return redirect('detalle_emergencia', emergencia_id=emergencia.id)


@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
def triaje_modal(request, emergencia_id):

    emergencia = get_object_or_404(Emergencia, pk=emergencia_id)
    triaje = emergencia.triajes.first()

    if request.method == 'POST':
        form = TriajeEmergenciaForm(request.POST, instance=triaje)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.emergencia = emergencia
            obj.full_clean()
            obj.save()
            _auditoria_emergencia(emergencia, request.user, 'Triaje registrado/actualizado')

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, 'Triaje guardado correctamente.')
            return redirect('detalle_emergencia', emergencia_id=emergencia.id)

    else:
        form = TriajeEmergenciaForm(instance=triaje)

    return render(
        request,
        'Emergencia/modal_triaje.html',
        {'form': form, 'emergencia': emergencia}
    )


@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
def ver_triaje(request, emergencia_id):

    emergencia = get_object_or_404(Emergencia, id=emergencia_id)
    triaje = emergencia.triajes.order_by('-fecha').first()

    return render(request, 'Emergencia/ver_triaje.html', {
        'triaje': triaje,
        'emergencia': emergencia
    })


@login_required
@rol_requerido(['DOCTOR'])
@require_POST
def evaluacion_emergencia(request, emergencia_id):
    emergencia = get_object_or_404(Emergencia, pk=emergencia_id)
    doctor = request.user.doctor_perfil
    evaluacion = emergencia.evaluaciones.first()

    form = EvaluacionEmergenciaForm(request.POST, instance=evaluacion)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.emergencia = emergencia
        obj.doctor = doctor
        obj.save()
        _auditoria_emergencia(emergencia, request.user, 'Evaluación médica registrada')
        messages.success(request, 'Evaluación guardada correctamente.')
    else:
        messages.error(request, 'Corrige los errores en la evaluación.')

    return redirect('detalle_emergencia', emergencia_id=emergencia.id)


@login_required
@rol_requerido(['DOCTOR'])
@require_POST
def evolucion_emergencia(request, emergencia_id):
    emergencia = get_object_or_404(Emergencia, pk=emergencia_id)
    doctor = request.user.doctor_perfil

    form = EvolucionEmergenciaForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.emergencia = emergencia
        obj.doctor = doctor
        obj.save()
        _auditoria_emergencia(emergencia, request.user, 'Nota de evolución agregada')
        messages.success(request, 'Evolución registrada.')
    else:
        messages.error(request, 'No se pudo registrar la evolución.')

    return redirect('detalle_emergencia', emergencia_id=emergencia.id)


@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
@require_POST
@transaction.atomic
def insumo_emergencia(request, emergencia_id):
    emergencia = get_object_or_404(Emergencia, pk=emergencia_id)
    form = DetalleInsumoEmergenciaForm(request.POST)

    if form.is_valid():
        try:
            obj = form.save(commit=False)
            obj.emergencia = emergencia
            obj.save()
            _auditoria_emergencia(
                emergencia,
                request.user,
                f'Insumo usado: {obj.insumo.nombre_ins} x {obj.cantidad}'
            )
            messages.success(request, 'Insumo registrado y stock actualizado.')
        except ValidationError as e:
            messages.error(request, '; '.join(e.messages) if hasattr(e, 'messages') else str(e))
    else:
        messages.error(request, 'Datos de insumo inválidos.')

    return redirect('detalle_emergencia', emergencia_id=emergencia.id)


@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
@require_POST
def procedimiento_emergencia(request, emergencia_id):
    emergencia = get_object_or_404(Emergencia, pk=emergencia_id)
    form = ProcedimientoEmergenciaForm(request.POST)

    if form.is_valid():
        obj = form.save(commit=False)
        obj.emergencia = emergencia
        obj.save()
        _auditoria_emergencia(
            emergencia,
            request.user,
            f'Procedimiento: {obj.nombre}'
        )
        messages.success(request, 'Procedimiento registrado.')
    else:
        messages.error(request, 'No se pudo registrar el procedimiento.')

    return redirect('detalle_emergencia', emergencia_id=emergencia.id)


@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
@require_POST
@transaction.atomic
def solicitar_examen_emergencia(request, emergencia_id):
    emergencia = get_object_or_404(Emergencia, pk=emergencia_id)
    examen_id = request.POST.get('examen_id')

    if not examen_id:
        messages.error(request, 'Debe seleccionar un examen.')
        return redirect('detalle_emergencia', emergencia_id=emergencia.id)

    examen = get_object_or_404(Examen, pk=examen_id)

    if emergencia.paciente:
        paciente = emergencia.paciente
        familiar = None
    elif emergencia.familiar and emergencia.familiar.paciente_titular:
        paciente = emergencia.familiar.paciente_titular
        familiar = emergencia.familiar
    else:
        messages.error(
            request,
            'La emergencia debe tener un paciente registrado para solicitar exámenes.'
        )
        return redirect('detalle_emergencia', emergencia_id=emergencia.id)

    doctor = None
    if request.user.rol == 'DOCTOR':
        doctor = request.user.doctor_perfil

    realizar = RealizarExamen.objects.create(
        paciente=paciente,
        familiar=familiar,
        examen=examen,
        doctor=doctor,
        total=examen.precio_exa,
        observacion=f'Solicitado desde emergencia {emergencia.numero}',
    )

    ExamenRealizado.objects.create(
        realizar_examen=realizar,
        examen=examen,
        subtotal=examen.precio_exa,
    )

    SolicitudExamenEmergencia.objects.create(
        emergencia=emergencia,
        realizar_examen=realizar,
    )

    _auditoria_emergencia(
        emergencia,
        request.user,
        f'Examen solicitado: {examen.nom_exa}'
    )
    messages.success(request, 'Examen solicitado correctamente.')
    return redirect('detalle_emergencia', emergencia_id=emergencia.id)
