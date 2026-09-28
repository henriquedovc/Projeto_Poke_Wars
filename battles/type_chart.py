# Tabela de efetividade de tipos (Geração 6 em diante, 18 tipos).
# Estrutura: TYPE_CHART[tipo_do_golpe][tipo_do_defensor] = multiplicador
# Só ficam listados os casos diferentes de 1x; o resto é neutro.

TYPE_CHART = {
    'normal':   {'rock': 0.5, 'steel': 0.5, 'ghost': 0},
    'fire':     {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2,
                 'rock': 0.5, 'dragon': 0.5, 'steel': 2},
    'water':    {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2,
                 'rock': 2, 'dragon': 0.5},
    'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0,
                 'flying': 2, 'dragon': 0.5},
    'grass':    {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5,
                 'ground': 2, 'flying': 0.5, 'bug': 0.5, 'rock': 2,
                 'dragon': 0.5, 'steel': 0.5},
    'ice':      {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5,
                 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
    'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5,
                 'psychic': 0.5, 'bug': 0.5, 'rock': 2, 'ghost': 0,
                 'dark': 2, 'steel': 2, 'fairy': 0.5},
    'poison':   {'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5,
                 'ghost': 0.5, 'steel': 0, 'fairy': 2},
    'ground':   {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2,
                 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2},
    'flying':   {'electric': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2,
                 'rock': 0.5, 'steel': 0.5},
    'psychic':  {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'dark': 0,
                 'steel': 0.5},
    'bug':      {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5,
                 'flying': 0.5, 'psychic': 2, 'ghost': 0.5, 'dark': 2,
                 'steel': 0.5, 'fairy': 0.5},
    'rock':     {'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5,
                 'flying': 2, 'bug': 2, 'steel': 0.5},
    'ghost':    {'normal': 0, 'psychic': 2, 'ghost': 2, 'dark': 0.5},
    'dragon':   {'dragon': 2, 'steel': 0.5, 'fairy': 0},
    'dark':     {'fighting': 0.5, 'psychic': 2, 'ghost': 2, 'dark': 0.5,
                 'fairy': 0.5},
    'steel':    {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2,
                 'rock': 2, 'steel': 0.5, 'fairy': 2},
    'fairy':    {'fire': 0.5, 'fighting': 2, 'poison': 0.5, 'dragon': 2,
                 'dark': 2, 'steel': 0.5},
}

STAB_MULTIPLIER = 1.5


def get_type_multiplier(move_type, defender_types):
    """
    Multiplicador de efetividade de um golpe contra um defensor.
    defender_types é uma lista com 1 ou 2 tipos (o segundo pode ser None).
    Contra dois tipos, os multiplicadores se multiplicam entre si
    (ex: 2 x 2 = 4x, 2 x 0.5 = 1x, qualquer coisa x 0 = 0).
    """
    multiplier = 1.0
    for defender_type in defender_types:
        if defender_type is None:
            continue
        multiplier *= TYPE_CHART.get(move_type, {}).get(defender_type, 1.0)
    return multiplier


def get_stab(move_type, attacker_types):
    """1.5x se o tipo do golpe for igual a um dos tipos do atacante, senão 1x."""
    if move_type in attacker_types:
        return STAB_MULTIPLIER
    return 1.0