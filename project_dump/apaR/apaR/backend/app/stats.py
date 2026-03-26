from __future__ import annotations

from typing import Any

from .data_store import DataStore


def reliability_score(player: dict[str, Any]) -> float:
    """Compute a simple reliability score based on matches played or fallback to id hash."""
    stats = player.get("stats_by_format") or player.get("statsByFormat") or {}
    matches_played = 0
    for fmt_stats in stats.values():
        if isinstance(fmt_stats, dict):
            matches_played += int(fmt_stats.get("matches", 0))
    base = min(matches_played * 2, 40)
    return 60 + base  # range roughly 60-100


def recent_form(player: dict[str, Any], last_n_sets: int = 10) -> float:
    """Approximate recent form using win% if present, otherwise a modest baseline."""
    stats = player.get("stats_by_format") or player.get("statsByFormat") or {}
    win_pct = None
    for fmt_stats in stats.values():
        if isinstance(fmt_stats, dict) and "win_pct" in fmt_stats:
            win_pct = float(fmt_stats.get("win_pct", 0))
            break
    if win_pct is not None:
        return win_pct
    # fallback: assume neutral recent form
    return 50.0


def matchup_history(player: dict[str, Any], opponent_team_id: str | None, data_store: DataStore | None = None) -> float:
    """Lightweight matchup weight. If we have matches in the datastore, weight by appearances."""
    if opponent_team_id and data_store:
        try:
            matches = data_store.matches_filtered(team_id=opponent_team_id, player_id=player.get("id"))
            # simple weight: more appearances vs opponent yields small boost
            return min(len(matches) * 5, 20)
        except Exception:
            pass
    return 10.0
