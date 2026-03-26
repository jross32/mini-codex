"""V2 monster functions"""
def spawn_monster(level):
    base=[{'name':'Goblin','hp':25,'atk':7,'def':2,'gold':70},{'name':'Orc','hp':45,'atk':10,'def':3,'gold':130},{'name':'Troll','hp':75,'atk':14,'def':4,'gold':220},{'name':'Dragon','hp':140,'atk':20,'def':7,'gold':700}]
    idx=min(max(0,level-1),len(base)-1)
    m=dict(base[idx])
    m['hp'] += level*6
    m['max_hp'] = m['hp']
    return m


def monster_is_alive(monster):
    return monster['hp'] > 0

