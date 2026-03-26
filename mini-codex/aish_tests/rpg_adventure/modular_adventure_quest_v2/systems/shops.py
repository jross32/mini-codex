"""V2 branching shop functions"""
import random

def shop_catalogs():
    return {'blacksmith':[('Iron Sword',120),('Steel Shield',140)],'apothecary':[('Potion',60),('Mega Potion',180)],'arcane':[('Rune Stone',220),('Mana Draught',130)],'general':[('Rope',20),('Torch',15)],'night_market':[('Shadow Dagger',360),('Cursed Charm',420)]}


def choose_shop_type():
    types=['blacksmith','apothecary','arcane','general']
    if random.random() < 0.15:
        return 'night_market'
    return random.choice(types)


def rare_trader_event():
    if random.random() < 0.1:
        return {'name':'Wandering Relic Broker','items':[('Phoenix Blade',900),('Ancient Aegis',1100)]}
    return None


def apply_purchase(player, item, price):
    if player['gold'] < price:
        return False
    player['gold'] -= price
    player['inventory'].append(item)
    return True

