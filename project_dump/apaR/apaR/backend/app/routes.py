from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import text
from sqlalchemy.engine import Engine

from pathlib import Path

from .data_store import DataStore, Dataset
from .snapshots import latest_snapshot, list_snapshots, save_snapshot

api_bp = Blueprint("api", __name__)


@api_bp.get("/health")
def health() -> tuple[dict[str, str], int]:
    """Return basic status, dataset cache info, and DB connectivity."""
    settings = current_app.config["SETTINGS"]
    status = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
    }

    # Database connectivity check (best-effort)
    engine: Engine | None = current_app.config.get("DB_ENGINE")
    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            status["database"] = "reachable"
        except Exception:  # pragma: no cover - logged upstream if needed
            status["database"] = "unreachable"

    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        data_store.ensure_loaded()
        status["data"] = {
            "status": "loaded",
            "last_loaded_at": data_store.last_loaded_at.isoformat() if data_store.last_loaded_at else None,
            "source": data_store.last_loaded_file.name if data_store.last_loaded_file else None,
        }
    except Exception as exc:  # noqa: BLE001
        status["data"] = {"status": "unavailable", "error": str(exc)}

    return jsonify(status), 200


@api_bp.get("/db-health")
def db_health() -> tuple[dict[str, object], int]:
    """Health check for database connection and schema.
    
    Returns database type, connection status, and present tables.
    No secrets exposed. Public endpoint for diagnostics.
    """
    engine: Engine | None = current_app.config.get("DB_ENGINE")
    
    # Determine database kind from URL
    db_url = str(engine.url) if engine else ""
    db_kind = "postgres" if "postgresql" in db_url.lower() else "sqlite"
    
    # Check connection and list tables
    db_connected = False
    tables_present = []
    last_error = None
    
    try:
        from sqlalchemy import inspect
        
        # Try to connect and get table names
        inspector = inspect(engine)
        tables_present = inspector.get_table_names()
        db_connected = True
    except Exception as exc:  # noqa: BLE001
        db_connected = False
        last_error = str(exc)
    
    return jsonify({
        "ok": True,
        "db_kind": db_kind,
        "db_connected": db_connected,
        "tables_present": sorted(tables_present),
        "required_tables": ["user_contexts", "users"],
        "tables_ok": all(t in tables_present for t in ["users", "user_contexts"]),
        "last_error": last_error,
    }), 200


@api_bp.get("/meta")
def meta() -> tuple[dict[str, object], int]:
    """Expose dataset metadata and collection counts."""
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        dataset: Dataset = data_store.ensure_loaded()
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "data_unavailable", "detail": str(exc)}), 503

    counts = {
        "divisions": len(dataset["divisions"]),
        "teams": len(dataset["teams"]),
        "players": len(dataset["players"]),
        "matches": len(dataset["matches"]),
        "locations": len(dataset["locations"]),
    }

    # Determine source: "mock" or "real"
    source = "mock" if data_store.is_mock_data else "real"
    
    # Get generated_at from dataset meta if available
    generated_at = dataset.get("meta", {}).get("generated_at")
    
    # Build banner message
    meta_banner = "Using mock data - for development only" if data_store.is_mock_data else "Live data"

    response = {
        "meta": dataset["meta"],
        "league": dataset["league"],
        "counts": counts,
        "source": source,
        "active_file": data_store.last_loaded_file.name if data_store.last_loaded_file else None,
        "generated_at": generated_at,
        "meta_banner": meta_banner,
        "last_loaded_at": data_store.last_loaded_at.isoformat() if data_store.last_loaded_at else None,
    }
    return jsonify(response), 200


@api_bp.post("/import")
def import_latest() -> tuple[dict[str, object], int]:
    """Reload the latest dataset from disk and persist a snapshot."""
    data_store: DataStore = current_app.config["DATA_STORE"]
    engine: Engine = current_app.config["DB_ENGINE"]

    before_snapshot = latest_snapshot(engine)
    before_payload: Dataset | None = before_snapshot["payload"] if before_snapshot else None

    # Optional upload support
    upload = request.files.get("file")
    if upload:
        data_dir = Path(data_store.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        dest = data_dir / f"upload_{int(datetime.now().timestamp())}.json"
        upload.save(dest)

    try:
        dataset: Dataset = data_store.load()
        save_snapshot(engine, dataset, data_store.last_loaded_file.name if data_store.last_loaded_file else None)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "import_failed", "detail": str(exc)}), 500

    diffs = _diff_datasets(before_payload, dataset)
    counts = {
        "divisions": len(dataset["divisions"]),
        "teams": len(dataset["teams"]),
        "players": len(dataset["players"]),
        "matches": len(dataset["matches"]),
        "locations": len(dataset["locations"]),
    }
    return (
        jsonify(
            {
                "status": "reloaded",
                "last_loaded_at": data_store.last_loaded_at.isoformat() if data_store.last_loaded_at else None,
                "source": data_store.last_loaded_file.name if data_store.last_loaded_file else None,
                "counts": counts,
                "diffs": diffs,
            }
        ),
        200,
    )


@api_bp.get("/updates")
def list_updates() -> tuple[dict[str, object], int]:
    """Return recent snapshots with computed diffs to the previous snapshot."""
    engine: Engine = current_app.config["DB_ENGINE"]
    try:
        snapshots = list_snapshots(engine, limit=20)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "snapshot_list_failed", "detail": str(exc)}), 500

    timeline: list[dict[str, object]] = []
    for idx, snap in enumerate(snapshots):
        payload: Dataset = snap["payload"]
        prev_payload: Dataset | None = snapshots[idx + 1]["payload"] if idx + 1 < len(snapshots) else None
        diffs = _diff_datasets(prev_payload, payload)
        timeline.append(
            {
                "id": snap["id"],
                "created_at": snap["created_at"].isoformat() if hasattr(snap["created_at"], "isoformat") else snap["created_at"],
                "source_file": snap.get("source_file"),
                "meta": snap.get("meta") or {},
                "counts": {
                    "divisions": len(payload.get("divisions", [])),
                    "teams": len(payload.get("teams", [])),
                    "players": len(payload.get("players", [])),
                    "matches": len(payload.get("matches", [])),
                    "locations": len(payload.get("locations", [])),
                },
                "diffs": diffs,
            }
        )

    return jsonify({"snapshots": timeline}), 200


# ---------- Onboarding (slim lookups) ----------
@api_bp.get("/onboarding/divisions")
def onboarding_divisions() -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        dataset: Dataset = data_store.ensure_loaded()
        divisions = dataset.get("divisions", []) or []
        payload = []
        for div in divisions:
            payload.append(
                {
                    "id": _as_str(div.get("id")),
                    "name": div.get("name") or div.get("title"),
                    "format": div.get("format"),
                    "day": div.get("night") or div.get("day"),
                    "location_name": div.get("location") or div.get("location_name"),
                }
            )
        return jsonify({"divisions": payload}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "onboarding_divisions_failed", "detail": str(exc)}), 500


@api_bp.get("/onboarding/teams")
def onboarding_teams() -> tuple[dict[str, object], int]:
    division_filter = request.args.get("division_id")
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        teams = data_store.all_teams()
        payload = []
        for team in teams:
            team_div_id = _first_present(team, ("division_id", "divisionId"))
            if division_filter and str(team_div_id) != division_filter:
                continue
            roster = data_store.players_for_team(_as_str(team.get("id")))
            payload.append(
                {
                    "id": _as_str(team.get("id")),
                    "name": team.get("name"),
                    "home_location": _first_present(team, ("location_id", "locationId", "home_location")),
                    "roster_count": len(roster),
                }
            )
        return jsonify({"teams": payload}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "onboarding_teams_failed", "detail": str(exc)}), 500


@api_bp.get("/onboarding/leagues")
def onboarding_leagues() -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        dataset: Dataset = data_store.ensure_loaded()
        league = dataset.get("league") or {}
        default = {
            "id": _as_str(league.get("id")) or "default",
            "name": league.get("name") or league.get("title") or "League",
        }
        return jsonify({"leagues": [default]}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "onboarding_leagues_failed", "detail": str(exc)}), 500


@api_bp.get("/onboarding/sessions")
def onboarding_sessions() -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        divisions = data_store.all_divisions()
        sessions = []
        for div in divisions:
            if div.get("session"):
                sessions.append(str(div.get("session")))
        unique_sessions = sorted(set(sessions))
        if not unique_sessions:
            unique_sessions = ["default"]
        payload = [{"id": sess, "name": sess} for sess in unique_sessions]
        return jsonify({"sessions": payload}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "onboarding_sessions_failed", "detail": str(exc)}), 500


# ---------- Helpers ----------
def _as_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


def _first_present(item: dict[str, object], keys: tuple[str, ...], default: object | None = None) -> object | None:
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return default


def _as_int(value: object | None, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:  # noqa: BLE001
        return default


def _ensure_list(value: object | None) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _diff_datasets(
    before: Dataset | None, after: Dataset
) -> dict[str, list[dict[str, object]]]:
    """Compute diffs: standings ranks, team points, player SL/win%, division moves."""
    if before is None:
        return {
            "teams_moved": [],
            "players_sl_changed": [],
            "standings_changed": [],
            "team_points_changed": [],
            "win_pct_swings": [],
        }

    before_teams = {str(team["id"]): team for team in before.get("teams", []) if "id" in team}
    after_teams = {str(team["id"]): team for team in after.get("teams", []) if "id" in team}

    teams_moved: list[dict[str, object]] = []
    for team_id, new_team in after_teams.items():
        old_team = before_teams.get(team_id)
        if not old_team:
            continue
        old_div = _first_present(old_team, ("division_id", "divisionId"))
        new_div = _first_present(new_team, ("division_id", "divisionId"))
        if old_div != new_div:
            teams_moved.append({"team_id": team_id, "from": old_div, "to": new_div})

    def _skill_level(player: dict[str, object]) -> object | None:
        return _first_present(player, ("sl", "skill_level", "skillLevel", "skill_level_9", "skill_level_8"))

    before_players = {str(p["id"]): p for p in before.get("players", []) if "id" in p}
    after_players = {str(p["id"]): p for p in after.get("players", []) if "id" in p}
    players_sl_changed: list[dict[str, object]] = []
    win_pct_swings: list[dict[str, object]] = []
    for player_id, new_player in after_players.items():
        old_player = before_players.get(player_id)
        if not old_player:
            continue
        old_sl = _skill_level(old_player)
        new_sl = _skill_level(new_player)
        if old_sl != new_sl:
            players_sl_changed.append({"player_id": player_id, "from": old_sl, "to": new_sl})

        old_win = None
        new_win = None
        if isinstance(old_player.get("stats_by_format"), dict):
            for fmt_stats in old_player["stats_by_format"].values():
                if isinstance(fmt_stats, dict) and "win_pct" in fmt_stats:
                    old_win = fmt_stats.get("win_pct")
                    break
        if isinstance(new_player.get("stats_by_format"), dict):
            for fmt_stats in new_player["stats_by_format"].values():
                if isinstance(fmt_stats, dict) and "win_pct" in fmt_stats:
                    new_win = fmt_stats.get("win_pct")
                    break
        if old_win is not None and new_win is not None and old_win != new_win:
            win_pct_swings.append({"player_id": player_id, "from": old_win, "to": new_win})

    def standings_map(dataset: Dataset) -> dict[str, dict[str, dict[str, object]]]:
        mapping: dict[str, dict[str, dict[str, object]]] = {}
        for division in dataset.get("divisions", []):
            div_id = str(division.get("id"))
            standings = division.get("standings") or []
            mapping[div_id] = {
                str(entry.get("team_id")): {"rank": entry.get("rank"), "points": entry.get("points")}
                for entry in standings
                if entry.get("team_id") is not None
            }
        return mapping

    before_standings = standings_map(before)
    after_standings = standings_map(after)
    standings_changed: list[dict[str, object]] = []
    team_points_changed: list[dict[str, object]] = []
    for div_id, teams in after_standings.items():
        for team_id, new_entry in teams.items():
            old_entry = before_standings.get(div_id, {}).get(team_id)
            if not old_entry:
                continue
            if new_entry.get("rank") != old_entry.get("rank"):
                standings_changed.append(
                    {"division_id": div_id, "team_id": team_id, "from": old_entry.get("rank"), "to": new_entry.get("rank")}
                )
            if new_entry.get("points") != old_entry.get("points"):
                team_points_changed.append(
                    {"division_id": div_id, "team_id": team_id, "from": old_entry.get("points"), "to": new_entry.get("points")}
                )

    return {
        "teams_moved": teams_moved,
        "players_sl_changed": players_sl_changed,
        "standings_changed": standings_changed,
        "team_points_changed": team_points_changed,
        "win_pct_swings": win_pct_swings,
    }


# ---------- Divisions ----------
@api_bp.get("/divisions")
def list_divisions() -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        divisions = data_store.all_divisions()
        response = []
        for division in divisions:
            division_id = _as_str(division.get("id"))
            team_ids = data_store.team_ids_for_division(division_id) if division_id else []
            response.append(
                {
                    "id": division_id,
                    "name": division.get("name") or division.get("title"),
                    "night": division.get("night"),
                    "format": division.get("format"),
                    "session": division.get("session"),
                    "team_ids": team_ids,
                }
            )
        return jsonify({"divisions": response}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "data_unavailable", "detail": str(exc)}), 503


@api_bp.get("/divisions/<division_id>")
def get_division(division_id: str) -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        division = data_store.get_division(division_id)
        if not division:
            return jsonify({"error": "not_found"}), 404

        team_ids = data_store.team_ids_for_division(division_id)
        payload = {
            "id": _as_str(division.get("id")),
            "name": division.get("name") or division.get("title"),
            "night": division.get("night"),
            "format": division.get("format"),
            "session": division.get("session"),
            "standings": division.get("standings") or [],
            "team_ids": team_ids,
        }
        return jsonify(payload), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "data_unavailable", "detail": str(exc)}), 503


# ---------- Teams ----------
def _player_summary(player: dict[str, object]) -> dict[str, object]:
    return {
        "id": _as_str(player.get("id")),
        "name": player.get("name") or player.get("full_name") or player.get("display_name"),
        "team_id": _first_present(player, ("team_id", "teamId")),
        "division_id": _first_present(player, ("division_id", "divisionId")),
    }


@api_bp.get("/teams/<team_id>")
def get_team(team_id: str) -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        team = data_store.get_team(team_id)
        if not team:
            return jsonify({"error": "not_found"}), 404

        roster: list[dict[str, object]] = []

        # Prefer roster derived from players dataset for accuracy.
        players_from_dataset = data_store.players_for_team(team_id)
        roster.extend(_player_summary(player) for player in players_from_dataset)

        # Merge in any roster ids listed on the team record itself.
        roster_ids = _ensure_list(team.get("player_ids") or team.get("players"))
        existing_ids = {member["id"] for member in roster if member["id"] is not None}
        for player_id in roster_ids:
            player = data_store.get_player(player_id)
            if player and _as_str(player.get("id")) not in existing_ids:
                roster.append(_player_summary(player))

        # Deduplicate by id while preserving order.
        seen: set[str | None] = set()
        deduped: list[dict[str, object]] = []
        for member in roster:
            member_id = member.get("id")
            if member_id in seen:
                continue
            seen.add(member_id)
            deduped.append(member)

        payload = {
            "id": _as_str(team.get("id")),
            "name": team.get("name"),
            "division_id": _first_present(team, ("division_id", "divisionId")),
            "location_id": _first_present(team, ("location_id", "locationId")),
            "roster": deduped,
        }
        return jsonify(payload), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "data_unavailable", "detail": str(exc)}), 503


# ---------- Players ----------
@api_bp.get("/players/<player_id>")
def get_player(player_id: str) -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        player = data_store.get_player(player_id)
        if not player:
            return jsonify({"error": "not_found"}), 404

        stats_source = (
            player.get("stats_by_format")
            or player.get("statsByFormat")
            or player.get("stats")
            or {}
        )
        stats_by_format = stats_source if isinstance(stats_source, dict) else {}

        payload = {
            "id": _as_str(player.get("id")),
            "name": player.get("name") or player.get("full_name") or player.get("display_name"),
            "team_id": _first_present(player, ("team_id", "teamId")),
            "division_id": _first_present(player, ("division_id", "divisionId")),
            "stats_by_format": stats_by_format,
        }
        return jsonify(payload), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "data_unavailable", "detail": str(exc)}), 503


# ---------- Matches ----------
def _match_date_filter_args() -> tuple[datetime | None, datetime | None]:
    def parse(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:  # noqa: BLE001
            return None

    date_from = parse(request.args.get("from"))
    date_to = parse(request.args.get("to"))
    return date_from, date_to


def _match_summary(match: dict[str, object]) -> dict[str, object]:
    home_score = _as_int(
        _first_present(match, ("home_score", "homeScore", "home_points", "homePoints"))
    )
    away_score = _as_int(
        _first_present(match, ("away_score", "awayScore", "away_points", "awayPoints"))
    )
    return {
        "id": _as_str(match.get("id")),
        "division_id": _first_present(match, ("division_id", "divisionId")),
        "home_team_id": _first_present(match, ("home_team_id", "homeTeamId")),
        "away_team_id": _first_present(match, ("away_team_id", "awayTeamId")),
        "played_at": match.get("played_at") or match.get("playedAt") or match.get("date"),
        "location_id": _first_present(match, ("location_id", "locationId")),
        "status": match.get("status") or match.get("state"),
        "score": {"home": home_score, "away": away_score},
    }


@api_bp.get("/matches")
def list_matches() -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        division_filter = request.args.get("division")
        team_filter = request.args.get("team")
        player_filter = request.args.get("player")
        date_from, date_to = _match_date_filter_args()
        matches = data_store.matches_filtered(
            division_id=division_filter,
            team_id=team_filter,
            player_id=player_filter,
            date_from=date_from,
            date_to=date_to,
        )
        summaries = [_match_summary(match) for match in matches]
        return jsonify({"matches": summaries}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "data_unavailable", "detail": str(exc)}), 503


def _expanded_sets(sets: list[dict[str, object]]) -> tuple[list[dict[str, object]], int, int]:
    expanded: list[dict[str, object]] = []
    home_points = 0
    away_points = 0
    for idx, set_row in enumerate(sets):
        home_score = _as_int(
            _first_present(set_row, ("home_score", "homeScore", "home_points", "homePoints"))
        )
        away_score = _as_int(
            _first_present(set_row, ("away_score", "awayScore", "away_points", "awayPoints"))
        )
        home_points += home_score
        away_points += away_score
        expanded.append(
            {
                "index": idx,
                "home_score": home_score,
                "away_score": away_score,
                "winner_team_id": _first_present(set_row, ("winner_team_id", "winnerTeamId")),
                "home_player_ids": _ensure_list(
                    _first_present(
                        set_row,
                        ("home_player_ids", "homePlayerIds", "home_players", "homePlayers"),
                    )
                ),
                "away_player_ids": _ensure_list(
                    _first_present(
                        set_row,
                        ("away_player_ids", "awayPlayerIds", "away_players", "awayPlayers"),
                    )
                ),
            }
        )
    return expanded, home_points, away_points


@api_bp.get("/matches/<match_id>")
def get_match(match_id: str) -> tuple[dict[str, object], int]:
    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        match = data_store.get_match(match_id)
        if not match:
            return jsonify({"error": "not_found"}), 404

        sets_raw = match.get("sets") if isinstance(match.get("sets"), list) else []
        sets, home_points, away_points = _expanded_sets(cast(list[dict[str, object]], sets_raw))

        payload = {
            "id": _as_str(match.get("id")),
            "division_id": _first_present(match, ("division_id", "divisionId")),
            "played_at": match.get("played_at") or match.get("playedAt") or match.get("date"),
            "location_id": _first_present(match, ("location_id", "locationId")),
            "teams": {
                "home": {
                    "id": _first_present(match, ("home_team_id", "homeTeamId")),
                    "score": _as_int(
                        _first_present(match, ("home_score", "homeScore", "home_points", "homePoints")),
                        default=home_points,
                    ),
                },
                "away": {
                    "id": _first_present(match, ("away_team_id", "awayTeamId")),
                    "score": _as_int(
                        _first_present(match, ("away_score", "awayScore", "away_points", "awayPoints")),
                        default=away_points,
                    ),
                },
            },
            "sets": sets,
            "totals": {
                "home": {"points": home_points, "sets": len(sets)},
                "away": {"points": away_points, "sets": len(sets)},
            },
        }
        return jsonify(payload), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "data_unavailable", "detail": str(exc)}), 503


# ---------- Search ----------
@api_bp.get("/search")
def search() -> tuple[dict[str, object], int]:
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"query": "", "divisions": [], "teams": [], "players": []}), 200

    data_store: DataStore = current_app.config["DATA_STORE"]
    try:
        q = query.lower()
        divisions = [
            {
                "id": _as_str(div.get("id")),
                "name": div.get("name") or div.get("title"),
                "night": div.get("night"),
                "format": div.get("format"),
                "session": div.get("session"),
            }
            for div in data_store.all_divisions()
            if (
                (isinstance(div.get("name"), str) and q in div["name"].lower())
                or (isinstance(div.get("title"), str) and q in div["title"].lower())
            )
        ]
        teams = [
            {
                "id": _as_str(team.get("id")),
                "name": team.get("name"),
                "division_id": _first_present(team, ("division_id", "divisionId")),
            }
            for team in data_store.all_teams()
            if isinstance(team.get("name"), str) and q in team["name"].lower()
        ]
        players = [
            _player_summary(player)
            for player in data_store.all_players()
            if (
                (isinstance(player.get("name"), str) and q in player["name"].lower())
                or (isinstance(player.get("full_name"), str) and q in player["full_name"].lower())
                or (isinstance(player.get("display_name"), str) and q in player["display_name"].lower())
            )
        ]

        return jsonify({"query": query, "divisions": divisions, "teams": teams, "players": players}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "data_unavailable", "detail": str(exc)}), 503
