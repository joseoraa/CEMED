from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from datetime import datetime, timedelta,time
from django.utils import timezone
from .models import *
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory
from .models import RealizarExamen, ExamenRealizado, DetalleInsumoExamen


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))



# =======================================================

class CambiarPasswordForm(forms.Form):
    old_password = forms.CharField(
        label="Contraseña Actual",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

# =======================================================

class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = ['nombre_espe']
        widgets = {
            'nombre_espe': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese especialidad'
            })
        }



class FamiliarPacienteForm(forms.ModelForm):

    class Meta:
        model = FamiliarPaciente

        fields = [
            'paciente_titular',
            'nombre',
            'apellido',
            'sexo',
            'fecha_nacimiento',
            'parentesco',
            'telefono',
            'observacion'
        ]

        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={'type': 'date'}
            )
        }
# =======================================================

# sexo en la playa
class RegistroPacienteForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['tipo_cedula','cedula', 'nombre', 'apellido','sexo', 'fecha_nacimiento', 'telefono', 'email']

        widgets = {
            'tipo_cedula': forms.Select(attrs={'class': 'form-select'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date','max': (datetime.now().date() + timedelta(days=0)).isoformat()}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.PACIENTE
        usuario.username = self.cleaned_data['cedula']  # OJO: asignar username también
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario

# =======================================================

class CrearUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['tipo_cedula','cedula', 'nombre', 'apellido','sexo', 'fecha_nacimiento', 'telefono', 'email', 'rol']
        widgets = {
            'tipo_cedula': forms.Select(attrs={'class': 'form-select'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date','max': (datetime.now().date() + timedelta(days=0)).isoformat()}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)

        # ⚠️ IMPORTANTE: Evita el error "Duplicate entry '' for key 'username'"
        usuario.username = usuario.cedula  

        # Guardar contraseña encriptada
        usuario.set_password(self.cleaned_data["password1"])

        if commit:
            usuario.save()
        return usuario

# =======================================================

class EditarUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese nueva contraseña'}),
        required=False
    )
    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita la nueva contraseña'}),
        required=False
    )

    class Meta:
        model = Usuario
        fields = ['cedula', 'nombre', 'apellido', 'fecha_nacimiento', 'telefono', 'email', 'rol']
        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),

            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Coloca placeholders con los valores actuales
        for field_name in ['nombre', 'apellido', 'fecha_nacimiento', 'telefono', 'email']:
            if self.instance and getattr(self.instance, field_name):
                self.fields[field_name].widget.attrs['placeholder'] = str(getattr(self.instance, field_name))

            if self.instance and self.instance.fecha_nacimiento:
                self.fields['fecha_nacimiento'].initial = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Las contraseñas no coinciden")
        return p2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        p = self.cleaned_data.get('password1')
        if p:
            usuario.set_password(p)
        if commit:
            usuario.save()
        return usuario

# =======================================================

class UsuarioActualizarForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'fecha_nacimiento', 'telefono', 'email']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# =======================================================

class DoctorPerfilForm(forms.ModelForm):
    imagen = forms.ImageField(
        required=False,
        label='📸 Foto de Perfil',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Doctorperfil
        fields = ['especialidad','precio_consulta', 'imagen', 'descripcion']
        labels = {
            'especialidad': '🩺 Especialidad',
            'descripcion': '📝 Descripción',
            'precio_consulta': '$ precio_consulta'
        }
        widgets = {
            'especialidad': forms.Select (attrs={'class': 'form-control', 'placeholder': 'Especialidad'}),
            'precio_consulta': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01, 'min': 0}),           
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción sobre ti'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Evitar mostrar link de imagen actual
        self.fields['imagen'].widget.template_name = 'django/forms/widgets/input.html'

# =======================================================

class ExamenMedicoForm(forms.ModelForm):
    class Meta:
        model = ExamenMedico
        fields = ['nombre_examen', 'archivo', 'fecha_examen', 'descripcion']   
        widgets = {
            'fecha_examen': forms.DateInput(attrs={'type': 'date', 'class': 'form-control','min': datetime.now().date().isoformat(),
                    'max': (datetime.now().date() + timedelta(days=30)).isoformat(),}),
            'nombre_examen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Hemograma'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }
# =======================================================


class HorarioDoctorForm(forms.ModelForm):

    class Meta:
        model = HorarioDoctor
        fields = ['dia', 'hora_inicio', 'hora_fin']

        labels = {
            'dia': 'Día de la Semana',
            'hora_inicio': 'Hora de Inicio',
            'hora_fin': 'Hora Final',
        }

        widgets = {
            'dia': forms.Select(attrs={
                'class': 'form-select',
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'hora_fin': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }

    def clean(self):
            cleaned_data = super().clean()
            dia = cleaned_data.get("dia")
            hora_inicio = cleaned_data.get("hora_inicio")
            hora_fin = cleaned_data.get("hora_fin")

            if hora_inicio and hora_fin and hora_inicio >= hora_fin:
                self.add_error("hora_fin", "La hora final debe ser mayor que la hora de inicio.")

            # Validación de múltiplos de 30 minutos (sigue funcionando igual)
            for field_name, hora in [('hora_inicio', hora_inicio), ('hora_fin', hora_fin)]:
                if hora:
                    if hora.minute not in (0, 30):
                        self.add_error(field_name, "La hora debe ser en múltiplos de 30 minutos (ej: 08:00, 08:30, 09:00).")

            # Validar que no se repita el día
            if self.instance.doctor:
                existe = HorarioDoctor.objects.filter(
                    doctor=self.instance.doctor,
                    dia=dia
                )
                if self.instance.pk:
                    existe = existe.exclude(pk=self.instance.pk)

                if existe.exists():
                    self.add_error("dia", "Este día ya tiene un horario registrado.")

            return cleaned_data

    # ========================    # ========================    # ========================


# =======================================================

class SliderImagenForm(forms.ModelForm):
    class Meta:
        model = SliderImagen
        fields = ['titulo', 'descripcion', 'imagen', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# =======================================================

class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = ['codigo_exa', 'nom_exa', 'tipo_exa', 'caracteristica_exa', 'precio_exa']

        labels = {
            'codigo_exa': 'Código del Examen',
            'nom_exa': 'Nombre del Examen',
            'tipo_exa': 'Tipo de Examen',
            'caracteristica_exa': 'Características',
            'precio_exa': 'Precio',
        }

        widgets = {
            'codigo_exa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el código del examen',
            }),
            'nom_exa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre del examen',
            }),
            'tipo_exa': forms.Select(attrs={
                'class': 'form-select',
            }),
            'caracteristica_exa': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese características del examen',
                'rows': 3,
            }),
            'precio_exa': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el precio',
                'step': '0.01',
                'min': '0',
            }),
        }

# 1. VALIDACIÓN DE CÓDIGO (Mayúsculas + Unicidad)
    def clean_codigo_exa(self):
        codigo = self.cleaned_data.get('codigo_exa').upper()
        
        # Verificar si el código ya existe (excluyendo el objeto actual si estamos editando)
        existe = Examen.objects.filter(codigo_exa=codigo)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
            
        if existe.exists():
            raise ValidationError("¡Atención! Este código de examen ya está registrado.")
        
        if len(codigo) < 3:
            raise ValidationError("El código es demasiado corto (mínimo 3 caracteres).")
            
        return codigo

    # 2. VALIDACIÓN DE NOMBRE (Mayúsculas + Unicidad)
    def clean_nom_exa(self):
        nombre = self.cleaned_data.get('nom_exa').upper()
        
        # Verificar si el nombre ya existe
        existe = Examen.objects.filter(nom_exa=nombre)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
            
        if existe.exists():
            raise ValidationError("Ya existe un examen con este nombre.")
            
        return nombre

    # 3. VALIDACIÓN DE CARACTERÍSTICAS (Solo Mayúsculas)
    def clean_caracteristica_exa(self):
        dato = self.cleaned_data.get('caracteristica_exa')
        return dato.upper() if dato else dato

    # 4. VALIDACIÓN GENERAL (Para errores que cruzan campos)
    def clean(self):
        cleaned_data = super().clean()
        precio = cleaned_data.get('precio_exa')
        tipo = cleaned_data.get('tipo_exa')

        # Ejemplo de error general: Si el tipo es 'ESPECIAL' el precio no puede ser 0
        if tipo and precio is not None:
            if "ESPECIAL" in str(tipo).upper() and precio <= 0:
                raise ValidationError(
                    "Los exámenes de tipo especial deben tener un precio mayor a 0."
                )
        return cleaned_data

# =======================================================

class InsumoMedicoForm(forms.ModelForm):
    class Meta:
        model = InsumoMedico
        fields = [
            'codigo_ins',
            'nombre_ins',
            'presentacion_ins',
            'descripcion_ins',
            'cantidad_ins',
            'precio_unitario_ins',
            'fecha_caducidad_ins',
            'proveedor_ins'
        ]

        labels = {
            'codigo_ins': 'Código de Insumo',
            'nombre_ins': 'Nombre del Insumo',
            'presentacion_ins': 'Presentación',
            'descripcion_ins': 'Descripción / Observaciones',
            'cantidad_ins': 'Cantidad en Stock',
            'precio_unitario_ins': 'Precio Unitario',
            'fecha_caducidad_ins': 'Fecha de Caducidad',
            'proveedor_ins': 'Proveedor',
        }

        widgets = {
            'codigo_ins': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: INS001'}),
            'nombre_ins': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del insumo'}),
            'presentacion_ins': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Caja, frasco, unidad...'}),
            'descripcion_ins': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opcional'}),
            'cantidad_ins': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'precio_unitario_ins': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01, 'min': 0}),
            'fecha_caducidad_ins': forms.DateInput(attrs={'class': 'form-control', 'type': 'date','min': datetime.now().date().isoformat(),}),
            'proveedor_ins': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
        }

    def clean_fecha_caducidad_ins(self):
        fecha = self.cleaned_data.get('fecha_caducidad_ins')
        if fecha and fecha < date.today():
            raise forms.ValidationError("La fecha de caducidad no puede ser anterior a hoy.")
        return fecha

    def clean_cantidad_ins(self):
        cantidad = self.cleaned_data.get('cantidad_ins')
        if cantidad is not None and cantidad < 0:
            raise forms.ValidationError("La cantidad no puede ser negativa.")
        return cantidad

    def clean_precio_unitario_ins(self):
        precio = self.cleaned_data.get('precio_unitario_ins')
        if precio is not None and precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio
    

# =======================================================

class HistoriaMedicaForm(forms.ModelForm):
    class Meta:
        model = HistoriaMedica
        fields = [
            'antecedentes',
            'alergias',
            'enfermedades_cronicas',
            'motivo_consulta',
            'diagnostico',
            'observaciones'
        ]
        widgets = {
            'antecedentes': forms.Textarea(
                attrs={
                    'class': 'form-control rounded shadow-sm',
                    'placeholder': 'Escribe los antecedentes del paciente...',
                    'rows': 2
                }
            ),
            'alergias': forms.Textarea(
                attrs={
                    'class': 'form-control rounded shadow-sm',
                    'placeholder': 'Indica si tiene alguna alergia...',
                    'rows': 2
                }
            ),
            'enfermedades_cronicas': forms.Textarea(
                attrs={
                    'class': 'form-control rounded shadow-sm',
                    'placeholder': 'Enfermedades crónicas conocidas...',
                    'rows': 2
                }
            ),
            
            'diagnostico': forms.Textarea(
                attrs={
                    'class': 'form-control rounded shadow-sm',
                    'placeholder': 'Enfermedades crónicas conocidas...',
                    'rows': 2
                }
            ),

            'motivo_consulta': forms.Textarea(
                attrs={
                    'class': 'form-control rounded shadow-sm',
                    'placeholder': 'Enfermedades crónicas conocidas...',
                    'rows': 2
                }
            ),

            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control rounded shadow-sm',
                    'placeholder': 'Observaciones adicionales...',
                    'rows': 2
                }
            ),
        }
        labels = {
            'antecedentes': 'Antecedentes',
            'alergias': 'Alergias',
            'enfermedades_cronicas': 'Enfermedades Crónicas',
            'diagnostico': 'Diagnóstico',
            'motivo_consulta': 'Motivo de Consulta',
            'observaciones': 'Observaciones'
        }
        
# =======================================================


# ==========================================================
# FORM PARA PACIENTE
# ==========================================================

class CitaPacienteForm(forms.ModelForm):
    TIPO_CITA = (
        ('PACIENTE', 'Para mí'),
        ('FAMILIAR', 'Para un familiar'),
    )

    tipo = forms.ChoiceField(
        choices=TIPO_CITA,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo'})
    )

    familiar = forms.ModelChoiceField(
        queryset=FamiliarPaciente.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_familiar'})
    )

    hora = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_hora'})
    )

    class Meta:
        model = CitaMedica
        fields = ['tipo', 'familiar', 'doctor', 'fecha', 'motivo']

        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor'}),
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_fecha',
                'min': datetime.now().date().isoformat(),
                'max': (datetime.now().date() + timedelta(days=30)).isoformat(),
            }),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['hora'].choices = [('', 'Seleccione doctor y fecha')]

        self.fields['doctor'].queryset = Doctorperfil.objects.filter(
            especialidad__isnull=False
        ).select_related('especialidad', 'usuario')

        # 👇 familiares del usuario logueado
        if self.user:
            self.fields['familiar'].queryset = FamiliarPaciente.objects.filter(
                paciente_titular=self.user,
                activo=True
            )

        # ---------------- HORAS (tu lógica intacta) ----------------
        if 'doctor' in self.data and 'fecha' in self.data:
            doctor_id = self.data.get('doctor')
            fecha_str = self.data.get('fecha')

            if doctor_id and fecha_str:
                try:
                    doctor = Doctorperfil.objects.get(id=doctor_id)
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

                    dias_map = {
                        0: 'lunes', 1: 'martes', 2: 'miercoles',
                        3: 'jueves', 4: 'viernes', 5: 'sabado', 6: 'domingo',
                    }

                    dia_semana = dias_map[fecha.weekday()]

                    horarios = HorarioDoctor.objects.filter(
                        doctor=doctor,
                        dia=dia_semana
                    )

                    horas_choices = [('', 'Seleccione la hora deseada')]

                    for horario in horarios:
                        hora_actual = datetime.combine(fecha, horario.hora_inicio)
                        hora_fin = datetime.combine(fecha, horario.hora_fin)

                        while hora_actual < hora_fin:
                            hora_str = hora_actual.strftime('%H:%M')

                            ocupada = CitaMedica.objects.filter(
                                doctor=doctor,
                                fecha=fecha,
                                hora=hora_actual.time()
                            ).exclude(estado='CANCELADA').exists()

                            ahora = datetime.now()
                            if fecha == ahora.date() and hora_actual <= ahora:
                                ocupada = True

                            if not ocupada:
                                horas_choices.append((hora_str, hora_str))

                            hora_actual += timedelta(minutes=30)

                    self.fields['hora'].choices = horas_choices

                except Exception as e:
                    print("Error horas:", e)

    def clean(self):

        cleaned_data = super().clean()

        tipo = cleaned_data.get('tipo')
        familiar = cleaned_data.get('familiar')

        doctor = cleaned_data.get('doctor')
        fecha = cleaned_data.get('fecha')

        hora_str = cleaned_data.get('hora')

        if tipo == 'FAMILIAR' and not familiar:
            raise ValidationError(
                "Debe seleccionar un familiar."
            )

        if tipo == 'PACIENTE':
            cleaned_data['familiar'] = None


        if not doctor or not fecha or not hora_str:
            return cleaned_data

        try:
            hora = datetime.strptime(
                hora_str,
                '%H:%M'
            ).time()

        except Exception:
            raise ValidationError({
                'hora': "Hora inválida."
            })

        paciente = self.user
        fecha_hora_cita = datetime.combine(
            fecha,
            hora
        )

        if fecha_hora_cita < datetime.now():

            raise ValidationError({
                'fecha': (
                    "No se puede agendar una cita "
                    "en el pasado."
                )
            })
        # =====================================================
        # =====================================================
        fecha_minima = fecha - timedelta(days=8)

        filtro = CitaMedica.objects.filter(
            doctor=doctor,
            fecha__gte=fecha_minima,
            estado__in=[
                'PENDIENTE',
                'CONFIRMADA',
                'ATENDIDA'
            ]
        )

        # Si la cita es para el paciente titular
        if tipo == 'PACIENTE':

            filtro = filtro.filter(
                paciente=paciente,
                familiar__isnull=True
            )

        # Si la cita es para un familiar
        elif tipo == 'FAMILIAR':

            filtro = filtro.filter(
                familiar=familiar
            )

        ultima_cita = filtro.exclude(
            pk=self.instance.pk if self.instance.pk else None
        ).order_by(
            '-fecha',
            '-hora'
        ).first()

        if ultima_cita:

            dias_diferencia = (
                fecha - ultima_cita.fecha
            ).days

            if dias_diferencia < 8:

                raise ValidationError({
                    'fecha': (
                        f"Debe esperar al menos 8 días para "
                        f"pedir otra cita con este doctor. "
                        f"Última cita: "
                        f"{ultima_cita.fecha.strftime('%d/%m/%Y')}"
                    )
                })
        # =====================================================
        # 3. VALIDAR HORA DENTRO DEL HORARIO
        # =====================================================

        dias_map = {
            0: 'lunes',
            1: 'martes',
            2: 'miercoles',
            3: 'jueves',
            4: 'viernes',
            5: 'sabado',
            6: 'domingo'
        }

        dia_semana = dias_map[fecha.weekday()]

        horario_valido = HorarioDoctor.objects.filter(
            doctor=doctor,
            dia=dia_semana,
            hora_inicio__lte=hora,
            hora_fin__gte=hora
        ).exists()

        if not horario_valido:

            raise ValidationError({
                'hora': (
                    "La hora seleccionada no "
                    "está dentro del horario "
                    "del doctor."
                )
            })

        # =====================================================
        # 4. VALIDAR HORA OCUPADA
        # =====================================================

        cita_existente = CitaMedica.objects.filter(
            doctor=doctor,
            fecha=fecha,
            hora=hora
        ).exclude(
            estado='CANCELADA'
        ).exclude(
            pk=self.instance.pk if self.instance.pk else None
        ).exists()

        if cita_existente:

            raise ValidationError({
                'hora': (
                    "La hora seleccionada ya "
                    "está ocupada."
                )
            })

        return cleaned_data



# ==========================================================
class CitaAdminForm(forms.ModelForm):

    TIPO = (
        ('PACIENTE', 'Paciente'),
        ('FAMILIAR', 'Familiar'),
    )

    tipo = forms.ChoiceField(
        choices=TIPO,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo'})
    )

    familiar = forms.ModelChoiceField(
        queryset=FamiliarPaciente.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_familiar'})
    )

    hora = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_hora'})
    )

    class Meta:
        model = CitaMedica
        fields = ['tipo', 'paciente', 'familiar', 'doctor', 'fecha', 'hora', 'motivo', 'estado']

        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-select', 'id': 'id_paciente'}),
            'doctor': forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor'}),
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_fecha',
                'min': datetime.now().date().isoformat(),
                'max': (datetime.now().date() + timedelta(days=15)).isoformat(),
            }),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('initial', {}).get('user')
        super().__init__(*args, **kwargs)

        # pacientes
        self.fields['paciente'].queryset = Usuario.objects.filter(
            rol='PACIENTE'
        ).order_by('nombre', 'apellido')

        # familiares
        self.fields['familiar'].queryset = FamiliarPaciente.objects.all()

        # doctores
        self.fields['doctor'].queryset = Doctorperfil.objects.filter(
            especialidad__isnull=False
        ).select_related('especialidad', 'usuario')

        self.fields['hora'].choices = [('', 'Seleccione doctor y fecha')]

        if not self.instance.pk:
            self.fields.pop('estado')

        # horas dinámicas
        if self.data.get('doctor') and self.data.get('fecha'):
            try:
                doctor = Doctorperfil.objects.get(id=self.data.get('doctor'))
                fecha = datetime.strptime(self.data.get('fecha'), '%Y-%m-%d').date()

                dias_map = {
                    0: 'lunes', 1: 'martes', 2: 'miercoles',
                    3: 'jueves', 4: 'viernes', 5: 'sabado', 6: 'domingo'
                }

                horarios = HorarioDoctor.objects.filter(
                    doctor=doctor,
                    dia=dias_map[fecha.weekday()]
                )

                horas_choices = [('', 'Seleccione una hora')]

                for horario in horarios:
                    hora_actual = datetime.combine(fecha, horario.hora_inicio)
                    hora_fin = datetime.combine(fecha, horario.hora_fin)

                    while hora_actual < hora_fin:
                        hora_str = hora_actual.strftime('%H:%M')

                        ocupada = CitaMedica.objects.filter(
                            doctor=doctor,
                            fecha=fecha,
                            hora=hora_actual.time()
                        ).exclude(estado='CANCELADA').exists()

                        if not ocupada:
                            horas_choices.append((hora_str, hora_str))

                        hora_actual += timedelta(minutes=30)

                self.fields['hora'].choices = horas_choices

            except Exception as e:
                print("Error horas admin:", e)

    def clean(self):

        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        paciente = cleaned_data.get('paciente')
        familiar = cleaned_data.get('familiar')
        doctor = cleaned_data.get('doctor')
        fecha = cleaned_data.get('fecha')
        hora_str = cleaned_data.get('hora')

        if not all([tipo, doctor, fecha, hora_str]):
            return cleaned_data
        
        try:

            hora = datetime.strptime(
                hora_str,
                '%H:%M'
            ).time()

        except ValueError:

            raise ValidationError({
                'hora': "Hora inválida"
            })

        # =====================================================
        # VALIDAR TIPO PACIENTE / FAMILIAR
        # =====================================================

        if tipo == 'PACIENTE':

            if not paciente:

                raise ValidationError({
                    'paciente': (
                        "Debe seleccionar un paciente"
                    )
                })

            cleaned_data['familiar'] = None

        elif tipo == 'FAMILIAR':

            if not familiar:

                raise ValidationError({
                    'familiar': (
                        "Debe seleccionar un familiar"
                    )
                })

            cleaned_data['paciente'] = None

            # obtener paciente titular
            paciente = familiar.paciente_titular

        # =====================================================
        # 1. NO PERMITIR FECHAS PASADAS
        # =====================================================

        fecha_hora_cita = datetime.combine(
            fecha,
            hora
        )

        if fecha_hora_cita < datetime.now():

            raise ValidationError({
                'fecha': (
                    "No se puede agendar una cita "
                    "en el pasado."
                )
            })

        # =====================================================
        # 2. VALIDAR 8 DÍAS MISMO DOCTOR
        # =====================================================
        fecha_minima = fecha - timedelta(days=8)

        filtro = CitaMedica.objects.filter(
            doctor=doctor,
            fecha__gte=fecha_minima,
            estado__in=[
                'PENDIENTE',
                'CONFIRMADA',
                'ATENDIDA'
            ]
        )

        # Si la cita es para el paciente titular
        if tipo == 'PACIENTE':

            filtro = filtro.filter(
                paciente=paciente,
                familiar__isnull=True
            )

        # Si la cita es para un familiar
        elif tipo == 'FAMILIAR':

            filtro = filtro.filter(
                familiar=familiar
            )

        ultima_cita = filtro.exclude(
            pk=self.instance.pk if self.instance.pk else None
        ).order_by(
            '-fecha',
            '-hora'
        ).first()

        if ultima_cita:

            dias_diferencia = (
                fecha - ultima_cita.fecha
            ).days

            if dias_diferencia < 8:

                raise ValidationError({
                    'fecha': (
                        f"Debe esperar al menos 8 días para "
                        f"pedir otra cita con este doctor. "
                        f"Última cita: "
                        f"{ultima_cita.fecha.strftime('%d/%m/%Y')}"
                    )
                })
        # =====================================================
        # 3. VALIDAR HORARIO DEL DOCTOR
        # =====================================================

        dias_map = {
            0: 'lunes',
            1: 'martes',
            2: 'miercoles',
            3: 'jueves',
            4: 'viernes',
            5: 'sabado',
            6: 'domingo'
        }

        dia_semana = dias_map[fecha.weekday()]

        horario_valido = HorarioDoctor.objects.filter(
            doctor=doctor,
            dia=dia_semana,
            hora_inicio__lte=hora,
            hora_fin__gte=hora
        ).exists()

        if not horario_valido:

            raise ValidationError({
                'hora': (
                    "La hora seleccionada no "
                    "está dentro del horario "
                    "del doctor."
                )
            })

        # =====================================================
        # 4. VALIDAR HORA OCUPADA
        # =====================================================

        cita_existente = CitaMedica.objects.filter(
            doctor=doctor,
            fecha=fecha,
            hora=hora
        ).exclude(
            estado='CANCELADA'
        ).exclude(
            pk=self.instance.pk if self.instance.pk else None
        ).exists()

        if cita_existente:

            raise ValidationError({
                'hora': (
                    "La hora seleccionada ya "
                    "está ocupada."
                )
            })

        return cleaned_data


    # def clean(self):
    #     cleaned_data = super().clean()

    #     tipo = cleaned_data.get('tipo')
    #     paciente = cleaned_data.get('paciente')
    #     familiar = cleaned_data.get('familiar')
    #     doctor = cleaned_data.get('doctor')
    #     fecha = cleaned_data.get('fecha')
    #     hora_str = cleaned_data.get('hora')

    #     if not all([tipo, doctor, fecha, hora_str]):
    #         return cleaned_data

    #     # convertir hora
    #     try:
    #         hora = datetime.strptime(hora_str, '%H:%M').time()
    #     except ValueError:
    #         raise ValidationError({'hora': "Hora inválida"})

    #     # validar tipo
    #     if tipo == 'PACIENTE' and not paciente:
    #         raise ValidationError("Debe seleccionar un paciente")

    #     if tipo == 'FAMILIAR' and not familiar:
    #         raise ValidationError("Debe seleccionar un familiar")




    #     return cleaned_data


# class CitaAdminForm(forms.ModelForm):
#     hora = forms.ChoiceField(
#         choices=[],
#         required=True,
#         widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_hora'})
#     )

#     class Meta:
#         model = CitaMedica
#         fields = ['paciente', 'doctor', 'fecha', 'motivo','estado']  # sin 'hora'
#         widgets = {
#             'paciente': forms.Select(attrs={'class': 'form-select'}),
#             'doctor': forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor',}),
#             'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_fecha','min': datetime.now().date().isoformat(),'max': (datetime.now().date() + timedelta(days=15)).isoformat(),}),
#             'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'estado': forms.Select(attrs={'class': 'form-select'}), 
#         }

#     def __init__(self, *args, **kwargs):
#             super().__init__(*args, **kwargs)

#             self.fields['paciente'].queryset = Usuario.objects.filter(rol='PACIENTE').order_by('nombre', 'apellido')
#             # self.fields['doctor'].queryset = Doctorperfil.objects.all().order_by('usuario__nombre')

#             self.fields['doctor'].queryset = Doctorperfil.objects.filter(
#                 especialidad__isnull=False
#             ).select_related(
#                 'especialidad', 'usuario'
#             ).order_by(
#                 'especialidad__nombre_espe', 
#                 'usuario__nombre'
#             )
#             # Hora por defecto
#             self.fields['hora'].choices = [('', 'Seleccione primero doctor y fecha')]
#             # self.fields['doctor'].queryset = Doctorperfil.objects.all().order_by(
#             #     'especialidad__nombre_espe', 
#             #     'usuario__nombre'
#             # )
#             if not self.instance.pk:
#                 self.fields.pop('estado')

#             # Si viene datos del POST (para recargar horas dinámicamente)
#             if self.data and 'doctor' in self.data and 'fecha' in self.data:
#                 doctor_id = self.data.get('doctor')
#                 fecha_str = self.data.get('fecha')

#                 if doctor_id and fecha_str:
#                     try:
#                         doctor = Doctorperfil.objects.get(id=doctor_id)
#                         fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

#                         dias_map = {
#                             0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves',
#                             4: 'viernes', 5: 'sabado', 6: 'domingo'
#                         }

#                         dia_semana = dias_map[fecha.weekday()]

#                         horarios = HorarioDoctor.objects.filter(
#                             doctor=doctor,
#                             dia=dia_semana
#                         )

#                         horas_choices = [('', 'Seleccione una hora')]

#                         for horario in horarios:
#                             hora_actual = datetime.combine(fecha, horario.hora_inicio)
#                             hora_fin = datetime.combine(fecha, horario.hora_fin)

#                             while hora_actual < hora_fin:
#                                 hora_str = hora_actual.strftime('%H:%M')
#                                 hora_time = hora_actual.time()

#                                 # Verificar si la hora está ocupada
#                                 ocupada = CitaMedica.objects.filter(
#                                     doctor=doctor,
#                                     fecha=fecha,
#                                     hora=hora_time
#                                 ).exclude(estado='CANCELADA').exists()

#                                 # Si es hoy, no permitir horas pasadas
#                                 ahora = datetime.now()
#                                 if fecha == ahora.date() and hora_actual <= ahora:
#                                     ocupada = True

#                                 if not ocupada:
#                                     horas_choices.append((hora_str, hora_str))

#                                 hora_actual += timedelta(minutes=30)

#                         self.fields['hora'].choices = horas_choices

#                     except Exception as e:
#                         print("Error cargando horas:", e)
#                         self.fields['hora'].choices = [('', 'Error al cargar horarios')]

#     def clean(self):
#             cleaned_data = super().clean()

#             # paciente = cleaned_data.get('paciente')
#             paciente = cleaned_data.get('paciente')
#             doctor   = cleaned_data.get('doctor')
#             fecha    = cleaned_data.get('fecha')
#             hora_str = cleaned_data.get('hora')   # viene como string desde ChoiceField

#             if not all([paciente, doctor, fecha, hora_str]):
#                 return cleaned_data

#             # Convertir hora string a time
#             try:
#                 hora = datetime.strptime(hora_str, '%H:%M').time()
#             except ValueError:
#                 raise ValidationError({'hora': _("Formato de hora inválido.")})

#             # 1. No permitir citas en el pasado (doble protección)
#             fecha_hora_cita = datetime.combine(fecha, hora)
#             if fecha_hora_cita < datetime.now():
#                 raise ValidationError({
#                     'fecha': _("No se puede agendar una cita en el pasado.")
#                 })


#             # 2. Regla de 8 días SOLO con el mismo doctor
#             fecha_minima = fecha - timedelta(days=8)

#             ultima_cita = CitaMedica.objects.filter(
#                 paciente=paciente,
#                 doctor=doctor,  # 👈 mismo doctor
#                 fecha__gte=fecha_minima,
#                 estado__in=['PENDIENTE', 'CONFIRMADA', 'ATENDIDA']
#             ).exclude(
#                 pk=self.instance.pk if self.instance.pk else None
#             ).order_by('-fecha', '-hora').first()

#             if ultima_cita:
#                 dias_diferencia = (fecha - ultima_cita.fecha).days

#                 if dias_diferencia < 8:
#                     raise ValidationError({
#                         'fecha': _(
#                             f"Debe esperar al menos 8 días para pedir otra cita con este doctor. "
#                             f"Última cita: {ultima_cita.fecha.strftime('%d/%m/%Y')}"
#                         )
#                     })

#             # 3. Regla de 8 días SOLO con el mismo doctor
#             fecha_minima = fecha - timedelta(days=8)

#             ultima_cita = CitaMedica.objects.filter(
#                 paciente=paciente,
#                 doctor=doctor,
#                 fecha__gte=fecha_minima,
#                 estado__in=['PENDIENTE', 'CONFIRMADA', 'ATENDIDA']
#             ).exclude(
#                 pk=self.instance.pk if self.instance.pk else None
#             ).order_by('-fecha', '-hora').first()

#             if ultima_cita:
#                 dias_diferencia = (fecha - ultima_cita.fecha).days

#                 if dias_diferencia < 8:
#                     raise ValidationError({
#                         'fecha': _(
#                             f"Debe esperar al menos 8 días para pedir otra cita con este doctor. "
#                             f"Última cita: {ultima_cita.fecha.strftime('%d/%m/%Y')}"
#                         )
#                     })

#             # 4. Validar que la hora esté dentro del horario del doctor
#             dias_map = {0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves',
#                         4: 'viernes', 5: 'sabado', 6: 'domingo'}

#             dia_semana = dias_map[fecha.weekday()]

#             if not HorarioDoctor.objects.filter(
#                 doctor=doctor,
#                 dia=dia_semana,
#                 hora_inicio__lte=hora,
#                 hora_fin__gte=hora
#             ).exists():
#                 raise ValidationError({
#                     'hora': _("La hora seleccionada no está dentro del horario del doctor.")
#                 })

#             return cleaned_data


# =======================================================

class DetalleInsumoCitaForm(forms.ModelForm):
    class Meta:
        model = DetalleInsumoCita
        fields = ['insumo', 'cantidad']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['insumo'].queryset = InsumoMedico.objects.all()

        # 🔥 AGREGAR data-stock y data-precio
        choices = []
        for insumo in InsumoMedico.objects.all():
            choices.append((
                insumo.id,
                f"{insumo.nombre_ins}",
                {
                    'data-stock': insumo.cantidad_ins,
                    'data-precio': insumo.precio_unitario_ins
                }
            ))

        self.fields['insumo'].widget = forms.Select(
            attrs={'class': 'form-control'},
            choices=[(c[0], c[1]) for c in choices]
        )

        # 👇 ESTO ES LO IMPORTANTE
        self.fields['insumo'].widget.choices = [
            (insumo.id, f"{insumo.nombre_ins}", {
                'data-stock': insumo.cantidad_ins,
                'data-precio': insumo.precio_unitario_ins
            })
            for insumo in InsumoMedico.objects.all()
        ]


# ==========================================
class BCVForm(forms.ModelForm):
    class Meta:
        model = BCV
        fields = ['valor']


# ==========================================
class RealizarExamenForm(forms.ModelForm):

    persona = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_persona'
        })
    )

    class Meta:
        model = RealizarExamen

        fields = [
            'persona',
            'doctor',
            'observacion'
        ]

        widgets = {

            'doctor': forms.Select(attrs={
                'class': 'form-select'
            }),

            'observacion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        opciones = []
        pacientes = Usuario.objects.filter(
            rol='PACIENTE'
        ).order_by('nombre', 'apellido')
        for paciente in pacientes:
            opciones.append((
                f'PACIENTE-{paciente.id}',
                f'{paciente.nombre} {paciente.apellido} '
                f'({paciente.tipo_cedula}-{paciente.cedula})'
            ))
        familiares = FamiliarPaciente.objects.select_related(
            'paciente_titular'
        ).order_by('nombre', 'apellido')
        for familiar in familiares:
            opciones.append((
                f'FAMILIAR-{familiar.id}',
                f'{familiar.nombre} {familiar.apellido} '
                f'({familiar.parentesco}) '
                # f'- Titular: '
                # f'{familiar.paciente_titular.nombre} '
                # f'{familiar.paciente_titular.apellido}'            
                ))
        self.fields['persona'].choices = [
            ('', 'Seleccione paciente o familiar')
        ] + opciones






class RealizarExamenDoctorForm(forms.ModelForm):

    persona = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_persona'
        })
    )

    class Meta:
        model = RealizarExamen

        fields = [
            'persona',
            'observacion'
        ]

        widgets = {
            'observacion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        opciones = []

        pacientes = Usuario.objects.filter(
            rol='PACIENTE'
        ).order_by(
            'nombre',
            'apellido'
        )

        for paciente in pacientes:

            opciones.append((
                f'PACIENTE-{paciente.id}',
                f'{paciente.nombre} {paciente.apellido}'
            ))

        familiares = FamiliarPaciente.objects.select_related(
            'paciente_titular'
        ).order_by(
            'nombre',
            'apellido'
        )

        for familiar in familiares:

            opciones.append((
                f'FAMILIAR-{familiar.id}',
                f'{familiar.nombre} {familiar.apellido}'
            ))

        self.fields['persona'].choices = [
            ('', 'Seleccione paciente o familiar')
        ] + opciones
# ==========================================# ==========================================
class ExamenRealizadoForm(forms.ModelForm):
    class Meta:
        model = ExamenRealizado
        fields = ['examen']
    
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('examen'):
            raise forms.ValidationError("Debe seleccionar un examen.")
        return cleaned_data




# ==========================================
class DetalleInsumoExamenForm(forms.ModelForm):
    class Meta:
        model = DetalleInsumoExamen
        fields = ['insumo', 'cantidad']
    
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('insumo'):
            raise forms.ValidationError("Debe seleccionar un insumo.")
        return cleaned_data
    



# ==========================================
# FORMULARIO PARA ADMINISTRADOR
# ==========================================
class FamiliarPacienteAdminForm(forms.ModelForm):

    class Meta:
        model = FamiliarPaciente
        fields = [
            'paciente_titular',
            'nombre',
            'apellido',
            'sexo',
            'fecha_nacimiento',
            'parentesco',
            'telefono',
            'observacion',
            'activo',
        ]

        widgets = {
            'paciente_titular': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'parentesco': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['paciente_titular'].queryset = Usuario.objects.filter(
            rol=Usuario.PACIENTE
        )

        self.fields['paciente_titular'].label = "Paciente Titular"


# ==========================================
# FORMULARIO PARA PACIENTE

class AsignarFamiliarPacienteForm(forms.Form):

    familiar = forms.ModelChoiceField(
        queryset=FamiliarPaciente.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Familiar existente"
    )

    paciente = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(rol=Usuario.PACIENTE),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Paciente titular"
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 👇 SOLO familiares sin paciente asignado
        self.fields['familiar'].queryset = FamiliarPaciente.objects.filter(
            paciente_titular__isnull=True
        )
# ==========================================
class FamiliarPacienteForm(forms.ModelForm):

    class Meta:
        model = FamiliarPaciente
        fields = [
            'nombre',
            'apellido',
            'sexo',
            'fecha_nacimiento',
            'parentesco',
            'telefono',
            'observacion',
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'parentesco': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
        }



# ==================== FORMSETS ====================
# Formsets usando los forms personalizados
ExamenRealizadoFormSet = inlineformset_factory(
    RealizarExamen,
    ExamenRealizado,
    form=ExamenRealizadoForm,
    extra=1,
    can_delete=True,
)


DetalleInsumoExamenFormSet = inlineformset_factory(
    RealizarExamen,
    DetalleInsumoExamen,
    form=DetalleInsumoExamenForm,
    extra=1,
    can_delete=True,
)


# ====================  ====================# ====================  ====================# ====================  ====================# ====================  ====================
class AsignarTitularForm(forms.Form):

    paciente = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(
            rol=Usuario.PACIENTE
        ),
        required=False,
        label='Paciente Titular'
    )

    crear_nuevo = forms.BooleanField(
        required=False
    )

    cedula = forms.CharField(required=False)
    nombre = forms.CharField(required=False)
    apellido = forms.CharField(required=False)

    sexo = forms.ChoiceField(
        choices=Usuario.SEXOS,
        required=False
    )

    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'type':'date'}
        )
    )

    telefono = forms.CharField(required=False)
















# ====================  ====================
# ====================  ====================
class EmergenciaForm(forms.ModelForm):


    tipo_persona = forms.ChoiceField(
        choices=[
            ('EXISTENTE', 'Existente'),
            ('NUEVO_PACIENTE', 'Nuevo Paciente'),
            ('NUEVO', 'Nuevo'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}) )


    id_persona = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:

        model = Emergencia

        fields = [


            'cedula',
            'telefono',

            'nombre_paciente',
            'apellido_paciente',
            'sexo',
            'fecha_nacimiento',

            'responsable',
            'telefono_responsable',

            'motivo_consulta',
        ]

        widgets = {


            'cedula': forms.TextInput(attrs={'class': 'form-control'}),

            'telefono': forms.TextInput(attrs={'class': 'form-control'}),

            'nombre_paciente': forms.TextInput(attrs={'class': 'form-control'}),

            'apellido_paciente': forms.TextInput(attrs={'class': 'form-control'}),

            'sexo': forms.Select(attrs={'class': 'form-select'}),

            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'responsable': forms.TextInput(attrs={'class': 'form-control'}),

            'telefono_responsable': forms.TextInput(attrs={'class': 'form-control'}),

            'motivo_consulta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        opciones = []

        # PACIENTES
        pacientes = Usuario.objects.filter(rol=Usuario.PACIENTE)
        for p in pacientes:
            opciones.append((
                f"U_{p.id}",
                f"👤 {p.nombre} {p.apellido} - CI {p.cedula}"
            ))

        # FAMILIARES
        familiares = FamiliarPaciente.objects.all()
        for f in familiares:
            opciones.append((
                f"F_{f.id}",
                f"👪 {f.nombre} {f.apellido} - {f.parentesco}"
            ))

        self.fields['id_persona'].choices = opciones
        self.fields['cedula'].required = False
        self.fields['telefono'].required = False
        self.fields['nombre_paciente'].required = False
        self.fields['apellido_paciente'].required = False
        self.fields['sexo'].required = False
        self.fields['fecha_nacimiento'].required = False

    def clean(self):
        cleaned = super().clean()

        tipo_persona = cleaned.get('tipo_persona')
        id_persona = cleaned.get('id_persona')

        if tipo_persona == 'EXISTENTE':

            if not id_persona:
                self.add_error(
                    'id_persona',
                    'Debe seleccionar una persona.'
                )

        elif tipo_persona in ['NUEVO', 'NUEVO_PACIENTE']:

            campos = [
                'nombre_paciente',
                'apellido_paciente',
                'sexo',
                'fecha_nacimiento',
                'telefono',
            ]

            if tipo_persona == 'NUEVO_PACIENTE':
                campos.append('cedula')

            for campo in campos:
                if not cleaned.get(campo):
                    self.add_error(
                        campo,
                        'Este campo es obligatorio.'
                    )

        return cleaned
# ====================  ====================

class TriajeEmergenciaForm(forms.ModelForm):

    class Meta:

        model = TriajeEmergencia

        exclude = ['emergencia']

        widgets = {

            'temperatura': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'tension_arterial': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'frecuencia_cardiaca': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'frecuencia_respiratoria': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'saturacion_oxigeno': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'peso': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'prioridad': forms.Select(attrs={
                'class': 'form-select'
            }),

            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }

        help_texts = {

            'temperatura':
                'Normal: 36°C - 37.5°C',

            'tension_arterial':
                'Normal: 90/60 - 120/80 mmHg',

            'frecuencia_cardiaca':
                'Normal: 60 - 100 lpm',

            'frecuencia_respiratoria':
                'Normal: 12 - 20 rpm',

            'saturacion_oxigeno':
                'Normal: 95% - 100%',

            'peso':
                'Peso en Kg'
        }


class EvaluacionEmergenciaForm(forms.ModelForm):
    class Meta:
        model = EvaluacionEmergencia
        exclude = ['emergencia', 'doctor', 'fecha']
        widgets = {
            'enfermedad_actual': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'examen_fisico': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'impresion_diagnostica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EvolucionEmergenciaForm(forms.ModelForm):
    class Meta:
        model = EvolucionEmergencia
        exclude = ['emergencia', 'doctor', 'fecha']
        widgets = {
            'nota': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EmergenciaEstadoForm(forms.ModelForm):
    class Meta:
        model = Emergencia
        fields = ['estado', 'observacion']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DetalleInsumoEmergenciaForm(forms.ModelForm):
    class Meta:
        model = DetalleInsumoEmergencia
        exclude = ['emergencia', 'fecha']
        widgets = {
            'insumo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['insumo'].queryset = InsumoMedico.objects.filter(
            cantidad_ins__gt=0
        ).order_by('nombre_ins')


class ProcedimientoEmergenciaForm(forms.ModelForm):
    class Meta:
        model = ProcedimientoEmergencia
        exclude = ['emergencia', 'fecha']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }









# ====================  ====================
# ====================  ====================
# ====================  ====================
# ====================  ====================
# ====================  ====================
# ====================  ====================
# ====================  ====================


# ====================  ====================























# ====================  ====================



















# ====================  ====================


















# ====================  ====================



















# ====================  ====================






















# ====================  ====================





















# ====================  ====================