from django.urls import path

from . import views

urlpatterns = [
    path('', views.pokedex_list, name='home'),
    path('', views.pokedex_list, name='pokedex_list'),
    path('capturar/', views.gacha_view, name='gacha'),
    path('meus-pokemons/', views.my_pokemons, name='my_pokemons'),
    path('meus-pokemons/deletar/', views.delete_filtered_captures, name='delete_filtered_captures'),
    path('meus-pokemons/<int:captura_id>/', views.pokemon_detail, name='pokemon_detail'),
]
