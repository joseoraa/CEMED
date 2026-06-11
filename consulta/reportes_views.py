from collections import Counter
from datetime import date
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
import calendar
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from django.db.models.functions import TruncMonth
from .decoradores import rol_requerido
from .models import *




def _mes_anio_desde_request(request):
    hoy = timezone.localdate()
    try:
        mes = int(request.GET.get('mes', hoy.month))
    except (TypeError, ValueError):
        mes = hoy.month
    try:
        anio = int(request.GET.get('anio', hoy.year))
    except (TypeError, ValueError):
        anio = hoy.year
    mes = max(1, min(12, mes))
    return mes, anio


MESES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


def _nombre_mes(mes):
    return dict(MESES).get(mes, str(mes))


def _filtrar_citas(request):
    solo_atendidas = request.GET.get('solo_atendidas', '1') == '1'
    tipo = request.GET.get('tipo', 'general')

    citas = CitaMedica.objects.select_related(
        'paciente',
        'familiar',
        'familiar__paciente_titular',
        'doctor__usuario',
        'doctor__especialidad',
    ).select_related('factura')

    if solo_atendidas:
        citas = citas.filter(estado=CitaMedica.ATENDIDA)

    titulo = 'CITAS MÉDICAS ATENDIDAS' if solo_atendidas else 'CITAS MÉDICAS'

    if tipo == 'doctor':
        doctor_id = request.GET.get('doctor')
        if doctor_id:
            citas = citas.filter(doctor_id=doctor_id)
            dr = Doctorperfil.objects.select_related('usuario').filter(id=doctor_id).first()
            if dr:
                titulo = (
                    f"CITAS ATENDIDAS — DR. {dr.usuario.nombre} {dr.usuario.apellido}"
                )

    elif tipo == 'especialidad':
        esp_id = request.GET.get('especialidad')
        if esp_id:
            citas = citas.filter(doctor__especialidad_id=esp_id)
            esp = Especialidad.objects.filter(id=esp_id).first()
            if esp:
                titulo = f"CITAS ATENDIDAS — ESPECIALIDAD {esp.nombre_espe}"

    elif tipo == 'fecha':
        fecha = request.GET.get('fecha')
        if fecha:
            citas = citas.filter(fecha=fecha)
            titulo = f"CITAS ATENDIDAS — {fecha}"

    elif tipo == 'mes':
        mes, anio = _mes_anio_desde_request(request)
        citas = citas.filter(fecha__month=mes, fecha__year=anio)
        titulo = f"CITAS ATENDIDAS — {_nombre_mes(mes).upper()} {anio}"

    elif tipo == 'rango_fecha':
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        if fecha_inicio and fecha_fin:
            citas = citas.filter(fecha__range=[fecha_inicio, fecha_fin])
            titulo = f"CITAS ATENDIDAS — DEL {fecha_inicio} AL {fecha_fin}"

    elif tipo == 'estado' and not solo_atendidas:
        estado = request.GET.get('estado')
        if estado:
            citas = citas.filter(estado=estado)
            titulo = f"CITAS — ESTADO {estado}"

    citas = citas.order_by('-fecha', '-hora')
    return citas, titulo


def _resumen_citas(citas):
    total = citas.count()
    por_estado = Counter(citas.values_list('estado', flat=True))

    total_bs = Decimal('0.00')
    total_usd = Decimal('0.00')
    for cita in citas:
        total_bs += cita.total or Decimal('0.00')
        if hasattr(cita, 'factura') and cita.factura:
            total_usd += cita.factura.total_usd or Decimal('0.00')
        elif cita.tasa_bcv_aplicada and cita.tasa_bcv_aplicada > 0 and cita.total:
            total_usd += (cita.total / cita.tasa_bcv_aplicada).quantize(Decimal('0.01'))

    return {
        'total': total,
        'por_estado': por_estado,
        'total_bs': total_bs,
        'total_usd': total_usd,
    }


# def _insumos_consumidos(request):
#     hoy = timezone.localdate()

#     mes = int(request.GET.get('mes', hoy.month))
#     anio = int(request.GET.get('anio', hoy.year))

#     fecha_inicio = request.GET.get('fecha_inicio')
#     fecha_fin = request.GET.get('fecha_fin')
#     tipo_filtro = request.GET.get('tipo_filtro', 'mes')

#     qs = MovimientoStock.objects.filter(tipo=MovimientoStock.SALIDA)


#     if tipo_filtro == 'rango' and fecha_inicio and fecha_fin:
#         qs = qs.filter(fecha__date__range=[fecha_inicio, fecha_fin])
#         titulo = f"INSUMOS MÁS UTILIZADOS — DEL {fecha_inicio} AL {fecha_fin}"
#     else:
#         qs = qs.filter(fecha__month=mes, fecha__year=anio)
#         titulo = f"INSUMOS MÁS UTILIZADOS — {_nombre_mes(mes).upper()} {anio}"

#     filas = (
#         qs.values(
#             'insumo__id',
#             'insumo__codigo_ins',
#             'insumo__nombre_ins',
#             'insumo__presentacion_ins',
#             'insumo__precio_unitario_ins',
#         )
#         .annotate(
#             total_cantidad=Sum('cantidad'),
#             total_costo=Sum(
#                 ExpressionWrapper(
#                     F('cantidad') * F('insumo__precio_unitario_ins'),
#                     output_field=DecimalField(max_digits=12, decimal_places=2),
#                 )
#             ),
#         )
#         .order_by('-total_cantidad')
#     )

#     total_general = sum(f['total_costo'] or 0 for f in filas)
#     return list(filas), titulo, total_general, mes, anio


def _insumos_consumidos(request):

    qs = MovimientoStock.objects.filter(tipo=MovimientoStock.SALIDA)
    tipo_filtro = request.GET.get('tipo_filtro', 'mes')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    hoy = timezone.localdate()
    mes = int(request.GET.get('mes', hoy.month))
    anio = int(request.GET.get('anio', hoy.year))


    if tipo_filtro == 'rango' and fecha_inicio and fecha_fin:
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        qs = qs.filter(fecha__range=[inicio, fin])

        titulo = f"INSUMOS — DEL {fecha_inicio} AL {fecha_fin}"
    
    # inicio = date(anio, mes, 1)

    # if mes == 12:
    #     fin = date(anio + 1, 1, 1)
    # else:
    #     fin = date(anio, mes + 1, 1)
    inicio = timezone.make_aware(datetime(anio, mes, 1, 0, 0, 0))

    if mes == 12:
        fin = timezone.make_aware(datetime(anio + 1, 1, 1, 0, 0, 0))
    else:
        fin = timezone.make_aware(datetime(anio, mes + 1, 1, 0, 0, 0))

    qs = qs.filter(fecha__gte=inicio, fecha__lt=fin)

    titulo = f"INSUMOS — {_nombre_mes(mes).upper()} {anio}"

    filas = (
        qs.values(
            'insumo__id',
            'insumo__codigo_ins',
            'insumo__nombre_ins',
            'insumo__presentacion_ins',
            'insumo__precio_unitario_ins',
        )
        .annotate(
            total_cantidad=Sum('cantidad'),
            total_costo=Sum(
                ExpressionWrapper(
                    F('cantidad') * F('insumo__precio_unitario_ins'),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
        )
        .order_by('-total_cantidad')
    )

    total_general = sum(f['total_costo'] or 0 for f in filas)

    return list(filas), titulo, total_general, mes, anio


def _examenes_mes(request):
    mes, anio = _mes_anio_desde_request(request)
    doctor_id = request.GET.get('doctor')
    tipo = request.GET.get('tipo')
    inicio = timezone.make_aware(datetime(anio, mes, 1, 0, 0, 0))

    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fin = timezone.make_aware(datetime(anio, mes, ultimo_dia, 23, 59, 59))

    examenes = RealizarExamen.objects.filter(
        fecha__gte=inicio,
        fecha__lte=fin
    ).select_related(
        'paciente',
        'familiar',
        'doctor__usuario'
    
    ).prefetch_related(
    'examenes_realizados__examen',
    'movimientos_stock').order_by('-fecha')



    if tipo:
        examenes = examenes.filter(
            examenes_realizados__examen__tipo_exa=tipo
        ).distinct()


    if doctor_id:
        examenes = examenes.filter(doctor_id=doctor_id)

        dr = (
            Doctorperfil.objects
            .select_related('usuario')
            .filter(id=doctor_id)
            .first()
        )


        titulo = (
            f"EXÁMENES REALIZADOS — {_nombre_mes(mes).upper()} {anio}"
            + (
                f" — DR. {dr.usuario.nombre} {dr.usuario.apellido}"
                if dr else ""
            )
        )

     
    else:
        titulo = f"EXÁMENES REALIZADOS — {_nombre_mes(mes).upper()} {anio}"

    filas = []

    total_examenes = Decimal('0.00')
    total_insumos = Decimal('0.00')
    total_general = Decimal('0.00')

    for ex in examenes:

        sub_ex = sum(
            item.subtotal or Decimal('0.00')
            for item in ex.examenes_realizados.all().select_related('examen')
        )

        sub_ins = sum(
            item.total_movimiento or Decimal('0.00')
            for item in ex.movimientos_stock.all()
        )

        total = ex.total or (sub_ex + sub_ins)

        total_examenes += sub_ex
        total_insumos += sub_ins
        total_general += total

        filas.append({
            'examen': ex,
            'sub_examenes': sub_ex,
            'sub_insumos': sub_ins,
            'total': total,
        })

    resumen = {
        'cantidad': len(filas),
        'total_examenes': total_examenes,
        'total_insumos': total_insumos,
        'total_general': total_general,
    }

    return filas, titulo, resumen, mes, anio


def _render_pdf(template_name, context, filename):
    html = get_template(template_name).render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    pisa.CreatePDF(html, dest=response)
    return response


def _contexto_filtros():
    return {
        'doctores': Doctorperfil.objects.select_related('usuario', 'especialidad').order_by(
            'usuario__apellido'
        ),
        'especialidades': Especialidad.objects.all(),
        'estados': CitaMedica.ESTADOS,
        'meses': MESES,
        'anio_actual': timezone.localdate().year,
        'mes_actual': timezone.localdate().month,
    }


@login_required
@rol_requerido(['ADMIN'])
def reportes_contabilidad(request):
    return render(request, 'reportes/contabilidad.html')


@login_required
@rol_requerido(['ADMIN'])
def reporte_citas(request):
    ctx = _contexto_filtros()
    mostrar = request.GET.get('ver') == '1'

    if mostrar:
        citas, titulo = _filtrar_citas(request)
        resumen = _resumen_citas(citas)
        ctx.update({
            'mostrar_resultados': True,
            'citas': citas,
            'titulo_reporte': titulo,
            'resumen': resumen,
            'filtros': request.GET,
        })
    else:
        ctx['mostrar_resultados'] = False
        ctx['filtros'] = {}

    return render(request, 'reportes/reporte_citas.html', ctx)


@login_required
@rol_requerido(['ADMIN'])
def generar_pdf_citas(request):
    citas, titulo = _filtrar_citas(request)
    resumen = _resumen_citas(citas)
    return _render_pdf(
        'reportes/pdf_citas.html',
        {
            'citas': citas,
            'titulo': titulo,
            'total': resumen['total'],
            'por_estado': resumen['por_estado'],
            'total_bs': resumen['total_bs'],
            'total_usd': resumen['total_usd'],
            'fecha_generacion': timezone.now(),
        },
        'reporte_citas.pdf',
    )


@login_required
@rol_requerido(['ADMIN'])
def reporte_insumos(request):
    ctx = _contexto_filtros()
    mostrar = request.GET.get('ver') == '1'

    if mostrar:
        filas, titulo, total_general, mes, anio = _insumos_consumidos(request)
        ctx.update({
            'mostrar_resultados': True,
            'filas': filas,
            'titulo_reporte': titulo,
            'total_general': total_general,
            'mes': mes,
            'anio': anio,
            'filtros': request.GET,
        })



    else:
        ctx['mostrar_resultados'] = False
        ctx['filtros'] = {}

    return render(request, 'reportes/reporte_insumos.html', ctx)


@login_required
@rol_requerido(['ADMIN'])
def generar_pdf_insumos(request):
    filas, titulo, total_general, mes, anio = _insumos_consumidos(request)
    return _render_pdf(
        'reportes/pdf_insumos.html',
        {
            'filas': filas,
            'titulo': titulo,
            'total_general': total_general,
            'fecha_generacion': timezone.now(),
        },
        'reporte_insumos.pdf',
    )


@login_required
@rol_requerido(['ADMIN'])
def reporte_examenes(request):
    ctx = _contexto_filtros()
    mostrar = request.GET.get('ver') == '1'

    if mostrar:
        filas, titulo, resumen, mes, anio = _examenes_mes(request)
        ctx.update({
            'mostrar_resultados': True,
            'filas': filas,
            'titulo_reporte': titulo,
            'resumen': resumen,
            'mes': mes,
            'anio': anio,
            'filtros': request.GET,
            
        })
    else:
        ctx['mostrar_resultados'] = False
        ctx['filtros'] = {}

    return render(request, 'reportes/reporte_examenes.html', ctx)


@login_required
@rol_requerido(['ADMIN'])
def generar_pdf_examenes(request):
    filas, titulo, resumen, mes, anio = _examenes_mes(request)
    return _render_pdf(
        'reportes/pdf_examenes.html',
        {
            'filas': filas,
            'titulo': titulo,
            'resumen': resumen,
            'fecha_generacion': timezone.now(),
        },
        'reporte_examenes.pdf',
    )
