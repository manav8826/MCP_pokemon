"""
battle_simulator.py
Contains the BattleSimulator class, which manages the entire logic for a
Pokémon battle, including our unique damage formula and Energy System.
"""
import random
from typing import Optional, List
from pokemon_data_manager import PokemonDataManager
from pokemon_models import Move, BattlePokemon, StatusEffect, Pokemon

class BattleSimulator:
    """Manages the logic for a Pokémon battle simulation."""
    def __init__(self, data_manager: PokemonDataManager):
        self.data_manager = data_manager

    def _calculate_damage(self, attacker: BattlePokemon, defender: BattlePokemon, move: Move) -> tuple[int, str]:
        """(UNIQUE & BALANCED LOGIC) Calculates damage with a more stable custom formula."""
        if not move.power or move.power == 0:
            return 0, ""

        if move.category == 'physical':
            attack_stat = attacker.pokemon.stats.attack
            defense_stat = defender.pokemon.stats.defense
        else: # special
            attack_stat = attacker.pokemon.stats.special_attack
            defense_stat = defender.pokemon.stats.special_defense
        
        if attacker.status == StatusEffect.BURN and move.category == 'physical':
            attack_stat /= 2

        # THE FIX: This new formula adds a constant to the denominator.
        # This acts as a "shock absorber" to prevent absurdly high damage numbers
        # when a strong attacker hits a Pokémon with very low defenses.
        # The core logic is still a unique Power Ratio, but it's now balanced.
        power_ratio = (attack_stat / (defense_stat + 50)) 
        
        target_types = [t.lower() for t in defender.pokemon.types]
        effectiveness_multiplier = self.data_manager.get_type_effectiveness(move.type, target_types)
        
        random_factor = random.uniform(0.9, 1.1)
        
        base_damage = (move.power * power_ratio) * 1.5 # Multiplier to keep damage impactful
        final_damage = int(base_damage * effectiveness_multiplier * random_factor)

        effectiveness_text = ""
        if effectiveness_multiplier > 1: effectiveness_text = "It's super effective!"
        elif effectiveness_multiplier < 1: effectiveness_text = "It's not very effective..."
        
        return max(1, final_damage), effectiveness_text

    def _get_move_energy_cost(self, move: Move) -> int:
        """(UNIQUE LOGIC) Determines energy cost based on move power."""
        if not move.power or move.power < 40: return 10
        if move.power < 70: return 20
        if move.power < 100: return 30
        return 40

    def _select_move(self, attacker: BattlePokemon, opponent: BattlePokemon) -> Optional[Move]:
        """(SMARTER AI) A simple AI to select a move, avoiding sacrificial moves."""
        sacrificial_moves = ["self-destruct", "explosion", "final-gambit"]
        
        usable_moves = [
            m for m in attacker.pokemon.moves_sample 
            if self._get_move_energy_cost(m) <= attacker.current_energy 
            and m.name.lower() not in sacrificial_moves
        ]
        if not usable_moves: return None
        
        best_move = usable_moves[0]
        max_damage = 0
        
        for move in usable_moves:
            potential_damage, _ = self._calculate_damage(attacker, opponent, move)
            if potential_damage > max_damage:
                max_damage = potential_damage
                best_move = move
        return best_move

    def _apply_status_effect(self, move: Move, defender: BattlePokemon) -> Optional[str]:
        """Applies a status effect to a Pokémon based on the move used."""
        if defender.status != StatusEffect.NONE:
            return None

        move_type = move.type.lower()
        if move_type == 'poison' and random.random() < 0.3:
            defender.status = StatusEffect.POISON
            return f"{defender.pokemon.name} was poisoned!"
        if move_type == 'fire' and random.random() < 0.1:
            defender.status = StatusEffect.BURN
            return f"{defender.pokemon.name} was burned!"
        if move_type == 'electric' and random.random() < 0.1:
            defender.status = StatusEffect.PARALYSIS
            return f"{defender.pokemon.name} was paralyzed!"
            
        return None

    def _handle_pre_turn_status(self, pokemon: BattlePokemon, log: List[str]) -> bool:
        """Handles status effects that can prevent a Pokémon from moving."""
        if pokemon.status == StatusEffect.PARALYSIS:
            if random.random() < 0.25:
                log.append(f"{pokemon.pokemon.name} is paralyzed! It can't move!")
                return False
        return True

    def _handle_post_turn_status(self, pokemon: BattlePokemon, log: List[str]):
        """Handles status effects that deal damage at the end of a turn."""
        if pokemon.status == StatusEffect.POISON:
            damage = max(1, pokemon.pokemon.stats.hp // 8)
            pokemon.current_hp = max(0, pokemon.current_hp - damage)
            log.append(f"{pokemon.pokemon.name} is hurt by poison! [-{damage} HP]")
        elif pokemon.status == StatusEffect.BURN:
            damage = max(1, pokemon.pokemon.stats.hp // 16)
            pokemon.current_hp = max(0, pokemon.current_hp - damage)
            log.append(f"{pokemon.pokemon.name} is hurt by its burn! [-{damage} HP]")

    def run_simulation(self, p1_data: Pokemon, p2_data: Pokemon) -> str:
        """Runs the entire battle simulation and returns a formatted log."""
        p1 = BattlePokemon(pokemon=p1_data, current_hp=p1_data.stats.hp, current_energy=100)
        p2 = BattlePokemon(pokemon=p2_data, current_hp=p2_data.stats.hp, current_energy=100)
        
        log = [f"A battle is about to begin between {p1.pokemon.name} and {p2.pokemon.name}!", ""]
        turn = 0

        while p1.current_hp > 0 and p2.current_hp > 0 and turn < 50:
            turn += 1
            log.append(f"--- Turn {turn} ---")
            
            p1_speed = p1.pokemon.stats.speed * (0.5 if p1.status == StatusEffect.PARALYSIS else 1)
            p2_speed = p2.pokemon.stats.speed * (0.5 if p2.status == StatusEffect.PARALYSIS else 1)

            attacker, defender = (p1, p2) if p1_speed >= p2_speed else (p2, p1)
            
            log.append(f"({p1.pokemon.name}: {p1.current_hp} HP, {p1.current_energy} E, {p1.status.value}) vs ({p2.pokemon.name}: {p2.current_hp} HP, {p2.current_energy} E, {p2.status.value})")

            for current_attacker, current_defender in [(attacker, defender), (defender, attacker)]:
                if current_attacker.current_hp <= 0: continue
                
                can_move = self._handle_pre_turn_status(current_attacker, log)
                if not can_move: continue

                move = self._select_move(current_attacker, current_defender)
                if not move:
                    current_attacker.current_energy = min(100, current_attacker.current_energy + 50)
                    log.append(f"{current_attacker.pokemon.name} is low on energy and Rests! [+50 Energy]")
                    continue
                
                energy_cost = self._get_move_energy_cost(move)
                current_attacker.current_energy -= energy_cost
                
                damage, effectiveness_text = self._calculate_damage(current_attacker, current_defender, move)
                current_defender.current_hp = max(0, current_defender.current_hp - damage)
                
                log.append(f"{current_attacker.pokemon.name} used {move.name}! It dealt {damage} damage. {effectiveness_text}")

                if move.name.lower() in ["self-destruct", "explosion"]:
                    log.append(f"{current_attacker.pokemon.name} fainted after using its move!")
                    current_attacker.current_hp = 0

                status_message = self._apply_status_effect(move, current_defender)
                if status_message: log.append(status_message)
                
                if current_defender.current_hp <= 0:
                    log.append(f"{current_defender.pokemon.name} has fainted!")
                    break
            
            if p1.current_hp > 0 and p2.current_hp > 0:
                self._handle_post_turn_status(p1, log)
                if p1.current_hp <= 0: log.append(f"{p1.pokemon.name} has fainted!")
                self._handle_post_turn_status(p2, log)
                if p2.current_hp <= 0: log.append(f"{p2.pokemon.name} has fainted!")
            
            log.append("")

        log.append("--- Battle Over! ---")
        winner = "Draw"
        if p1.current_hp > 0 and p2.current_hp <= 0: winner = p1.pokemon.name
        elif p2.current_hp > 0 and p1.current_hp <= 0: winner = p2.pokemon.name

        log.append(f"The winner is: {winner}!")

        hp_bar1 = '█' * int(p1.current_hp / p1.pokemon.stats.hp * 20) + '-' * (20 - int(p1.current_hp / p1.pokemon.stats.hp * 20))
        hp_bar2 = '█' * int(p2.current_hp / p2.pokemon.stats.hp * 20) + '-' * (20 - int(p2.current_hp / p2.pokemon.stats.hp * 20))
        log.append("\n---\n**Final Battle State:**")
        log.append(f"**{p1.pokemon.name}:**\n[{hp_bar1}] {p1.current_hp}/{p1.pokemon.stats.hp} HP\nEnergy Remaining: {p1.current_energy}/100")
        log.append(f"\n**{p2.pokemon.name}:**\n[{hp_bar2}] {p2.current_hp}/{p2.pokemon.stats.hp} HP\nEnergy Remaining: {p2.current_energy}/100")

        return "\n".join(log)

