import requests

BASE_URL = "https://pokeapi.co/api/v2/"


def buscar_pokemon(identificador):
    """Busca dados de forma/stats/tipos de um Pokemon (endpoint /pokemon/)."""
    resposta = requests.get(f"{BASE_URL}pokemon/{identificador}")
    resposta.raise_for_status()
    return resposta.json()


def buscar_especie(identificador):
    """Busca dados da espécie: capture_rate, is_legendary, is_mythical (endpoint /pokemon-species/)."""
    resposta = requests.get(f"{BASE_URL}pokemon-species/{identificador}")
    resposta.raise_for_status()
    return resposta.json()


def extrair_stat(dados_pokemon, nome_stat):
    """Procura um stat específico (ex: 'hp', 'attack') dentro da lista de stats."""
    for entrada in dados_pokemon['stats']:
        if entrada['stat']['name'] == nome_stat:
            return entrada['base_stat']
    return 0

def buscar_movimento(identificador):
    """Busca dados de um golpe específico (endpoint /move/)."""
    resposta = requests.get(f"{BASE_URL}move/{identificador}")
    resposta.raise_for_status()
    return resposta.json()


def extrair_learnset_level_up(dados_pokemon):
    """
    Retorna uma lista de (nome_do_golpe, nivel) só dos golpes aprendidos
    por level-up, pegando o menor nível encontrado entre as versões do jogo.
    """
    learnset = {}

    for entrada in dados_pokemon['moves']:
        nome_golpe = entrada['move']['name']

        for detalhe in entrada['version_group_details']:
            if detalhe['move_learn_method']['name'] == 'level-up':
                nivel = detalhe['level_learned_at']
                if nivel > 0:
                    if nome_golpe not in learnset or nivel < learnset[nome_golpe]:
                        learnset[nome_golpe] = nivel

    return list(learnset.items())