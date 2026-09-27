from django.apps import AppConfig


class JogadoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jogadores'

    def ready(self):
        import jogadores.models  # garante que o signal seja registrado