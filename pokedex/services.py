from .models import EspeciePokemon, PokemonCapturado
from .gacha import sortear_ivs


def capturar_pokemon(perfil_jogador, especie_id, apelido=None):
    """Cria um PokemonCapturado pra um jogador, com IVs sorteados no momento da captura."""
    especie = EspeciePokemon.objects.get(id=especie_id)
    ivs = sortear_ivs()

    pokemon_capturado = PokemonCapturado.objects.create(
        jogador=perfil_jogador,
        especie=especie,
        apelido=apelido,
        iv_hp=ivs['iv_hp'],
        iv_ataque=ivs['iv_ataque'],
        iv_defesa=ivs['iv_defesa'],
        iv_ataque_especial=ivs['iv_ataque_especial'],
        iv_defesa_especial=ivs['iv_defesa_especial'],
        iv_velocidade=ivs['iv_velocidade'],
    )

    return pokemon_capturado