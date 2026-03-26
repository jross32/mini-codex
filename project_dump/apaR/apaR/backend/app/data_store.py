from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict, cast
from zoneinfo import ZoneInfo


class Dataset(TypedDict):
    meta: dict[str, Any]
    league: dict[str, Any]
    divisions: list[dict[str, Any]]
    teams: list[dict[str, Any]]
    players: list[dict[str, Any]]
    matches: list[dict[str, Any]]
    locations: list[dict[str, Any]]


class DataStore:
    """Caches the latest dataset from disk and builds quick lookups."""

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.data: Dataset | None = None
        self.last_loaded_at: datetime | None = None
        self.last_loaded_file: Path | None = None
        self.is_mock_data: bool = False
        self._divisions_by_id: dict[str, dict[str, Any]] = {}
        self._teams_by_id: dict[str, dict[str, Any]] = {}
        self._players_by_id: dict[str, dict[str, Any]] = {}
        self._matches_by_id: dict[str, dict[str, Any]] = {}

    def ensure_loaded(self) -> Dataset:
        """Load the latest dataset if nothing is cached."""
        if self.data is None:
            return self.load()
        return self.data

    def get_dataset(self) -> Dataset:
        """Return the cached dataset, loading if needed."""
        return self.ensure_loaded()

    def all_divisions(self) -> list[dict[str, Any]]:
        return list(self.ensure_loaded()["divisions"])

    def all_teams(self) -> list[dict[str, Any]]:
        return list(self.ensure_loaded()["teams"])

    def all_players(self) -> list[dict[str, Any]]:
        return list(self.ensure_loaded()["players"])

    def all_matches(self) -> list[dict[str, Any]]:
        return list(self.ensure_loaded()["matches"])

    def load(self) -> Dataset:
        """Load, validate, and index the most recent JSON dataset."""
        dataset_path = self._latest_file()
        dataset = self._load_dataset(dataset_path)
        self._validate_top_level(dataset)
        self._build_indexes(dataset)

        # Track if using mock data
        mock_path = Path(__file__).parent.parent / "data" / "mock" / "leagueData.json"
        self.is_mock_data = dataset_path == mock_path

        # Ensure meta.source is set appropriately
        if "meta" not in dataset:
            dataset["meta"] = {}
        dataset["meta"]["source"] = "mock" if self.is_mock_data else dataset["meta"].get("source", "real")

        self.data = dataset
        self.last_loaded_file = dataset_path
        self.last_loaded_at = datetime.now(timezone.utc)
        return dataset

    def get_division(self, division_id: str | int) -> dict[str, Any] | None:
        self.ensure_loaded()
        return self._divisions_by_id.get(str(division_id))

    def get_team(self, team_id: str | int) -> dict[str, Any] | None:
        self.ensure_loaded()
        return self._teams_by_id.get(str(team_id))

    def get_player(self, player_id: str | int) -> dict[str, Any] | None:
        self.ensure_loaded()
        return self._players_by_id.get(str(player_id))

    def get_match(self, match_id: str | int) -> dict[str, Any] | None:
        self.ensure_loaded()
        return self._matches_by_id.get(str(match_id))

    def team_ids_for_division(self, division_id: str | int) -> list[str]:
        self.ensure_loaded()
        division_str = str(division_id)
        return [
            str(team_id)
            for team_id, team in self._teams_by_id.items()
            if self._match_id(team, ("division_id", "divisionId")) == division_str
        ]

    def players_for_team(self, team_id: str | int) -> list[dict[str, Any]]:
        self.ensure_loaded()
        team_str = str(team_id)
        return [
            player
            for player in self.all_players()
            if self._match_id(player, ("team_id", "teamId")) == team_str
        ]

    def matches_filtered(
        self,
        division_id: str | None = None,
        team_id: str | None = None,
        player_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict[str, Any]]:
        matches = self.all_matches()

        def parse_date(value: Any) -> datetime | None:
            if not value:
                return None
            try:
                return datetime.fromisoformat(str(value))
            except Exception:  # noqa: BLE001
                return None

        def match_within_date_range(match: dict[str, Any]) -> bool:
            when = (
                match.get("played_at")
                or match.get("playedAt")
                or match.get("date")
                or match.get("scheduled_at")
            )
            dt = parse_date(when)
            if date_from and dt and dt < date_from:
                return False
            if date_to and dt and dt > date_to:
                return False
            return True

        def match_division_filter(match: dict[str, Any]) -> bool:
            if not division_id:
                return True
            match_div = self._match_id(match, ("division_id", "divisionId"))
            return match_div == str(division_id)

        def match_team_filter(match: dict[str, Any]) -> bool:
            if not team_id:
                return True
            team_str = str(team_id)
            home = self._match_id(match, ("home_team_id", "homeTeamId"))
            away = self._match_id(match, ("away_team_id", "awayTeamId"))
            teams_field = match.get("team_ids") or match.get("teams") or []
            if isinstance(teams_field, dict):
                teams_field = list(teams_field.values())
            team_ids = [str(tid) for tid in teams_field] if isinstance(teams_field, list) else []
            return team_str in (home, away) or team_str in team_ids

        def match_player_filter(match: dict[str, Any]) -> bool:
            if not player_id:
                return True
            player_str = str(player_id)
            sets = match.get("sets") if isinstance(match.get("sets"), list) else []
            for set_row in sets:
                home_players = set_row.get("home_player_ids") or set_row.get("homePlayerIds") or []
                away_players = set_row.get("away_player_ids") or set_row.get("awayPlayerIds") or []
                if isinstance(home_players, dict):
                    home_players = list(home_players.values())
                if isinstance(away_players, dict):
                    away_players = list(away_players.values())
                home_ids = [str(pid) for pid in home_players] if isinstance(home_players, list) else []
                away_ids = [str(pid) for pid in away_players] if isinstance(away_players, list) else []
                if player_str in home_ids or player_str in away_ids:
                    return True

            # Fallback to generic player_ids field if present on match.
            generic_players = match.get("player_ids") or match.get("players") or []
            if isinstance(generic_players, dict):
                generic_players = list(generic_players.values())
            generic_ids = [str(pid) for pid in generic_players] if isinstance(generic_players, list) else []
            return player_str in generic_ids

        filtered = [
            match
            for match in matches
            if match_division_filter(match)
            and match_team_filter(match)
            and match_player_filter(match)
            and match_within_date_range(match)
        ]

        filtered.sort(
            key=lambda m: (
                parse_date(
                    m.get("played_at")
                    or m.get("playedAt")
                    or m.get("date")
                    or m.get("scheduled_at")
                )
                or datetime.fromtimestamp(0, tz=ZoneInfo("UTC"))
            ),
            reverse=True,
        )
        return filtered

    def _latest_file(self) -> Path:
        """Find latest dataset file, with fallback to mock data if active_dataset.json missing/empty."""
        # Check for active_dataset.json first (real data)
        active_file = self.data_dir / "active_dataset.json"
        if active_file.exists() and active_file.stat().st_size > 0:
            return active_file

        # Fallback to mock data if available
        mock_file = Path(__file__).parent.parent / "data" / "mock" / "leagueData.json"
        if mock_file.exists() and mock_file.stat().st_size > 0:
            return mock_file

        # Last resort: find any JSON file in data_dir by mtime (if data_dir exists)
        if self.data_dir.exists() and self.data_dir.is_dir():
            candidates = sorted(
                self.data_dir.glob("*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            if candidates:
                return candidates[0]

        # All options exhausted
        raise FileNotFoundError(
            f"No dataset found. Checked for active_dataset.json in {self.data_dir}, "
            f"mock data at {mock_file}, and JSON files in {self.data_dir}"
        )

    def _load_dataset(self, dataset_path: Path) -> Dataset:
        with dataset_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError(f"Dataset must be a JSON object: {dataset_path.name}")
        return cast(Dataset, loaded)

    def _validate_top_level(self, dataset: Dataset) -> None:
        required_keys = {"meta", "league", "divisions", "teams", "players", "matches", "locations"}
        missing = [key for key in required_keys if key not in dataset]
        if missing:
            raise ValueError(f"Dataset missing required keys: {', '.join(missing)}")
        # Ensure list-typed keys are lists to match expected schema relationships.
        for list_key in ("divisions", "teams", "players", "matches", "locations"):
            if not isinstance(dataset[list_key], list):
                raise ValueError(f"Dataset key '{list_key}' must be a list")

    def _build_indexes(self, dataset: Dataset) -> None:
        self._divisions_by_id = self._index_items(dataset["divisions"], "division")
        self._teams_by_id = self._index_items(dataset["teams"], "team")
        self._players_by_id = self._index_items(dataset["players"], "player")
        self._matches_by_id = self._index_items(dataset["matches"], "match")

    def _index_items(self, items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for item in items:
            if "id" not in item:
                raise ValueError(f"{label.title()} missing id field")
            item_id = str(item["id"])
            indexed[item_id] = item
        return indexed

    def _match_id(self, item: dict[str, Any], keys: tuple[str, str]) -> str | None:
        for key in keys:
            if key in item:
                return str(item[key])
        return None
