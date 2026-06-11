from datetime import date, timedelta
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from consulta.models import InsumoMedico, Examen  # Ajusta 'consulta' si tu app se llama diferente

Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Carga automáticamente usuarios (pacientes, doctores), insumos médicos y exámenes de prueba con datos variados'

    def generar_datos_aleatorios(self):
        """Genera una fecha de nacimiento entre 20 y 70 años atrás y un teléfono único"""
        hoy = date.today()
        # 20 años son aprox 7300 días, 70 años son aprox 25550 días
        dias_atras = random.randint(7300, 25550)
        fecha_nac = hoy - timedelta(days=dias_atras)
        
        # Generar un número de teléfono móvil de 11 dígitos con prefijos comunes
        prefijo = random.choice(["0414", "0424", "0412", "0416", "0426"])
        cuerpo = "".join(str(random.randint(0, 9)) for _ in range(7))
        telefono = f"{prefijo}{cuerpo}"
        
        return fecha_nac, telefono

    def handle(self, *args, **options):
        self.stdout.write('Iniciando la carga de datos de prueba variados...')
        
        # 1. CARGA DE EXÁMENES (Laboratorio e Imagenología)
        examenes_lista = [
            {"codigo": "HEM", "nombre": "Hematología Completa", "tipo": "LABORATORIO", "precio": 15.00},
            {"codigo": "GLU", "nombre": "Glicemia Pre y Post", "tipo": "LABORATORIO", "precio": 8.50},
            {"codigo": "URE", "nombre": "Urea y Creatinina", "tipo": "LABORATORIO", "precio": 12.00},
            {"codigo": "PER", "nombre": "Perfil Lipídico", "tipo": "LABORATORIO", "precio": 20.00},
            {"codigo": "HIV", "nombre": "Prueba de VIH (Elisa)", "tipo": "LABORATORIO", "precio": 25.00},
            {"codigo": "RXT", "nombre": "Radiografía de Tórax", "tipo": "IMAGENEOLOGIA", "precio": 35.00},
            {"codigo": "ECO", "nombre": "Eco Abdominal Total", "tipo": "IMAGENEOLOGIA", "precio": 45.00},
            {"codigo": "TAC", "nombre": "Tomografía Craneal", "tipo": "IMAGENEOLOGIA", "precio": 120.00},
            {"codigo": "RMN", "nombre": "Resonancia Magnética", "tipo": "IMAGENEOLOGIA", "precio": 250.00},
            {"codigo": "ECG", "nombre": "Electrocardiograma", "tipo": "OTROS", "precio": 15.00},
        ]

        exa_creados = 0
        for exa in examenes_lista:
            if not Examen.objects.filter(codigo_exa=exa["codigo"].upper()).exists():
                Examen.objects.create(
                    codigo_exa=exa["codigo"],
                    nom_exa=exa["nombre"],
                    tipo_exa=exa["tipo"],
                    precio_exa=exa["precio"],
                    caracteristica_exa="PRUEBA"
                )
                exa_creados += 1
        self.stdout.write(self.style.SUCCESS(f'✓ {exa_creados} exámenes nuevos creados.'))

        # 2. CARGA DE INSUMOS MÉDICOS (20 unidades variadas)
        insumos_lista = [
            {"cod": "001", "nom": "Jeringas 5ml", "pres": "Caja x 100", "cant": 50, "precio": 12.50, "prov": "Medisur"},
            {"cod": "002", "nom": "Guantes de Látex M", "pres": "Caja x 100", "cant": 80, "precio": 15.00, "prov": "Medisur"},
            {"cod": "003", "nom": "Tapabocas Quirúrgicos", "pres": "Caja x 50", "cant": 120, "precio": 8.00, "prov": "FarmaTodo"},
            {"cod": "004", "nom": "Alcohol Antiséptico 70%", "pres": "Frasco 1L", "cant": 5, "precio": 4.50, "prov": "Química Global"},
            {"cod": "005", "nom": "Algodón en Esferas", "pres": "Bolsa 500g", "cant": 15, "precio": 3.20, "prov": "FarmaTodo"},
            {"cod": "006", "nom": "Gasa Estéril 10x10", "pres": "Paquete x 20", "cant": 60, "precio": 6.00, "prov": "Medisur"},
            {"cod": "007", "nom": "Yodopovidona Solución", "pres": "Frasco 500ml", "cant": 18, "precio": 9.50, "prov": "Química Global"},
            {"cod": "008", "nom": "Catéter Intravenoso 18G", "pres": "Unidad", "cant": 200, "precio": 1.20, "prov": "Gedeca"},
            {"cod": "009", "nom": "Catéter Intravenoso 22G", "pres": "Unidad", "cant": 150, "precio": 1.20, "prov": "Gedeca"},
            {"cod": "010", "nom": "Adhesivo Médico (Tirro)", "pres": "Unidad", "cant": 30, "precio": 2.50, "prov": "FarmaTodo"},
            {"cod": "011", "nom": "Paracetamol 500mg", "pres": "Caja x 100 tab", "cant": 40, "precio": 10.00, "prov": "Calox"},
            {"cod": "012", "nom": "Ibuprofeno 400mg", "pres": "Caja x 20 tab", "cant": 35, "precio": 5.50, "prov": "Calox"},
            {"cod": "013", "nom": "Solución Fisiológica 0.9%", "pres": "Bolsa 500ml", "cant": 12, "precio": 3.00, "prov": "Gedeca"},
            {"cod": "014", "nom": "Agua Destilada", "pres": "Ampolla 10ml", "cant": 100, "precio": 0.50, "prov": "Química Global"},
            {"cod": "015", "nom": "Sutura Nylon 3-0", "pres": "Caja x 12", "cant": 15, "precio": 18.00, "prov": "Medisur"},
            {"cod": "016", "nom": "Sutura Crómico 2-0", "pres": "Caja x 12", "cant": 82, "precio": 22.00, "prov": "Medisur"},
            {"cod": "017", "nom": "Scalp Nro 23", "pres": "Unidad", "cant": 90, "precio": 0.90, "prov": "Gedeca"},
            {"cod": "018", "nom": "Bajalenguas de Madera", "pres": "Paquete x 100", "cant": 25, "precio": 4.00, "prov": "FarmaTodo"},
            {"cod": "019", "nom": "Gel para Ultrasonido", "pres": "Galón", "cant": 44, "precio": 15.50, "prov": "Química Global"},
            {"cod": "020", "nom": "Tubos de Ensayo", "pres": "Gradilla x 50", "cant": 12, "precio": 14.00, "prov": "Medisur"},
        ]

        ins_creados = 0
        for ins in insumos_lista:
            if not InsumoMedico.objects.filter(codigo_ins=ins["cod"]).exists():
                InsumoMedico.objects.create(
                    codigo_ins=ins["cod"],
                    nombre_ins=ins["nom"],
                    presentacion_ins=ins["pres"],
                    cantidad_ins=ins["cant"],
                    precio_unitario_ins=ins["precio"],
                    fecha_caducidad_ins=date(2027, 6, 15),
                    proveedor_ins=ins["prov"],
                    descripcion_ins="LOTE DE CARGA AUTOMÁTICA"
                )
                ins_creados += 1
        self.stdout.write(self.style.SUCCESS(f'✓ {ins_creados} insumos médicos nuevos creados.'))

        # 3. CARGA DE USUARIOS: 15 PACIENTES (Fechas y Teléfonos Dinámicos)
        pacientes_lista = [
            ("21000001", "JUAN", "PEREZ", "MASCULINO", "juan.perez@email.com"),
            ("21000002", "MARIA", "RODRIGUEZ", "FEMENINO", "maria.rod@email.com"),
            ("21000003", "CARLOS", "GONZALEZ", "MASCULINO", "carlos.gonz@email.com"),
            ("21000004", "ANA", "MARTINEZ", "FEMENINO", "ana.mart@email.com"),
            ("21000005", "LUIS", "GOMEZ", "MASCULINO", "luis.gomez@email.com"),
            ("21000006", "CARMEN", "HERNANDEZ", "FEMENINO", "carmen.hern@email.com"),
            ("21000007", "PEDRO", "DIAZ", "MASCULINO", "pedro.diaz@email.com"),
            ("21000008", "LUISA", "FERNANDEZ", "FEMENINO", "luisa.fer@email.com"),
            ("21000009", "JORGE", "LOPEZ", "MASCULINO", "jorge.lopez@email.com"),
            ("21000010", "ELENA", "ALVAREZ", "FEMENINO", "elena.alv@email.com"),
            ("21000011", "MIGUEL", "GARCIA", "MASCULINO", "miguel.gar@email.com"),
            ("21000012", "ROSA", "TORRES", "FEMENINO", "rosa.torres@email.com"),
            ("21000013", "DAVID", "RAMIREZ", "MASCULINO", "david.ram@email.com"),
            ("21000014", "SONIA", "FLORES", "FEMENINO", "sonia.flo@email.com"),
            ("21000015", "JOSE", "BENITEZ", "MASCULINO", "jose.ben@email.com"),
        ]

        pac_creados = 0
        for cedula, nom, ape, sexo, email in pacientes_lista:
            if not Usuario.objects.filter(cedula=cedula).exists():
                fecha_nac, tlf = self.generar_datos_aleatorios()
                user = Usuario.objects.create_user(
                    username=cedula,
                    cedula=cedula,
                    tipo_cedula=Usuario.VENEZOLANO,
                    nombre=nom,
                    apellido=ape,
                    sexo=sexo,
                    email=email,
                    rol=Usuario.PACIENTE,
                    fecha_nacimiento=fecha_nac,
                    telefono=tlf
                )
                user.set_password("123456")
                user.save()
                pac_creados += 1
        self.stdout.write(self.style.SUCCESS(f'✓ {pac_creados} pacientes nuevos creados.'))

        # 4. CARGA DE USUARIOS: 10 DOCTORES (Fechas y Teléfonos Dinámicos)
        doctores_lista = [
            ("11000001", "MANUEL", "SILVA", "MASCULINO", "manuel.silva@med.com"),
            ("11000002", "PATRICIA", "MENDOZA", "FEMENINO", "patricia.men@med.com"),
            ("11000003", "RICARDO", "CASTILLO", "MASCULINO", "ricardo.cas@med.com"),
            ("11000004", "DIANA", "SANTOS", "FEMENINO", "diana.santos@med.com"),
            ("11000005", "FRANCISCO", "ROJAS", "MASCULINO", "fran.rojas@med.com"),
            ("11000006", "GABRIELA", "COLMENARES", "FEMENINO", "gaby.col@med.com"),
            ("11000007", "ALEJANDRO", "RONDON", "MASCULINO", "ale.rondon@med.com"),
            ("11000008", "VANESSA", "MEDINA", "FEMENINO", "vanessa.med@med.com"),
            ("11000009", "HECTOR", "SUAREZ", "MASCULINO", "hector.sua@med.com"),
            ("11000010", "REBECA", "PEÑA", "FEMENINO", "rebeca.pena@med.com"),
        ]

        doc_creados = 0
        for cedula, nom, ape, sexo, email in doctores_lista:
            if not Usuario.objects.filter(cedula=cedula).exists():
                fecha_nac, tlf = self.generar_datos_aleatorios()
                user = Usuario.objects.create_user(
                    username=cedula,
                    cedula=cedula,
                    tipo_cedula=Usuario.VENEZOLANO,
                    nombre=nom,
                    apellido=ape,
                    sexo=sexo,
                    email=email,
                    rol=Usuario.DOCTOR,
                    is_staff=True,
                    fecha_nacimiento=fecha_nac,
                    telefono=tlf
                )
                user.set_password("123456")
                user.save()
                doc_creados += 1
        self.stdout.write(self.style.SUCCESS(f'✓ {doc_creados} doctores nuevos creados.'))
        
        self.stdout.write(self.style.SUCCESS('¡Proceso de inicialización masiva finalizado exitosamente!'))