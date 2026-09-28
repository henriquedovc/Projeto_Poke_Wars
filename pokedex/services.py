from .models import EspeciePokemon, PokemonCapturado, EspecieMovimento
from .gacha import sortear_ivs

MAXIMO_GOLPES = 4


def equipar_golpes_iniciais(pokemon_capturado):
    """
    Equipa até 4 golpes no pokemon, seguindo a regra dos jogos oficiais:
    os golpes mais recentes que a espécie já aprenderia até o nível atual.
    """
    aprendidos = (
        EspecieMovimento.objects
        .filter(
            especie=pokemon_capturado.especie,
            nivel_aprendizado__lte=pokemon_capturado.nivel,
        )
        .select_related('movimento')
        .order_by('-nivel_aprendizado')[:MAXIMO_GOLPES]
    )

    # Fallback: se a espécie não aprende nada até esse nível (acontece com
    # alguns pokemons), pega os golpes de menor nível disponíveis
    if not aprendidos:
        aprendidos = (
            EspecieMovimento.objects
            .filter(especie=pokemon_capturado.especie)
            .select_related('movimento')
            .order_by('nivel_aprendizado')[:MAXIMO_GOLPES]
        )

    pokemon_capturado.movimentos_atuais.set(
        [registro.movimento for registro in aprendidos]
    )


def capturar_pokemon(perfil_jogador, especie_id, apelido=None):
    """Cria um PokemonCapturado pra um jogador, com IVs sorteados e golpes equipados."""
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

    equipar_golpes_iniciais(pokemon_capturado)

    return pokemon_capturado