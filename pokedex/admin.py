from django.contrib import admin
from .models import EspeciePokemon, PokemonCapturado, Move, EspecieMovimento

admin.site.register(EspeciePokemon)
admin.site.register(PokemonCapturado)
admin.site.register(Move)
admin.site.register(EspecieMovimento)