"""V2 terminal ui functions"""
import sys
import time

def clear_screen():
    print(chr(27) + '[2J' + chr(27) + '[H')


def loading_bar(msg):
    for i in range(0,101,5):
        filled=i//5
        bar='#'*filled + '-'*(20-filled)
        sys.stdout.write(f'\r{msg}: [{bar}] {i}%')
        sys.stdout.flush()
        time.sleep(0.01)
    print()


def title_banner(text):
    print()
    print(text.center(80))
    print()


def print_status(player):
    print(f"LVL {player['level']} | HP {player['hp']}/{player['max_hp']} | EXP {player['exp']}/{player['level']*100} | GOLD {player['gold']}")

