from django.db import models
from jogadores.models import PerfilJogador


class EspeciePokemon(models.Model):
    RARIDADE_CHOICES = [
        ('comum', 'Comum'),
        ('incomum', 'Incomum'),
        ('raro', 'Raro'),
        ('epico', 'Épico'),
        ('lendario', 'Lendário'),
        ('mitico', 'Mítico'),
    ]

    pokeapi_id = models.IntegerField(unique=True)
    nome = models.CharField(max_length=100)
    tipo_primario = models.CharField(max_length=50)
    tipo_secundario = models.CharField(max_length=50, blank=True, null=True)

    hp_base = models.IntegerField()
    ataque_base = models.IntegerField()
    defesa_base = models.IntegerField()
    ataque_especial_base = models.IntegerField()
    defesa_especial_base = models.IntegerField()
    velocidade_base = models.IntegerField()

    sprite_url = models.URLField(blank=True, null=True)

    # Dados da PokeAPI usados para calcular a raridade da espécie
    capture_rate = models.IntegerField(default=255)  # 0 (difícil) a 255 (fácil)
    is_legendary = models.BooleanField(default=False)
    is_mythical = models.BooleanField(default=False)
    raridade = models.CharField(max_length=20, choices=RARIDADE_CHOICES, default='comum')

    def __str__(self):
        return self.nome


class PokemonCapturado(models.Model):
    jogador = models.ForeignKey(PerfilJogador, on_delete=models.CASCADE, related_name='pokemons')
    especie = models.ForeignKey(EspeciePokemon, on_delete=models.CASCADE)
    apelido = models.CharField(max_length=100, blank=True, null=True)
    nivel = models.IntegerField(default=1)
    data_captura = models.DateTimeField(auto_now_add=True)

    # IVs individuais — o "gacha" de cada status (0 a 31)
    iv_hp = models.IntegerField(default=0)
    iv_ataque = models.IntegerField(default=0)
    iv_defesa = models.IntegerField(default=0)
    iv_ataque_especial = models.IntegerField(default=0)
    iv_defesa_especial = models.IntegerField(default=0)
    iv_velocidade = models.IntegerField(default=0)

    def __str__(self):
        nome_exibido = self.apelido if self.apelido else self.especie.nome
        return f"{nome_exibido} (Nv. {self.nivel}) - {self.jogador.usuario.username}"