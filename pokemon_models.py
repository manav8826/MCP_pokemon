"""
pokemon_models.py
Defines the dataclasses that structure all Pokémon-related data.
This clean structure makes the rest of the code easy to manage.
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

# (NEW) Defines the possible status conditions for a Pokémon
class StatusEffect(Enum):
    NONE = "Healthy"
    POISON = "Poisoned"
    BURN = "Burned"
    PARALYSIS = "Paralyzed"

@dataclass
class Move:
    """Stores all relevant information for a single Pokémon move."""
    name: str
    type: str
    category: str  # e.g., 'physical', 'special'
    power: Optional[int]
    accuracy: Optional[int]
    effect: str

@dataclass
class PokemonStats:
    """Stores the base stats for a Pokémon."""
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

@dataclass
class Pokemon:
    """The main dataclass to hold all fetched data for a Pokémon."""
    id: int
    name: str
    types: List[str]
    stats: PokemonStats
    abilities: List[str]
    moves_sample: List[Move]
    evolution_paths: List[str]
    flavor_text: str
    ev_yield: str
    sprite_url: Optional[str]

@dataclass
class BattlePokemon:
    """
    Represents a Pokémon's state *during* a battle. This is separate
    from its base stats to track dynamic values like current HP.
    """
    pokemon: Pokemon
    current_hp: int
    current_energy: int
    # (NEW) Add a field to track the current status effect
    status: StatusEffect = StatusEffect.NONE

