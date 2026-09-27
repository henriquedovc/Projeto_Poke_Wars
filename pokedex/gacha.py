import random

IV_MINIMO = 0
IV_MAXIMO = 31  # mesmo valor máximo usado nos jogos oficiais

# Faixas de raridade por status (IV), da mais alta pra mais baixa.
# A primeira faixa cuja porcentagem "bater" é usada.
FAIXAS_RARIDADE_IV = [
    (1.0, 'mitico'),      # exatamente 31 — valor máximo possível
    (0.90, 'lendario'),   # 90% a 99%
    (0.80, 'epico'),      # 80% a 89%
    (0.65, 'raro'),        # 65% a 79%
    (0.50, 'incomum'),    # 50% a 64%
    (0.0, 'comum'),        # abaixo de 50%
]


def sortear_ivs():
    """Sorteia um valor de IV (0-31) para cada status, de forma independente."""
    return {
        'iv_hp': random.randint(IV_MINIMO, IV_MAXIMO),
        'iv_ataque': random.randint(IV_MINIMO, IV_MAXIMO),
        'iv_defesa': random.randint(IV_MINIMO, IV_MAXIMO),
        'iv_ataque_especial': random.randint(IV_MINIMO, IV_MAXIMO),
        'iv_defesa_especial': random.randint(IV_MINIMO, IV_MAXIMO),
        'iv_velocidade': random.randint(IV_MINIMO, IV_MAXIMO),
    }


def calcular_raridade_por_porcentagem(porcentagem):
    """Recebe um valor de 0.0 a 1.0 e devolve o rótulo de raridade correspondente."""
    for limite, raridade in FAIXAS_RARIDADE_IV:
        if porcentagem >= limite:
            return raridade
    return 'comum'


def calcular_raridade_de_iv(valor_iv, iv_maximo=IV_MAXIMO):
    """Raridade de um único status, a partir do valor de IV sorteado."""
    porcentagem = valor_iv / iv_maximo
    return calcular_raridade_por_porcentagem(porcentagem)


def calcular_raridade_geral(ivs: dict, iv_maximo=IV_MAXIMO):
    """Raridade 'geral' do pokemon, a partir da média dos IVs sorteados."""
    media = sum(ivs.values()) / len(ivs)
    porcentagem = media / iv_maximo
    return calcular_raridade_por_porcentagem(porcentagem)


def calcular_raridade_especie(capture_rate, is_legendary, is_mythical):
    """Define a raridade de uma espécie com base em dados reais da franquia."""
    if is_mythical:
        return 'mitico'
    if is_legendary:
        return 'lendario'

    # Quanto menor o capture_rate, mais difícil de capturar no jogo oficial
    dificuldade = 1 - (capture_rate / 255)

    if dificuldade >= 0.90:
        return 'epico'
    elif dificuldade >= 0.65:
        return 'raro'
    elif dificuldade >= 0.45:
        return 'incomum'
    else:
        return 'comum'