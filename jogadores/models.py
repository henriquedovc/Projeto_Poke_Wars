from django.db import models

# Create your models here.

from django.contrib.auth.models import User

class PerfilJogador(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.usuario.username