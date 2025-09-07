"""
pokemon_data_manager.py
Contains the PokemonDataManager class, responsible for all interactions
with the PokéAPI, including fetching, parsing, and caching data.
"""
import httpx
import random
from typing import List, Any, Optional
from pokemon_models import Pokemon, PokemonStats, Move

POKEAPI_BASE = "https://pokeapi.co/api/v2"

class PokemonDataManager:
    """Manages all Pokémon data fetching, parsing, and caching."""
    def __init__(self):
        self.cache: dict[str, Pokemon] = {}
        # (THE FIX IS HERE) This is the complete, real type chart.
        self.type_chart = {
            "normal": {"fighting": 2.0, "ghost": 0.0},
            "fighting": {"flying": 2.0, "rock": 0.5, "bug": 0.5, "psychic": 2.0, "dark": 0.5, "fairy": 2.0},
            "flying": {"rock": 2.0, "bug": 0.5, "grass": 0.5, "electric": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.0},
            "poison": {"fighting": 0.5, "poison": 0.5, "ground": 2.0, "bug": 0.5, "grass": 0.5, "psychic": 2.0, "fairy": 0.5},
            "ground": {"water": 2.0, "grass": 2.0, "ice": 2.0, "poison": 0.5, "rock": 0.5, "electric": 0.0},
            "rock": {"fighting": 2.0, "ground": 2.0, "steel": 2.0, "water": 2.0, "grass": 2.0, "normal": 0.5, "flying": 0.5, "poison": 0.5, "fire": 0.5},
            "bug": {"flying": 2.0, "rock": 2.0, "fire": 2.0, "fighting": 0.5, "ground": 0.5, "grass": 0.5},
            "ghost": {"ghost": 2.0, "dark": 2.0, "normal": 0.0, "fighting": 0.0, "poison": 0.5, "bug": 0.5},
            "steel": {"fighting": 2.0, "ground": 2.0, "fire": 2.0, "normal": 0.5, "flying": 0.5, "rock": 0.5, "bug": 0.5, "steel": 0.5, "grass": 0.5, "psychic": 0.5, "ice": 0.5, "dragon": 0.5, "fairy": 0.5, "poison": 0.0},
            "fire": {"ground": 2.0, "rock": 2.0, "water": 2.0, "bug": 0.5, "steel": 0.5, "fire": 0.5, "grass": 0.5, "ice": 0.5, "fairy": 0.5},
            "water": {"grass": 2.0, "electric": 2.0, "steel": 0.5, "fire": 0.5, "water": 0.5, "ice": 0.5},
            "grass": {"flying": 2.0, "poison": 2.0, "bug": 2.0, "fire": 2.0, "ice": 2.0, "ground": 0.5, "water": 0.5, "grass": 0.5, "electric": 0.5},
            "electric": {"ground": 2.0, "flying": 0.5, "steel": 0.5, "electric": 0.5},
            "psychic": {"bug": 2.0, "ghost": 2.0, "dark": 2.0, "fighting": 0.5, "psychic": 0.5},
            "ice": {"fighting": 2.0, "rock": 2.0, "steel": 2.0, "fire": 2.0, "ice": 0.5},
            "dragon": {"ice": 2.0, "dragon": 2.0, "fairy": 2.0, "fire": 0.5, "water": 0.5, "grass": 0.5, "electric": 0.5},
            "dark": {"fighting": 2.0, "bug": 2.0, "fairy": 2.0, "ghost": 0.5, "dark": 0.5, "psychic": 0.0},
            "fairy": {"poison": 2.0, "steel": 2.0, "fighting": 0.5, "bug": 0.5, "dark": 0.5, "dragon": 0.0}
        }

    def get_type_effectiveness(self, move_type: str, target_types: List[str]) -> float:
        """(FIXED) Calculates the real type effectiveness multiplier."""
        multiplier = 1.0
        move_type = move_type.lower()
        for t in target_types:
            target_type = t.lower()
            if target_type in self.type_chart and move_type in self.type_chart[target_type]:
                multiplier *= self.type_chart[target_type][move_type]
        return multiplier

    async def _fetch_and_parse_moves(self, client: httpx.AsyncClient, primary_data: dict) -> List[Move]:
        """(FIXED) Fetches and intelligently curates a strategic moveset."""
        
        pokemon_types = [t['type']['name'] for t in primary_data['types']]
        all_move_refs = primary_data['moves']
        random.shuffle(all_move_refs) # Shuffle to get variety

        # Prioritize STAB moves (Same Type Attack Bonus)
        stab_moves = []
        other_moves = []

        for move_ref in all_move_refs:
            try:
                move_res = await client.get(move_ref['move']['url'])
                if move_res.status_code == 200:
                    move_data = move_res.json()
                    
                    # We only want moves that deal damage for this simple simulator
                    if move_data.get("power") is None or move_data.get("power") == 0:
                        continue
                    
                    effect_description = "No effect description available."
                    for entry in move_data.get('effect_entries', []):
                        if entry.get('language', {}).get('name') == 'en':
                            effect_description = entry.get('short_effect', "N/A")
                            effect_description = effect_description.replace("$effect_chance", str(move_data.get('effect_chance', '')))
                            break
                    
                    new_move = Move(
                        name=move_data["name"].capitalize().replace('-', ' '),
                        type=move_data["type"]["name"],
                        power=move_data.get("power"),
                        accuracy=move_data.get("accuracy"),
                        effect=effect_description,
                        category=move_data["damage_class"]["name"]
                    )

                    # Sort moves into STAB and non-STAB lists
                    if new_move.type in pokemon_types:
                        stab_moves.append(new_move)
                    else:
                        other_moves.append(new_move)

            except httpx.HTTPError:
                continue
        
        # Create a final moveset of 4 moves: prioritize STAB, then fill with others
        final_moveset = stab_moves[:2] + other_moves
        return final_moveset[:4]

    async def _fetch_and_parse_evolution(self, client: httpx.AsyncClient, species_url: str) -> tuple[List[str], str]:
        """Fetches and parses the full evolution chain and flavor text."""
        species_res = await client.get(species_url)
        if species_res.status_code != 200:
            return [], "No flavor text available."
        
        species_data = species_res.json()
        
        flavor_text = "No Pokédex entry found."
        for entry in species_data.get('flavor_text_entries', []):
            if entry.get('language', {}).get('name') == 'en':
                flavor_text = entry.get('flavor_text', flavor_text).replace('\n', ' ').replace('\f', ' ')
                break
        
        evo_chain_url = species_data.get("evolution_chain", {}).get("url")
        evolution_paths = []
        if evo_chain_url:
            evo_res = await client.get(evo_chain_url)
            if evo_res.status_code == 200:
                evo_data = evo_res.json()
                parsed_paths = self._parse_evolution_chain_recursive(evo_data.get('chain', {}))
                evolution_paths = [" -> ".join(path) for path in parsed_paths]

        return evolution_paths, flavor_text

    def _parse_evolution_chain_recursive(self, chain_data: dict) -> List[List[str]]:
        """Recursively parses the evolution chain to handle branches."""
        my_name = chain_data['species']['name'].capitalize()
        next_nodes = chain_data.get('evolves_to', [])

        if not next_nodes:
            return [[my_name]]

        all_paths = []
        for node in next_nodes:
            child_paths = self._parse_evolution_chain_recursive(node)
            for path in child_paths:
                all_paths.append([my_name] + path)
        
        return all_paths

    async def _fetch_primary_data(self, client: httpx.AsyncClient, name: str) -> Optional[dict]:
        """Fetches the main data from the /pokemon/{name} endpoint."""
        response = await client.get(f"{POKEAPI_BASE}/pokemon/{name.lower()}")
        if response.status_code != 200:
            return None
        return response.json()

    def _get_ev_yield(self, primary_data: dict) -> str:
        """Parses the EV yield from the stats data."""
        evs = []
        for stat in primary_data.get('stats', []):
            if stat['effort'] > 0:
                evs.append(f"{stat['effort']} {stat['stat']['name'].upper().replace('-', ' ')}")
        return ", ".join(evs) if evs else "N/A"

    async def get_pokemon_details(self, name: str) -> Optional[Pokemon]:
        """The main public method to fetch and assemble all Pokémon data."""
        if name.lower() in self.cache:
            return self.cache[name.lower()]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                primary_data = await self._fetch_primary_data(client, name)
                if not primary_data: return None

                stats = PokemonStats(
                    hp=primary_data['stats'][0]['base_stat'],
                    attack=primary_data['stats'][1]['base_stat'],
                    defense=primary_data['stats'][2]['base_stat'],
                    special_attack=primary_data['stats'][3]['base_stat'],
                    special_defense=primary_data['stats'][4]['base_stat'],
                    speed=primary_data['stats'][5]['base_stat'],
                )

                evolution_paths, flavor_text = await self._fetch_and_parse_evolution(client, primary_data['species']['url'])
                moves = await self._fetch_and_parse_moves(client, primary_data)

                pokemon = Pokemon(
                    id=primary_data['id'],
                    name=primary_data['name'].capitalize(),
                    types=[t['type']['name'].capitalize() for t in primary_data['types']],
                    stats=stats,
                    abilities=[a['ability']['name'].capitalize().replace('-', ' ') for a in primary_data['abilities']],
                    moves_sample=moves,
                    evolution_paths=evolution_paths,
                    flavor_text=flavor_text,
                    ev_yield=self._get_ev_yield(primary_data),
                    sprite_url=primary_data['sprites']['front_default']
                )

                self.cache[name.lower()] = pokemon
                return pokemon
        except (httpx.HTTPError, KeyError) as e:
            # Log the error if you have a logger configured
            return None

