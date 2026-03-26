#!/usr/bin/env python3
"""Update registry to categorize all game tools under game_systems."""

game_tools = [
    'character_name_input', 'character_stat_strength_init', 'character_stat_defense_init', 'character_stat_wisdom_init',
    'character_hp_calculator', 'character_level_initializer', 'character_experience_initializer', 'character_gold_initializer',
    'character_damage_formula', 'character_damage_reducer_by_defense', 'character_heal_limiter', 'character_experience_accumulator',
    'character_level_threshold_calculator', 'character_effective_levelup_check', 'character_level_incrementer', 'character_hp_growth_on_level',
    'character_stat_growth_on_level', 'character_experience_reset_on_level', 'character_state_serializer', 'character_is_alive_checker',
    'character_system_generator', 'combat_system_generator', 'monster_system_generator', 'rest_system_generator',
    'saveload_system_generator', 'shop_system_generator', 'ui_effects_generator', 'rpg_adventure_builder', 'rpg_game_builder', 'game_orchestrator'
]

# Read registry
with open('ai_repo_tools/tools/registry.py', 'r') as f:
    content = f.read()

# Replace category for all game tools
for tool in game_tools:
    old = f'"{tool}": {{\n        "category": "execution",'
    new = f'"{tool}": {{\n        "category": "game_systems",'
    content = content.replace(old, new)

# Write back
with open('ai_repo_tools/tools/registry.py', 'w') as f:
    f.write(content)

print(f'✓ Updated {len(game_tools)} game tools to game_systems category')
