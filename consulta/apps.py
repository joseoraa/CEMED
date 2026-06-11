from django.apps import AppConfig
from django.db.models.signals import post_migrate

class ConsultaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'consulta'

    def ready(self):
        # Importar la función que crea grupos y conectarla al post_migrate
        from .signals import crear_grupos
        post_migrate.connect(crear_grupos, sender=self)
        import consulta.signals
