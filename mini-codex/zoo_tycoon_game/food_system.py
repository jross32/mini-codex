def food_revenue(stall_count, visitors=200):
    conv = min(0.65, visitors / 500)
    return round(stall_count * conv * 420.0, 2)

def queue_len(visitors, stalls):
    return max(0, round((visitors / max(stalls, 1)) * 0.3 - 10))