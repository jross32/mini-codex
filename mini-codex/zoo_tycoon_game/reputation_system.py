def zoo_rating(visitors, cash):
    vis_score = min(visitors, 500) / 100
    cash_score = min(cash, 100000) / 25000
    return max(1, min(5, round(vis_score + cash_score)))

def aggregate(scores):
    if not scores:
        return {'avg': 5.0, 'total': 0}
    return {'avg': round(sum(scores) / len(scores), 2), 'total': len(scores)}