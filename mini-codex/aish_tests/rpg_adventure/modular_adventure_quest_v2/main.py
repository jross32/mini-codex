"""V2 main game loop"""
from entities.character import new_character, character_is_alive, character_gain_exp
from entities.monster import spawn_monster, monster_is_alive
from systems.combat import combat_round
from systems.shops import shop_catalogs, choose_shop_type, rare_trader_event, apply_purchase
from systems.rest import rest_locations, apply_rest
from core.save_load import save_game, load_game
from ui.terminal_ui import clear_screen, loading_bar, title_banner, print_status

def explore(player):
    monster = spawn_monster(player['level'])
    print(f"A wild {monster['name']} appears!")
    while character_is_alive(player) and monster_is_alive(monster):
        print(f"Monster HP: {monster['hp']}")
        action=input('1.Attack 2.Run >> ').strip()
        if action=='2':
            print('You escaped.')
            return
        r = combat_round(player, monster)
        print(f"You dealt {r['player_damage']}; enemy dealt {r['enemy_damage']}.")
    if character_is_alive(player):
        print('Victory!')
        player['gold'] += monster['gold']
        leveled = character_gain_exp(player, monster['gold'])
        if leveled:
            print('Level up!')
    else:
        print('You fell in battle, but are revived at town.')
        player['hp'] = player['max_hp']


def shop_menu(player):
    catalogs = shop_catalogs()
    stype = choose_shop_type()
    print(f"Shop type: {stype}")
    items = catalogs[stype]
    for i,(n,p) in enumerate(items,1):
        print(f"{i}. {n} - {p}g")
    rare = rare_trader_event()
    if rare:
        print(f"Rare trader: {rare['name']}")
    idx = int(input('Buy index (0 skip): ') or '0')
    if idx > 0 and idx <= len(items):
        n,p = items[idx-1]
        if apply_purchase(player,n,p):
            print(f"Bought {n}")
        else:
            print('Not enough gold')


def rest_menu(player):
    spots = rest_locations()
    for i,(n,h,c) in enumerate(spots,1):
        print(f"{i}. {n} heal {h} cost {c}")
    idx = int(input('Choice (0 cancel): ') or '0') - 1
    if idx >= 0:
        out = apply_rest(player, idx)
        if out['ok']:
            print(f"Rested at {out['name']}")
        else:
            print('Rest failed')


def game_loop(player, save_path):
    while True:
        clear_screen()
        print_status(player)
        print('\n1.Explore 2.Shop 3.Rest 4.Save 5.Quit')
        c=input('>> ').strip()
        if c=='1':
            explore(player)
        elif c=='2':
            shop_menu(player)
        elif c=='3':
            rest_menu(player)
        elif c=='4':
            save_game(player, save_path)
            print('Saved.')
        elif c=='5':
            return


def main():
    save_path = 'aish_tests/save_v2.json'
    clear_screen()
    loading_bar('Loading V2')
    title_banner('=== ADVENTURE QUEST V2 ===')
    print('1. New Game\n2. Load Game\n3. Exit')
    c=input('>> ').strip()
    if c == '1':
        name=input('Name: ').strip() or 'HeroV2'
        player=new_character(name)
        game_loop(player, save_path)
    elif c == '2':
        p=load_game(save_path)
        if p is None:
            print('No V2 save found')
            return
        game_loop(p, save_path)
    else:
        return

