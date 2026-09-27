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