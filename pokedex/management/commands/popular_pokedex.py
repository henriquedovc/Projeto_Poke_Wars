from django.core.management.base import BaseCommand
from pokedex.models import EspeciePokemon
from pokedex.pokeapi_client import buscar_pokemon, buscar_especie, extrair_stat
from pokedex.gacha import calcular_raridade_especie


class Command(BaseCommand):
    help = "Popula a tabela EspeciePokemon buscando dados da PokeAPI"

    def add_arguments(self, parser):
        parser.add_argument(
            '--quantidade',
            type=int,
            default=1028,
            help='Quantos Pokemons buscar, a partir do id 1'
        )

    def handle(self, *args, **opcoes):
        quantidade = opcoes['quantidade']
        falhas = []

        for pokeapi_id in range(1, quantidade + 1):
            if EspeciePokemon.objects.filter(pokeapi_id=pokeapi_id).exists():
                self.stdout.write(f"#{pokeapi_id} já existe, pulando.")
                continue

            try:
                dados_pokemon = buscar_pokemon(pokeapi_id)
                dados_especie = buscar_especie(pokeapi_id)

                tipos = [t['type']['name'] for t in dados_pokemon['types']]
                tipo_primario = tipos[0]
                tipo_secundario = tipos[1] if len(tipos) > 1 else None

                capture_rate = dados_especie['capture_rate']
                is_legendary = dados_especie['is_legendary']
                is_mythical = dados_especie['is_mythical']

                raridade = calcular_raridade_especie(capture_rate, is_legendary, is_mythical)

                EspeciePokemon.objects.create(
                    pokeapi_id=pokeapi_id,
                    nome=dados_pokemon['name'],
                    tipo_primario=tipo_primario,
                    tipo_secundario=tipo_secundario,
                    hp_base=extrair_stat(dados_pokemon, 'hp'),
                    ataque_base=extrair_stat(dados_pokemon, 'attack'),
                    defesa_base=extrair_stat(dados_pokemon, 'defense'),
                    ataque_especial_base=extrair_stat(dados_pokemon, 'special-attack'),
                    defesa_especial_base=extrair_stat(dados_pokemon, 'special-defense'),
                    velocidade_base=extrair_stat(dados_pokemon, 'speed'),
                    sprite_url=dados_pokemon['sprites']['front_default'],
                    capture_rate=capture_rate,
                    is_legendary=is_legendary,
                    is_mythical=is_mythical,
                    raridade=raridade,
                )

                self.stdout.write(self.style.SUCCESS(f"#{pokeapi_id} {dados_pokemon['name']} ({raridade}) criado."))

            except Exception as erro:
                falhas.append(pokeapi_id)
                self.stdout.write(self.style.ERROR(f"#{pokeapi_id} falhou: {erro}"))
                continue

        if falhas:
            self.stdout.write(self.style.WARNING(f"\nIDs que falharam: {falhas}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nImportação concluída sem falhas."))