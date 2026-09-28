import math
import random
from .type_chart import get_type_multiplier, get_stab

CRIT_CHANCE = 1 / 24
CRIT_MULTIPLIER = 1.5
RANDOM_MIN = 0.85
RANDOM_MAX = 1.0


def check_hit(move, rng=random):
    """Sorteia se o golpe acerta. Precisão None significa que nunca erra."""
    if move.accuracy is None:
        return True
    return rng.randint(1, 100) <= move.accuracy


def use_move(attacker, defender, move, rng=random):
    """
    Executa um golpe: aplica o dano no defensor e devolve um resumo do que aconteceu.
    O parâmetro rng permite trocar o sorteio por um controlado (útil em testes).
    """
    resultado = {
        'move': move.name,
        'hit': False,
        'damage': 0,
        'effectiveness': 1.0,
        'critical': False,
    }

    if not check_hit(move, rng):
        return resultado
    resultado['hit'] = True

    # Golpes de status ainda não têm efeito implementado
    if move.power is None or move.category == 'status':
        return resultado

    effectiveness = get_type_multiplier(move.type, defender.types)
    resultado['effectiveness'] = effectiveness
    if effectiveness == 0:
        return resultado

    if move.category == 'fisico':
        attack, defense = attacker.attack, defender.defense
    else:
        attack, defense = attacker.sp_attack, defender.sp_defense

    # Fórmula oficial de dano base
    base = ((2 * attacker.level // 5 + 2) * move.power * attack // defense) // 50 + 2

    critical = rng.random() < CRIT_CHANCE
    modifier = (
        get_stab(move.type, attacker.types)
        * effectiveness
        * rng.uniform(RANDOM_MIN, RANDOM_MAX)
        * (CRIT_MULTIPLIER if critical else 1.0)
    )

    damage = max(1, math.floor(base * modifier))
    defender.current_hp = max(0, defender.current_hp - damage)

    resultado['damage'] = damage
    resultado['critical'] = critical
    return resultado