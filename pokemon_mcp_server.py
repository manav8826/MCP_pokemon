"""
pokemon_mcp_server.py
The main entry point for the MCP server.
Handles MCP protocol interactions, defines tools, and formats the final output.
"""
from mcp.server.fastmcp import FastMCP
from pokemon_data_manager import PokemonDataManager
from pokemon_models import Pokemon, BattlePokemon # Import BattlePokemon
from battle_simulator import BattleSimulator # Import the new simulator

# --- MCP Server Setup and Class Initialization ---
app = FastMCP("professional-pokemon-server")
data_manager = PokemonDataManager()
battle_simulator = BattleSimulator(data_manager) # Create an instance of the simulator

# --- Helper function for formatting Part 1 output ---
def _format_pokemon_details(pokemon: Pokemon) -> str:
    """Formats the rich Pokemon data object into a clean Markdown string."""
    
    # (Your unique novelty feature)
    def _get_strategic_role(stats: 'PokemonStats') -> str:
        if stats.speed > 110 and (stats.attack > 100 or stats.special_attack > 100):
            return "⚡ Fast Sweeper: Aims to out-speed and defeat opponents quickly."
        if (stats.hp > 100 and (stats.defense > 100 or stats.special_defense > 100)):
            return "🛡️ Bulky Wall: Designed to withstand many hits and wear down the opponent."
        if stats.attack > stats.special_attack + 15: role = "Physical Attacker"
        elif stats.special_attack > stats.attack + 15: role = "Special Attacker"
        else: role = "Mixed Attacker"
        if stats.speed > 95: return f"⚡ Fast {role}: Focuses on striking first with powerful attacks."
        elif stats.hp > 85 and (stats.defense > 85 or stats.special_defense > 85):
            return f"🛡️ Bulky {role}: Can take hits while dealing consistent damage."
        else: return f"⚖️ Balanced {role}: A versatile fighter with well-rounded stats."

    lines = [
        f"🌟 **{pokemon.name}** (#{pokemon.id:03d})",
        "---",
        f"_{pokemon.flavor_text}_",
        f"\n**🏷️ Type(s):** {' / '.join(t.capitalize() for t in pokemon.types)}",
        f"**🧠 Strategic Role:** {_get_strategic_role(pokemon.stats)}\n",
        "**📊 Base Stats:**",
        f"- ❤️ **HP:** {pokemon.stats.hp}",
        f"- ⚔️ **Attack:** {pokemon.stats.attack}",
        f"- 🛡️ **Defense:** {pokemon.stats.defense}",
        f"- 🔮 **Sp. Atk:** {pokemon.stats.special_attack}",
        f"- 💠 **Sp. Def:** {pokemon.stats.special_defense}",
        f"- 💨 **Speed:** {pokemon.stats.speed}",
        f"- **📈 Total:** {sum(vars(pokemon.stats).values())}\n",
        f"**⚡ Abilities:** {', '.join(pokemon.abilities)}",
        f"**💪 Training Focus (EV Yield):** {pokemon.ev_yield}\n",
        "**🌱 Evolution Line(s):**"
    ]
    if pokemon.evolution_paths:
        for path in pokemon.evolution_paths:
            lines.append(f"- {path}")
    else:
        lines.append(f"- {pokemon.name} does not evolve.")
    
    lines.append("\n**🥊 Sample Moveset:**")
    for move in pokemon.moves_sample:
        lines.append(f"- **{move.name}** ({move.type.capitalize()})")
        lines.append(f"  - _Power: {move.power or 'N/A'}, Accuracy: {move.accuracy or 'N/A'}_")
        lines.append(f"  - Effect: {move.effect}")

    return "\n".join(lines)

# --- MCP Tool Definitions ---

@app.tool()
async def get_pokemon_details(name: str) -> str:
    """
    (Part 1) Fetches professional-grade data for a Pokémon, including a strategic analysis.
    """
    pokemon_object = await data_manager.get_pokemon_details(name)
    if not pokemon_object:
        return f"Error: Could not find data for Pokémon '{name}'."
    return _format_pokemon_details(pokemon_object)

@app.tool()
async def simulate_battle(pokemon1: str, pokemon2: str) -> str:
    """
    (Part 2) Simulates a battle between two Pokémon using a custom energy-based combat system.
    Provides a turn-by-turn log and a final summary.
    """
    p1_data = await data_manager.get_pokemon_details(pokemon1)
    if not p1_data:
        return f"Error: Could not find data for Pokémon '{pokemon1}' to start the battle."

    p2_data = await data_manager.get_pokemon_details(pokemon2)
    if not p2_data:
        return f"Error: Could not find data for Pokémon '{pokemon2}' to start the battle."
    
    # THIS IS THE FIX: Call the correct function name `run_simulation`
    battle_log = battle_simulator.run_simulation(p1_data, p2_data)
    
    return battle_log

