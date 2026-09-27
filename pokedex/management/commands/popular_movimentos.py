from django.core.management.base import BaseCommand
from pokedex.models import EspeciePokemon, Move, EspecieMovimento
from pokedex.pokeapi_client import buscar_pokemon, buscar_movimento, extrair_learnset_level_up


class Command(BaseCommand):
    help = "Popula golpes (Move) e o learnset (EspecieMovimento) a partir da PokeAPI"

    def handle(self, *args, **opcoes):
        especies = EspeciePokemon.objects.all()
        total = especies.count()
        falhas = []

        for indice, especie in enumerate(especies, start=1):
            try:
                dados_pokemon = buscar_pokemon(especie.pokeapi_id)
                learnset = extrair_learnset_level_up(dados_pokemon)

                for nome_golpe, nivel in learnset:
                    movimento = Move.objects.filter(nome=nome_golpe).first()

                    if not movimento:
                        dados_golpe = buscar_movimento(nome_golpe)
                        movimento = Move.objects.create(
                            pokeapi_id=dados_golpe['id'],
                            nome=dados_golpe['name'],
                            tipo=dados_golpe['type']['name'],
                            categoria=dados_golpe['damage_class']['name'] if dados_golpe['damage_class'] else 'status',
                            poder=dados_golpe['power'],
                            precisao=dados_golpe['accuracy'],
                            pp=dados_golpe['pp'] or 10,
                            prioridade=dados_golpe['priority'],
                        )

                    EspecieMovimento.objects.get_or_create(
                        especie=especie,
                        movimento=movimento,
                        defaults={'nivel_aprendizado': nivel},
                    )

                self.stdout.write(self.style.SUCCESS(
                    f"[{indice}/{total}] {especie.nome}: {len(learnset)} golpes processados."
                ))

            except Exception as erro:
                falhas.append(especie.pokeapi_id)
                self.stdout.write(self.style.ERROR(f"[{indice}/{total}] {especie.nome} falhou: {erro}"))
                continue

        if falhas:
            self.stdout.write(self.style.WARNING(f"\nEspécies (pokeapi_id) que falharam: {falhas}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nImportação de golpes concluída sem falhas."))