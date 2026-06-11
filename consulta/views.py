import json
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.core.serializers import serialize
from django.db import IntegrityError
from django.db.models import Count, Max
from django.forms.widgets import HiddenInput
from django.urls import reverse_lazy
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.generic import View, TemplateView, ListView, UpdateView, CreateView, DeleteView
from django.views.generic.edit import FormView
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponseForbidden
from django import forms
from django.utils import timezone
from django.template.loader import get_template
from django.forms.utils import ErrorDict
from django.core.management import call_command
from django.conf import settings
from django.contrib import messages
from functools import wraps
from io import BytesIO
import secrets
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.urls import reverse
from datetime import datetime, date, time, timedelta
from collections import defaultdict
from django.forms import modelformset_factory
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.timezone import now
from .models import *
from .forms import *
from .decoradores import rol_requerido
from django.template.loader import render_to_string
from django.db import transaction
from django.db.models import (    Sum,    F,    DecimalField,    ExpressionWrapper)
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.template.loader import get_template
from xhtml2pdf import pisa
from dateutil.relativedelta import relativedelta
from collections import Counter
from django.db.models.functions import Coalesce, Cast
from django.db.models.functions import ExtractMonth
from django.db.models.functions import ExtractYear
import calendar
import json
# from reportlab.lib.pagesizes import letter, landscape
# from reportlab.lib import colors
# from reportlab.platypus import (
#     SimpleDocTemplate, Table, TableStyle, Paragraph,
#     Spacer, Image, PageBreak)
# from reportlab.lib.enums import TA_CENTER,TA_LEFT,TA_JUSTIFY,TA_RIGHT
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.pdfgen import canvas
# from reportlab.lib.units import inch, mm
from .emergencia_views import *
from .reportes_views import *

# ====================================

# ====================================
def solo_no_logueado(view_func):
    """
    Evita que un usuario logueado acceda a la vista.
    Redirige al dashboard correspondiente según su rol.
    """
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            rol_redirect = {
                "PACIENTE": "pacientes_home",
                "ENFERMERA": "admin_home",
                "DOCTOR": "doctor_home",
                "ADMIN": "admin_home"
            }
            return redirect(rol_redirect.get(request.user.rol, "home"))
        return view_func(request, *args, **kwargs)
    return wrapper

# ====================================

# ====================================
@solo_no_logueado
def inicio(request):
    slider_imagenes = list(SliderImagen.objects.filter(activo=True))

    slides = []
    total = len(slider_imagenes)

    for i in range(total):
        izquierda = slider_imagenes[i - 1] if total > 1 else None
        centro = slider_imagenes[i]
        derecha = slider_imagenes[(i + 1) % total] if total > 1 else None

        slides.append({
            'izquierda': izquierda,
            'centro': centro,
            'derecha': derecha
        })

    return render(request, 'Inicio/index.html', {
        'slides': slides
    })

# ==========================actualizar usuario==========method_decorator([login_required, never_cache], name='dispatch')
@login_required
def actualizar_datos(request):
    user = request.user

    if request.method == 'POST':
        form = UsuarioActualizarForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Datos actualizados correctamente")
            return redirect('home')  # redirige a la página de inicio
    else:
        form = UsuarioActualizarForm(instance=user)

    context = {'form': form}
    return render(request, 'usuarios/actualizar_datos.html', context)
# ====================================
# ====================================
@login_required
def cambiar_password(request):
    user = request.user

    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()  # guarda la nueva contraseña
            logout(request)  # cierra sesión automáticamente
            messages.success(request, "✅ Contraseña cambiada correctamente. Por favor, inicia sesión de nuevo.")
            return redirect('login')  # redirige a login
    else:
        form = PasswordChangeForm(user)

    context = {'form': form}
    return render(request, 'usuarios/cambiar_password.html', context)

@login_required(login_url='inicio')
def home(request):
    rol_redirect = {
        "PACIENTE": "pacientes_home",
        "ENFERMERA": "enfermera_home",
        "DOCTOR": "doctor_home",
        "ADMIN": "admin_home"
    }
    return redirect(rol_redirect.get(request.user.rol, "login"))


# ====================================
@solo_no_logueado
def login_view(request):

    # 🔁 Si ya está autenticado
    if request.user.is_authenticated:
        rol_redirect = {
            "PACIENTE": "pacientes_home",
            "ENFERMERA": "enfermera_home",
            "DOCTOR": "doctor_home",
            "ADMIN": "admin_home"
        }
        return redirect(rol_redirect.get(request.user.rol, "home"))

    if request.method == "POST":

        cedula = request.POST.get("cedula")
        password = request.POST.get("password")

        try:
            user = Usuario.objects.get(cedula=cedula)
        except Usuario.DoesNotExist:
            messages.error(request, "❌ Usuario incorrecto")
            return render(request, "usuarios/login.html")

        if user.bloqueado:
            messages.error(request, " Usuario bloqueado. Contacte al administrador.")
            return render(request, "usuarios/login.html")

        # 🔐 Autenticación
        user_auth = authenticate(request, username=cedula, password=password)

        if user_auth:


            user_auth.intentos_fallidos = 0
            user_auth.save()

            login(request, user_auth)

            messages.success(request, f"Bienvenido {user_auth.nombre}!")

            rol_redirect = {
                "PACIENTE": "pacientes_home",
                "ENFERMERA": "enfermera_home",
                "DOCTOR": "doctor_home",
                "ADMIN": "admin_home"
            }

            return redirect(rol_redirect.get(user_auth.rol, "home"))

        else:

            # ❌ Aumentar intentos fallidos
            user.intentos_fallidos += 1

            # 🔒 Bloquear al tercer intento
            if user.intentos_fallidos >= 3:
                user.bloqueado = True
                messages.error(request, "⛔ Usuario bloqueado por 3 intentos fallidos")
            else:
                restantes = 3 - user.intentos_fallidos
                messages.error(request, f"❌ Contraseña incorrecta. Intentos restantes: {restantes}")

            user.save()

    return render(request, "usuarios/login.html")
# ====================================
@login_required
@rol_requerido(['ADMIN'])
def desbloquear_usuario(request, id):

    usuario = get_object_or_404(Usuario, id=id)

    usuario.bloqueado = False
    usuario.intentos_fallidos = 0
    usuario.save()

    messages.success(request, f"Usuario {usuario.nombre} desbloqueado correctamente")

    return redirect('listar_usuarios')

# ====================================
def logout_view(request):
    logout(request)
    return redirect("login")
# ====================================
@login_required
@rol_requerido(['ADMIN'])
def crear_usuario(request):
    if request.method == "POST":
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect('admin_home')  # Volver al dashboard del admin
    else:
        form = CrearUsuarioForm()
    
    return render(request, 'admin/crear_usuario.html', {'form': form})

# ====================================
@login_required
@rol_requerido(['ADMIN'])
def listar_usuarios(request):
    lista_usuarios = Usuario.objects.all().order_by('id')
    paginator = Paginator(lista_usuarios, 10)
    page_number = request.GET.get('page')
    usuarios_paginados = paginator.get_page(page_number)
    return render(request, 'admin/listar_usuarios.html', {
        'usuarios': usuarios_paginados
    })

# =====================================
@login_required
@rol_requerido(['ADMIN'])
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, pk=user_id)
    if request.method == "POST":
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect('listar_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario)
    return render(request, 'admin/editar_usuario.html', {'form': form, 'usuario': usuario})

# =====================================
@login_required
@rol_requerido(['ADMIN'])
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, pk=user_id)

    if request.method == "POST":
        usuario.delete()
        messages.success(request, "Usuario eliminado correctamente.")
        return redirect("listar_usuarios")

    return render(request, "admin/eliminar_usuario.html", {"usuario": usuario})

# =====================================
@login_required
def pacientes_home(request):
    paciente = request.user
    citas = CitaMedica.objects.filter(paciente=paciente)
    total_citas = citas.count()
    citas_pendientes = citas.filter(estado="PENDIENTE").count()
    citas_confirmadas = citas.filter(estado="CONFIRMADA").count()
    citas_atendidas = citas.filter(estado="ATENDIDA").count()

    proxima_cita = citas.filter(
        fecha__gte=date.today()
    ).order_by("fecha", "hora").first()
    familiares = FamiliarPaciente.objects.filter(paciente_titular=paciente)
    total_familiares = familiares.count()
    examenes_recientes = RealizarExamen.objects.select_related(
        'paciente',
        'familiar',
        'doctor',
        'doctor__usuario',
        'examen'
    ).prefetch_related(
    'examenes_realizados',
    'examenes_realizados__examen'

    ).filter(
        Q(paciente=paciente) |
        Q(familiar__paciente_titular=paciente)
    ).order_by('-id')[:10]

    total_examenes = ExamenRealizado.objects.filter(
        Q(realizar_examen__paciente=paciente) |
        Q(realizar_examen__familiar__paciente_titular=paciente)
    ).count()

    context = {
        "total_citas": total_citas,
        "citas_pendientes": citas_pendientes,
        "citas_confirmadas": citas_confirmadas,
        "citas_atendidas": citas_atendidas,
        "proxima_cita": proxima_cita,
        "total_familiares": total_familiares,
        "total_examenes": total_examenes,
        "examenes_recientes": examenes_recientes,
    }

    return render(request, "pacientes/home.html", context)
# =====================================
@login_required
def enfermera_home(request):
    return redirect('admin_home')

# =====================================
@login_required
def doctor_home(request):
    user = request.user
    try:
        perfil = user.doctor_perfil
    except Doctorperfil.DoesNotExist:
        messages.error(request, "No tienes un perfil de doctor asociado.")
        return redirect('home')

    hoy = date.today()

    # ✔ USAMOS PERFIL, NO USER
    citas_hoy_qs = CitaMedica.objects.filter(
        doctor=perfil,
        fecha=hoy
    )

    examenes_realizados = RealizarExamen.objects.filter(
        doctor=perfil
    ).count()

    context = {
        'perfil': perfil,

        'citas_hoy': citas_hoy_qs.count(),
        'citas_pendientes': citas_hoy_qs.filter(estado='PENDIENTE').count(),
        'citas_atendidas_hoy': citas_hoy_qs.filter(estado='ATENDIDA').count(),

        'examenes_realizados': examenes_realizados,
    }

    return render(request, "doctor/home.html", context)
# ====================================
@login_required
def especialidades(request):
    # Obtenemos todas las especialidades ordenadas (el orden es vital para paginar)
    lista_especialidades = Especialidad.objects.all().order_by('nombre_espe') 

    if request.method == 'POST':
        form = EspecialidadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('especialidades')
    else:
        form = EspecialidadForm()

    # --- Lógica de Paginación ---
    paginator = Paginator(lista_especialidades, 5) # 5 elementos por página
    page_number = request.GET.get('page')
    especialidades_paginadas = paginator.get_page(page_number)

    return render(request, 'doctor/especialidad.html', {
        'form': form,
        'especialidades': especialidades_paginadas # Pasamos el objeto paginado
    })

@login_required
def editar_especialidad(request, id):
    especialidad = get_object_or_404(Especialidad, id=id)

    if request.method == 'POST':
        form = EspecialidadForm(request.POST, instance=especialidad)
        if form.is_valid():
            form.save()

    return redirect('especialidades')


@login_required
def eliminar_especialidad(request, id):
    especialidad = get_object_or_404(Especialidad, id=id)

    if request.method == 'POST':
        especialidad.delete()

    return redirect('especialidades')
# ====================================

@login_required
def editar_perfil_doctor(request):
    doctor = request.user.doctor_perfil
    if request.method == 'POST':
        form = DoctorPerfilForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil de doctor actualizado correctamente.")
            return redirect('doctor_home')
    else:
        form = DoctorPerfilForm(instance=doctor)

    return render(request, 'doctor/editar_perfil.html', {'form': form})
# ====================================
# ====================================
# ====================================
@login_required
def registrar_horario(request, doctor_id):
    doctor = get_object_or_404(Doctorperfil, id=doctor_id)
    horarios = doctor.horarios.all()  # Obtener horarios existentes
    errores = []

    if request.method == "POST":
        dias = request.POST.getlist("dia")
        horas_inicio = request.POST.getlist("hora_inicio")
        horas_fin = request.POST.getlist("hora_fin")

        horarios_a_guardar = []
        dias_vistos = set()

        for i, (dia, inicio, fin) in enumerate(zip(dias, horas_inicio, horas_fin), start=1):
            # Validación campos vacíos
            if not dia or not inicio or not fin:
                errores.append(f"El horario está incompleto.")
                continue

            # Validación hora_inicio < hora_fin
            if inicio >= fin:
                errores.append(f"Verifique la Hora.")
                continue

            # Validar días repetidos en la misma request
            if dia in dias_vistos:
                errores.append(f"El horario ({dia}) está repetido en la misma solicitud.")
                continue
            dias_vistos.add(dia)

            # Validar que no exista ya en la base de datos
            if HorarioDoctor.objects.filter(doctor=doctor, dia=dia).exists():
                errores.append(f" Este {dia} ya tiene un horario registrado .")
                continue

            horarios_a_guardar.append((dia, inicio, fin))

        # Si no hay errores, guardar horarios
        if not errores:
            for dia, inicio, fin in horarios_a_guardar:
                HorarioDoctor.objects.create(
                    doctor=doctor,
                    dia=dia,
                    hora_inicio=inicio,
                    hora_fin=fin
                )
            return redirect('registrar_horario', doctor_id=doctor.id)

    # GET o si hay errores
    form = HorarioDoctorForm()
    return render(request, 'doctor/registrar_horario.html', {
        'form': form,
        'doctor': doctor,
        'horarios': horarios,
        'errores': errores
    })

# ====================================
# ====================================

@login_required
def eliminar_horario(request, horario_id):
    horario = get_object_or_404(HorarioDoctor, id=horario_id)
    doctor_id = horario.doctor.id
    horario.delete()
    return redirect('registrar_horario', doctor_id=doctor_id)

# ====================================
# ====================================

@login_required
def editar_horario(request, horario_id):
    horario = get_object_or_404(HorarioDoctor, id=horario_id)
    errores = []

    if request.method == "POST":
        form = HorarioDoctorForm(request.POST, instance=horario)
        if form.is_valid():
            form.save()
            return redirect('registrar_horario', doctor_id=horario.doctor.id)
        else:
            # Captura los errores del form
            for field, msgs in form.errors.items():
                for msg in msgs:
                    errores.append(f"{field}: {msg}")

    # Redirige a registrar_horario mostrando los errores en el template
    doctor = horario.doctor
    horarios = doctor.horarios.all()
    form_nuevo = HorarioDoctorForm()  # formulario para agregar nuevos

    return render(request, 'doctor/registrar_horario.html', {
        'form': form_nuevo,
        'doctor': doctor,
        'horarios': horarios,
        'errores': errores
    })

# ====================================
# ====================================
# ====================================

@login_required
def examenes(request):
    examenes = Examen.objects.all().order_by('codigo_exa')

    if request.method == "POST":
        form = ExamenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Examen guardado correctamente!") 
            return redirect('examenes')
        else:
            messages.error(request, "Error al guardar. Revisa los datos.") 
    else:
        form = ExamenForm()

    return render(request, 'examenes/examenes.html', {
        'examenes': examenes,
        'form': form,
        'form_editar': ExamenForm(),
    })

# =====================================
# =====================================

@login_required
def editar_examen(request, examen_id):

    examen = get_object_or_404(Examen, id=examen_id)

    if request.method == "POST":

        form = ExamenForm(request.POST, instance=examen)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                f"Examen {examen.nom_exa} actualizado con éxito."
            )
        else:
            messages.error(request, "Error al actualizar el examen.")
    return redirect('lista_examenes')

# =====================================
# =====================================

@login_required
def eliminar_examen(request, examen_id):
    examen = get_object_or_404(Examen, id=examen_id)

    if request.method == "POST":
        examen.delete()
        messages.error(request, "El examen ha sido eliminado.")

    return redirect('lista_examenes')  # ← CORREGIDO

# =====================================
# =====================================
@login_required
def lista_examenes(request):

    buscar = request.GET.get('buscar', '')

    lista_examenes = Examen.objects.all()

    if buscar:
        lista_examenes = lista_examenes.filter(
            Q(codigo_exa__icontains=buscar) |
            Q(nom_exa__icontains=buscar)|
            Q(tipo_exa__icontains=buscar)
        )

    lista_examenes = lista_examenes.order_by('nom_exa')

    paginator = Paginator(lista_examenes, 10)
    page_number = request.GET.get('page')
    examenes_paginados = paginator.get_page(page_number)

    return render(request, 'examenes/lista_examenes.html', {
        'examen': examenes_paginados,
        'buscar': buscar,
    })
# ====================================
@login_required
def examenes_disponibles(request):

    buscar = request.GET.get('buscar', '')

    lista_examenes = Examen.objects.all()

    # 🔎 BUSCADOR REAL (backend)
    if buscar:
        lista_examenes = lista_examenes.filter(
            Q(nom_exa__icontains=buscar) |
            Q(tipo_exa__icontains=buscar)
        )

    lista_examenes = lista_examenes.order_by(
        'tipo_exa',
        'nom_exa'
    )

    paginator = Paginator(lista_examenes, 10)
    page_number = request.GET.get('page')
    examen = paginator.get_page(page_number)

    return render(request, 'examenes/examenes_disponibles.html', {
        'examen': examen,
        'buscar': buscar
    })
# ====================================
@login_required
def doctores_disponibles(request):

    buscar = request.GET.get('buscar', '')

    lista_doctores = Doctorperfil.objects.select_related(
        'usuario',
        'especialidad'
    ).prefetch_related(
        'horarios'
    )
    if buscar:
        lista_doctores = lista_doctores.filter(
            Q(usuario__nombre__icontains=buscar) |
            Q(usuario__apellido__icontains=buscar) |
            Q(especialidad__nombre_espe__icontains=buscar)
        )

    lista_doctores = lista_doctores.order_by(
        'especialidad__nombre_espe',
        'usuario__nombre'
    )

    paginator = Paginator(lista_doctores, 8)
    page_number = request.GET.get('page')
    doctores = paginator.get_page(page_number)

    return render(request, 'doctor/doctores_disponibles.html', {
        'doctores': doctores,
        'buscar': buscar
    })

# =====================================
@login_required
def insumos(request):
    insumos = InsumoMedico.objects.all().order_by('fecha_caducidad_ins')
    insumos_bajos = InsumoMedico.objects.filter(
        cantidad_ins__lte=F('stock_minimo')
    )


    if request.method == "POST":
        form = InsumoMedicoForm(request.POST)
        if form.is_valid():
            insumo = form.save()
            messages.success(request, f"✅ El insumo '{insumo.nombre_ins}' fue creado correctamente.")
            return redirect('insumos')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = InsumoMedicoForm()

    return render(request, 'insumos/insumos.html', {
        'insumos': insumos,
        'insumos_bajos': insumos_bajos,
        'form': form,
    })




# ====================================
@login_required
def lista_insumos(request):
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)

    insumos_qs = InsumoMedico.objects.all().order_by('nombre_ins')

    if query:
        insumos_qs = insumos_qs.filter(
            Q(codigo_ins__icontains=query) |
            Q(nombre_ins__icontains=query)
        )

    insumos_bajos = InsumoMedico.objects.filter(cantidad_ins__lte=F('stock_minimo'))

    paginator = Paginator(insumos_qs, 10)
    page_obj = paginator.get_page(page_number)

    # ===================== AJAX =====================
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
        data_insumos = [{
            'id': i.id,
            'codigo': i.codigo_ins,
            'nombre': i.nombre_ins,
            'cantidad': i.cantidad_ins,
        } for i in page_obj]

        return JsonResponse({
            'insumos': data_insumos,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'number': page_obj.number,
            'num_pages': paginator.num_pages,
        })
    
    contexto_modales = []

    for insumo in insumos_qs:
        movimientos = insumo.movimientos.select_related(
            'usuario',
            'cita__paciente',
            'cita__doctor',
            'realizar_examen__paciente',
            'realizar_examen__doctor',
        ).order_by('-fecha')

        total_entradas = movimientos.filter(tipo='ENTRADA').aggregate(
            total=Coalesce(Sum('cantidad'), 0)
        )['total']

        total_salidas = movimientos.filter(tipo='SALIDA').aggregate(
            total=Coalesce(Sum('cantidad'), 0)
        )['total']

        contexto_modales.append({
            'insumo': insumo,
            'movimientos': movimientos,
            'total_entradas': total_entradas,
        'total_salidas': total_salidas,
    })
    return render(request, 'insumos/listainsumos.html', {
        'insumos': page_obj,
        'insumos_bajos': insumos_bajos,
        'modales_data': contexto_modales,
    })

    # contexto_modales = []

    # for insumo in page_obj:
    #     movimientos = insumo.movimientos.select_related(
    #         'usuario',
    #         'cita__paciente',
    #         'cita__doctor',
    #         'realizar_examen__paciente',
    #         'realizar_examen__doctor',
    #     ).order_by('-fecha')

    #     total_entradas = movimientos.filter(tipo='ENTRADA').aggregate(
    #         total=Coalesce(Sum('cantidad'), 0)
    #     )['total']

    #     total_salidas = movimientos.filter(tipo='SALIDA').aggregate(
    #         total=Coalesce(Sum('cantidad'), 0)
    #     )['total']

    #     contexto_modales.append({
    #         'insumo': insumo,
    #         'movimientos': movimientos,
    #         'total_entradas': total_entradas,
    #         'total_salidas': total_salidas,
    #     })

    # return render(request, 'insumos/listainsumos.html', {
    #     'insumos': page_obj,
    #     'insumos_bajos': insumos_bajos,
    #     'modales_data': contexto_modales,
    # })
# ====================================


# ====================================
@login_required
def entrada_insumo(request, insumo_id):
    insumo = get_object_or_404(InsumoMedico, id=insumo_id)

    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad'))
        descripcion = request.POST.get('descripcion', '')

        MovimientoStock.objects.create(
            insumo=insumo,
            tipo='ENTRADA',
            cantidad=cantidad,
            stock_anterior=insumo.cantidad_ins,
            stock_actual=insumo.cantidad_ins + cantidad,
            descripcion=descripcion,
            usuario=request.user,          # ← Esto debe estar
        )

        insumo.cantidad_ins += cantidad
        insumo.save()

        messages.success(request, f'Se registraron {cantidad} unidades de {insumo.nombre_ins}')
    
    return redirect('lista_insumos')
# ====================================
@login_required
def mostrar_insumo(request, insumo_id):
    insumo = get_object_or_404(InsumoMedico, id=insumo_id)
    return render(request, 'insumos/mostrar_insumo.html', {
        'i': insumo
    })

# =====================================
@login_required
def editar_insumo(request, insumo_id):

    insumo = get_object_or_404(InsumoMedico, id=insumo_id)

    if request.method == "POST":
        insumo.codigo_ins = request.POST.get("codigo_ins")
        insumo.nombre_ins = request.POST.get("nombre_ins")
        insumo.presentacion_ins = request.POST.get("presentacion_ins")
        insumo.descripcion_ins = request.POST.get("descripcion_ins")
        insumo.cantidad_ins = request.POST.get("cantidad_ins")
        insumo.precio_unitario_ins = Decimal(request.POST.get("precio_unitario_ins"))   
        insumo.fecha_caducidad_ins = request.POST.get("fecha_caducidad_ins")
        insumo.proveedor_ins = request.POST.get("proveedor_ins")

        insumo.save()

        messages.success(request, f"✏️ El insumo '{insumo.nombre_ins}' fue actualizado correctamente.")

    return redirect('lista_insumos')


# ====================================
@login_required
def eliminar_insumo(request, insumo_id):
    insumo = get_object_or_404(InsumoMedico, id=insumo_id)
    if request.method == "POST":
        nombre = insumo.nombre_ins
        insumo.delete()
        messages.success(request, f"🗑️ El insumo '{nombre}' fue eliminado correctamente.")
    return redirect('lista_insumos')

# =====================================
@login_required
def admin_home(request):

    hoy = date.today()

    pacientes_count = Usuario.objects.filter(
        rol=Usuario.PACIENTE
    ).count()

    doctores_count = Usuario.objects.filter(
        rol=Usuario.DOCTOR
    ).count()

    enfermeras_count = Usuario.objects.filter(
        rol=Usuario.ENFERMERA
    ).count()

    administradores_count = Usuario.objects.filter(
        rol=Usuario.ADMINISTRACION
    ).count()

    citas_hoy = CitaMedica.objects.filter(
        fecha=hoy
    ).count()

    citas_pendientes = CitaMedica.objects.filter(
        estado='PENDIENTE'
    ).count()

    citas_confirmadas = CitaMedica.objects.filter(
        estado='CONFIRMADA'
    ).count()

    citas_atendidas = CitaMedica.objects.filter(
        estado='ATENDIDA'
    ).count()

    examenes_count = RealizarExamen.objects.count()

    insumos_count = InsumoMedico.objects.count()

    stock_bajo = InsumoMedico.objects.filter(
        cantidad_ins__lte=10
    ).count()

    ahora = timezone.localtime()

    proximas_citas = CitaMedica.objects.select_related(
        'doctor__usuario'
    ).filter(
        estado__in=[
            CitaMedica.PENDIENTE,
            CitaMedica.CONFIRMADA
        ]
    ).filter(
        Q(fecha__gt=ahora.date()) |
        Q(
            fecha=ahora.date(),
            hora__gte=ahora.time()
        )
    ).order_by(
        'fecha',
        'hora'
    )[:10]

    ultimos_examenes = RealizarExamen.objects.select_related(
        'paciente',
        'doctor'
    ).order_by('-id')[:10]

    context = {
        'pacientes_count': pacientes_count,
        'doctores_count': doctores_count,
        'enfermeras_count': enfermeras_count,
        'administradores_count': administradores_count,

        'citas_hoy': citas_hoy,
        'citas_pendientes': citas_pendientes,
        'citas_confirmadas': citas_confirmadas,
        'citas_atendidas': citas_atendidas,

        'examenes_count': examenes_count,
        'insumos_count': insumos_count,
        'stock_bajo': stock_bajo,

        'proximas_citas': proximas_citas,
        'ultimos_examenes': ultimos_examenes,
    }

    return render(
        request,
        "admin/home.html",
        context
    )
# ====================================

# ====================================
@solo_no_logueado
def registro_paciente(request):
    if request.method == "POST":
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario registrado correctamente. Ahora puedes iniciar sesión.")
            return redirect("login")
    else:
        form = RegistroPacienteForm()
    
    return render(request, "usuarios/registro.html", {"form": form})



# ====================================
def admin_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.rol == "ADMIN")(view_func))
    return decorated_view_func
# ==========================================
@admin_required
def slider_agregar(request):
    if request.method == 'POST':
        form = SliderImagenForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('slider_listado')
    else:
        form = SliderImagenForm()
    return render(request, 'admin/slider_agregar.html', {'form': form})


# =====================================
@admin_required
def slider_listado(request):
    imagenes = SliderImagen.objects.all()
    return render(request, 'admin/slider_listado.html', {'imagenes': imagenes})
# =====================================
# =====================================
@admin_required
def alternar_estado_slider(request, pk):
    imagen = get_object_or_404(SliderImagen, pk=pk)
    imagen.activo = not imagen.activo
    imagen.save()
    return redirect('slider_listado')
# =====================================
@admin_required
def eliminar_slider(request, pk):
    imagen = get_object_or_404(SliderImagen, pk=pk)
    imagen.delete()
    return redirect('slider_listado')


# =====================================

# =====================================
@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
def lista_pacientes(request):
    pacientes = Usuario.objects.filter(rol=Usuario.PACIENTE).order_by('apellido', 'nombre')
    familiares = FamiliarPaciente.objects.filter( activo=True)
    return render(request, 'pacientes/lista_pacientes.html', {'pacientes': pacientes,'familiares': familiares,})
# ====================================PACIENTES PACIENTES 

# =====================================
@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
def buscar_pacientes(request):

    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)

    pacientes = Usuario.objects.filter(
        rol=Usuario.PACIENTE
    )

    familiares = FamiliarPaciente.objects.filter(
        activo=True
    )

    if query:

        pacientes = pacientes.filter(
            Q(cedula__icontains=query) |
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query)
        )

        familiares = familiares.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query)
        )

    data = []
    for p in pacientes:

        data.append({
            'id': p.id,
            'tipo': 'PACIENTE',
            'cedula': f"{p.tipo_cedula}-{p.cedula}",
            'nombre': f"{p.nombre} {p.apellido}",
            'email': p.email,
            'telefono': p.telefono or 'N/A'        })
    # FAMILIARES
    for f in familiares:

        data.append({
            'id': f.id,
            'tipo': 'FAMILIAR',
            'cedula': 'SIN CÉDULA',
            'nombre': f"{f.nombre} {f.apellido}",
            'email': 'N/A',
            'telefono': f.telefono or 'N/A'
        })
    data = sorted(data, key=lambda x: x['nombre'])
    paginator = Paginator(data, 10)
    page_obj = paginator.get_page(page_number)
    return JsonResponse({
        'pacientes': list(page_obj),
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'number': page_obj.number,
        'num_pages': paginator.num_pages,
    })
# =====================================
@login_required
def mis_examenes_medicos(request):
    user = request.user
    historia = None
    if user.rol == Usuario.PACIENTE:
        historia = HistoriaMedica.objects.filter(paciente=user).first()
    if not historia:
        familiar = FamiliarPaciente.objects.filter(
            paciente_titular=user
        ).first()

        if familiar:
            historia = HistoriaMedica.objects.filter(
                familiar=familiar
            ).first()
    examenes = historia.examenes.all().order_by('-fecha_examen') if historia else []
    return render(request, 'pacientes/mis_examenes.html', {
        'historia': historia,
        'examenes': examenes
    })

# # =====================================
@login_required
def historia_medica_modal(request, tipo, paciente_id):

    paciente = None
    familiar = None

    if tipo == 'PACIENTE':

        paciente = get_object_or_404(
            Usuario,
            id=paciente_id,
            rol=Usuario.PACIENTE
        )

        historia = HistoriaMedica.objects.filter(
            paciente=paciente
        ).first()

        nombre = f"{paciente.nombre} {paciente.apellido}"

    else:

        familiar = get_object_or_404(
            FamiliarPaciente,
            id=paciente_id
        )

        historia = HistoriaMedica.objects.filter(
            familiar=familiar
        ).first()

        nombre = f"{familiar.nombre} {familiar.apellido}"

    # =========================
    if request.method == 'POST':

        form = HistoriaMedicaForm(request.POST, instance=historia)

        if form.is_valid():

            historia = form.save(commit=False)

            # asignar relación
            if paciente:
                historia.paciente = paciente

            if familiar:
                historia.familiar = familiar

            historia.save()

            # =========================
            # 🔥 GUARDAR EXAMEN MÉDICO
            # =========================
            if request.FILES.get('archivo'):

                ExamenMedico.objects.create(
                    historia_medica=historia,
                    nombre_examen=request.POST.get('nombre_examen', ''),
                    fecha_examen=request.POST.get('fecha_examen') or None,
                    archivo=request.FILES.get('archivo'),
                    descripcion=request.POST.get('descripcion', '')
                )

            html = render_to_string(
                'pacientes/historia_modal.html',
                {
                    'form': HistoriaMedicaForm(instance=historia),
                    'historia': historia,
                    'paciente': paciente,
                    'familiar': familiar,
                    'nombre': nombre,
                },
                request=request
            )

            return JsonResponse({
                'success': True,
                'html': html,
                'message': 'Guardado correctamente'
            })

        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    # =========================
    # GET
    # =========================
    form = HistoriaMedicaForm(instance=historia)

    html = render_to_string(
        'pacientes/historia_modal.html',
        {
            'form': form,
            'historia': historia,
            'paciente': paciente,
            'familiar': familiar,
            'nombre': nombre,
        },
        request=request
    )

    return JsonResponse({
        'html': html,
        'paciente_nombre': nombre
    })
# =====================================



# =====================================
@login_required
def ver_historia_medica(request, tipo, paciente_id):

    paciente = None
    familiar = None
    historia = None

    if tipo == 'PACIENTE':

        paciente = get_object_or_404(
            Usuario,
            id=paciente_id,
            rol=Usuario.PACIENTE
        )

        historia = getattr(paciente, 'historia_medica', None)
        fecha_nacimiento = paciente.fecha_nacimiento

    else:

        familiar = get_object_or_404(
            FamiliarPaciente,
            id=paciente_id
        )

        historia = getattr(familiar, 'historia_medica', None)
        fecha_nacimiento = familiar.fecha_nacimiento

    hoy = date.today()

    edad = hoy.year - fecha_nacimiento.year

    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1

    examenes_ordenados = []

    if historia:
        examenes_ordenados = historia.examenes.all().order_by('-fecha_examen')

    html = render_to_string(
        'pacientes/ver_historia_medica.html',
        {
            'paciente': paciente,
            'familiar': familiar,
            'historia': historia,
            'edad': edad,
            'examenes': examenes_ordenados,
        },
        request=request
    )

    nombre_paciente = ""

    if paciente:
        nombre_paciente = f"{paciente.nombre} {paciente.apellido}"

    if familiar:
        nombre_paciente = f"{familiar.nombre} {familiar.apellido}"

    return JsonResponse({
        'html': html,
        'paciente_nombre': nombre_paciente
    })
# =====================================

# =====================================


@login_required
def lista_doctores(request):
    doctores = Usuario.objects.filter(rol=Usuario.DOCTOR).order_by('apellido', 'nombre')
    return render(request, 'doctor/lista_doctores.html', {'doctores': doctores})
# ====================================d

@login_required
def buscar_doctores(request):
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    order_by = request.GET.get('order', 'apellido') # Recibe el criterio de orden

    # Optimizamos la consulta con select_related para evitar múltiples hits a la BD
    doctores_qs = Usuario.objects.filter(
        rol=Usuario.DOCTOR
    ).select_related('doctor_perfil', 'doctor_perfil__especialidad').order_by(order_by, 'nombre')

    if query:
        doctores_qs = doctores_qs.filter(
            Q(cedula__icontains=query) |
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query)
        )

    paginator = Paginator(doctores_qs, 5) # 5 por página
    page_obj = paginator.get_page(page_number)

    data_doctores = []
    for d in page_obj:
        # Manejo seguro de la relación perfil/especialidad
        perfil = getattr(d, 'doctor_perfil', None)
        especialidad = "Sin especialidad"
        if perfil and perfil.especialidad:
            especialidad = perfil.especialidad.nombre_espe

        data_doctores.append({
            'id': d.id,
            'cedula': f"{d.tipo_cedula}{d.cedula}",
            'nombre': f"{d.nombre} {d.apellido}",
            'email': d.email,
            'telefono': d.telefono or 'N/A',
            'especialidad': especialidad,
        })

    return JsonResponse({
        'doctores': data_doctores,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'number': page_obj.number,
        'num_pages': paginator.num_pages,
    })

# =====================================
# =====================================
@login_required
def seleccion_pdf_doctores(request):

    especialidades = Especialidad.objects.all()

    doctores = Doctorperfil.objects.select_related(
        'usuario',
        'especialidad'
    ).prefetch_related(
        'horarios'
    ).order_by(
        'especialidad__nombre_espe',
        'usuario__apellido'
    )

    especialidad_id = request.GET.get('especialidad')
    doctor_id = request.GET.get('doctor')

    if especialidad_id:
        doctores = doctores.filter(especialidad_id=especialidad_id)

    if doctor_id:
        doctores = doctores.filter(id=doctor_id)

    context = {
        'especialidades': especialidades,
        'doctores': doctores,
        'especialidad_id': especialidad_id,
        'doctor_id': doctor_id,
    }

    return render(
        request,
        'doctor/seleccion_pdf_doctores.html',
        context
    )
# =====================================
@login_required
def pdf_doctores_horarios(request):

    especialidad_id = request.GET.get('especialidad')
    doctor_id = request.GET.get('doctor')

    doctores = Doctorperfil.objects.select_related(
        'usuario',
        'especialidad'
    ).prefetch_related(
        'horarios'
    ).order_by(
        'especialidad__nombre_espe',
        'usuario__apellido'
    )

    if especialidad_id:
        doctores = doctores.filter(especialidad_id=especialidad_id)

    if doctor_id:
        doctores = doctores.filter(id=doctor_id)

    template = get_template(
        'doctor/pdf_doctores_horarios.html'
    )

    html = template.render({
        'doctores': doctores
    })

    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = (
        'inline; filename="doctores_horarios.pdf"'
    )

    pisa.CreatePDF(
        html,
        dest=response
    )
    return response
# =====================================




# =====================================
@login_required
def obtener_horas_disponibles(request):
    doctor_id = request.GET.get('doctor_id')
    fecha_str = request.GET.get('fecha')

    if not doctor_id or not fecha_str:
        return JsonResponse({'horas': []})

    try:
        doctor = Doctorperfil.objects.get(id=doctor_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (Doctorperfil.DoesNotExist, ValueError):
        return JsonResponse({'horas': []})

    dias_map = {
        0: 'lunes',
        1: 'martes',
        2: 'miercoles',
        3: 'jueves',
        4: 'viernes',
        5: 'sabado',
        6: 'domingo',
    }

    dia_semana = dias_map[fecha.weekday()]

    horarios = HorarioDoctor.objects.filter(
        doctor=doctor,
        dia=dia_semana
    )

    horas_disponibles = []

    for horario in horarios:
        hora_actual = datetime.combine(fecha, horario.hora_inicio)
        hora_fin = datetime.combine(fecha, horario.hora_fin)

        while hora_actual < hora_fin:
            hora_str = hora_actual.strftime('%H:%M')

            # Verificar si esa hora ya está ocupada
            ocupada = CitaMedica.objects.filter(
                doctor=doctor,
                fecha=fecha,
                hora=hora_actual.time()
            ).exclude(estado='CANCELADA').exists()

            # Evitar horas pasadas si es hoy
            ahora = datetime.now()
            if fecha == ahora.date() and hora_actual <= ahora:
                ocupada = True

            if not ocupada:
                horas_disponibles.append({
                    'value': hora_str,
                    'label': hora_str
                })

            # Intervalo de 30 minutos
            hora_actual += timedelta(minutes=30)

    return JsonResponse({'horas': horas_disponibles})


# =====================================================================
@login_required
def solicitar_cita(request):

    if request.user.rol != 'PACIENTE':
        messages.error(request, "No tienes permiso para solicitar citas.")
        return redirect('inicio')

    if request.method == 'POST':

        form = CitaPacienteForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():

            try:

                hora_obj = datetime.strptime(
                    form.cleaned_data['hora'],
                    '%H:%M'
                ).time()

                tipo = form.cleaned_data['tipo']

                # =========================================
                # CREAR CITA VACÍA
                # =========================================

                cita = CitaMedica()

                cita.doctor = form.cleaned_data['doctor']
                cita.fecha = form.cleaned_data['fecha']
                cita.hora = hora_obj
                cita.motivo = form.cleaned_data['motivo']
                cita.estado = 'PENDIENTE'
                cita.creado_por = request.user

                if tipo == 'PACIENTE':

                    cita.paciente = request.user
                    cita.familiar = None

                elif tipo == 'FAMILIAR':

                    cita.paciente = None
                    cita.familiar = form.cleaned_data['familiar']

                # 🔥 IMPORTANTE
                cita._from_form = True

                cita.save()


                messages.success(
                    request,
                    "Su cita fue registrada correctamente."
                )

                return redirect('mis_citas')

            except Exception as e:

                print("ERROR:", e)

                messages.error(
                    request,
                    f"Error: {e}"
                )

        else:

            print(form.errors)

            messages.error(
                request,
                "Corrige los errores."
            )

    else:

        form = CitaPacienteForm(
            user=request.user
        )

    return render(
        request,
        'Citas/solicitar_cita.html',
        {
            'form': form
        }
    )
# =====================================================================

# =====================================================================
@login_required
def mis_citas(request):
    if request.user.rol != 'PACIENTE':
        messages.error(request, "No tienes permiso para ver esta sección.")
        return redirect('inicio')

    citas = CitaMedica.objects.filter(
        Q(paciente=request.user) |
        Q(familiar__paciente_titular=request.user)
    ).select_related('doctor__usuario').order_by('-fecha', '-hora')

    return render(request, 'Citas/mis_citas.html', {'citas': citas})


# =====================================================================
@login_required
def cancelar_mi_cita(request, cita_id):
    if request.user.rol != 'PACIENTE':
        messages.error(request, "No tienes permiso.")
        return redirect('inicio')

    cita = get_object_or_404(CitaMedica, id=cita_id, paciente=request.user)

    if cita.estado in ['ATENDIDA', 'CANCELADA']:
        messages.warning(request, "Esta cita no se puede cancelar.")
    else:
        cita.estado = 'CANCELADA'
        cita.save()
        messages.success(request, "Tu cita fue cancelada correctamente.")

    return redirect('mis_citas')

# =====================================================================

# =====================================================================
@login_required
def lista_citas(request):

    busqueda = request.GET.get('buscar', '').strip()
    estados = request.GET.getlist('estado')

    hoy = timezone.localdate()

    citas_list = CitaMedica.objects.select_related(
        'paciente',
        'doctor__usuario',
        'creado_por'
    )

    # Si NO hay filtros, mostrar solo las citas de hoy
    if not busqueda and not estados:
        citas_list = citas_list.filter(fecha=hoy)

    else:

        if busqueda:
            citas_list = citas_list.filter(
                Q(paciente__nombre__icontains=busqueda) |
                Q(paciente__apellido__icontains=busqueda) |
                Q(familiar__nombre__icontains=busqueda) |
                Q(familiar__apellido__icontains=busqueda) |
                Q(doctor__usuario__nombre__icontains=busqueda) |
                Q(doctor__usuario__apellido__icontains=busqueda) |
                Q(estado__icontains=busqueda)
            )


        if estados:
            citas_list = citas_list.filter(
                estado__in=estados
            )

    citas_list = citas_list.order_by('fecha', 'hora')

    paginator = Paginator(citas_list, 10)
    page = request.GET.get('page')
    citas = paginator.get_page(page)

    return render(request, 'Citas/lista_citas.html', {
        'citas': citas,
        'buscar': busqueda,
        'estados_seleccionados': estados
    })

# =====================================================================

# =====================================================================s
@login_required
def crear_cita_admin(request):
    if request.user.rol != 'ADMIN':
        messages.error(request, "No tienes permiso para crear citas.")
        return redirect('inicio')

    if request.method == 'POST':
        form = CitaAdminForm(request.POST)

        if form.is_valid():
            try:
                cita = form.save(commit=False)
                cita.creado_por = request.user

                hora_str = form.cleaned_data['hora']
                cita.hora = datetime.strptime(hora_str, '%H:%M').time()

                tipo = form.cleaned_data['tipo']

                if tipo == 'PACIENTE':
                    cita.paciente = form.cleaned_data['paciente']
                    cita.familiar = None

                else:
                    cita.familiar = form.cleaned_data['familiar']
                    cita.paciente = None

                cita.save()

                messages.success(request, "Cita creada correctamente.")
                return redirect('lista_citas')

            except Exception as e:
                messages.error(request, f"Error: {e}")

    else:
        form = CitaAdminForm()

    return render(request, 'Citas/crear_cita_admin.html', {'form': form})
# =====================================================================

# =====================================================================
@login_required
def editar_cita_admin(request, cita_id):
    if request.user.rol != 'ADMIN':
        messages.error(request, "No tienes permiso para editar citas.")
        return redirect('inicio')
    cita = get_object_or_404(CitaMedica, id=cita_id)
    if request.method == 'POST':
        form = CitaAdminForm(request.POST, instance=cita)
        if form.is_valid():
            try:
                cita = form.save(commit=False)
                hora_str = form.cleaned_data['hora']
                cita.hora = datetime.strptime(
                    hora_str,
                    '%H:%M'
                ).time()
                tipo = form.cleaned_data.get('tipo')

                if tipo == 'PACIENTE':

                    cita.paciente = form.cleaned_data.get('paciente')
                    cita.familiar = None

                elif tipo == 'FAMILIAR':

                    cita.familiar = form.cleaned_data.get('familiar')
                    cita.paciente = None
                cita.save()
                messages.success(
                    request,
                    "Cita médica actualizada correctamente."                )
                return redirect('lista_citas')

            except Exception as e:

                print("ERROR:", e)

                messages.error(
                    request,
                    f"Error al actualizar la cita: {e}"
                )

        else:

            print(form.errors)

            messages.error(
                request,
                "Corrige los errores del formulario."            )
    else:
        form = CitaAdminForm(instance=cita)
    return render(request, 'Citas/editar_cita_admin.html', {
        'form': form,
        'cita': cita
    })
# =====================================================================
# ADMIN - CONFIRMAR CITA
# =====================================================================
@login_required
def confirmar_cita(request, cita_id):
    ALLOWED_ROLES = ['ADMIN', 'DOCTOR']

    if request.user.rol not in ALLOWED_ROLES:
        messages.error(request, "No tienes permiso.")
        return redirect('inicio')

    cita = get_object_or_404(CitaMedica, id=cita_id)
    cita.estado = 'CONFIRMADA'
    cita.save()

    messages.success(request, "Cita confirmada correctamente.")
    return redirect('lista_citas')

# ===================================================================================================================
@login_required
def marcar_cita_atendida(request, cita_id):
    if request.user.rol != 'ADMIN':
        messages.error(request, "No tienes permiso.")
        return redirect('inicio')

    cita = get_object_or_404(CitaMedica, id=cita_id)
    precio_consulta = getattr(cita.doctor, 'precio_consulta', Decimal('0.00'))
    bcv_actual = BCV.objects.order_by('-fecha').first()
    tasa_bcv = bcv_actual.valor if bcv_actual else Decimal('1.00')
    total_usd = precio_consulta.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_bs = (total_usd * tasa_bcv).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    cita.tasa_bcv_aplicada = tasa_bcv
    cita.total = total_bs
    cita.estado = 'ATENDIDA'
    cita.save()

    Factura.objects.update_or_create(
        cita=cita,
        defaults={
            'total': total_bs,
            'tasa_bcv_fijada': tasa_bcv,
            'total_usd': total_usd,
            'total_bs': total_bs,
        }
    )

    messages.success(request, "La cita fue marcada como atendida.")
    return redirect('lista_citas')

# =====================================================================
# ADMIN - CANCELAR CITA
# =====================================================================
@login_required
def cancelar_cita_admin(request, cita_id):
    if request.user.rol != 'ADMIN':
        messages.error(request, "No tienes permiso.")
        return redirect('inicio')

    cita = get_object_or_404(CitaMedica, id=cita_id)
    cita.estado = 'CANCELADA'
    cita.save()

    messages.success(request, "La cita fue cancelada correctamente.")
    return redirect('lista_citas')

# =====================================================================
# ADMIN - ELIMINAR CITA
# =====================================================================
@login_required
def eliminar_cita_admin(request, cita_id):
    if request.user.rol != 'ADMIN':
        messages.error(request, "No tienes permiso.")
        return redirect('inicio')

    cita = get_object_or_404(CitaMedica, id=cita_id)
    cita.delete()

    messages.success(request, "La cita fue eliminada correctamente.")
    return redirect('lista_citas')

# =====================================================================
# DOCTOR - VER SUS CITAS
# =====================================================================
@login_required
def citas_doctor(request):

    if request.user.rol != 'DOCTOR':
        messages.error(
            request,
            "No tienes permiso para ver esta sección."
        )
        return redirect('inicio')

    try:
        doctor = request.user.doctor_perfil
    except:
        messages.error(
            request,
            "No tienes un perfil de doctor asociado."
        )
        return redirect('inicio')

    busqueda = request.GET.get('buscar', '').strip()
    estados = request.GET.getlist('estado')

    citas = CitaMedica.objects.filter(
        doctor=doctor
    ).select_related(
        'paciente',
        'familiar'
    )

    # Actualizar estados automáticamente
    for cita in citas:
        cita.actualizar_estado_auto()

    hoy = timezone.localdate()

    # Si no hay filtros ni búsqueda,
    # mostrar solo citas de hoy en adelante
    if not busqueda and not estados:
        citas = citas.filter(
            fecha__gte=hoy
        )

    # Buscador
    if busqueda:
        citas = citas.filter(
            Q(paciente__nombre__icontains=busqueda) |
            Q(paciente__apellido__icontains=busqueda) |
            Q(familiar__nombre__icontains=busqueda) |
            Q(familiar__apellido__icontains=busqueda) |
            Q(estado__icontains=busqueda)
        )

    # Filtro por estados
    if estados:
        citas = citas.filter(
            estado__in=estados
        )

    # Ordenar por fecha más cercana
    citas = citas.order_by(
        'fecha',
        'hora'
    )

    paginator = Paginator(
        citas,
        10
    )

    page = request.GET.get('page')
    citas = paginator.get_page(page)

    return render(
        request,
        'Citas/citas_doctor.html',
        {
            'citas': citas,
            'buscar': busqueda,
            'estados_seleccionados': estados,
        }
    )
# =====================================
@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
def atender_cita(request, cita_id):
    cita = get_object_or_404(CitaMedica, id=cita_id)

    if request.user.rol == 'DOCTOR':
        try:
            if cita.doctor_id != request.user.doctor_perfil.id:
                messages.error(request, "No puedes atender citas de otro doctor.")
                return redirect('citas_doctor')
        except Doctorperfil.DoesNotExist:
            messages.error(request, "Perfil de doctor no encontrado.")
            return redirect('doctor_home')
    if cita.estado == CitaMedica.ATENDIDA:
        messages.warning(request, "Esta cita ya fue atendida.")
        return render(request, 'Citas/atender_cita.html', {
            'cita': cita,
            'bloqueada': True
        })
    
    DetalleFormSet = modelformset_factory(
        DetalleInsumoCita,
        form=DetalleInsumoCitaForm,
        extra=1,
        can_delete=True
    )
    precio_consulta = getattr(
        cita.doctor,
        'precio_consulta',
        Decimal('0.00')
    )
    insumos = InsumoMedico.objects.all()
    insumos_data = [
        {
            "id": i.id,
            "nombre": i.nombre_ins,
            "stock": i.cantidad_ins,
            "precio": float(i.precio_unitario_ins)
        }
        for i in insumos    ]
    if request.method == 'POST':
        formset = DetalleFormSet(
            request.POST,
            queryset=DetalleInsumoCita.objects.none()        )
        if formset.is_valid():
            try:
                with transaction.atomic():
                    bcv_actual = BCV.objects.order_by('-fecha').first()
                    tasa_bcv = (
                        bcv_actual.valor
                        if bcv_actual
                        else Decimal('1.00')
                    )
                    subtotal_insumos = Decimal('0.00')
                    hay_insumos = False
                    for form in formset:
                        if not form.cleaned_data:
                            continue
                        if form.cleaned_data.get('DELETE'):
                            continue
                        insumo = form.cleaned_data.get('insumo')
                        cantidad = form.cleaned_data.get('cantidad')
                        if not insumo or not cantidad:
                            continue
                        if cantidad > insumo.cantidad_ins:
                            messages.error(
                                request,
                                f"No hay suficiente stock de {insumo.nombre_ins}"
                            )
                            return redirect(
                                'atender_cita',
                                cita_id=cita.id
                            )
                        detalle = form.save(commit=False)
                        detalle.cita = cita
                        detalle.save()
                        subtotal = (
                            insumo.precio_unitario_ins * cantidad
                        ).quantize(
                            Decimal('0.01'),
                            rounding=ROUND_HALF_UP
                        )
                        subtotal_insumos = (
                            subtotal_insumos + subtotal
                        ).quantize(
                            Decimal('0.01'),
                            rounding=ROUND_HALF_UP
                        )
                        hay_insumos = True

                    total_usd = precio_consulta
                    if hay_insumos:
                        total_usd = (
                            subtotal_insumos + precio_consulta
                        ).quantize(
                            Decimal('0.01'),
                            rounding=ROUND_HALF_UP
                        )
                    total_bs = (
                        total_usd * tasa_bcv
                    ).quantize(
                        Decimal('0.01'),
                        rounding=ROUND_HALF_UP
                    )
                    cita.tasa_bcv_aplicada = tasa_bcv
                    cita.total = total_bs
                    cita.estado = CitaMedica.ATENDIDA
                    cita.save()
                    Factura.objects.update_or_create(
                        cita=cita,
                        defaults={
                            'total': total_bs,
                            'tasa_bcv_fijada': tasa_bcv,
                            'total_usd': total_usd,
                            'total_bs': total_bs                       }                    )
                    messages.success(
                        request,
                        "Cita atendida correctamente."                    )
                    return redirect(
                        'ver_factura',
                        cita_id=cita.id                    )
            except Exception as e:

                messages.error(
                    request,
                    f"Error al guardar: {str(e)}"
                )

        else:
            messages.error(request, "Formulario inválido.")

    else:

        formset = DetalleFormSet(
            queryset=DetalleInsumoCita.objects.none()
        )

    return render(request, 'Citas/atender_cita.html', {
        'cita': cita,
        'formset': formset,
        'precio_consulta': precio_consulta,
        'insumos_json': json.dumps(insumos_data)
    })
# ==========================================================
@login_required
def ver_factura(request, cita_id):

    cita = get_object_or_404(
        CitaMedica,
        id=cita_id
    )

    factura = getattr(cita, 'factura', None)

    if not factura:

        messages.error(
            request,
            "La factura no existe para esta cita."
        )

        return redirect('lista_citas')
    tasa_bcv = (
        factura.tasa_bcv_fijada
        or Decimal('1.00')
    )
    detalles = cita.detalles_insumos.select_related('insumo')
    subtotal_insumos_usd = Decimal('0.00')
    for d in detalles:
        precio_unitario = (
            d.insumo.precio_unitario_ins
            or Decimal('0.00')        )
        cantidad = d.cantidad or 0
        d.subtotal_usd = (
            precio_unitario * cantidad
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP        )
        d.subtotal_bs = (
            d.subtotal_usd * tasa_bcv
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP        )
        subtotal_insumos_usd = (
            subtotal_insumos_usd + d.subtotal_usd
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP        )
    precio_consulta_usd = (
        getattr(
            cita.doctor,
            'precio_consulta',
            Decimal('0.00')
        )
        or Decimal('0.00')    )
    total_usd = factura.total_usd.quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP    )
    total_bs = factura.total_bs.quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP    )
    return render(request, 'Citas/ver_factura.html', {
        'cita': cita,
        'factura': factura,
        'detalles': detalles,
        'tasa_bcv': tasa_bcv,
        'subtotal_insumos_usd': subtotal_insumos_usd,
        'subtotal_insumos_bs': (
            subtotal_insumos_usd * tasa_bcv
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP        ),
        'precio_consulta_usd': precio_consulta_usd,
        'precio_consulta_bs': (
            precio_consulta_usd * tasa_bcv
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        ),
        'total_usd': total_usd,
        'total_bs': total_bs,    })
# =====================================

@login_required
def ver_factura_print(request, cita_id):
    cita = get_object_or_404(CitaMedica, id=cita_id)

    factura = getattr(cita, 'factura', None)

    if not factura:
        messages.error(request, "La factura no existe.")
        return redirect('lista_citas')

    tasa_bcv = cita.tasa_bcv_aplicada or 1.00

    detalles = cita.detalles_insumos.select_related('insumo')

    subtotal_insumos_usd = 0

    for d in detalles:
        precio = d.insumo.precio_unitario_ins or 0
        d.subtotal_usd = precio * d.cantidad
        d.subtotal_bs = d.subtotal_usd * tasa_bcv
        subtotal_insumos_usd += d.subtotal_usd

    precio_consulta_usd = getattr(cita.doctor, 'precio_consulta', 0) or 0

    total_usd = subtotal_insumos_usd + precio_consulta_usd
    total_bs = total_usd * tasa_bcv

    return render(request, 'Citas/ver_factura_print.html', {
        'cita': cita,
        'factura': factura,
        'detalles': detalles,
        'tasa_bcv': tasa_bcv,
        'subtotal_insumos_usd': subtotal_insumos_usd,
        'precio_consulta_usd': precio_consulta_usd,
        'total_usd': total_usd,
        'total_bs': total_bs,
    })
# =====================================


@login_required
def historial_stock(request, insumo_id):
    insumo = get_object_or_404(
        InsumoMedico.objects.prefetch_related(
            'movimientos',
            'movimientos__cita__doctor__usuario',
            'movimientos__cita__paciente',
            'movimientos__realizar_examen__doctor',
            'movimientos__realizar_examen__paciente',
            'movimientos__usuario',   # ← Nuevo
        ),
        id=insumo_id
    )

    total_entradas = insumo.movimientos.filter(
        tipo='ENTRADA'
    ).aggregate(
        total=Coalesce(Sum('cantidad'), 0)
    )['total']

    total_salidas = insumo.movimientos.filter(
        tipo='SALIDA'
    ).aggregate(
        total=Coalesce(Sum('cantidad'), 0)
    )['total']

    movimientos = insumo.movimientos.select_related(
    'usuario',
    'cita__paciente',
    'cita__doctor',
    'realizar_examen__paciente',
    'realizar_examen__doctor',).order_by('-fecha')

    return render(request, 'inventario/historial_stock.html', {
        'insumo': insumo,
        'movimientos': movimientos,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
    })
# =====================================
# =====================================

@login_required
def agregar_stock(request, insumo_id):
    insumo = get_object_or_404(InsumoMedico, id=insumo_id)
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad'))
        if cantidad <= 0:
            messages.error(request, 'Cantidad inválida')
            return redirect('inventario')
        stock_anterior = insumo.cantidad_ins
        insumo.cantidad_ins += cantidad
        insumo.save()
        MovimientoStock.objects.create(
            insumo=insumo,
            tipo=MovimientoStock.ENTRADA,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_actual=insumo.cantidad_ins,
            descripcion='Entrada manual de inventario',
            usuario=request.user
        )
        messages.success(request, 'Stock agregado correctamente')
        return redirect('inventario')
    
# =====================================

# =====================================
@login_required
@rol_requerido(['ADMIN'])
def crear_bcv(request):

    hoy = now().date()
    if not request.user.is_staff:
        return HttpResponseForbidden("No tienes permiso para modificar el BCV")

    if BCV.objects.filter(fecha__date=hoy).exists():
        messages.warning(request, "Ya existe un BCV registrado para hoy.")
        return redirect('insumos')

    if request.method == "POST":
        valor = request.POST.get("valor")

        if valor:
            BCV.objects.create(
                valor=valor,
                creado_por=request.user
            )
            messages.success(request, "BCV registrado correctamente.")
            return redirect('home')

    return render(request, 'admin/crear_bcv.html')

# =====================================
@login_required
def grafico_consumo_insumos(request):

    insumos = InsumoMedico.objects.all().order_by('nombre_ins')

    insumo_id = request.GET.get('insumo')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    movimientos = MovimientoStock.objects.select_related('insumo').all()

    nombre_insumo = "Todos los Insumos"

    # FILTRO POR INSUMO
    if insumo_id:
        movimientos = movimientos.filter(insumo_id=insumo_id)
        insumo = InsumoMedico.objects.get(id=insumo_id)
        nombre_insumo = insumo.nombre_ins

    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        movimientos = movimientos.filter(fecha__gte=fecha_inicio)

    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
        movimientos = movimientos.filter(fecha__lte=fecha_fin)

    entradas = sum(m.cantidad for m in movimientos if m.tipo == MovimientoStock.ENTRADA)
    salidas = sum(m.cantidad for m in movimientos if m.tipo == MovimientoStock.SALIDA)

    total_entradas = sum(
        m.cantidad * float(m.insumo.precio_unitario_ins)
        for m in movimientos if m.tipo == MovimientoStock.ENTRADA
    )

    total_salidas = sum(
        m.cantidad * float(m.insumo.precio_unitario_ins)
        for m in movimientos if m.tipo == MovimientoStock.SALIDA
    )

    context = {
        'insumos': insumos,
        'movimientos': movimientos,
        'entradas': entradas,
        'salidas': salidas,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'nombre_insumo': nombre_insumo,
        'insumo_id': insumo_id,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }

    return render(request, 'inventario/grafico_consumo.html', context)
# =========================================================================


@login_required
@transaction.atomic
def asignar_titular_familiar(request, familiar_id):

    familiar = get_object_or_404(
        FamiliarPaciente,
        id=familiar_id
    )

    pacientes = Usuario.objects.filter(
        rol=Usuario.PACIENTE
    ).order_by('nombre')

    if request.method == 'POST':

        opcion = request.POST.get('tipo_titular')


        if opcion == 'EXISTENTE':

            paciente_id = request.POST.get(
                'paciente_titular'
            )

            if not paciente_id:

                messages.error(
                    request,
                    'Debe seleccionar un paciente.'
                )

            else:

                familiar.paciente_titular_id = paciente_id
                familiar.save()

                messages.success(
                    request,
                    'Titular asignado correctamente.'
                )

                return redirect('registrar_examen')
        elif opcion == 'NUEVO':

            cedula = request.POST.get('cedula')

            # Si ya existe lo reutilizamos
            titular = Usuario.objects.filter(
                cedula=cedula
            ).first()

            if titular:

                messages.info(
                    request,
                    'Ya existía un paciente con esa cédula. '
                    'Se asignó automáticamente.'
                )

            else:

                titular = Usuario.objects.create_user(
                    cedula=cedula,
                    email=f"{cedula}@hospital.com",
                    password=secrets.token_urlsafe(10),
                    nombre=request.POST.get('nombre'),
                    apellido=request.POST.get('apellido'),
                    sexo=request.POST.get('sexo'),
                    fecha_nacimiento=request.POST.get(
                        'fecha_nacimiento'
                    ),
                    telefono=request.POST.get('telefono'),
                    rol=Usuario.PACIENTE
                )

            familiar.paciente_titular = titular
            familiar.save()

            messages.success(
                request,
                'Paciente titular asignado correctamente.'
            )

            return redirect('registrar_examen')

    return render(
        request,
        'examenes/asignar_titular.html',
        {
            'familiar': familiar,
            'pacientes': pacientes
        }
    )




# =========================================================================# =========================================================================## =========================================================================# =========================================================================#
@login_required
def asignar_familiar_paciente(request):

    if request.user.rol != Usuario.ADMINISTRACION:
        return redirect('inicio')

    form = AsignarFamiliarPacienteForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():

            familiar = form.cleaned_data['familiar']
            paciente = form.cleaned_data['paciente']

            familiar.paciente_titular = paciente
            familiar.save()

            messages.success(request, "Familiar asignado correctamente")
            return redirect('lista_carga_familiar_admin')

    return render(request, 'familiares/asignar_familiar.html', {
        'form': form
    })
# =========================================================================# =========================================================================# =========================================================================

@login_required
@rol_requerido(['ADMIN', 'DOCTOR'])
@transaction.atomic
def registrar_examen(request):

    if request.method == 'POST':

        form = RealizarExamenForm(request.POST)

        examen_formset = ExamenRealizadoFormSet(
            request.POST,
            prefix='examenes'
        )

        insumo_formset = DetalleInsumoExamenFormSet(
            request.POST,
            prefix='insumos'
        )

        if (
            form.is_valid() and
            examen_formset.is_valid() and
            insumo_formset.is_valid()
        ):
            realizar_examen = form.save(commit=False)

            persona = form.cleaned_data.get('persona')

            tipo, id_persona = persona.split('-')

            # ===================================
            # PACIENTE
            # ===================================
            if tipo == 'PACIENTE':

                paciente = Usuario.objects.get(id=id_persona)

                realizar_examen.paciente = paciente
                realizar_examen.familiar = None

            # ===================================
            # FAMILIAR
            # ===================================
            elif tipo == 'FAMILIAR':

                familiar = FamiliarPaciente.objects.get(id=id_persona)

                if not familiar.paciente_titular:
                    url = reverse(
                        'asignar_titular_familiar',
                        kwargs={'familiar_id': familiar.id}
                    )
                    return redirect(f'{url}?next=examen')


                realizar_examen.familiar = familiar
                realizar_examen.paciente = familiar.paciente_titular

            realizar_examen.save()

            total = Decimal('0.00')

            # ====================================
            # EXÁMENES
            # ====================================
            for form_examen in examen_formset.forms:

                if (
                    form_examen.has_changed() and
                    not form_examen.cleaned_data.get('DELETE')
                ):

                    detalle = form_examen.save(commit=False)

                    if detalle.examen:

                        detalle.realizar_examen = realizar_examen
                        detalle.subtotal = detalle.examen.precio_exa
                        detalle.save()

                        total += detalle.subtotal

            # ====================================
            # INSUMOS
            # ====================================
            for form_insumo in insumo_formset.forms:

                if (
                    form_insumo.has_changed() and
                    not form_insumo.cleaned_data.get('DELETE')
                ):

                    detalle_ins = form_insumo.save(commit=False)

                    if detalle_ins.insumo:

                        detalle_ins.realizar_examen = realizar_examen
                        detalle_ins.save()

                        total += detalle_ins.subtotal

            realizar_examen.total = total
            realizar_examen.save()

            messages.success(
                request,
                "Examen registrado correctamente."
            )

            return redirect('listar_examenes')

    else:

        form = RealizarExamenForm()

        examen_formset = ExamenRealizadoFormSet(
            queryset=ExamenRealizado.objects.none(),
            prefix='examenes'
        )

        insumo_formset = DetalleInsumoExamenFormSet(
            queryset=DetalleInsumoExamen.objects.none(),
            prefix='insumos'
        )

    return render(request, 'examenes/registrar_examen.html', {
        'form': form,
        'examen_formset': examen_formset,
        'insumo_formset': insumo_formset,
    })
# =========================================================================

@login_required
@transaction.atomic
def registrar_examen_doctor(request, cita_id):

    if request.user.rol != 'DOCTOR':
        messages.error(request, 'No autorizado')
        return redirect('inicio')

    cita = get_object_or_404(CitaMedica, id=cita_id)
    if cita.paciente:
        initial_persona = f'PACIENTE-{cita.paciente.id}'
    elif cita.familiar:
        initial_persona = f'FAMILIAR-{cita.familiar.id}'
    else:
        initial_persona = None

    if request.method == 'POST':

        form = RealizarExamenDoctorForm(    request.POST,    initial={        'persona': initial_persona    })
        
        examen_formset = ExamenRealizadoFormSet(
            request.POST,
            prefix='examenes'
        )

        insumo_formset = DetalleInsumoExamenFormSet(
            request.POST,
            prefix='insumos'
        )

        if form.is_valid() and examen_formset.is_valid() and insumo_formset.is_valid():

            realizar_examen = form.save(commit=False)

            # 🔥 RELACIÓN CON CITA
            realizar_examen.cita = cita

            persona = form.cleaned_data['persona']
            tipo, persona_id = persona.split('-')

            if tipo == 'PACIENTE':

                paciente = Usuario.objects.filter(id=persona_id).first()

                if not paciente:
                    messages.error(request, "Paciente no encontrado.")
                    return redirect('citas_doctor')

                realizar_examen.paciente = paciente
                realizar_examen.familiar = None

            else:

                familiar = FamiliarPaciente.objects.filter(id=persona_id).first()

                if not familiar:
                    messages.error(request, "Familiar no encontrado.")
                    return redirect('citas_doctor')

                # 🔥 VALIDACIÓN CRÍTICA
                if not familiar.paciente_titular:
                    messages.error(
                        request,
                        "Este familiar no tiene paciente titular asignado."
                    )

                    return redirect(
                        'asignar_titular_familiar',
                        familiar_id=familiar.id
                    ) + f"?next=doctor_examen&cita_id={cita.id}"

                realizar_examen.familiar = familiar
                realizar_examen.paciente = familiar.paciente_titular
            # ======================================
            realizar_examen.doctor = request.user.doctor_perfil
            realizar_examen.save()
            # ======================================
            total = Decimal('0.00')

            for detalle_form in examen_formset:
                if detalle_form.has_changed() and not detalle_form.cleaned_data.get('DELETE'):
                    detalle = detalle_form.save(commit=False)
                    if detalle.examen:
                        detalle.realizar_examen = realizar_examen
                        detalle.subtotal = detalle.examen.precio_exa
                        detalle.save()
                        total += detalle.subtotal
            for detalle_form in insumo_formset:
                if detalle_form.has_changed() and not detalle_form.cleaned_data.get('DELETE'):
                    detalle = detalle_form.save(commit=False)
                    if detalle.insumo:
                        detalle.realizar_examen = realizar_examen
                        detalle.save()
                        total += detalle.subtotal
            realizar_examen.total = total
            realizar_examen.save()
            messages.success(request, 'Examen registrado correctamente')
            return redirect('citas_doctor')
    else:
        form = RealizarExamenDoctorForm(
            initial={
                'persona': (
                    f'PACIENTE-{cita.paciente.id}'
                    if cita.paciente
                    else f'FAMILIAR-{cita.familiar.id}'
                    if cita.familiar
                    else None
                )
            }
        )


        examen_formset = ExamenRealizadoFormSet(
            queryset=ExamenRealizado.objects.none(),
            prefix='examenes'
        )

        insumo_formset = DetalleInsumoExamenFormSet(
            queryset=DetalleInsumoExamen.objects.none(),
            prefix='insumos'
        )

    return render(
        request,
        'doctor/registrar_examen_doctor.html',
        {
            'form': form,
            'examen_formset': examen_formset,
            'insumo_formset': insumo_formset,
            'cita': cita
        }
    )
# =========================================================================
# # =========================================================================# =========================================================================
@login_required
def mis_examenes_doctor(request):

    doctor = request.user.doctor_perfil  # 🔥 IMPORTANTE

    examenes = RealizarExamen.objects.filter(
        doctor=doctor
    ).order_by('-id')

    return render(
        request,
        'doctor/mis_examenes_doctor.html',
        {
            'examenes': examenes
        }
    )

# =========================================================================
@login_required
@rol_requerido(['DOCTOR'])
def detalle_examen_doctor(request, examen_id):
    examen = get_object_or_404(
        RealizarExamen,
        id=examen_id,
        doctor=request.user.doctor_perfil
    )

    total_examenes = sum(
        item.subtotal for item in examen.examenes_realizados.all()
    )
    total_insumos = sum(
        item.subtotal for item in examen.insumos.all()
    )

    return render(
        request,
        'doctor/detalle_examen_doctor.html',
        {
            'examen': examen,
            'total_examenes': total_examenes,
            'total_insumos': total_insumos,
        }
    )


@login_required
@rol_requerido(['DOCTOR'])
def detalle_examen_doctor_print(request, examen_id):
    examen = get_object_or_404(
        RealizarExamen,
        id=examen_id,
        doctor=request.user.doctor_perfil
    )

    total_examenes = sum(
        item.subtotal for item in examen.examenes_realizados.all()
    )
    total_insumos = sum(
        item.subtotal for item in examen.insumos.all()
    )

    return render(
        request,
        'doctor/detalle_examen_doctor_print.html',
        {
            'examen': examen,
            'total_examenes': total_examenes,
            'total_insumos': total_insumos,
            'now': timezone.now(),
        }
    )


# =========================================================================
@login_required
def listar_examenes(request):

    query = request.GET.get('q', '')

    examenes = RealizarExamen.objects.select_related(
        'paciente',
        'doctor',
    ).prefetch_related(
        'examenes_realizados__examen'
    )


    if query:
        examenes = examenes.filter(
            Q(paciente__nombre__icontains=query) |
            Q(paciente__apellido__icontains=query) |

        # 👨‍⚕️ DOCTOR (a través de usuario)
            Q(doctor__usuario__nombre__icontains=query) |
            Q(doctor__usuario__apellido__icontains=query) |
            Q(doctor__usuario__cedula__icontains=query) |

            Q(familiar__nombre__icontains=query) |
            Q(familiar__apellido__icontains=query)
        )
    examenes = examenes.order_by('-id')

    paginator = Paginator(examenes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'examenes/listar_examenes.html', {
        'examenes': page_obj,
        'page_obj': page_obj,
        'query': query,
    })
# =========================================================================
# =========================================================================

@login_required
def detalle_examen(request, examen_id):
    examen = get_object_or_404(RealizarExamen, id=examen_id)
    
    # Cálculos correctos
    total_examenes = sum(item.subtotal for item in examen.examenes_realizados.all())
    total_insumos = sum(item.subtotal for item in examen.insumos.all())

    return render(request, 'examenes/detalle_examen.html', {
        'examen': examen,
        'total_examenes': total_examenes,
        'total_insumos': total_insumos,
    })
# =====================================
@login_required
def detalle_examen_print(request, examen_id):
    examen = get_object_or_404(RealizarExamen, id=examen_id)
    
    total_examenes = sum(item.subtotal for item in examen.examenes_realizados.all())
    total_insumos = sum(item.subtotal for item in examen.insumos.all())

    return render(request, 'examenes/detalle_examen_print.html', {
        'examen': examen,
        'total_examenes': total_examenes,
        'total_insumos': total_insumos,
        'now': timezone.now(),
    })
# =========================================================================# =========================================================================
# =====================================
@login_required
def reporte_pacientes(request):
    return render(request, 'reportes/reporte_pacientes.html')
# =========================================================================
# =====================================

def calcular_edad(fecha_nacimiento):
    hoy = date.today()
    return relativedelta(hoy, fecha_nacimiento).years

# =====================================
@login_required
def generar_pdf_pacientes(request):

    tipo = request.GET.get('tipo')

    pacientes_query = Usuario.objects.filter(
        rol=Usuario.PACIENTE
    )

    familiares_query = FamiliarPaciente.objects.select_related(
        'paciente_titular'
    ).all()

    titulo_reporte = "LISTADO GENERAL DE PACIENTES"

    pacientes = []

    # =====================================
    # FILTRO POR SEXO
    # =====================================
    if tipo == 'sexo':

        sexo = request.GET.get('sexo')

        pacientes_query = pacientes_query.filter(
            sexo__iexact=sexo.strip()
        )

        familiares_query = familiares_query.filter(
            sexo__iexact=sexo.strip()
        )

        titulo_reporte = (
            f"LISTADO DE PACIENTES {sexo}"
        )

    # =====================================
    # FILTRO POR EDAD
    # =====================================
    elif tipo == 'edad':

        edad_minima = int(
            request.GET.get('edad', 0)
        )

        titulo_reporte = (
            f"LISTADO DE PACIENTES MAYORES DE "
            f"{edad_minima} AÑOS"
        )

        # PACIENTES
        for paciente in pacientes_query:

            edad = calcular_edad(
                paciente.fecha_nacimiento
            )

            if edad >= edad_minima:

                pacientes.append({
                    'paciente': paciente,
                    'edad': edad,
                    'es_familiar': False
                })

        # FAMILIARES
        for familiar in familiares_query:

            edad = calcular_edad(
                familiar.fecha_nacimiento
            )

            if edad >= edad_minima:

                pacientes.append({
                    'paciente': familiar,
                    'edad': edad,
                    'es_familiar': True
                })

    # =====================================
    # GENERAL O SEXO
    # =====================================
    else:

        pacientes.extend([
            {
                'paciente': paciente,
                'edad': calcular_edad(
                    paciente.fecha_nacimiento
                ),
                'es_familiar': False
            }
            for paciente in pacientes_query
        ])

        pacientes.extend([
            {
                'paciente': familiar,
                'edad': calcular_edad(
                    familiar.fecha_nacimiento
                ),
                'es_familiar': True
            }
            for familiar in familiares_query
        ])

    # Si es sexo, agregamos los familiares ya filtrados
    if tipo == 'sexo':

        pacientes.extend([
            {
                'paciente': familiar,
                'edad': calcular_edad(
                    familiar.fecha_nacimiento
                ),
                'es_familiar': True
            }
            for familiar in familiares_query
        ])

        pacientes.extend([
            {
                'paciente': paciente,
                'edad': calcular_edad(
                    paciente.fecha_nacimiento
                ),
                'es_familiar': False
            }
            for paciente in pacientes_query
        ])

    template = get_template(
        'reportes/pdf_pacientes.html'
    )

    context = {
        'pacientes': pacientes,
        'titulo_reporte': titulo_reporte,
    }

    html = template.render(context)

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        'inline; filename="reporte_pacientes.pdf"'
    )

    pisa.CreatePDF(
        html,
        dest=response
    )

    return response
    # =========================    # =========================

# =====================================
# Reportes de contabilidad (módulo dedicado)


# =====================================
@login_required
def estadisticas_mensuales(request):

    movimientos = (
        MovimientoStock.objects
        .select_related('insumo', 'cita', 'realizar_examen')
        .order_by('-fecha')
    )
    total_entradas = sum(
        m.cantidad * m.insumo.precio_unitario_ins
        for m in movimientos if m.tipo == 'ENTRADA'
    )

    total_salidas = sum(
        m.cantidad * m.insumo.precio_unitario_ins
        for m in movimientos if m.tipo == 'SALIDA'
    )
    balance = total_entradas - total_salidas
    entradas_labels = []
    entradas_valores = []

    salidas_labels = []
    salidas_valores = []

    historial = []

    for mov in movimientos:

        nombre = mov.insumo.nombre_ins

        # CALCULO DINERO
        gasto = mov.cantidad * mov.insumo.precio_unitario_ins

        # ENTRADAS
        if mov.tipo == 'ENTRADA':

            entradas_labels.append(nombre)
            entradas_valores.append(mov.cantidad)

        # SALIDAS
        else:

            salidas_labels.append(nombre)
            salidas_valores.append(mov.cantidad)

        # DESCRIPCION USO
        uso = "Sin descripción"

        if mov.cita:
            uso = f"Cita Médica #{mov.cita.id}"

        elif mov.realizar_examen:
            uso = f"Examen #{mov.realizar_examen.id}"

        elif mov.descripcion:
            uso = mov.descripcion


        historial.append({

            'insumo': nombre,
            'tipo': mov.tipo,
            'cantidad': mov.cantidad,

            # COSTO POR MOVIMIENTO
            'costo': float(gasto),

            # COLOR LÓGICO (para el template)
            'color': 'success' if mov.tipo == 'ENTRADA' else 'danger',

            'uso': uso,
            'fecha': mov.fecha.strftime('%d/%m/%Y %H:%M')

        })

    context = {

        'entradas_labels': json.dumps(entradas_labels),
        'entradas_valores': json.dumps(entradas_valores),

        'salidas_labels': json.dumps(salidas_labels),
        'salidas_valores': json.dumps(salidas_valores),

        'historial': historial,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,    
        'balance': balance     
    }

    return render(
        request,
        'inventario/estadisticas_mensuales.html',
        context
    )
# =====================================
@login_required
def crear_familiar(request):

    if request.method == 'POST':

        form = FamiliarPacienteForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Familiar registrado correctamente')
            return redirect('lista_pacientes')

    else:
        form = FamiliarPacienteForm()

    return render(
        request,
        'familiares/crear.html',
        {'form': form}
    )
# =====================================

@login_required
def crear_familiar_paciente(request):

    if request.user.rol != Usuario.PACIENTE:
        return redirect('inicio')

    if request.method == 'POST':
        form = FamiliarPacienteForm(request.POST)

        if form.is_valid():

            familiar = form.save(commit=False)

            # ASIGNAR EL PACIENTE LOGUEADO
            familiar.paciente_titular = request.user

            familiar.save()

            return redirect('mis_familiares')

    else:
        form = FamiliarPacienteForm()

    return render(request, 'familiares/crear_familiar_paciente.html', {
        'form': form
    })
# ==========================================

@login_required
def crear_familiar_admin(request):

    if request.user.rol != Usuario.ADMINISTRACION:
        return redirect('inicio')

    if request.method == 'POST':
        form = FamiliarPacienteAdminForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_carga_familiar_admin')

    else:
        form = FamiliarPacienteAdminForm()

    return render(request, 'familiares/crear_familiar_admin.html', {
        'form': form
    })


# ==========================================# ==========================================
@login_required
def mis_familiares(request):

    if request.user.rol != Usuario.PACIENTE:
        return redirect('inicio')

    familiares = FamiliarPaciente.objects.filter(
    paciente_titular=request.user,    activo=True).order_by('nombre')

    return render(request, 'familiares/mis_familiares.html', {
        'familiares': familiares
    })



# ==========================================# ==========================================
@login_required
def editar_familiar_paciente(request, familiar_id):
    if request.user.rol != Usuario.PACIENTE:
        return redirect('inicio')
    familiar = get_object_or_404(
        FamiliarPaciente,
        id=familiar_id,
        paciente_titular=request.user    )
    if request.method == 'POST':
        form = FamiliarPacienteForm(
            request.POST,
            instance=familiar        )
        if form.is_valid():
            familiar = form.save(commit=False)
            familiar.paciente_titular = request.user
            familiar.save()
            return redirect('mis_familiares')
    else:
        form = FamiliarPacienteForm(instance=familiar)
    return render(
        request,
        'familiares/editar_familiar_paciente.html',
        {
            'form': form,
            'familiar': familiar
        }
    )
# ==========================================# ==========================================
@login_required
def eliminar_familiar_paciente(request, familiar_id):
    if request.user.rol != Usuario.PACIENTE:
        return redirect('inicio')
    familiar = get_object_or_404(
        FamiliarPaciente,
        id=familiar_id,
        paciente_titular=request.user    )
    familiar.activo = False
    familiar.save()
    return redirect('mis_familiares')

# ==========================================# ==========================================
@login_required
def lista_carga_familiar_admin(request):

    if request.user.rol != Usuario.ADMINISTRACION:
        return redirect('inicio')

    buscar = request.GET.get('buscar', '')

    titulares = Usuario.objects.filter(
        rol=Usuario.PACIENTE
    ).prefetch_related(
        'familiares'
    ).annotate(
        total_familiares=Count('familiares')
    )
    if buscar:
        titulares = titulares.filter(
            Q(nombre__icontains=buscar) |
            Q(apellido__icontains=buscar) |
            Q(cedula__icontains=buscar) |
            Q(email__icontains=buscar)

        )
    titulares = titulares.order_by('first_name')
    paginator = Paginator(titulares, 10)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'familiares/lista_carga_familiar_admin.html',
        {
            'page_obj': page_obj,
            'buscar': buscar
        }
    )

# Re-export emergencia views from dedicated module


























# ==========================================# ==========================================


# ==========================================













# ==========================================