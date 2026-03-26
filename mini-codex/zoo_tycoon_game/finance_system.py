def ticket_rev(visitors, price):
    return round(visitors * price, 2)

def daily_expense(animals, extra=200.0):
    return round(sum(a.upkeep / 30 for a in animals) + extra, 2)

def pnl(rev, exp):
    return round(rev - exp, 2)