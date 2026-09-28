def calculate_hp(base, iv, level):
    """HP real do pokemon naquele nível (fórmula oficial, sem EVs)."""
    return (2 * base + iv) * level // 100 + level + 10


def calculate_stat(base, iv, level):
    """Qualquer outro status (ataque, defesa, etc.) naquele nível (sem EVs e natureza)."""
    return (2 * base + iv) * level // 100 + 5