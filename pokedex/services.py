from .models import EspeciePokemon, PokemonCapturado, EspecieMovimento
from .gacha import sortear_ivs

MAXIMO_GOLPES = 4


def obter_golpes_por_nivel(especie, nivel):
    """
    Devolve até 4 golpes (objetos Move) que uma espécie teria naquele nível,
    seguindo a regra dos jogos oficiais: os mais recentes do learnset.
    """
    aprendidos = list(
        EspecieMovimento.objects
        .filter(especie=especie, nivel_aprendizado__lte=nivel)
        .select_related('movimento')
        .order_by('-nivel_aprendizado')[:MAXIMO_GOLPES]
    )

    # Fallback: se a espécie não aprende nada até esse nível
    if not aprendidos:
        aprendidos = list(
            EspecieMovimento.objects
            .filter(especie=especie)
            .select_related('movimento')
            .order_by('nivel_aprendizado')[:MAXIMO_GOLPES]
        )

    return [registro.movimento for registro in aprendidos]


def equipar_golpes_iniciais(pokemon_capturado):
    """Equipa no pokemon capturado os golpes que ele teria no nível atual."""
    golpes = obter_golpes_por_nivel(pokemon_capturado.especie, pokemon_capturado.nivel)
    pokemon_capturado.movimentos_atuais.set(golpes)


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