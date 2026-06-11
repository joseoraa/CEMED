from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator, RegexValidator
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum

# class UsuarioManager(BaseUserManager):
#     use_in_migrations = True

#     def create_user(self, cedula, email, password=None, **extra_fields):
#         if not cedula:
#             raise ValueError("La cédula debe ser proporcionada")
#         email = self.normalize_email(email)
#         user = self.model(cedula=cedula, email=email, **extra_fields)
#         extra_fields['username'] = cedula
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
    
#     def create_superuser(self, cedula, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('rol', Usuario.ADMINISTRACION) 

#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('El superusuario debe tener is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('El superusuario debe tener is_superuser=True.')
        
#         return self.create_user(cedula, email, password, **extra_fields)

# ================================================================================================================================
class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, cedula, email, password=None, **extra_fields):

        if not cedula:
            raise ValueError("La cédula debe ser proporcionada")

        email = self.normalize_email(email)

        # 🔥 CLAVE: asignar antes de crear el modelo
        extra_fields['username'] = cedula

        user = self.model(
            cedula=cedula,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cedula, email, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', Usuario.ADMINISTRACION)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self.create_user(cedula, email, password, **extra_fields)

# ==========================================
class Usuario(AbstractUser):
    PACIENTE = "PACIENTE"
    ENFERMERA = "ENFERMERA"
    DOCTOR = "DOCTOR"
    ADMINISTRACION = "ADMIN"

    ROLES = [
        (PACIENTE, "Paciente"),
        (ENFERMERA, "Enfermera"),
        (DOCTOR, "Doctor"),
        (ADMINISTRACION, "Administración"),
    ]

    cedula = models.CharField(
        max_length=8,
        unique=True,
        validators=[RegexValidator(r'^\d+$', 'La cédula debe contener solo números')],
        verbose_name="Cédula"
    )

    VENEZOLANO = "V"
    EXTRANJERO = "E"
    JURIDICO = "J"
    GUBERNAMENTAL = "G"
    PASAPORTE = "P"

    TIPOS_CEDULA = [
        (VENEZOLANO, "V"),
        (EXTRANJERO, "E"),
        (JURIDICO, "J"),
        (GUBERNAMENTAL, "G"),
        (PASAPORTE, "P"),
    ]

    tipo_cedula = models.CharField(
        max_length=5,
        choices=TIPOS_CEDULA,
        default=VENEZOLANO
    )

    MASCULINO = "MASCULINO"
    FEMENINO = "FEMENINO"

    SEXOS = [
        (MASCULINO, "MASCULINO"),
        (FEMENINO, "FEMENINO"),
    ]

    sexo = models.CharField(
        max_length=12,
        choices=SEXOS,
        blank=True,
        null=True
    )

    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField(default=date(2000, 1, 1))
    telefono = models.CharField(max_length=11, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROLES, default=PACIENTE)
    email = models.EmailField(unique=True, max_length=254, blank=True, null=True)
    bloqueado = models.BooleanField(default=False)
    intentos_fallidos = models.IntegerField(default=0)

    USERNAME_FIELD = 'cedula'
    REQUIRED_FIELDS = ['tipo_cedula','nombre', 'apellido','sexo', 'fecha_nacimiento', 'email']

    objects = UsuarioManager()

    def __str__(self):
        return f"{self.tipo_cedula}-{self.cedula} - {self.nombre} {self.apellido} "

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.upper()
        if self.apellido:
            self.apellido = self.apellido.upper()
        super().save(*args, **kwargs)

# ==========================================
class FamiliarPaciente(models.Model):
    HIJO = "HIJO"
    MADRE = "MADRE"
    PADRE = "PADRE"
    ESPOSA = "ESPOSA"
    ESPOSO = "ESPOSO"
    HERMANO = "HERMANO"
    OTRO = "OTRO"
    PARENTESCOS = [
        (HIJO, "Hijo"),
        (MADRE, "Madre"),
        (PADRE, "Padre"),
        (ESPOSA, "Esposa"),
        (HERMANO, "Hermano"),
        (OTRO, "Otro"),    ]
    paciente_titular = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'PACIENTE'},
        related_name='familiares',null=True,blank=True  )
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    sexo = models.CharField(
        max_length=12,
        choices=Usuario.SEXOS    )
    fecha_nacimiento = models.DateField(default=date(2000, 1, 1))
    parentesco = models.CharField(
        max_length=20,
        choices=PARENTESCOS, blank=True,null=True    )
    telefono = models.CharField(
        max_length=11,
        blank=True,
        null=True    )
    observacion = models.TextField(        blank=True,        null=True    )
    fecha_registro = models.DateTimeField(        auto_now_add=True    )
    activo = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.parentesco}"
    
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        self.apellido = self.apellido.upper()
        super().save(*args, **kwargs) 

# ================================================================
class Especialidad(models.Model):
    nombre_espe = models.CharField(max_length=100, unique=True)

    class Meta:
            # Esto garantiza el orden alfabético en los Forms automáticamente
            ordering = ['nombre_espe']
            verbose_name = "Especialidad"
            verbose_name_plural = "Especialidades"

    def __str__(self):
        return self.nombre_espe.upper()

    def save(self, *args, **kwargs):
        self.nombre_espe = self.nombre_espe.upper()
        super().save(*args, **kwargs)

# ================================================================
class Doctorperfil(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_perfil')
    especialidad = models.ForeignKey( Especialidad,on_delete=models.SET_NULL,null=True,
            blank=True, related_name='doctores')
    precio_consulta = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Precio de Consulta",default=0.00)
    imagen = models.ImageField(upload_to='doctores/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
            # CAMBIO AQUÍ: 
            # Ordenamos por el campo 'nombre_espe' que está DENTRO de 'especialidad'
        ordering = ['especialidad__nombre_espe'] 
            
        verbose_name = "Doctor Perfil"
        verbose_name_plural = "Perfiles Doctores"

    def __str__(self):
        return f" {self.especialidad}  Dr. {self.usuario.nombre} {self.usuario.apellido} "

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


# ================================================================================================================================
class HorarioDoctor(models.Model):
    DIAS_SEMANA = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]

    doctor = models.ForeignKey(
        Doctorperfil,
        on_delete=models.CASCADE,
        related_name='horarios'
    )

    dia = models.CharField(max_length=20, choices=DIAS_SEMANA)

    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.doctor} - {self.dia} {self.hora_inicio} - {self.hora_fin}"

# ================================================================================================================================
class SliderImagen(models.Model):
    titulo = models.CharField(max_length=20, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='slider/')
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']  # más recientes primero


    def __str__(self):
        return self.titulo if self.titulo else "Imagen Slider"

# ================================================================================================================================
class Examen(models.Model):
    LABORATORIO= "LABORATORIO"
    IMAGENEOLOGIA= "IMAGENEOLOGIA"
    OTRO = "OTROS"

    codigo_exa = models.CharField(max_length=3, unique=True, verbose_name="Código del Examen")
    nom_exa = models.CharField(max_length=30, verbose_name="Nombre del Examen")

    TIPOS = [
        ('LABORATORIO', 'LABORATORIO'),
        ('IMAGENEOLOGIA', 'IMAGENEOLOGIA'),
        ('OTROS', 'OTROS'),
    ]
    tipo_exa = models.CharField(max_length=20, choices=TIPOS,  verbose_name="Tipo de Examen", default=LABORATORIO)
    caracteristica_exa = models.CharField(max_length=15, blank=True, null=True, verbose_name="Características")
    precio_exa = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Precio")
    creado_en_exa = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    actualizado_exa= models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    def save(self, *args, **kwargs):
        if self.codigo_exa:
            self.codigo_exa = self.codigo_exa.upper()
        if self.nom_exa:
            self.nom_exa = self.nom_exa.upper()
        if self.caracteristica_exa:
            self.caracteristica_exa = self.caracteristica_exa.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo_exa} - {self.nom_exa} ({self.tipo_exa})"
    

# ================================================================================================================================


# ================================================================================================================================
class InsumoMedico(models.Model):
    codigo_ins = models.CharField(max_length=20, unique=True, verbose_name="Código de Insumo")   
    nombre_ins = models.CharField(max_length=100, verbose_name="Nombre del Insumo")
    presentacion_ins = models.CharField(max_length=100, verbose_name="Presentación (ej: caja, frasco, unidad)")
    descripcion_ins = models.TextField(blank=True, null=True, verbose_name="Descripción / Observaciones")
    cantidad_ins = models.PositiveIntegerField(default=0, verbose_name="Cantidad en Stock")
    precio_unitario_ins = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    fecha_caducidad_ins = models.DateField(verbose_name="Fecha de Caducidad")
    proveedor_ins = models.CharField(max_length=100, blank=True, null=True, verbose_name="Proveedor")
    creado_en_ins = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    actualizado_en_ins = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    stock_minimo = models.PositiveIntegerField(default=10)


    class Meta:
        ordering = ['fecha_caducidad_ins', 'nombre_ins']
        verbose_name = "Insumo Médico"
        verbose_name_plural = "Insumos Médicos"

    def __str__(self):
        return f"{self.nombre_ins} ({self.presentacion_ins}) CANTIDAD: {self.cantidad_ins}"
    
    def stock_bajo(self):
        return self.cantidad_ins <= self.stock_minimo

    def save(self, *args, **kwargs):
        if self.nombre_ins:
            self.nombre_ins = self.nombre_ins.upper()
        if self.presentacion_ins:
            self.presentacion_ins = self.presentacion_ins.upper()
        if self.proveedor_ins:
            self.proveedor_ins = self.proveedor_ins.upper()
        if self.descripcion_ins:
            self.descripcion_ins = self.descripcion_ins.upper()
        super().save(*args, **kwargs)

    def esta_caducado(self):
        return self.fecha_caducidad_ins < date.today()
    
# ================================================================================================================================



# ================================================================================================================================
class HistoriaMedica(models.Model):
    paciente = models.OneToOneField(
        Usuario, null=True,
        blank=True,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'PACIENTE'},
        related_name='historia_medica'
    )
    familiar = models.OneToOneField(
        FamiliarPaciente,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='historia_medica'
    )
    antecedentes = models.TextField(blank=True)
    alergias = models.TextField(blank=True)
    enfermedades_cronicas = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    diagnostico = models.TextField (blank=True)
    motivo_consulta = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.paciente:
            return f"Historia - {self.paciente.nombre}"

        if self.familiar:
            return f"Historia - {self.familiar.nombre}"
        return "Historia Médica"

    def save(self, *args, **kwargs):
        if self.antecedentes:
            self.antecedentes = self.antecedentes.upper()

        if self.diagnostico:
            self.diagnostico = self.diagnostico.upper()

        if self.motivo_consulta:
            self.motivo_consulta = self.motivo_consulta.upper()
        if self.alergias:
            self.alergias = self.alergias.upper()
        if self.enfermedades_cronicas:
            self.enfermedades_cronicas = self.enfermedades_cronicas.upper()
        if self.observaciones:
            self.observaciones = self.observaciones.upper()
        super().save(*args, **kwargs)

# ================================================================================================================================
class ExamenMedico(models.Model):
    historia_medica = models.ForeignKey(
        HistoriaMedica, 
        on_delete=models.CASCADE, 
        related_name='examenes'
    )
    nombre_examen = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='examenes_medicos/%Y/%m/%d/')
    fecha_examen = models.DateField()
    descripcion = models.TextField(blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_examen} - {self.historia_medica.paciente}"

    def save(self, *args, **kwargs):
        if self.nombre_examen:
            self.nombre_examen = self.nombre_examen.upper()
        super().save(*args, **kwargs)

# ================================================================================================================================
class CitaMedica(models.Model):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    ATENDIDA = "ATENDIDA"
    NO_ASISTIO = "NO_ASISTIO"
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (CONFIRMADA, "Confirmada"),
        (CANCELADA, "Cancelada"),
        (ATENDIDA, "Atendida"),
        (NO_ASISTIO, "No asistió"),
    ]

    paciente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,null=True,
        blank=True,
        related_name='citas_paciente',
        limit_choices_to={'rol': 'PACIENTE'}
    )
    familiar = models.ForeignKey(
        'FamiliarPaciente',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='citas_familiar'
    )
    doctor = models.ForeignKey(
        Doctorperfil,
        on_delete=models.CASCADE,
        related_name='citas_doctor'
    )

    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.TextField(blank=True, null=True)
    estado = models.CharField( max_length=15,choices=ESTADOS,default=PENDIENTE)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citas_creadas'
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tasa_bcv_aplicada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1.00
    )


    class Meta:
        ordering = ['fecha', 'hora']
        verbose_name = "Cita Médica"
        verbose_name_plural = "Citas Médicas"
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'fecha', 'hora'],
                name='unique_cita_doctor_fecha_hora'
            )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
     
    @property
    def paciente_real(self):
        if self.paciente:
            return self.paciente
        if self.familiar:
            return self.familiar.paciente_titular   

    def actualizar_estado_auto(self):
        ahora = timezone.now()


        fecha_hora_cita = timezone.make_aware( datetime.combine(self.fecha, self.hora))
        if self.estado in [self.ATENDIDA, self.CANCELADA]:
            return

        if fecha_hora_cita < ahora:

            if self.estado == self.PENDIENTE:
                self.estado = self.NO_ASISTIO

            elif self.estado == self.CONFIRMADA:
                self.estado = self.NO_ASISTIO

            self.save(update_fields=['estado'])

    def __str__(self):
        if self.paciente:
            return f"{self.paciente.nombre} {self.paciente.apellido}"

        if self.familiar:
            return f"{self.familiar.nombre} {self.familiar.apellido}"

        return "Cita Médica"

# ================================================================================================================================
class DetalleInsumoCita(models.Model):
    cita = models.ForeignKey(CitaMedica, on_delete=models.CASCADE, related_name='detalles_insumos')
    insumo = models.ForeignKey(InsumoMedico, on_delete=models.CASCADE, blank=True, null=True)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cita} - {self.insumo.nombre_ins} x {self.cantidad}"
    
    def save(self, *args, **kwargs):

        if self.pk is None:

            if self.cantidad > self.insumo.cantidad_ins:
                raise ValidationError(
                    f'Stock insuficiente para {self.insumo.nombre_ins}'
                )

            stock_anterior = self.insumo.cantidad_ins

            # GUARDAR DETALLE
            super().save(*args, **kwargs)

            # DESCONTAR STOCK
            self.insumo.cantidad_ins -= self.cantidad
            self.insumo.save()

            # REGISTRAR MOVIMIENTO
            MovimientoStock.objects.create(
                insumo=self.insumo,
                tipo=MovimientoStock.SALIDA,
                cantidad=self.cantidad,
                stock_anterior=stock_anterior,
                stock_actual=self.insumo.cantidad_ins,
                descripcion=f'Uso en cita médica #{self.cita.id}',
                cita=self.cita,
                usuario=self.cita.doctor.usuario
            )

        else:
            super().save(*args, **kwargs)

# ================================================================================================================================

# ================================================================================================================================
class Factura(models.Model):
    cita = models.OneToOneField(CitaMedica, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    tasa_bcv_fijada = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    total_usd = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    total_bs = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)

    def __str__(self):
        return f"Factura #{self.id} - {self.cita}"
    

# ================================================================================================================================
# ================================================================================================================================
class MovimientoStock(models.Model):

    ENTRADA = 'ENTRADA'
    SALIDA = 'SALIDA'

    TIPOS = [
        (ENTRADA, 'Entrada'),
        (SALIDA, 'Salida'),
    ]

    insumo = models.ForeignKey(
        'InsumoMedico',
        on_delete=models.CASCADE,
        related_name='movimientos')
    tipo = models.CharField(
        max_length=10,
        choices=TIPOS)
    cantidad = models.PositiveIntegerField()
    stock_anterior = models.PositiveIntegerField()
    stock_actual = models.PositiveIntegerField()

    descripcion = models.CharField(
        max_length=255,
        blank=True,
        null=True)
    cita = models.ForeignKey(
        'CitaMedica',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_stock')
    realizar_examen = models.ForeignKey(
        'RealizarExamen',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_stock')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.insumo.nombre_ins} - {self.tipo} ({self.cantidad})"
    @property
    def total_movimiento(self):
        return self.cantidad * self.insumo.precio_unitario_ins
    

# ================================================================================================================================
# ================================================================================================================================
class BCV(models.Model):

    fecha = models.DateTimeField(auto_now_add=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bcv_creados'
    )

    class Meta:
        ordering = ['-fecha']
        verbose_name = "BCV"
        verbose_name_plural = "BCV"

        constraints = [
            models.UniqueConstraint(fields=['fecha'], name='bcv_unico_por_dia')
        ]
        
    def __str__(self):
        return f"{self.valor} - {self.fecha.date()}"
    
# ================================================================================================================================
# ================================================================================================================================
class RealizarExamen(models.Model):
    paciente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'PACIENTE'}
    )
    cita = models.ForeignKey(CitaMedica, on_delete=models.CASCADE, null=True, blank=True)

    familiar = models.ForeignKey(
        'FamiliarPaciente',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='examen_familiar'
    )

    examen = models.ForeignKey(
        Examen,
        on_delete=models.CASCADE,null=True,blank=True,
    )

    doctor = models.ForeignKey(
        Doctorperfil,   # ✅ igual que CitaMedica
        on_delete=models.SET_NULL,
        null=True,blank=True,
        related_name='examenes_doctor'
    )

    fecha = models.DateTimeField(auto_now_add=True)

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.paciente} - {self.examen}"

  # ================================================================================================================================


# ================================================================================================================================
class ExamenRealizado(models.Model):

    realizar_examen = models.ForeignKey(
        RealizarExamen,
        on_delete=models.CASCADE,
        related_name='examenes_realizados'
    )

    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
  
# ================================================================================================================================

class DetalleInsumoExamen(models.Model):
    realizar_examen = models.ForeignKey(
        RealizarExamen,
        on_delete=models.CASCADE,
        related_name='insumos'
    )

    insumo = models.ForeignKey(
        InsumoMedico,
        on_delete=models.CASCADE
    )

    cantidad = models.PositiveIntegerField(default=1)

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def save(self, *args, **kwargs):

        if self.pk is None:

            if self.cantidad > self.insumo.cantidad_ins:
                raise ValidationError(
                    f'Stock insuficiente para {self.insumo.nombre_ins}'
                )

            stock_anterior = self.insumo.cantidad_ins

            self.subtotal = (
                self.insumo.precio_unitario_ins * self.cantidad
            )

            super().save(*args, **kwargs)

            self.insumo.cantidad_ins -= self.cantidad
            self.insumo.save()

            MovimientoStock.objects.create(
                insumo=self.insumo,
                tipo=MovimientoStock.SALIDA,
                cantidad=self.cantidad,
                stock_anterior=stock_anterior,
                stock_actual=self.insumo.cantidad_ins,
                descripcion=f'Uso en examen #{self.realizar_examen.id}',
                realizar_examen=self.realizar_examen,
                usuario=self.realizar_examen.doctor.usuario if self.realizar_examen.doctor else None
            )

        else:
            super().save(*args, **kwargs)

# ================================================================================================================================
class Emergencia(models.Model):

    ACTIVA = 'ACTIVA'
    ALTA = 'ALTA'
    HOSPITALIZADO = 'HOSPITALIZADO'
    REFERIDO = 'REFERIDO'
    FALLECIDO = 'FALLECIDO'

    ESTADOS = [
        (ACTIVA, 'Activa'),
        (ALTA, 'Alta'),
        (HOSPITALIZADO, 'Hospitalizado'),
        (REFERIDO, 'Referido'),
        (FALLECIDO, 'Fallecido'),
    ]

    PACIENTE = 'PACIENTE'
    FAMILIAR = 'FAMILIAR'
    PACIENTE_NUEVO = 'PACIENTE_NUEVO'
    FAMILIAR_NUEVO = 'FAMILIAR_NUEVO'

    numero = models.CharField(
        max_length=20,
        unique=True
    )


    paciente = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'rol': 'PACIENTE'},
        related_name='emergencias'
    )

    familiar = models.ForeignKey(
        FamiliarPaciente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergencias'
    )
    cedula = models.CharField(
        max_length=8,
        blank=True,
        null=True
    )

    telefono = models.CharField(
        max_length=12,
        blank=True,
        null=True
    )

    nombre_paciente = models.CharField(
        max_length=100,
        blank=True
    )

    apellido_paciente = models.CharField(
        max_length=100,
        blank=True
    )

    sexo = models.CharField(
        max_length=12,
        choices=Usuario.SEXOS,
        blank=True,
        null=True
    )

    fecha_nacimiento = models.DateField(
    )

    responsable = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    telefono_responsable = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    motivo_consulta = models.TextField()

    fecha_ingreso = models.DateTimeField(
        auto_now_add=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ACTIVA
    )

    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergencias_creadas'
    )

    observacion = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-fecha_ingreso']

    def __str__(self):

        if self.paciente:
            return f"{self.numero} - {self.paciente}"

        if self.familiar:
            return f"{self.numero} - {self.familiar}"

        return f"{self.numero} - {self.nombre_paciente} {self.apellido_paciente}"


    @property
    def edad(self):
        

        if self.paciente and self.paciente.fecha_nacimiento:
            return relativedelta(date.today(), self.paciente.fecha_nacimiento).years

        if self.familiar and self.familiar.fecha_nacimiento:
            return relativedelta(date.today(), self.familiar.fecha_nacimiento).years

        if self.fecha_nacimiento:
            return relativedelta(date.today(), self.fecha_nacimiento).years

        return None

    @property
    def nombre_completo(self):
        if self.paciente:
            return f"{self.paciente.nombre} {self.paciente.apellido}"
        if self.familiar:
            return f"{self.familiar.nombre} {self.familiar.apellido}"
        return f"{self.nombre_paciente} {self.apellido_paciente}".strip()
# ================================================================================================================================
class TriajeEmergencia(models.Model):

    ROJO = 'ROJO'
    NARANJA = 'NARANJA'
    AMARILLO = 'AMARILLO'
    VERDE = 'VERDE'
    AZUL = 'AZUL'

    PRIORIDADES = [
        (ROJO, 'Rojo'),
        (NARANJA, 'Naranja'),
        (AMARILLO, 'Amarillo'),
        (VERDE, 'Verde'),
        (AZUL, 'Azul'),
    ]

    emergencia = models.ForeignKey(Emergencia, on_delete=models.CASCADE, related_name='triajes')

    temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    tension_arterial = models.CharField(max_length=20, blank=True)
    frecuencia_cardiaca = models.PositiveIntegerField(null=True, blank=True)
    frecuencia_respiratoria = models.PositiveIntegerField(null=True, blank=True)
    saturacion_oxigeno = models.PositiveIntegerField(null=True, blank=True)
    peso = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    prioridad = models.CharField(max_length=10, choices=PRIORIDADES)

    observacion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def clean(self):

        if self.temperatura and (self.temperatura < 25 or self.temperatura > 45):
            raise ValidationError("Temperatura fuera de rango")

        if self.saturacion_oxigeno and (self.saturacion_oxigeno > 100):
            raise ValidationError("Saturación inválida")

        if self.frecuencia_cardiaca and self.frecuencia_cardiaca > 250:
            raise ValidationError("Frecuencia cardíaca inválida")

        if self.frecuencia_respiratoria and self.frecuencia_respiratoria > 60:
            raise ValidationError("Frecuencia respiratoria inválida")

# ================================================================================================================================
class EvaluacionEmergencia(models.Model):

    emergencia = models.ForeignKey(
        Emergencia,
        on_delete=models.CASCADE,
        related_name='evaluaciones'
    )

    doctor = models.ForeignKey(
        Doctorperfil,
        on_delete=models.SET_NULL,
        null=True
    )

    enfermedad_actual = models.TextField()

    examen_fisico = models.TextField()

    impresion_diagnostica = models.TextField()

    fecha = models.DateTimeField(
        auto_now_add=True
    )

# ================================================================================================================================
class EvolucionEmergencia(models.Model):

    emergencia = models.ForeignKey(
        Emergencia,
        on_delete=models.CASCADE,
        related_name='evoluciones'
    )

    doctor = models.ForeignKey(
        Doctorperfil,
        on_delete=models.SET_NULL,
        null=True
    )

    nota = models.TextField()

    fecha = models.DateTimeField(
        auto_now_add=True
    )


# ================================================================================================================================
class SolicitudExamenEmergencia(models.Model):

    emergencia = models.ForeignKey(
        Emergencia,
        on_delete=models.CASCADE,
        related_name='solicitudes_examen'
    )

    realizar_examen = models.ForeignKey(
        RealizarExamen,
        on_delete=models.CASCADE
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

# ================================================================================================================================
class DetalleInsumoEmergencia(models.Model):

    emergencia = models.ForeignKey(
        Emergencia,
        on_delete=models.CASCADE,
        related_name='insumos'
    )

    insumo = models.ForeignKey(
        InsumoMedico,
        on_delete=models.CASCADE
    )

    cantidad = models.PositiveIntegerField()

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.emergencia.numero} - {self.insumo.nombre_ins} x {self.cantidad}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            if self.cantidad > self.insumo.cantidad_ins:
                raise ValidationError(
                    f'Stock insuficiente para {self.insumo.nombre_ins}'
                )

            stock_anterior = self.insumo.cantidad_ins
            super().save(*args, **kwargs)

            self.insumo.cantidad_ins -= self.cantidad
            self.insumo.save()

            MovimientoStock.objects.create(
                insumo=self.insumo,
                tipo=MovimientoStock.SALIDA,
                cantidad=self.cantidad,
                stock_anterior=stock_anterior,
                stock_actual=self.insumo.cantidad_ins,
                descripcion=f'Uso en emergencia #{self.emergencia.id}',
            )
        else:
            super().save(*args, **kwargs)


# ================================================================================================================================
class ProcedimientoEmergencia(models.Model):

    emergencia = models.ForeignKey(
        Emergencia,
        on_delete=models.CASCADE
    )

    nombre = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )


# ================================================================================================================================
class AuditoriaEmergencia(models.Model):

    emergencia = models.ForeignKey(
        Emergencia,
        on_delete=models.CASCADE
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True
    )

    accion = models.CharField(
        max_length=200
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )


# ================================================================================================================================






