from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class PerfilJogador(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.usuario.username

    @receiver(post_save, sender=User)
    def criar_perfil_jogador(sender, instance, created, **kwargs):
        """Sempre que um novo User é criado, cria automaticamente um PerfilJogador vinculado."""
        if created:
            PerfilJogador.objects.get_or_create(usuario=instance)