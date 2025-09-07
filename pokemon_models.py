"""
pokemon_models.py
Defines the dataclasses for structuring all Pokémon-related data.
This ensures type safety and clean data handling throughout the application.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PokemonStats:
    """Represents the base stats of a Pokémon."""
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

@dataclass
class Move:
    """Represents a single move with its key attributes."""
    name: str
    type: str
    power: Optional[int]
    accuracy: Optional[int]
    effect: str

@dataclass
class Pokemon:
    """
    The core, comprehensive data model for a single Pokémon.
    This object is what will be cached and used by the server.
    """
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
