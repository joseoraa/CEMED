from django.core.management.base import BaseCommand
from consulta.models import Especialidad   # ← Cambia "miapp" por el nombre real de tu app

class Command(BaseCommand):
    help = 'Carga automáticamente las especialidades médicas iniciales'

    def handle(self, *args, **options):
        # Lista de especialidades (puedes agregar o quitar las que necesites)
        especialidades_lista = [
            "Cardiología",
            "Pediatría",
            "Ginecología",
            "Obstetricia",
            "Neurología",
            "Traumatología",
            "Ortopedia",
            "Dermatología",
            "Oftalmología",
            "Otorrinolaringología",
            "Psiquiatría",
            "Oncología",
            "Endocrinología",
            "Gastroenterología",
            "Nefrología",
            "Hematología",
            "Infectología",
            "Medicina Interna",
            "Medicina General",
            "Cirugía General",
            "Anestesiología",
            "Radiología",
            "Patología",
        ]

        creadas = 0
        ya_existentes = 0

        for nombre in especialidades_lista:
            # Usamos upper() porque tu modelo lo guarda en mayúsculas
            obj, created = Especialidad.objects.get_or_create(
                nombre_espe=nombre.upper()
            )
            if created:
                creadas += 1
            else:
                ya_existentes += 1

        # Mensajes bonitos al final
        self.stdout.write(
            self.style.SUCCESS(f'✓ Se crearon {creadas} especialidades nuevas.')
        )
        if ya_existentes > 0:
            self.stdout.write(
                self.style.WARNING(f'→ {ya_existentes} especialidades ya existían.')
            )
        self.stdout.write(self.style.SUCCESS('¡Carga de especialidades completada!'))