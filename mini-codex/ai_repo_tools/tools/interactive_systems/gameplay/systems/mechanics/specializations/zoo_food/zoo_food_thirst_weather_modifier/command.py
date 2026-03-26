"""
zoo_food_thirst_weather_modifier - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_food_thirst_weather_modifier(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_food_thirst_weather_modifier")
    weather_options = [("sunny",1.4,32),("hot",1.8,38),("cloudy",1.0,22),("mild",1.1,25),("rainy",0.8,18)]
    weather, modifier, temp = rng.choice(weather_options)
    thirst_rate = round(8 * modifier, 2)
    payload: Dict = {
        "success": True,
        "modifier": modifier,
        "weather": weather,
        "temp_celsius": temp,
        "thirst_rate_per_hour": thirst_rate,
        "drink_sales_boost_pct": round((modifier - 1) * 100, 1),
        "summary": f"Weather [{weather}, {temp}°C]: thirst x{modifier} ({thirst_rate}/h).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_food_thirst_weather_modifier(repo_path: str):
    code, payload = run_zoo_food_thirst_weather_modifier(repo_path)
    print(json.dumps(payload))
    return code, payload
