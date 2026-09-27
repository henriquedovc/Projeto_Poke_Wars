from math import ceil
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import ExpressionWrapper, F, IntegerField, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from jogadores.models import PerfilJogador
from .gacha import FAIXAS_RARIDADE_IV, calcular_raridade_de_iv, calcular_raridade_geral
from .models import EspeciePokemon, PokemonCapturado
from .services import capturar_pokemon


CAPTURE_COOLDOWN_SECONDS = 8


def _iv_total_expression():
	return ExpressionWrapper(
		F('iv_hp') + F('iv_ataque') + F('iv_defesa')
		+ F('iv_ataque_especial') + F('iv_defesa_especial') + F('iv_velocidade'),
		output_field=IntegerField(),
	)


def _capture_cleanup_preview(user, params):
	rarity_values = dict(EspeciePokemon.RARIDADE_CHOICES)
	selected_rarities = [value for value in params.getlist('raridade_especie') if value in rarity_values]
	iv_below = params.get('iv_geral_abaixo', '')
	iv_limits = {raridade: limite for limite, raridade in FAIXAS_RARIDADE_IV}
	if iv_below not in iv_limits:
		iv_below = ''
	mode = params.get('modo_filtro', 'qualquer')
	if mode not in ('qualquer', 'todos'):
		mode = 'qualquer'

	base = PokemonCapturado.objects.filter(jogador__usuario=user).select_related('especie')
	conditions = []
	if selected_rarities:
		conditions.append(Q(especie__raridade__in=selected_rarities))
	if iv_below:
		minimum_total = ceil(iv_limits[iv_below] * 6 * 31)
		conditions.append(Q(iv_total__lt=minimum_total))

	if not conditions:
		matches = base.none()
	else:
		matches = base.annotate(iv_total=_iv_total_expression())
		condition = conditions[0]
		for next_condition in conditions[1:]:
			condition = condition & next_condition if mode == 'todos' else condition | next_condition
		matches = matches.filter(condition)

	return matches, {
		'raridades': EspeciePokemon.RARIDADE_CHOICES,
		'raridades_selecionadas': selected_rarities,
		'iv_geral_abaixo': iv_below,
		'modo_filtro': mode,
		'quantidade_para_deletar': matches.count() if conditions else 0,
		'filtro_configurado': bool(conditions),
	}


def pokedex_list(request):
	base_pokemons = EspeciePokemon.objects.all()
	busca = request.GET.get('q', '').strip()
	tipo = request.GET.get('tipo', '').strip()
	raridade = request.GET.get('raridade', '').strip()
	pokemons = base_pokemons

	if busca:
		numero = busca[1:] if busca.startswith('#') else busca
		filtro_busca = Q(nome__icontains=busca)
		if numero.isdigit():
			filtro_busca |= Q(pokeapi_id=int(numero))
		pokemons = pokemons.filter(filtro_busca)
	if tipo:
		pokemons = pokemons.filter(Q(tipo_primario=tipo) | Q(tipo_secundario=tipo))
	if raridade in dict(EspeciePokemon.RARIDADE_CHOICES):
		pokemons = pokemons.filter(raridade=raridade)

	tipos = sorted({
		valor
		for primario, secundario in base_pokemons.values_list('tipo_primario', 'tipo_secundario')
		for valor in (primario, secundario)
		if valor
	})
	return render(request, 'pokedex/pokedex_list.html', {
		'pokemons': pokemons.order_by('pokeapi_id'),
		'total_pokemons': base_pokemons.count(),
		'tipos': tipos,
		'raridades': EspeciePokemon.RARIDADE_CHOICES,
		'filtros': {'q': busca, 'tipo': tipo, 'raridade': raridade},
	})


@login_required
def gacha_view(request):
	context = {}
	if request.method == 'POST':
		especie = EspeciePokemon.objects.order_by('?').first()
		if especie is None:
			context['erro_captura'] = 'Ainda não há Pokémon disponíveis para captura.'
		else:
			perfil, _ = PerfilJogador.objects.get_or_create(usuario=request.user)
			cooldown_key = f'pokemon-capture-cooldown:{perfil.pk}'
			now = time.time()
			if not cache.add(cooldown_key, now, timeout=CAPTURE_COOLDOWN_SECONDS):
				last_capture = cache.get(cooldown_key)
				if last_capture is None and cache.add(cooldown_key, now, timeout=CAPTURE_COOLDOWN_SECONDS):
					last_capture = None
				else:
					remaining = max(1, ceil(CAPTURE_COOLDOWN_SECONDS - (now - (last_capture or now))))
					context['erro_captura'] = f'Aguarde {remaining} segundo(s) para iniciar outra captura.'
					context['capture_cooldown_seconds'] = remaining
			if 'erro_captura' not in context:
				pokemon_capturado = capturar_pokemon(perfil, especie.id)
				context['pokemon_capturado'] = pokemon_capturado
				context['capture_cooldown_seconds'] = max(
					0,
					CAPTURE_COOLDOWN_SECONDS - (time.time() - now),
				)
				context['pokemon_revelacao'] = list(
					EspeciePokemon.objects.filter(sprite_url__isnull=False)
					.exclude(sprite_url='')
					.exclude(pk=pokemon_capturado.especie_id)
					.order_by('?')
					.values('nome', 'sprite_url')[:12]
				)

	_, context['limpeza'] = _capture_cleanup_preview(request.user, request.GET)

	return render(request, 'pokedex/gacha.html', context)


@login_required
def my_pokemons(request):
	base_capturas = PokemonCapturado.objects.filter(
		jogador__usuario=request.user
	).select_related('especie').order_by('-data_captura')
	busca = request.GET.get('q', '').strip()
	tipo = request.GET.get('tipo', '').strip()
	raridade = request.GET.get('raridade', '').strip()
	nivel_min = request.GET.get('nivel_min', '').strip()
	nivel_max = request.GET.get('nivel_max', '').strip()
	capturas = base_capturas

	if busca:
		filtro_busca = Q(especie__nome__icontains=busca) | Q(apelido__icontains=busca)
		capturas = capturas.filter(filtro_busca)
	if tipo:
		capturas = capturas.filter(Q(especie__tipo_primario=tipo) | Q(especie__tipo_secundario=tipo))
	if raridade in dict(EspeciePokemon.RARIDADE_CHOICES):
		capturas = capturas.filter(especie__raridade=raridade)
	if nivel_min.isdigit():
		capturas = capturas.filter(nivel__gte=int(nivel_min))
	else:
		nivel_min = ''
	if nivel_max.isdigit():
		capturas = capturas.filter(nivel__lte=int(nivel_max))
	else:
		nivel_max = ''

	tipos = sorted({
		valor
		for primario, secundario in base_capturas.values_list(
			'especie__tipo_primario', 'especie__tipo_secundario'
		).distinct()
		for valor in (primario, secundario)
		if valor
	})
	capturas = list(capturas)
	rotulos_raridade = dict(EspeciePokemon.RARIDADE_CHOICES)
	for captura in capturas:
		ivs = {
			'iv_hp': captura.iv_hp,
			'iv_ataque': captura.iv_ataque,
			'iv_defesa': captura.iv_defesa,
			'iv_ataque_especial': captura.iv_ataque_especial,
			'iv_defesa_especial': captura.iv_defesa_especial,
			'iv_velocidade': captura.iv_velocidade,
		}
		captura.media_ivs = f"{sum(ivs.values()) / len(ivs):.1f}".replace('.', ',')
		captura.raridade_iv_geral = calcular_raridade_geral(ivs)
		captura.raridade_iv_geral_label = rotulos_raridade[captura.raridade_iv_geral]
	_, limpeza = _capture_cleanup_preview(request.user, request.GET)
	return render(request, 'pokedex/my_pokemons.html', {
		'meus_pokemons': capturas,
		'total_capturas': base_capturas.count(),
		'tipos': tipos,
		'raridades': EspeciePokemon.RARIDADE_CHOICES,
		'filtros': {
			'q': busca,
			'tipo': tipo,
			'raridade': raridade,
			'nivel_min': nivel_min,
			'nivel_max': nivel_max,
		},
		'limpeza': limpeza,
	})


@login_required
@require_POST
def delete_filtered_captures(request):
	capturas, filtros = _capture_cleanup_preview(request.user, request.POST)
	return_to = request.POST.get('return_to', '')
	if not url_has_allowed_host_and_scheme(return_to, allowed_hosts={request.get_host()}):
		return_to = reverse('my_pokemons')

	if not filtros['filtro_configurado']:
		messages.error(request, 'Selecione ao menos um critério antes de deletar.')
	else:
		quantidade, _ = capturas.delete()
		messages.success(request, f'{quantidade} Pokémon(ns) deletado(s).')
	return redirect(return_to)


@login_required
def pokemon_detail(request, captura_id):
	captura = get_object_or_404(
		PokemonCapturado.objects.select_related('especie'),
		pk=captura_id,
		jogador__usuario=request.user,
	)
	atributos = [
		('HP', 'hp_base', 'iv_hp', True),
		('Ataque', 'ataque_base', 'iv_ataque', False),
		('Defesa', 'defesa_base', 'iv_defesa', False),
		('Ataque especial', 'ataque_especial_base', 'iv_ataque_especial', False),
		('Defesa especial', 'defesa_especial_base', 'iv_defesa_especial', False),
		('Velocidade', 'velocidade_base', 'iv_velocidade', False),
	]
	atributos_calculados = []
	ivs = {}
	for nome, campo_base, campo_iv, is_hp in atributos:
		base = getattr(captura.especie, campo_base)
		iv = getattr(captura, campo_iv)
		ivs[campo_iv] = iv
		raridade_iv = calcular_raridade_de_iv(iv)
		valor = ((2 * base + iv) * captura.nivel // 100) + captura.nivel + (10 if is_hp else 5)
		maximo = ((2 * 255 + 31) * captura.nivel // 100) + captura.nivel + (10 if is_hp else 5)
		atributos_calculados.append({
			'nome': nome,
			'base': base,
			'iv': iv,
			'raridade_iv': raridade_iv,
			'raridade_iv_label': dict(EspeciePokemon.RARIDADE_CHOICES)[raridade_iv],
			'valor': valor,
			'percentual': round(valor / maximo * 100) if maximo else 0,
		})
	media_ivs = f"{sum(ivs.values()) / len(ivs):.1f}".replace('.', ',')
	raridade_iv_geral = calcular_raridade_geral(ivs)

	return render(request, 'pokedex/pokemon_detail.html', {
		'captura': captura,
		'atributos': atributos_calculados,
		'nome_exibido': captura.apelido or captura.especie.nome,
		'media_ivs': media_ivs,
		'raridade_iv_geral': raridade_iv_geral,
		'raridade_iv_geral_label': dict(EspeciePokemon.RARIDADE_CHOICES)[raridade_iv_geral],
	})
