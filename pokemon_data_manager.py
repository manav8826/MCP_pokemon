"""
pokemon_data_manager.py
Contains the PokemonDataManager class, responsible for all interactions
with the PokéAPI, including fetching, parsing, and caching data.
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
# IMPORT CHANGE: Added a '.' for relative import within the package
# THE FIX
from pokemon_models import Pokemon, PokemonStats, Move

POKEAPI_BASE = "https://pokeapi.co/api/v2"

class PokemonDataManager:
    """Manages all Pokémon data fetching, parsing, and caching."""
    
    def __init__(self):
        self.cache: Dict[str, Pokemon] = {}

    async def get_pokemon_details(self, name: str) -> Optional[Pokemon]:
        identifier = name.lower().strip()
        if identifier in self.cache:
            return self.cache[identifier]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                pokemon_res, species_res = await self._fetch_primary_data(client, identifier)
                if not pokemon_res or not species_res: return None
                pokemon_data = pokemon_res.json()
                species_data = species_res.json()
                evolution_paths = await self._fetch_and_parse_evolution(client, species_data)
                moves_sample = await self._fetch_move_sample(client, pokemon_data.get('moves', []))
                pokemon_object = self._assemble_pokemon_object(pokemon_data, species_data, evolution_paths, moves_sample)
                self.cache[identifier] = pokemon_object
                return pokemon_object
        except httpx.HTTPError as e:
            print(f"HTTP Error fetching data for {name}: {e}")
            return None
    
    async def _fetch_primary_data(self, client: httpx.AsyncClient, name: str) -> tuple[Optional[httpx.Response], Optional[httpx.Response]]:
        pokemon_req = client.get(f"{POKEAPI_BASE}/pokemon/{name}")
        species_req = client.get(f"{POKEAPI_BASE}/pokemon-species/{name}")
        responses = await asyncio.gather(pokemon_req, species_req, return_exceptions=True)
        pokemon_res, species_res = responses
        if isinstance(pokemon_res, Exception) or pokemon_res.status_code != 200: return None, None
        if isinstance(species_res, Exception) or species_res.status_code != 200: return None, None
        return pokemon_res, species_res

    async def _fetch_and_parse_evolution(self, client: httpx.AsyncClient, species_data: dict) -> List[str]:
        evo_chain_url = species_data.get("evolution_chain", {}).get("url")
        if not evo_chain_url: return []
        evo_res = await client.get(evo_chain_url)
        if evo_res.status_code == 200:
            evo_data = evo_res.json()
            evolution_paths_raw = self._parse_evolution_chain(evo_data.get('chain', {}))
            return [" -> ".join(path) for path in evolution_paths_raw]
        return []

    def _parse_evolution_chain(self, chain_data: dict) -> List[List[str]]:
        my_name = chain_data['species']['name'].capitalize()
        next_nodes = chain_data.get('evolves_to', [])
        if not next_nodes: return [[my_name]]
        all_paths = []
        for node in next_nodes:
            child_paths = self._parse_evolution_chain(node)
            for path in child_paths:
                all_paths.append([my_name] + path)
        return all_paths

    async def _fetch_move_sample(self, client: httpx.AsyncClient, moves_data: list, sample_size: int = 5) -> List[Move]:
        detailed_moves = []
        moves_data.sort(key=lambda m: m['version_group_details'][-1]['level_learned_at'], reverse=True)
        for move_info in moves_data[:sample_size]:
            move_url = move_info['move']['url']
            try:
                move_res = await client.get(move_url)
                if move_res.status_code == 200:
                    move_data = move_res.json()
                    effect_entry = next((e for e in move_data.get('effect_entries', []) if e['language']['name'] == 'en'), None)
                    effect_text = "No effect description."
                    if effect_entry:
                        effect_text = effect_entry['short_effect'].replace('$effect_chance', str(move_data.get('effect_chance', '')))
                    detailed_moves.append(Move(name=move_data['name'].replace('-', ' ').title(), type=move_data['type']['name'], power=move_data.get('power'), accuracy=move_data.get('accuracy'), effect=effect_text))
            except httpx.HTTPError: continue
        return detailed_moves

    def _assemble_pokemon_object(self, p_data: dict, s_data: dict, evo_paths: list, moves: list) -> Pokemon:
        stats = {s['stat']['name'].replace('-', '_'): s['base_stat'] for s in p_data['stats']}
        flavor_text_entry = next((ft for ft in s_data.get('flavor_text_entries', []) if ft['language']['name'] == 'en'), None)
        flavor_text = flavor_text_entry['flavor_text'].replace('\n', ' ') if flavor_text_entry else "No Pokédex entry found."
        ev_yields = [f"{s['effort']} {s['stat']['name'].upper()}" for s in p_data['stats'] if s['effort'] > 0]
        return Pokemon(id=p_data['id'], name=p_data['name'].capitalize(), types=[t['type']['name'] for t in p_data['types']], stats=PokemonStats(**stats), abilities=[a['ability']['name'].replace('-', ' ').title() for a in p_data['abilities']], moves_sample=moves, evolution_paths=evo_paths, flavor_text=flavor_text, ev_yield=", ".join(ev_yields), sprite_url=p_data['sprites']['front_default'])
