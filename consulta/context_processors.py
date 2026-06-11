from django.db.models import F
from .models import InsumoMedico,BCV
from django.utils.timezone import now
from datetime import time
from django.utils.timezone import now, make_aware



def insumos_bajos(request):
    return {
        'insumos_bajos_global': InsumoMedico.objects.filter(
            cantidad_ins__lte=F('stock_minimo')
        )
    }

def bcv_context(request):

    ultimo = BCV.objects.order_by('-fecha').first()

    ahora = now()
    hoy = ahora.date()
    corte = ahora.replace(hour=16, minute=0, second=0, microsecond=0)

    # 👉 por defecto vencido
    bcv_vencido = True

    if ultimo:

        # 📅 si es fin de semana, siempre usar último BCV válido (viernes)
        if ahora.weekday() >= 5:  # sábado o domingo
            bcv_vencido = False

        else:
            # 🟡 antes de las 4PM → aún válido el BCV anterior
            if ahora < corte:
                if ultimo.fecha.date() == hoy:
                    bcv_vencido = False
            else:
                # 🔴 después de 4PM → solo válido si ya se actualizó hoy
                if ultimo.fecha.date() == hoy:
                    bcv_vencido = False

    return {
        'bcv_actual': ultimo.valor if ultimo else 0,
        'bcv_vencido': bcv_vencido
    }