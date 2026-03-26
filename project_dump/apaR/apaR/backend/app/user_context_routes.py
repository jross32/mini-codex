from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, current_app

from .auth import auth_required, get_current_user, _error
from .models import UserContext
from .data_store import DataStore

user_ctx_bp = Blueprint("user_ctx", __name__)

VALID_ROLES = {"captain", "player", "fan"}


def _validate_division(division_id: str | None) -> tuple[bool, dict | None]:
    """Validate that division_id exists in the dataset."""
    if not division_id:
        return True, None
    
    data_store: DataStore = current_app.config.get("DATA_STORE")
    if not data_store:
        return False, _error("internal_error", "Data store not available.", 500)
    
    try:
        division = data_store.get_division(division_id)
        if not division:
            return False, _error("invalid_division", f"Division '{division_id}' does not exist.", 400, field="division_id")
        return True, None
    except Exception as exc:  # noqa: BLE001
        current_app.logger.error("Division validation error: %s", exc)
        return False, _error("validation_error", "Unable to validate division.", 500)


def _validate_team(team_id: str | None, division_id: str | None) -> tuple[bool, dict | None]:
    """Validate that team_id exists and belongs to division_id."""
    if not team_id:
        return True, None
    
    data_store: DataStore = current_app.config.get("DATA_STORE")
    if not data_store:
        return False, _error("internal_error", "Data store not available.", 500)
    
    try:
        team = data_store.get_team(team_id)
        if not team:
            return False, _error("invalid_team", f"Team '{team_id}' does not exist.", 400, field="team_id")
        
        # If division_id is specified, verify team belongs to it
        if division_id:
            team_division_id = team.get("division_id")
            if team_division_id != division_id:
                return False, _error("team_not_in_division", f"Team '{team_id}' does not belong to division '{division_id}'.", 400, field="team_id")
        
        return True, None
    except Exception as exc:  # noqa: BLE001
        current_app.logger.error("Team validation error: %s", exc)
        return False, _error("validation_error", "Unable to validate team.", 500)


@user_ctx_bp.get("/user/context")
@auth_required
def get_context():
    user = get_current_user()
    if not user:
        return _error("unauthorized", "Login required.", 401)
    context = user.context.to_dict() if user.context else None
    return jsonify({"ok": True, "context": context}), 200


@user_ctx_bp.put("/user/context")
@auth_required
def upsert_context():
    user = get_current_user()
    if not user:
        return _error("unauthorized", "Login required.", 401)

    data = request.get_json(silent=True) or {}
    league_id = data.get("league_id")
    division_id = data.get("division_id")
    team_id = data.get("team_id")
    role = data.get("role") or "captain"

    # Validate role
    if role not in VALID_ROLES:
        return _error("invalid_role", "Role must be captain, player, or fan.", 400, field="role")

    # Validate division_id if provided
    is_valid, error_response = _validate_division(division_id)
    if not is_valid:
        return error_response

    # Validate team_id if provided (must also belong to division if both provided)
    is_valid, error_response = _validate_team(team_id, division_id)
    if not is_valid:
        return error_response

    db_session = current_app.config["DB_SESSION"]
    now = datetime.now(timezone.utc)

    if user.context:
        ctx = user.context
        ctx.league_id = league_id or ctx.league_id
        ctx.division_id = division_id or ctx.division_id
        ctx.team_id = team_id or ctx.team_id
        ctx.role = role or ctx.role
        ctx.updated_at = now
    else:
        ctx = UserContext(
            user_id=user.id,
            league_id=league_id,
            division_id=division_id,
            team_id=team_id,
            role=role,
            created_at=now,
            updated_at=now,
        )
        db_session.add(ctx)
        user.context = ctx

    db_session.add(user)
    db_session.commit()
    return jsonify({"ok": True, "context": ctx.to_dict()}), 200


@user_ctx_bp.post("/onboarding/complete")
@auth_required
def complete_onboarding():
    """Mark onboarding complete for the current user."""
    user = get_current_user()
    if not user:
        return _error("unauthorized", "Login required.", 401)

    # Verify user has completed onboarding setup (division, team, role)
    if not user.context:
        return _error("incomplete_setup", "Complete division and team selection first.", 400)
    
    context = user.context
    
    # Validate that division exists
    is_valid, error_response = _validate_division(context.division_id)
    if not is_valid:
        return error_response
    
    # Validate that team exists and belongs to division
    is_valid, error_response = _validate_team(context.team_id, context.division_id)
    if not is_valid:
        return error_response
    
    # Validate role is set
    if not context.role or context.role not in VALID_ROLES:
        context.role = "player"  # Default role if missing/invalid

    db_session = current_app.config["DB_SESSION"]
    try:
        user.onboarding_completed = True
        user.updated_at = datetime.now(timezone.utc)
        db_session.add(user)
        db_session.commit()
    except Exception as exc:  # noqa: BLE001
        db_session.rollback()
        current_app.logger.error("complete_onboarding failed: %s", exc, exc_info=True)
        return _error("onboarding_failed", "Unable to finish onboarding right now.", 500)

    context_dict = user.context.to_dict() if user.context else None
    return jsonify({"ok": True, "user": user.to_dict(), "context": context_dict}), 200
