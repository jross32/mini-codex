import random
from game_state import Animal, ZooState
from ticket_system import set_base_price, surge, child_price
from visitor_system import daily_visitors
from animal_system import health_tick, behavior, CATALOGUE
from food_system import food_revenue
from staff_system import get_salary
from finance_system import ticket_rev, daily_expense, pnl
from event_system import roll_event, season
from reputation_system import zoo_rating, aggregate
from progression_system import calc_prestige, unlock_check, UNLOCKS

RNG = random.Random(42)


def sep(title='', w=62):
    if title:
        p = (w - len(title) - 2) // 2
        print('=' * p + ' ' + title + ' ' + '=' * (w - p - len(title) - 2))
    else:
        print('=' * w)


def setup(state):
    for name, biome, cost, upkeep in CATALOGUE[:3]:
        state.animals.append(Animal(species=name, biome=biome, upkeep=upkeep))
    state.cash -= 25000
    sep('SETUP')
    print('  Animals: ' + str([a.species for a in state.animals]))
    print('  Starting cash: $' + f'{state.cash:,.0f}')
    sep()


def simulate_day(state, d):
    wknd = d % 7 in (6, 0)
    visitors = daily_visitors(RNG, wknd)
    price = surge(set_base_price(RNG), RNG.randint(60, 110))
    t_rev = ticket_rev(visitors, price)
    f_rev = food_revenue(3, visitors)
    exp = daily_expense(state.animals)
    ev = roll_event(RNG)
    ev_cost = 0
    ev_str = ''
    if ev:
        ev_cost = ev.get('cost', 0)
        state.cash -= ev_cost
        ev_str = ' [' + ev['name'] + ' $' + str(ev_cost) + ']'
        visitors = round(visitors * ev.get('boost', 1.0))
    net = pnl(t_rev + f_rev, exp + ev_cost)
    state.cash += pnl(t_rev + f_rev, exp)
    for a in state.animals:
        a.health = health_tick(a.health, a.keeper)
    snr = zoo_rating(visitors, state.cash)
    pts = calc_prestige(snr)
    state.prestige += pts
    state.reviews.append(snr)
    szn = season(d)
    wknd_flag = '*' if wknd else ' '
    rev_total = t_rev + f_rev
    tag = f'Day {d:2d} [{szn:6s}{wknd_flag}]'
    print(f'{tag}: {visitors:3d}vis  rev=${rev_total:,.0f}  exp=${exp:,.0f}  net=${net:+,.0f}  cash=${state.cash:,.0f}  stars={snr}{ev_str}')


def main():
    sep('ZOO TYCOON')
    print('  Text-based zoo management simulation')
    sep()
    state = ZooState()
    setup(state)
    print('Simulating 10 days...')
    print()
    for d in range(1, 11):
        simulate_day(state, d)
    print()
    sep('FINAL REPORT')
    agg = aggregate(state.reviews)
    cash_str = f'{state.cash:,.2f}'
    print('  Zoo cash   : $' + cash_str)
    print('  Prestige   : ' + str(state.prestige))
    print('  Animals    : ' + str(len(state.animals)))
    avg_str = str(agg['avg'])
    print('  Avg rating : ' + avg_str + '/5 stars')
    for feat, _ in UNLOCKS:
        u = unlock_check(feat, state.prestige)
        if u['unlocked']:
            print('  UNLOCKED   : ' + feat)
    sep()


if __name__ == '__main__':
    main()