from __future__ import annotations

import os
import random
import re
import json
import hashlib
import base64
import secrets
import threading
import time
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import and_, case, func, inspect, or_, text
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "lifeos-dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///lifeos.db").replace(
    "postgres://", "postgresql://", 1
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

TOKEN_MAX_AGE_SECONDS = int(os.getenv("LIFEOS_TOKEN_MAX_AGE_SECONDS", "604800"))
RESET_TOKEN_MAX_AGE_SECONDS = int(os.getenv("LIFEOS_RESET_TOKEN_MAX_AGE_SECONDS", "3600"))
MIN_PASSWORD_LENGTH = 8
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,24}$")
DEFAULT_DEMO_PASSWORD = os.getenv("LIFEOS_DEMO_PASSWORD", "demo12345")
DEFAULT_TESTUSER1_PASSWORD = os.getenv("LIFEOS_TESTUSER1_PASSWORD", "testuser123")
DEFAULT_ALLYDEV_PASSWORD = os.getenv("LIFEOS_ALLYDEV_PASSWORD", "allydev123")
EXPOSE_RESET_TOKEN = os.getenv("LIFEOS_EXPOSE_RESET_TOKEN", "1").strip().lower() in {"1", "true", "yes", "on"}
NOTIFICATION_GOAL_WINDOW_DAYS = int(os.getenv("LIFEOS_NOTIFICATION_GOAL_WINDOW_DAYS", "5"))
NOTIFICATION_MAX_ITEMS = int(os.getenv("LIFEOS_NOTIFICATION_MAX_ITEMS", "12"))
RECURRING_WORKER_ENABLED = os.getenv("LIFEOS_RECURRING_WORKER_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
RECURRING_WORKER_INTERVAL_SECONDS = max(int(os.getenv("LIFEOS_RECURRING_WORKER_INTERVAL_SECONDS", "120")), 30)
RECURRING_DEFAULT_BACKFILL_DAYS = max(int(os.getenv("LIFEOS_RECURRING_DEFAULT_BACKFILL_DAYS", "1")), 1)
RECURRING_MAX_BACKFILL_DAYS = max(int(os.getenv("LIFEOS_RECURRING_MAX_BACKFILL_DAYS", "7")), 1)
REMINDER_DELIVERY_ENABLED = os.getenv("LIFEOS_REMINDER_DELIVERY_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
REMINDER_DELIVERY_INTERVAL_SECONDS = max(int(os.getenv("LIFEOS_REMINDER_DELIVERY_INTERVAL_SECONDS", "300")), 60)
REMINDER_DEFAULT_DIGEST_HOUR_UTC = max(min(int(os.getenv("LIFEOS_REMINDER_DEFAULT_DIGEST_HOUR_UTC", "14")), 23), 0)
REMINDER_EMAIL_PROVIDER = os.getenv("LIFEOS_REMINDER_EMAIL_PROVIDER", "console").strip().lower()
REMINDER_SMS_PROVIDER = os.getenv("LIFEOS_REMINDER_SMS_PROVIDER", "console").strip().lower()
SMTP_HOST = os.getenv("LIFEOS_SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("LIFEOS_SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("LIFEOS_SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("LIFEOS_SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("LIFEOS_SMTP_USE_TLS", "1").strip().lower() in {"1", "true", "yes", "on"}
SMTP_FROM_EMAIL = os.getenv("LIFEOS_SMTP_FROM_EMAIL", "noreply@lifeos.app").strip()
TWILIO_ACCOUNT_SID = os.getenv("LIFEOS_TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("LIFEOS_TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("LIFEOS_TWILIO_FROM_NUMBER", "").strip()
REMINDER_LOG_MAX_ROWS = max(int(os.getenv("LIFEOS_REMINDER_LOG_MAX_ROWS", "2500")), 250)
SPACE_INVITE_DEFAULT_HOURS = max(int(os.getenv("LIFEOS_SPACE_INVITE_DEFAULT_HOURS", "72")), 1)
SPACE_INVITE_MAX_HOURS = max(int(os.getenv("LIFEOS_SPACE_INVITE_MAX_HOURS", "720")), SPACE_INVITE_DEFAULT_HOURS)
SPACE_INVITE_EXPIRY_ALERT_WINDOW_HOURS = max(int(os.getenv("LIFEOS_SPACE_INVITE_EXPIRY_ALERT_WINDOW_HOURS", "24")), 1)
SPACE_INVITE_EXPIRY_ALERT_MAX_ITEMS = max(int(os.getenv("LIFEOS_SPACE_INVITE_EXPIRY_ALERT_MAX_ITEMS", "8")), 1)
SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC = max(
    min(int(os.getenv("LIFEOS_SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC", "22")), 23),
    0,
)
SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC = max(
    min(int(os.getenv("LIFEOS_SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC", "7")), 23),
    0,
)
SPACE_ACTIVITY_NOTIFICATION_WINDOW_HOURS = max(int(os.getenv("LIFEOS_SPACE_ACTIVITY_NOTIFICATION_WINDOW_HOURS", "36")), 1)
SPACE_ACTIVITY_NOTIFICATION_MAX_EVENTS = max(int(os.getenv("LIFEOS_SPACE_ACTIVITY_NOTIFICATION_MAX_EVENTS", "120")), 10)
SPACE_ACTIVITY_NOTIFICATION_MAX_SPACES = max(int(os.getenv("LIFEOS_SPACE_ACTIVITY_NOTIFICATION_MAX_SPACES", "6")), 1)
SPACE_AUDIT_LOG_DEFAULT_LIMIT = max(int(os.getenv("LIFEOS_SPACE_AUDIT_LOG_DEFAULT_LIMIT", "30")), 5)
SPACE_IMPORT_PREVIEW_DETAIL_LIMIT = max(int(os.getenv("LIFEOS_SPACE_IMPORT_PREVIEW_DETAIL_LIMIT", "24")), 6)
SPACE_IMPORT_REPLACE_CONFIRM_PREFIX = (
    str(os.getenv("LIFEOS_SPACE_IMPORT_REPLACE_CONFIRM_PREFIX", "REPLACE SPACE")).strip() or "REPLACE SPACE"
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    coins = db.Column(db.Integer, nullable=False, default=0)
    season_pass_premium = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class RevokedAuthToken(db.Model):
    __tablename__ = "revoked_auth_tokens"
    __table_args__ = (db.UniqueConstraint("token_hash", name="uq_revoked_auth_tokens_hash"),)

    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    revoked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)


class ReminderChannelSettings(db.Model):
    __tablename__ = "reminder_channel_settings"
    __table_args__ = (db.UniqueConstraint("user_id", name="uq_reminder_settings_user"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    in_app_enabled = db.Column(db.Boolean, nullable=False, default=True)
    email_enabled = db.Column(db.Boolean, nullable=False, default=False, index=True)
    sms_enabled = db.Column(db.Boolean, nullable=False, default=False, index=True)
    email_address = db.Column(db.String(160), nullable=True)
    phone_number = db.Column(db.String(32), nullable=True)
    digest_hour_utc = db.Column(db.Integer, nullable=False, default=REMINDER_DEFAULT_DIGEST_HOUR_UTC)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ReminderDeliveryLog(db.Model):
    __tablename__ = "reminder_delivery_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    channel = db.Column(db.String(20), nullable=False, index=True)
    recipient = db.Column(db.String(160), nullable=False)
    provider = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(20), nullable=False, index=True)
    subject = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    notification_count = db.Column(db.Integer, nullable=False, default=0)
    dedupe_key = db.Column(db.String(120), nullable=True, index=True)
    error_message = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class Space(db.Model):
    __tablename__ = "spaces"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    default_member_notification_mode = db.Column(db.String(24), nullable=False, default="all")
    notification_quiet_hours_enabled = db.Column(db.Boolean, nullable=False, default=False)
    notification_quiet_hours_start_utc = db.Column(
        db.Integer,
        nullable=False,
        default=SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC,
    )
    notification_quiet_hours_end_utc = db.Column(
        db.Integer,
        nullable=False,
        default=SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class SpaceMember(db.Model):
    __tablename__ = "space_members"
    __table_args__ = (db.UniqueConstraint("space_id", "user_id", name="uq_space_members_space_user"),)

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="member", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class SpaceTask(db.Model):
    __tablename__ = "space_tasks"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    completed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="todo", index=True)
    task_type = db.Column(db.String(20), nullable=False, default="task", index=True)
    xp_reward = db.Column(db.Integer, nullable=False, default=25)
    priority = db.Column(db.String(20), nullable=False, default="medium")
    due_on = db.Column(db.Date, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class SpaceInvite(db.Model):
    __tablename__ = "space_invites"
    __table_args__ = (db.UniqueConstraint("invite_token", name="uq_space_invites_token"),)

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    accepted_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, default="member", index=True)
    invite_token = db.Column(db.String(96), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    accepted_at = db.Column(db.DateTime, nullable=True, index=True)
    revoked_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class SpaceRoleTemplate(db.Model):
    __tablename__ = "space_role_templates"
    __table_args__ = (db.UniqueConstraint("space_id", "role", name="uq_space_role_templates_space_role"),)

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, index=True)
    display_name = db.Column(db.String(80), nullable=False)
    can_manage_space = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_members = db.Column(db.Boolean, nullable=False, default=False)
    can_assign_admin = db.Column(db.Boolean, nullable=False, default=False)
    can_delete_space = db.Column(db.Boolean, nullable=False, default=False)
    can_create_tasks = db.Column(db.Boolean, nullable=False, default=True)
    can_complete_tasks = db.Column(db.Boolean, nullable=False, default=True)
    can_manage_tasks = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_invites = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SpaceActivityEvent(db.Model):
    __tablename__ = "space_activity_events"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    entity_type = db.Column(db.String(40), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    summary = db.Column(db.String(255), nullable=False)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class SpaceNotificationPreference(db.Model):
    __tablename__ = "space_notification_preferences"
    __table_args__ = (db.UniqueConstraint("space_id", "user_id", name="uq_space_notification_preferences_space_user"),)

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("spaces.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    mode = db.Column(db.String(24), nullable=False, default="all", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecurringRule(db.Model):
    __tablename__ = "recurring_rules"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    task_type = db.Column(db.String(20), nullable=False, default="task", index=True)
    priority = db.Column(db.String(20), nullable=False, default="medium")
    xp_reward = db.Column(db.Integer, nullable=False, default=20)
    frequency = db.Column(db.String(20), nullable=False, default="daily", index=True)
    interval = db.Column(db.Integer, nullable=False, default=1)
    days_of_week = db.Column(db.String(32), nullable=True)
    start_on = db.Column(db.Date, nullable=True)
    end_on = db.Column(db.Date, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    last_generated_on = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="todo", index=True)
    task_type = db.Column(db.String(20), nullable=False, default="task", index=True)
    xp_reward = db.Column(db.Integer, nullable=False, default=20)
    priority = db.Column(db.String(20), nullable=False, default="medium")
    due_on = db.Column(db.Date, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True, index=True)
    recurrence_rule_id = db.Column(db.Integer, db.ForeignKey("recurring_rules.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Habit(db.Model):
    __tablename__ = "habits"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    current_streak = db.Column(db.Integer, nullable=False, default=0)
    longest_streak = db.Column(db.Integer, nullable=False, default=0)
    last_completed_on = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class HabitLog(db.Model):
    __tablename__ = "habit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False, index=True)
    completed_on = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    target_value = db.Column(db.Integer, nullable=False)
    current_value = db.Column(db.Integer, nullable=False, default=0)
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class XpLedger(db.Model):
    __tablename__ = "xp_ledger"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    source = db.Column(db.String(120), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class CoinLedger(db.Model):
    __tablename__ = "coin_ledger"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    source = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class AvatarProfile(db.Model):
    __tablename__ = "avatar_profiles"
    __table_args__ = (db.UniqueConstraint("user_id", name="uq_avatar_profiles_user"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body_type = db.Column(db.String(20), nullable=False, default="male")
    style = db.Column(db.String(30), nullable=False, default="urban")
    top = db.Column(db.String(40), nullable=False, default="hoodie_blue")
    bottom = db.Column(db.String(40), nullable=False, default="jeans_dark")
    accessory = db.Column(db.String(40), nullable=False, default="none")
    palette = db.Column(db.String(30), nullable=False, default="cool")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ShopPurchase(db.Model):
    __tablename__ = "shop_purchases"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    item_key = db.Column(db.String(80), nullable=False, index=True)
    category = db.Column(db.String(30), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    price_coins = db.Column(db.Integer, nullable=False)
    metadata_json = db.Column(db.Text, nullable=True)
    purchased_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    claimed_at = db.Column(db.DateTime, nullable=True, index=True)
    claimed_note = db.Column(db.String(255), nullable=True)


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"
    __table_args__ = (db.UniqueConstraint("user_id", "achievement_key", name="uq_user_achievements_user_key"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    achievement_key = db.Column(db.String(80), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(8), nullable=False, default="\U0001F3C5")
    rarity = db.Column(db.String(20), nullable=False, default="common", index=True)
    target_value = db.Column(db.Integer, nullable=False, default=1)
    unlocked_value = db.Column(db.Integer, nullable=False, default=1)
    reward_xp = db.Column(db.Integer, nullable=False, default=0)
    reward_coins = db.Column(db.Integer, nullable=False, default=0)
    unlocked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class ChallengeClaim(db.Model):
    __tablename__ = "challenge_claims"
    __table_args__ = (
        db.UniqueConstraint("user_id", "challenge_key", "window_type", "window_key", name="uq_challenge_claims_user_window"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    challenge_key = db.Column(db.String(80), nullable=False, index=True)
    window_type = db.Column(db.String(20), nullable=False, index=True)
    window_key = db.Column(db.String(40), nullable=False, index=True)
    challenge_title = db.Column(db.String(160), nullable=False)
    reward_xp = db.Column(db.Integer, nullable=False, default=0)
    reward_coins = db.Column(db.Integer, nullable=False, default=0)
    claimed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class SeasonPassClaim(db.Model):
    __tablename__ = "season_pass_claims"
    __table_args__ = (
        db.UniqueConstraint("user_id", "season_key", "tier", name="uq_season_pass_claims_user_tier"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    season_key = db.Column(db.String(20), nullable=False, index=True)
    tier = db.Column(db.Integer, nullable=False, index=True)
    reward_xp = db.Column(db.Integer, nullable=False, default=0)
    reward_coins = db.Column(db.Integer, nullable=False, default=0)
    claimed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class SeasonPassPremiumClaim(db.Model):
    __tablename__ = "season_pass_premium_claims"
    __table_args__ = (
        db.UniqueConstraint("user_id", "season_key", "tier", name="uq_season_pass_premium_claims_user_tier"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    season_key = db.Column(db.String(20), nullable=False, index=True)
    tier = db.Column(db.Integer, nullable=False, index=True)
    reward_xp = db.Column(db.Integer, nullable=False, default=0)
    reward_coins = db.Column(db.Integer, nullable=False, default=0)
    claimed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


TASK_TYPE_LABELS = {"task": "Daily Task", "habit": "Habit", "quest": "Quest"}
VALID_TASK_TYPES = {"task", "habit", "quest"}
VALID_TASK_PRIORITIES = {"low", "medium", "high"}
VALID_TASK_STATUSES = {"todo", "done"}
VALID_SPACE_TASK_TYPES = {"task", "quest"}
VALID_RECURRING_FREQUENCIES = {"daily", "weekly"}
VALID_REMINDER_CHANNELS = {"email", "sms"}
VALID_SPACE_ROLES = {"owner", "admin", "member"}
ASSIGNABLE_SPACE_ROLES = {"admin", "member"}
SPACE_MANAGE_ROLES = {"owner", "admin"}
SPACE_TEMPLATE_ROLES = ("owner", "admin", "member")
EDITABLE_SPACE_TEMPLATE_ROLES = {"admin", "member"}
SPACE_PERMISSION_KEYS = (
    "can_manage_space",
    "can_manage_members",
    "can_assign_admin",
    "can_delete_space",
    "can_create_tasks",
    "can_complete_tasks",
    "can_manage_tasks",
    "can_manage_invites",
)
DEFAULT_SPACE_ROLE_DISPLAY_NAMES = {
    "owner": "Owner",
    "admin": "Admin",
    "member": "Member",
}
SPACE_INVITE_ANALYTICS_ROLE_BUCKETS = ("member", "admin", "other")
SPACE_INVITE_ANALYTICS_ROLE_LABELS = {
    "member": "Member links",
    "admin": "Admin links",
    "other": "Other links",
}
SPACE_ACTIVITY_TASK_EVENT_TYPES = {
    "space_task_created",
    "space_task_updated",
    "space_task_completed",
    "space_task_deleted",
    "space_task_reopened",
}
SPACE_ACTIVITY_AUDIT_EVENT_TYPES = {
    "space_role_template_updated",
    "space_member_role_updated",
    "space_notification_default_updated",
    "space_notification_default_applied",
    "space_notification_quiet_hours_updated",
    "space_snapshot_imported",
}
SPACE_NOTIFICATION_MODE_LABELS = {
    "all": "All updates",
    "priority_only": "Priority only",
    "digest_only": "Digest only",
    "muted": "Muted",
}
SPACE_NOTIFICATION_MODE_DESCRIPTIONS = {
    "all": "Show all shared queue updates in reminders and digests.",
    "priority_only": "Only high-signal shared queue updates appear in reminders and digests.",
    "digest_only": "Hide shared queue updates in reminders, but keep them in digests.",
    "muted": "Hide shared queue updates in both reminders and digests.",
}
VALID_SPACE_NOTIFICATION_MODES = set(SPACE_NOTIFICATION_MODE_LABELS.keys())
DEFAULT_SPACE_NOTIFICATION_MODE = "all"
SPACE_ACTIVITY_EVENT_LABELS = {
    "space_task_created": "created",
    "space_task_updated": "updated",
    "space_task_completed": "completed",
    "space_task_deleted": "deleted",
    "space_task_reopened": "reopened",
}
DEFAULT_SPACE_ROLE_PERMISSIONS: dict[str, dict[str, bool]] = {
    "owner": {
        "can_manage_space": True,
        "can_manage_members": True,
        "can_assign_admin": True,
        "can_delete_space": True,
        "can_create_tasks": True,
        "can_complete_tasks": True,
        "can_manage_tasks": True,
        "can_manage_invites": True,
    },
    "admin": {
        "can_manage_space": True,
        "can_manage_members": True,
        "can_assign_admin": False,
        "can_delete_space": False,
        "can_create_tasks": True,
        "can_complete_tasks": True,
        "can_manage_tasks": True,
        "can_manage_invites": True,
    },
    "member": {
        "can_manage_space": False,
        "can_manage_members": False,
        "can_assign_admin": False,
        "can_delete_space": False,
        "can_create_tasks": True,
        "can_complete_tasks": True,
        "can_manage_tasks": False,
        "can_manage_invites": False,
    },
}
WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MOTIVATIONAL_QUOTES = [
    {"text": "Progress stacks up when you keep showing up.", "author": "LifeOS"},
    {"text": "Discipline is remembering what you want most.", "author": "David Campbell"},
    {"text": "Small steps done daily become big wins.", "author": "LifeOS"},
    {"text": "Action creates momentum. Momentum creates confidence.", "author": "LifeOS"},
    {"text": "Focus on the process and the results will follow.", "author": "LifeOS"},
]

DEFAULT_XP_RULES: dict[str, int] = {
    "task.complete.task": 20,
    "task.complete.habit": 15,
    "task.complete.quest": 90,
    "task.priority_bonus.low": 0,
    "task.priority_bonus.medium": 5,
    "task.priority_bonus.high": 10,
    "habit.complete.manual": 10,
    "habit.create": 3,
    "goal.create": 8,
    "goal.progress.increment": 8,
    "goal.progress.complete_bonus": 60,
}


def load_xp_rules() -> dict[str, int]:
    rules = dict(DEFAULT_XP_RULES)
    raw = os.getenv("LIFEOS_XP_RULES_JSON", "").strip()
    if not raw:
        return rules

    try:
        override_payload = json.loads(raw)
    except json.JSONDecodeError:
        return rules

    if not isinstance(override_payload, dict):
        return rules

    for key, value in override_payload.items():
        if not isinstance(key, str):
            continue
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            continue
        if parsed_value < 0:
            continue
        rules[key] = parsed_value
    return rules


XP_RULES = load_xp_rules()


DEFAULT_COIN_RULES: dict[str, int] = {
    "task.complete.task": 12,
    "task.complete.habit": 9,
    "task.complete.quest": 45,
    "habit.complete.manual": 6,
    "habit.create": 2,
    "goal.create": 4,
    "goal.progress.increment": 4,
    "goal.progress.complete_bonus": 20,
    "space.complete.task": 14,
    "space.complete.quest": 38,
}


def load_coin_rules() -> dict[str, int]:
    rules = dict(DEFAULT_COIN_RULES)
    raw = os.getenv("LIFEOS_COIN_RULES_JSON", "").strip()
    if not raw:
        return rules

    try:
        override_payload = json.loads(raw)
    except json.JSONDecodeError:
        return rules

    if not isinstance(override_payload, dict):
        return rules

    for key, value in override_payload.items():
        if not isinstance(key, str):
            continue
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            continue
        if parsed_value < 0:
            continue
        rules[key] = parsed_value
    return rules


COIN_RULES = load_coin_rules()


def xp_rule_value(rule_key: str, fallback: int = 0) -> int:
    value = XP_RULES.get(rule_key, fallback)
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return max(fallback, 0)


def coin_rule_value(rule_key: str, fallback: int = 0) -> int:
    value = COIN_RULES.get(rule_key, fallback)
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return max(fallback, 0)


def calculate_task_completion_xp(task: Task) -> tuple[int, dict[str, int]]:
    base = xp_rule_value(f"task.complete.{task.task_type}", xp_rule_value("task.complete.task", 20))
    priority_bonus = xp_rule_value(f"task.priority_bonus.{task.priority}", 0)

    calculated = max(base + priority_bonus, 1)
    override_used = 0

    # Keep backward compatibility for existing seeded/manual task XP values.
    if task.xp_reward and task.xp_reward > 0 and task.xp_reward != 20:
        override_used = task.xp_reward
        calculated = max(task.xp_reward, 1)

    return calculated, {"base": base, "priority_bonus": priority_bonus, "override": override_used}


DEFAULT_AVATAR_PROFILE: dict[str, str] = {
    "body_type": "male",
    "style": "urban",
    "top": "hoodie_blue",
    "bottom": "jeans_dark",
    "accessory": "none",
    "palette": "cool",
}

AVATAR_OPTION_GROUPS: dict[str, list[dict[str, Any]]] = {
    "body_type": [
        {"key": "male", "label": "Male", "icon": "\u2642"},
        {"key": "female", "label": "Female", "icon": "\u2640"},
        {"key": "nonbinary", "label": "Non-Binary", "icon": "\u26A7"},
    ],
    "style": [
        {"key": "urban", "label": "Classic Human", "icon": "\U0001F642"},
        {"key": "explorer", "label": "Explorer Human", "icon": "\U0001F9D1"},
        {
            "key": "dragon",
            "label": "Dragon Head",
            "icon": "\U0001F432",
            "unlock_item_key": "avatar_style_dragon",
            "unlock_item_keys": ["avatar_style_dragon", "avatar_set_dragon"],
        },
        {
            "key": "unicorn",
            "label": "Unicorn Head",
            "icon": "\U0001F984",
            "unlock_item_key": "avatar_style_unicorn",
            "unlock_item_keys": ["avatar_style_unicorn", "avatar_set_unicorn"],
        },
        {
            "key": "alien",
            "label": "Alien Head",
            "icon": "\U0001F47D",
            "unlock_item_key": "avatar_style_alien",
            "unlock_item_keys": ["avatar_style_alien", "avatar_set_alien"],
        },
        {"key": "cyber", "label": "Robot Head", "icon": "\U0001F916", "unlock_item_key": "avatar_style_cyber"},
        {"key": "royal", "label": "Royal Crown", "icon": "\U0001F451", "unlock_item_key": "avatar_style_royal"},
    ],
    "top": [
        {"key": "hoodie_blue", "label": "Blue Hoodie", "icon": "\U0001F455"},
        {"key": "jacket_black", "label": "Black Jacket", "icon": "\U0001F9E5"},
        {"key": "armor_plasma", "label": "Plasma Armor", "icon": "\U0001F6E1", "unlock_item_key": "avatar_top_armor_plasma"},
        {"key": "suit_white", "label": "White Suit", "icon": "\U0001F935", "unlock_item_key": "avatar_top_suit_white"},
    ],
    "bottom": [
        {"key": "jeans_dark", "label": "Dark Jeans", "icon": "\U0001F456"},
        {"key": "joggers_gray", "label": "Gray Joggers", "icon": "\U0001F45F"},
        {"key": "tactical_black", "label": "Tactical Black", "icon": "\U0001F97E", "unlock_item_key": "avatar_bottom_tactical_black"},
        {"key": "formal_navy", "label": "Formal Navy", "icon": "\U0001F45E", "unlock_item_key": "avatar_bottom_formal_navy"},
    ],
    "accessory": [
        {"key": "none", "label": "None", "icon": "\u26AA"},
        {"key": "glasses_round", "label": "Round Glasses", "icon": "\U0001F576"},
        {"key": "halo_neon", "label": "Neon Halo", "icon": "\U0001F607", "unlock_item_key": "avatar_accessory_halo_neon"},
        {"key": "cape_shadow", "label": "Shadow Cape", "icon": "\U0001F977", "unlock_item_key": "avatar_accessory_cape_shadow"},
    ],
    "palette": [
        {"key": "cool", "label": "Cool Blue", "icon": "\U0001F535"},
        {"key": "warm", "label": "Warm Amber", "icon": "\U0001F7E0"},
        {"key": "neon", "label": "Neon Pulse", "icon": "\U0001F7E2", "unlock_item_key": "avatar_palette_neon"},
        {"key": "sunset", "label": "Sunset", "icon": "\U0001F7E1", "unlock_item_key": "avatar_palette_sunset"},
    ],
}

AVATAR_SET_SLOT_KEYS: tuple[str, ...] = ("style", "top", "bottom", "accessory", "palette")
AVATAR_SET_PART_PRICES_BY_RARITY: dict[str, dict[str, int]] = {
    "common": {"style": 70, "top": 60, "bottom": 55, "accessory": 50, "palette": 45},
    "uncommon": {"style": 88, "top": 75, "bottom": 70, "accessory": 62, "palette": 55},
    "rare": {"style": 108, "top": 92, "bottom": 84, "accessory": 76, "palette": 68},
    "epic": {"style": 128, "top": 110, "bottom": 100, "accessory": 90, "palette": 80},
    "legendary": {"style": 150, "top": 128, "bottom": 116, "accessory": 102, "palette": 92},
}
AVATAR_SET_BUNDLE_PRICE_BY_RARITY: dict[str, int] = {
    "common": 230,
    "uncommon": 285,
    "rare": 345,
    "epic": 405,
    "legendary": 470,
}
AVATAR_THEME_SET_BLUEPRINTS: list[dict[str, Any]] = [
    {
        "key": "unicorn",
        "label": "Unicorn Majesty Set",
        "icon": "\U0001F984",
        "description": "Bright rainbow magic with a full unicorn look.",
        "rarity": "epic",
        "slots": {
            "style": {"key": "unicorn", "label": "Unicorn Head", "icon": "\U0001F984"},
            "top": {"key": "unicorn_mane_hoodie", "label": "Mane Hoodie", "icon": "\U0001F455"},
            "bottom": {"key": "unicorn_rainbow_leggings", "label": "Rainbow Leggings", "icon": "\U0001F308"},
            "accessory": {"key": "unicorn_star_horn", "label": "Star Horn Aura", "icon": "\u2728"},
            "palette": {"key": "unicorn_rainbow", "label": "Rainbow Glow", "icon": "\U0001F308"},
        },
    },
    {
        "key": "dragon",
        "label": "Dragon Scale Set",
        "icon": "\U0001F409",
        "description": "Scale armor, ember glow, and dragon energy.",
        "rarity": "epic",
        "slots": {
            "style": {"key": "dragon", "label": "Dragon Head", "icon": "\U0001F432"},
            "top": {"key": "dragon_scale_armor", "label": "Scale Armor", "icon": "\U0001F6E1"},
            "bottom": {"key": "dragon_tail_guard", "label": "Tail Guard", "icon": "\U0001F97E"},
            "accessory": {"key": "dragon_wing_cloak", "label": "Wing Cloak", "icon": "\U0001FAB6"},
            "palette": {"key": "dragon_ember", "label": "Ember Flame", "icon": "\U0001F525"},
        },
    },
    {
        "key": "phoenix",
        "label": "Phoenix Rebirth Set",
        "icon": "\U0001F525",
        "description": "Mythic firebird aesthetic with sunfire tones.",
        "rarity": "legendary",
        "slots": {
            "style": {"key": "phoenix_mythic", "label": "Phoenix Crown", "icon": "\U0001F525"},
            "top": {"key": "phoenix_flare_cloak", "label": "Flare Cloak", "icon": "\U0001F9E5"},
            "bottom": {"key": "phoenix_feather_greaves", "label": "Feather Greaves", "icon": "\U0001F9B6"},
            "accessory": {"key": "phoenix_aura", "label": "Rebirth Aura", "icon": "\u2728"},
            "palette": {"key": "phoenix_sunfire", "label": "Sunfire", "icon": "\U0001F31E"},
        },
    },
    {
        "key": "frost_wolf",
        "label": "Frost Wolf Set",
        "icon": "\U0001F43A",
        "description": "Icy alpha style with winter aura.",
        "rarity": "rare",
        "slots": {
            "style": {"key": "frost_wolf_alpha", "label": "Wolf Head", "icon": "\U0001F43A"},
            "top": {"key": "frost_wolf_fur_jacket", "label": "Fur Jacket", "icon": "\U0001F9E5"},
            "bottom": {"key": "frost_wolf_stride", "label": "Tundra Stride", "icon": "\U0001F45F"},
            "accessory": {"key": "frost_wolf_fang", "label": "Fang Charm", "icon": "\U0001F9B7"},
            "palette": {"key": "frost_wolf_ice", "label": "Glacial Blue", "icon": "\U0001F9CA"},
        },
    },
    {
        "key": "shadow_ninja",
        "label": "Shadow Ninja Set",
        "icon": "\U0001F977",
        "description": "Stealth-first ninja drip with dark highlights.",
        "rarity": "epic",
        "slots": {
            "style": {"key": "shadow_ninja_mask", "label": "Ninja Mask", "icon": "\U0001F977"},
            "top": {"key": "shadow_ninja_shroud", "label": "Shadow Shroud", "icon": "\U0001F9E5"},
            "bottom": {"key": "shadow_ninja_wraps", "label": "Silent Wraps", "icon": "\U0001F97E"},
            "accessory": {"key": "shadow_ninja_blade", "label": "Hidden Blade", "icon": "\U0001F5E1"},
            "palette": {"key": "shadow_ninja_midnight", "label": "Midnight Fade", "icon": "\U0001F311"},
        },
    },
    {
        "key": "cosmic_mage",
        "label": "Cosmic Mage Set",
        "icon": "\U0001F9D9",
        "description": "Nebula robe and arcane star power.",
        "rarity": "legendary",
        "slots": {
            "style": {"key": "cosmic_mage_visor", "label": "Arcane Visor", "icon": "\U0001F9D9"},
            "top": {"key": "cosmic_mage_robe", "label": "Nebula Robe", "icon": "\U0001F52E"},
            "bottom": {"key": "cosmic_mage_drape", "label": "Starlight Drape", "icon": "\U0001F320"},
            "accessory": {"key": "cosmic_mage_orb", "label": "Orbiting Orb", "icon": "\U0001F52E"},
            "palette": {"key": "cosmic_mage_nebula", "label": "Nebula Mist", "icon": "\U0001F30C"},
        },
    },
    {
        "key": "pirate_captain",
        "label": "Pirate Captain Set",
        "icon": "\U0001F3F4",
        "description": "Sea-legend captain gear and tide colors.",
        "rarity": "rare",
        "slots": {
            "style": {"key": "pirate_captain_hat", "label": "Captain Hat", "icon": "\U0001F3A9"},
            "top": {"key": "pirate_captain_coat", "label": "Captain Coat", "icon": "\U0001F9E5"},
            "bottom": {"key": "pirate_captain_boots", "label": "Deck Boots", "icon": "\U0001F462"},
            "accessory": {"key": "pirate_captain_compass", "label": "Golden Compass", "icon": "\U0001F9ED"},
            "palette": {"key": "pirate_captain_tide", "label": "Deep Tide", "icon": "\U0001F30A"},
        },
    },
    {
        "key": "samurai_storm",
        "label": "Samurai Storm Set",
        "icon": "\U00002694",
        "description": "Blade-ready samurai armor with storm tones.",
        "rarity": "epic",
        "slots": {
            "style": {"key": "samurai_storm_helm", "label": "Storm Helm", "icon": "\U00002694"},
            "top": {"key": "samurai_storm_armor", "label": "Samurai Armor", "icon": "\U0001F6E1"},
            "bottom": {"key": "samurai_storm_plates", "label": "Armored Plates", "icon": "\U0001F97E"},
            "accessory": {"key": "samurai_storm_banner", "label": "Clan Banner", "icon": "\U0001F38F"},
            "palette": {"key": "samurai_storm_lightning", "label": "Lightning Gray", "icon": "\u26A1"},
        },
    },
    {
        "key": "jungle_druid",
        "label": "Jungle Druid Set",
        "icon": "\U0001F333",
        "description": "Nature-focused set with vine and leaf details.",
        "rarity": "rare",
        "slots": {
            "style": {"key": "jungle_druid_antlers", "label": "Druid Antlers", "icon": "\U0001F333"},
            "top": {"key": "jungle_druid_tunic", "label": "Canopy Tunic", "icon": "\U0001F455"},
            "bottom": {"key": "jungle_druid_vines", "label": "Vine Wraps", "icon": "\U0001F331"},
            "accessory": {"key": "jungle_druid_totem", "label": "Forest Totem", "icon": "\U0001F52E"},
            "palette": {"key": "jungle_druid_canopy", "label": "Canopy Green", "icon": "\U0001F7E2"},
        },
    },
    {
        "key": "galactic_pilot",
        "label": "Galactic Pilot Set",
        "icon": "\U0001F680",
        "description": "Spaceflight pilot gear with neon plasma accents.",
        "rarity": "epic",
        "slots": {
            "style": {"key": "galactic_pilot_helmet", "label": "Pilot Helmet", "icon": "\U0001F6F8"},
            "top": {"key": "galactic_pilot_jacket", "label": "Pilot Jacket", "icon": "\U0001F9E5"},
            "bottom": {"key": "galactic_pilot_thrusters", "label": "Thruster Boots", "icon": "\U0001F45F"},
            "accessory": {"key": "galactic_pilot_hud", "label": "HUD Visor", "icon": "\U0001F5A5"},
            "palette": {"key": "galactic_pilot_plasma", "label": "Plasma Glow", "icon": "\U0001F535"},
        },
    },
    {
        "key": "steampunk",
        "label": "Steampunk Gear Set",
        "icon": "\u2699",
        "description": "Brass and gears with a classic steampunk vibe.",
        "rarity": "rare",
        "slots": {
            "style": {"key": "steampunk_goggles", "label": "Gear Goggles", "icon": "\U0001F576"},
            "top": {"key": "steampunk_coat", "label": "Inventor Coat", "icon": "\U0001F9E5"},
            "bottom": {"key": "steampunk_gears", "label": "Gear Trousers", "icon": "\U0001F97E"},
            "accessory": {"key": "steampunk_drone", "label": "Clockwork Drone", "icon": "\U0001F916"},
            "palette": {"key": "steampunk_brass", "label": "Brass Tone", "icon": "\U0001F7E4"},
        },
    },
    {
        "key": "crystal_knight",
        "label": "Crystal Knight Set",
        "icon": "\U0001F48E",
        "description": "Prismatic plate armor and crystal highlights.",
        "rarity": "legendary",
        "slots": {
            "style": {"key": "crystal_knight_crown", "label": "Crystal Crown", "icon": "\U0001F48E"},
            "top": {"key": "crystal_knight_plate", "label": "Crystal Plate", "icon": "\U0001F6E1"},
            "bottom": {"key": "crystal_knight_sabaton", "label": "Crystal Sabaton", "icon": "\U0001F45E"},
            "accessory": {"key": "crystal_knight_shard", "label": "Shard Aura", "icon": "\u2728"},
            "palette": {"key": "crystal_knight_prism", "label": "Prism Light", "icon": "\U0001F308"},
        },
    },
    {
        "key": "ocean_guardian",
        "label": "Ocean Guardian Set",
        "icon": "\U0001F30A",
        "description": "Sea guardian armor with aqua details.",
        "rarity": "rare",
        "slots": {
            "style": {"key": "ocean_guardian_tidehelm", "label": "Tide Helm", "icon": "\U0001F433"},
            "top": {"key": "ocean_guardian_shellmail", "label": "Shell Mail", "icon": "\U0001F41A"},
            "bottom": {"key": "ocean_guardian_fins", "label": "Wave Striders", "icon": "\U0001F9B6"},
            "accessory": {"key": "ocean_guardian_trident", "label": "Trident Sigil", "icon": "\U0001F531"},
            "palette": {"key": "ocean_guardian_aqua", "label": "Aqua Glow", "icon": "\U0001F7E6"},
        },
    },
    {
        "key": "desert_nomad",
        "label": "Desert Nomad Set",
        "icon": "\U0001F42A",
        "description": "Heat-ready nomad robe with sandstorm palette.",
        "rarity": "uncommon",
        "slots": {
            "style": {"key": "desert_nomad_wrap", "label": "Nomad Wrap", "icon": "\U0001F9E3"},
            "top": {"key": "desert_nomad_robe", "label": "Nomad Robe", "icon": "\U0001F455"},
            "bottom": {"key": "desert_nomad_sandboots", "label": "Sand Boots", "icon": "\U0001F462"},
            "accessory": {"key": "desert_nomad_lantern", "label": "Travel Lantern", "icon": "\U0001F3EE"},
            "palette": {"key": "desert_nomad_dune", "label": "Dune Gold", "icon": "\U0001F7E1"},
        },
    },
    {
        "key": "thunder_rider",
        "label": "Thunder Rider Set",
        "icon": "\u26A1",
        "description": "High-speed electric rider outfit.",
        "rarity": "epic",
        "slots": {
            "style": {"key": "thunder_rider_visor", "label": "Rider Visor", "icon": "\u26A1"},
            "top": {"key": "thunder_rider_jacket", "label": "Volt Jacket", "icon": "\U0001F9E5"},
            "bottom": {"key": "thunder_rider_tracks", "label": "Storm Tracks", "icon": "\U0001F45F"},
            "accessory": {"key": "thunder_rider_arc", "label": "Arc Module", "icon": "\U0001F50B"},
            "palette": {"key": "thunder_rider_storm", "label": "Storm Neon", "icon": "\U0001F7EA"},
        },
    },
]


def normalize_avatar_set_rarity(value: Any) -> str:
    candidate = str(value or "rare").strip().lower()
    return candidate if candidate in AVATAR_SET_PART_PRICES_BY_RARITY else "rare"


def avatar_set_item_key(set_key: str) -> str:
    return f"avatar_set_{set_key}"


def avatar_piece_item_key(slot: str, set_key: str) -> str:
    return f"avatar_{slot}_{set_key}"


def build_avatar_theme_assets() -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_options: dict[str, list[dict[str, Any]]] = {slot: [] for slot in AVATAR_SET_SLOT_KEYS}
    generated_shop_items: list[dict[str, Any]] = []
    set_presets: list[dict[str, Any]] = []

    for set_row in AVATAR_THEME_SET_BLUEPRINTS:
        set_key = str(set_row.get("key", "")).strip().lower()
        if not set_key:
            continue
        set_label = str(set_row.get("label", set_key)).strip() or set_key
        set_icon = str(set_row.get("icon", "\u2728")).strip() or "\u2728"
        set_description = str(set_row.get("description", f"Unlock the full {set_label}.")).strip()
        set_rarity = normalize_avatar_set_rarity(set_row.get("rarity"))
        piece_prices = AVATAR_SET_PART_PRICES_BY_RARITY.get(set_rarity, AVATAR_SET_PART_PRICES_BY_RARITY["rare"])
        set_price = int(AVATAR_SET_BUNDLE_PRICE_BY_RARITY.get(set_rarity, AVATAR_SET_BUNDLE_PRICE_BY_RARITY["rare"]))
        bundle_item_key = avatar_set_item_key(set_key)
        slot_rows = set_row.get("slots", {})
        if not isinstance(slot_rows, dict):
            continue

        preset_slots: dict[str, str] = {}
        for slot in AVATAR_SET_SLOT_KEYS:
            option_row = slot_rows.get(slot)
            if not isinstance(option_row, dict):
                continue
            option_key = str(option_row.get("key", "")).strip().lower()
            if not option_key:
                continue
            option_label = str(option_row.get("label", option_key)).strip() or option_key
            option_icon = str(option_row.get("icon", "\u25C6")).strip() or "\u25C6"
            piece_item_key = avatar_piece_item_key(slot, set_key)
            unlock_keys = [piece_item_key, bundle_item_key]

            generated_options[slot].append(
                {
                    "key": option_key,
                    "label": option_label,
                    "icon": option_icon,
                    "unlock_item_key": piece_item_key,
                    "unlock_item_keys": unlock_keys,
                    "set_key": set_key,
                }
            )
            generated_shop_items.append(
                {
                    "item_key": piece_item_key,
                    "title": f"{set_label}: {option_label}",
                    "description": f"Unlock {option_label} for the {set_label}.",
                    "category": "avatar",
                    "price_coins": int(piece_prices.get(slot, 90)),
                    "repeatable": False,
                    "reward_type": "avatar_unlock",
                    "unlock_slot": slot,
                    "unlock_value": option_key,
                    "rarity": set_rarity,
                    "always_available": True,
                    "daily_stock": 260,
                    "set_key": set_key,
                    "set_label": set_label,
                }
            )
            preset_slots[slot] = option_key

        if len(preset_slots) < len(AVATAR_SET_SLOT_KEYS):
            continue

        generated_shop_items.append(
            {
                "item_key": bundle_item_key,
                "title": f"{set_label} Bundle",
                "description": f"Unlock the full {set_label} (all 5 parts) in one purchase.",
                "category": "avatar",
                "price_coins": set_price,
                "repeatable": False,
                "reward_type": "avatar_set_unlock",
                "unlock_set_key": set_key,
                "rarity": set_rarity,
                "always_available": True,
                "daily_stock": 180,
                "set_key": set_key,
                "set_label": set_label,
            }
        )
        set_presets.append(
            {
                "key": set_key,
                "label": set_label,
                "icon": set_icon,
                "description": set_description,
                "set_item_key": bundle_item_key,
                "slots": preset_slots,
            }
        )
    return generated_options, generated_shop_items, set_presets


def option_unlock_keys_from_row(option_row: dict[str, Any]) -> list[str]:
    raw_keys: list[str] = []
    single_key = str(option_row.get("unlock_item_key", "")).strip()
    if single_key:
        raw_keys.append(single_key)
    multi_keys = option_row.get("unlock_item_keys")
    if isinstance(multi_keys, (list, tuple, set)):
        for value in multi_keys:
            candidate = str(value or "").strip()
            if candidate:
                raw_keys.append(candidate)
    return sorted(set(raw_keys))


AVATAR_THEME_OPTIONS_BY_SLOT, AVATAR_THEME_SHOP_ITEMS, AVATAR_THEME_SET_PRESETS = build_avatar_theme_assets()
for _slot, _options in AVATAR_THEME_OPTIONS_BY_SLOT.items():
    slot_rows = AVATAR_OPTION_GROUPS.setdefault(_slot, [])
    slot_index = {
        str(row.get("key", "")).strip().lower(): row
        for row in slot_rows
        if isinstance(row, dict) and str(row.get("key", "")).strip()
    }
    for generated_option in _options:
        generated_key = str(generated_option.get("key", "")).strip().lower()
        if not generated_key:
            continue
        existing_option = slot_index.get(generated_key)
        if existing_option is None:
            slot_rows.append(generated_option)
            slot_index[generated_key] = generated_option
            continue
        merged_unlock_keys = sorted(
            set(option_unlock_keys_from_row(existing_option)) | set(option_unlock_keys_from_row(generated_option))
        )
        if merged_unlock_keys:
            existing_option["unlock_item_key"] = merged_unlock_keys[0]
            existing_option["unlock_item_keys"] = merged_unlock_keys
        if not existing_option.get("icon") and generated_option.get("icon"):
            existing_option["icon"] = generated_option.get("icon")
        if not existing_option.get("label") and generated_option.get("label"):
            existing_option["label"] = generated_option.get("label")
        if generated_option.get("set_key"):
            existing_option["set_key"] = generated_option.get("set_key")

AVATAR_SET_PRESETS: list[dict[str, Any]] = AVATAR_THEME_SET_PRESETS

SEASON_PASS_PREMIUM_SHOP_ITEM_KEY = "season_pass_premium_unlock"

SHOP_ITEMS: list[dict[str, Any]] = [
    {
        "item_key": "reward_coffee_break",
        "title": "Coffee Break",
        "description": "Treat yourself to a coffee or tea break.",
        "category": "self_reward",
        "price_coins": 45,
        "repeatable": True,
        "reward_type": "self_reward",
        "rarity": "common",
        "always_available": True,
        "daily_stock": 250,
        "user_daily_limit": 3,
    },
    {
        "item_key": "reward_rest_day",
        "title": "Light Day Pass",
        "description": "Take one intentionally lighter productivity day.",
        "category": "self_reward",
        "price_coins": 90,
        "repeatable": True,
        "reward_type": "self_reward",
        "rarity": "uncommon",
        "daily_stock": 80,
        "user_daily_limit": 1,
    },
    {
        "item_key": "reward_movie_night",
        "title": "Movie Night",
        "description": "Redeem for a movie night without guilt.",
        "category": "self_reward",
        "price_coins": 140,
        "repeatable": True,
        "reward_type": "self_reward",
        "rarity": "rare",
        "daily_stock": 40,
        "user_daily_limit": 1,
    },
    {
        "item_key": "reward_new_book",
        "title": "Buy a New Book",
        "description": "Pick up a book you have been wanting to read.",
        "category": "self_reward",
        "price_coins": 180,
        "repeatable": True,
        "reward_type": "self_reward",
        "rarity": "rare",
        "daily_stock": 35,
        "user_daily_limit": 1,
    },
    {
        "item_key": SEASON_PASS_PREMIUM_SHOP_ITEM_KEY,
        "title": "Season Pass Premium Track",
        "description": "Unlock the premium season pass reward track for this account.",
        "category": "season_pass",
        "price_coins": 320,
        "repeatable": False,
        "reward_type": "season_pass_premium_unlock",
        "rarity": "legendary",
        "always_available": True,
        "daily_stock": 500,
    },
    {
        "item_key": "avatar_style_cyber",
        "title": "Cyber Runner Style",
        "description": "Unlock the Cyber Runner style preset.",
        "category": "avatar",
        "price_coins": 120,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "style",
        "unlock_value": "cyber",
        "rarity": "uncommon",
        "always_available": True,
        "daily_stock": 120,
    },
    {
        "item_key": "avatar_style_royal",
        "title": "Royal Style",
        "description": "Unlock the Royal style preset.",
        "category": "avatar",
        "price_coins": 180,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "style",
        "unlock_value": "royal",
        "rarity": "rare",
        "daily_stock": 70,
    },
    {
        "item_key": "avatar_style_alien",
        "title": "Alien Head Style",
        "description": "Unlock the Alien head style.",
        "category": "avatar",
        "price_coins": 145,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "style",
        "unlock_value": "alien",
        "rarity": "rare",
        "always_available": True,
        "daily_stock": 95,
    },
    {
        "item_key": "avatar_top_armor_plasma",
        "title": "Plasma Armor Top",
        "description": "Unlock the Plasma Armor top.",
        "category": "avatar",
        "price_coins": 130,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "top",
        "unlock_value": "armor_plasma",
        "rarity": "rare",
        "daily_stock": 65,
    },
    {
        "item_key": "avatar_top_suit_white",
        "title": "White Suit Top",
        "description": "Unlock the White Suit top.",
        "category": "avatar",
        "price_coins": 155,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "top",
        "unlock_value": "suit_white",
        "rarity": "epic",
        "daily_stock": 45,
    },
    {
        "item_key": "avatar_bottom_tactical_black",
        "title": "Tactical Bottom",
        "description": "Unlock Tactical Black pants.",
        "category": "avatar",
        "price_coins": 110,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "bottom",
        "unlock_value": "tactical_black",
        "rarity": "uncommon",
        "daily_stock": 110,
    },
    {
        "item_key": "avatar_bottom_formal_navy",
        "title": "Formal Navy Bottom",
        "description": "Unlock Formal Navy pants.",
        "category": "avatar",
        "price_coins": 120,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "bottom",
        "unlock_value": "formal_navy",
        "rarity": "rare",
        "daily_stock": 80,
    },
    {
        "item_key": "avatar_accessory_halo_neon",
        "title": "Neon Halo",
        "description": "Unlock Neon Halo accessory.",
        "category": "avatar",
        "price_coins": 95,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "accessory",
        "unlock_value": "halo_neon",
        "rarity": "uncommon",
        "daily_stock": 120,
    },
    {
        "item_key": "avatar_accessory_cape_shadow",
        "title": "Shadow Cape",
        "description": "Unlock Shadow Cape accessory.",
        "category": "avatar",
        "price_coins": 150,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "accessory",
        "unlock_value": "cape_shadow",
        "rarity": "epic",
        "daily_stock": 50,
    },
    {
        "item_key": "avatar_palette_neon",
        "title": "Neon Palette",
        "description": "Unlock the Neon palette for your avatar.",
        "category": "avatar",
        "price_coins": 85,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "palette",
        "unlock_value": "neon",
        "rarity": "uncommon",
        "daily_stock": 130,
    },
    {
        "item_key": "avatar_palette_sunset",
        "title": "Sunset Palette",
        "description": "Unlock the Sunset palette for your avatar.",
        "category": "avatar",
        "price_coins": 85,
        "repeatable": False,
        "reward_type": "avatar_unlock",
        "unlock_slot": "palette",
        "unlock_value": "sunset",
        "rarity": "uncommon",
        "daily_stock": 130,
    },
]

_existing_shop_item_keys: set[str] = {
    str(item.get("item_key", "")).strip().lower()
    for item in SHOP_ITEMS
    if isinstance(item, dict) and str(item.get("item_key", "")).strip()
}
for _generated_item in AVATAR_THEME_SHOP_ITEMS:
    _generated_item_key = str(_generated_item.get("item_key", "")).strip().lower()
    if not _generated_item_key or _generated_item_key in _existing_shop_item_keys:
        continue
    SHOP_ITEMS.append(_generated_item)
    _existing_shop_item_keys.add(_generated_item_key)

SHOP_ITEMS_BY_KEY: dict[str, dict[str, Any]] = {item["item_key"]: item for item in SHOP_ITEMS}
AVATAR_SET_PRESETS_BY_KEY: dict[str, dict[str, Any]] = {
    str(set_row.get("key", "")).strip().lower(): set_row
    for set_row in AVATAR_SET_PRESETS
    if isinstance(set_row, dict) and str(set_row.get("key", "")).strip()
}
SHOP_CATEGORY_LABELS: dict[str, str] = {
    "self_reward": "Real-World Rewards",
    "season_pass": "Season Pass",
    "avatar": "Avatar Unlocks",
}
SHOP_CATEGORY_ORDER: dict[str, int] = {
    "season_pass": 0,
    "self_reward": 1,
    "avatar": 2,
}
SHOP_RARITY_LABELS: dict[str, str] = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",
    "epic": "Epic",
    "legendary": "Legendary",
}
SHOP_RARITY_ORDER: dict[str, int] = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}
SHOP_RARITY_ROTATION_BIAS: dict[str, int] = {
    "common": 0,
    "uncommon": 4_000_000,
    "rare": 14_000_000,
    "epic": 35_000_000,
    "legendary": 70_000_000,
}
SHOP_ROTATION_CATEGORY_SLOTS: dict[str, int] = {
    "self_reward": 2,
    "season_pass": 1,
    "avatar": 4,
}
SHOP_ROTATION_FALLBACK_SLOTS = 2
AVATAR_OPTION_INDEX: dict[str, dict[str, dict[str, Any]]] = {
    slot: {option["key"]: option for option in options}
    for slot, options in AVATAR_OPTION_GROUPS.items()
}
ACHIEVEMENT_DEFINITIONS: list[dict[str, Any]] = [
    {
        "key": "first_completion",
        "title": "First Win",
        "description": "Complete your first task, habit, or quest.",
        "icon": "\u2705",
        "metric": "task_done_total",
        "target": 1,
        "rarity": "common",
        "reward_xp": 20,
        "reward_coins": 10,
    },
    {
        "key": "xp_apprentice",
        "title": "XP Apprentice",
        "description": "Earn 1,000 total XP.",
        "icon": "\u2B50",
        "metric": "xp_total",
        "target": 1_000,
        "rarity": "uncommon",
        "reward_xp": 50,
        "reward_coins": 25,
    },
    {
        "key": "quest_hunter",
        "title": "Quest Hunter",
        "description": "Complete 5 quests.",
        "icon": "\U0001F9ED",
        "metric": "quest_done_total",
        "target": 5,
        "rarity": "rare",
        "reward_xp": 80,
        "reward_coins": 35,
    },
    {
        "key": "streak_guardian",
        "title": "Streak Guardian",
        "description": "Reach a 7-day habit streak.",
        "icon": "\U0001F525",
        "metric": "habit_streak_best",
        "target": 7,
        "rarity": "rare",
        "reward_xp": 100,
        "reward_coins": 40,
    },
    {
        "key": "shop_patron",
        "title": "Shop Patron",
        "description": "Spend 500 coins in the shop.",
        "icon": "\U0001FA99",
        "metric": "coins_spent_total",
        "target": 500,
        "rarity": "epic",
        "reward_xp": 120,
        "reward_coins": 50,
    },
    {
        "key": "avatar_collector",
        "title": "Avatar Collector",
        "description": "Unlock 4 avatar cosmetics.",
        "icon": "\U0001F9D1",
        "metric": "avatar_unlock_owned_total",
        "target": 4,
        "rarity": "epic",
        "reward_xp": 140,
        "reward_coins": 60,
    },
]
ACHIEVEMENT_DEFINITIONS_BY_KEY: dict[str, dict[str, Any]] = {row["key"]: row for row in ACHIEVEMENT_DEFINITIONS}
ACHIEVEMENT_RARITY_ORDER: dict[str, int] = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
CHALLENGE_DAILY_TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "daily_tasks_3",
        "title": "Daily Sprint",
        "description": "Complete 3 tasks today.",
        "metric": "task_done_total",
        "target": 3,
        "reward_xp": 35,
        "reward_coins": 16,
    },
    {
        "key": "daily_habits_2",
        "title": "Habit Lock-in",
        "description": "Complete 2 habits today.",
        "metric": "habit_done_total",
        "target": 2,
        "reward_xp": 30,
        "reward_coins": 14,
    },
    {
        "key": "daily_xp_120",
        "title": "Momentum Burst",
        "description": "Earn 120 XP today.",
        "metric": "xp_earned_total",
        "target": 120,
        "reward_xp": 45,
        "reward_coins": 20,
    },
    {
        "key": "daily_coins_45",
        "title": "Coin Crafter",
        "description": "Earn 45 coins today.",
        "metric": "coins_earned_total",
        "target": 45,
        "reward_xp": 35,
        "reward_coins": 18,
    },
    {
        "key": "daily_focus_4",
        "title": "Focus Four",
        "description": "Complete any 4 checklist items today.",
        "metric": "completion_total",
        "target": 4,
        "reward_xp": 40,
        "reward_coins": 18,
    },
]
CHALLENGE_WEEKLY_TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "weekly_tasks_16",
        "title": "Weekly Workhorse",
        "description": "Complete 16 tasks this week.",
        "metric": "task_done_total",
        "target": 16,
        "reward_xp": 120,
        "reward_coins": 55,
    },
    {
        "key": "weekly_habits_12",
        "title": "Habit Marathon",
        "description": "Complete 12 habits this week.",
        "metric": "habit_done_total",
        "target": 12,
        "reward_xp": 110,
        "reward_coins": 50,
    },
    {
        "key": "weekly_quests_3",
        "title": "Quest Push",
        "description": "Finish 3 quests this week.",
        "metric": "quest_done_total",
        "target": 3,
        "reward_xp": 130,
        "reward_coins": 60,
    },
    {
        "key": "weekly_xp_650",
        "title": "XP Climb",
        "description": "Earn 650 XP this week.",
        "metric": "xp_earned_total",
        "target": 650,
        "reward_xp": 140,
        "reward_coins": 65,
    },
    {
        "key": "weekly_coin_260",
        "title": "Coin Engine",
        "description": "Earn 260 coins this week.",
        "metric": "coins_earned_total",
        "target": 260,
        "reward_xp": 135,
        "reward_coins": 62,
    },
]
CHALLENGE_WINDOW_TYPES = {"daily", "weekly"}
CHALLENGE_ROTATION_COUNT_BY_WINDOW = {"daily": 3, "weekly": 3}
TIMELINE_DAY_RANGE_MIN = 7
TIMELINE_DAY_RANGE_MAX = 180
TIMELINE_DEFAULT_DAYS = 30
SEASON_PASS_XP_PER_TIER = 300
SEASON_PASS_MAX_TIER = 20
SEASON_PASS_COIN_BASE = 16
SEASON_PASS_COIN_STEP = 3
SEASON_PASS_RANGE_DAY_MIN = 7
SEASON_PASS_RANGE_DAY_MAX = 180
LEADERBOARD_DEFAULT_LIMIT = 15
LEADERBOARD_MIN_LIMIT = 3
LEADERBOARD_MAX_LIMIT = 50
LEADERBOARD_SCOPES = {"global", "network"}


def token_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="lifeos-auth")


def password_reset_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="lifeos-password-reset")


def issue_token(user: User) -> str:
    return token_serializer().dumps({"user_id": user.id, "nonce": secrets.token_urlsafe(8)})


def extract_bearer_token(header_value: str) -> str:
    value = str(header_value or "")
    if not value.startswith("Bearer "):
        return ""
    return value[7:].strip()


def hash_auth_token(token_value: str) -> str:
    return hashlib.sha256(str(token_value).encode("utf-8")).hexdigest()


def revoke_auth_token(token_value: str, *, user_id: int | None = None) -> None:
    safe_token = str(token_value or "").strip()
    if not safe_token:
        return
    token_hash = hash_auth_token(safe_token)
    existing = RevokedAuthToken.query.filter_by(token_hash=token_hash).first()
    if existing is not None:
        return
    db.session.add(
        RevokedAuthToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(seconds=max(TOKEN_MAX_AGE_SECONDS, 60)),
        )
    )


def is_auth_token_revoked(token_value: str) -> bool:
    safe_token = str(token_value or "").strip()
    if not safe_token:
        return False
    token_hash = hash_auth_token(safe_token)
    row = RevokedAuthToken.query.filter_by(token_hash=token_hash).first()
    return row is not None


def resolve_user_by_identifier(identifier: str) -> User | None:
    normalized_identifier = normalize_username(identifier)
    normalized_email = normalize_email(identifier)
    return User.query.filter(
        or_(
            func.lower(User.username) == normalized_identifier,
            func.lower(User.email) == normalized_email,
        )
    ).first()


def serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "coins": int(user.coins or 0),
        "season_pass_premium": bool(user.season_pass_premium),
    }


def normalize_username(value: str) -> str:
    return value.strip().lower()


def normalize_email(value: str) -> str:
    return value.strip().lower()


def auth_error(message: str, status_code: int = 401) -> tuple[dict[str, str], int]:
    return {"error": message}, status_code


def validate_password(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if len(password) > 128:
        return "Password is too long"
    return None


def resolve_authenticated_user() -> tuple[User | None, tuple[dict[str, str], int] | None]:
    header_value = request.headers.get("Authorization", "")
    token_value = extract_bearer_token(header_value)
    if not token_value:
        return None, auth_error("Missing bearer token", 401)
    if is_auth_token_revoked(token_value):
        return None, auth_error("Session expired. Please sign in again.", 401)

    try:
        payload = token_serializer().loads(token_value, max_age=TOKEN_MAX_AGE_SECONDS)
    except SignatureExpired:
        return None, auth_error("Session expired. Please sign in again.", 401)
    except BadSignature:
        return None, auth_error("Invalid auth token", 401)

    user_id = payload.get("user_id") if isinstance(payload, dict) else None
    if not isinstance(user_id, int):
        return None, auth_error("Invalid auth token", 401)

    user = db.session.get(User, user_id)
    if user is None:
        return None, auth_error("User not found", 401)

    return user, None


def require_auth(view_fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view_fn)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        auth_user, error = resolve_authenticated_user()
        if error is not None:
            return error
        kwargs["auth_user"] = auth_user
        return view_fn(*args, **kwargs)

    return wrapped


def xp_required_for_level(level: int) -> int:
    return 200 * max(level, 1)


def level_progress(total_xp: int) -> tuple[int, int, int]:
    level = 1
    remaining_xp = max(total_xp, 0)
    while remaining_xp >= xp_required_for_level(level):
        remaining_xp -= xp_required_for_level(level)
        level += 1
    return level, remaining_xp, xp_required_for_level(level)


def relative_day_label(day_value: date, today: date) -> str:
    if day_value == today:
        return "Today"
    if day_value == today - timedelta(days=1):
        return "Yesterday"
    return day_value.strftime("%b %d")


def daily_quote_for_user(user: User, today: date) -> dict[str, str]:
    return MOTIVATIONAL_QUOTES[(user.id + today.toordinal()) % len(MOTIVATIONAL_QUOTES)]


def parse_date_value(value: Any, field_name: str) -> tuple[date | None, str | None]:
    if value is None or value == "":
        return None, None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value, None
    if isinstance(value, str):
        try:
            return date.fromisoformat(value), None
        except ValueError:
            return None, f"{field_name} must be in YYYY-MM-DD format"
    return None, f"{field_name} must be a valid date string"


def parse_datetime_value(value: Any, field_name: str) -> tuple[datetime | None, str | None]:
    if value is None or value == "":
        return None, None
    if isinstance(value, datetime):
        parsed_dt = value
    elif isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None, None
        if candidate.endswith("Z"):
            candidate = f"{candidate[:-1]}+00:00"
        try:
            parsed_dt = datetime.fromisoformat(candidate)
        except ValueError:
            return None, f"{field_name} must be in ISO datetime format"
    else:
        return None, f"{field_name} must be a valid datetime string"

    if parsed_dt.tzinfo is not None:
        parsed_dt = parsed_dt.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed_dt, None


def parse_int_value(value: Any, field_name: str, minimum: int | None = None) -> tuple[int | None, str | None]:
    if value is None or value == "":
        return None, None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be an integer"
    if minimum is not None and parsed < minimum:
        return None, f"{field_name} must be at least {minimum}"
    return parsed, None


def parse_task_status(value: Any) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    normalized = str(value).strip().lower()
    if normalized not in VALID_TASK_STATUSES:
        return None, "status must be todo or done"
    return normalized, None


def parse_task_priority(value: Any) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    normalized = str(value).strip().lower()
    if normalized not in VALID_TASK_PRIORITIES:
        return None, "priority must be low, medium, or high"
    return normalized, None


def parse_task_type(value: Any) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    normalized = str(value).strip().lower()
    if normalized not in VALID_TASK_TYPES:
        return None, "task_type must be task, habit, or quest"
    return normalized, None


def parse_space_task_type(value: Any) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    normalized = str(value).strip().lower()
    if normalized not in VALID_SPACE_TASK_TYPES:
        return None, "task_type must be task or quest for shared spaces"
    return normalized, None


def parse_bool_value(value: Any, field_name: str) -> tuple[bool | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, bool):
        return value, None
    if isinstance(value, (int, float)):
        return bool(value), None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True, None
        if normalized in {"0", "false", "no", "off"}:
            return False, None
    return None, f"{field_name} must be a boolean value"


def parse_hour_value(value: Any, field_name: str) -> tuple[int | None, str | None]:
    if value is None or value == "":
        return None, None
    parsed, parsed_error = parse_int_value(value, field_name, 0)
    if parsed_error:
        return None, parsed_error
    if parsed is None:
        return None, None
    if parsed > 23:
        return None, f"{field_name} must be between 0 and 23"
    return parsed, None


def parse_email_address(value: Any, field_name: str) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    candidate = normalize_email(str(value))
    if "@" not in candidate or "." not in candidate.split("@")[-1]:
        return None, f"{field_name} must be a valid email"
    if len(candidate) > 160:
        return None, f"{field_name} is too long"
    return candidate, None


def parse_phone_number(value: Any, field_name: str) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    candidate = str(value).strip()
    normalized = re.sub(r"\s+", "", candidate)
    if len(normalized) < 8 or len(normalized) > 20:
        return None, f"{field_name} must be 8-20 characters"
    if not re.fullmatch(r"^\+?[0-9().-]+$", normalized):
        return None, f"{field_name} contains invalid characters"
    return normalized, None


def parse_reminder_channel(value: Any) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    normalized = str(value).strip().lower()
    if normalized not in VALID_REMINDER_CHANNELS and normalized != "all":
        return None, "channel must be email, sms, or all"
    return normalized, None


def parse_recurrence_frequency(value: Any) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    normalized = str(value).strip().lower()
    if normalized not in VALID_RECURRING_FREQUENCIES:
        return None, "frequency must be daily or weekly"
    return normalized, None


def parse_weekday_values(value: Any) -> tuple[list[int], str | None]:
    if value is None or value == "":
        return [], None

    raw_values: list[Any]
    if isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = [value]

    parsed_days: set[int] = set()
    for raw in raw_values:
        if raw is None or raw == "":
            continue
        try:
            day_int = int(raw)
        except (TypeError, ValueError):
            return [], "days_of_week must contain weekday numbers (0=Mon ... 6=Sun)"
        if day_int < 0 or day_int > 6:
            return [], "days_of_week values must be between 0 (Mon) and 6 (Sun)"
        parsed_days.add(day_int)

    return sorted(parsed_days), None


def encode_weekdays(days: list[int]) -> str | None:
    if not days:
        return None
    return ",".join(str(day) for day in sorted(set(days)))


def decode_weekdays(days_of_week: str | None) -> list[int]:
    if not days_of_week:
        return []
    parsed: list[int] = []
    for token in days_of_week.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            day = int(token)
        except ValueError:
            continue
        if 0 <= day <= 6:
            parsed.append(day)
    return sorted(set(parsed))


def parse_space_name(value: Any) -> tuple[str | None, str | None]:
    name = str(value or "").strip()
    if not name:
        return None, "name is required"
    if len(name) < 2:
        return None, "name must be at least 2 characters"
    if len(name) > 120:
        return None, "name is too long"
    return name, None


def parse_space_role(value: Any, *, allow_owner: bool = False) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    normalized = str(value).strip().lower()
    if normalized not in VALID_SPACE_ROLES:
        return None, "role must be owner, admin, or member"
    if normalized == "owner" and not allow_owner:
        return None, "owner role is reserved for the current space owner"
    return normalized, None


def parse_space_invite_hours(value: Any) -> tuple[int, str | None]:
    if value is None or value == "":
        return SPACE_INVITE_DEFAULT_HOURS, None
    parsed, parsed_error = parse_int_value(value, "expires_in_hours", 1)
    if parsed_error:
        return SPACE_INVITE_DEFAULT_HOURS, parsed_error
    if parsed is None:
        return SPACE_INVITE_DEFAULT_HOURS, None
    if parsed > SPACE_INVITE_MAX_HOURS:
        return SPACE_INVITE_DEFAULT_HOURS, f"expires_in_hours cannot exceed {SPACE_INVITE_MAX_HOURS}"
    return parsed, None


def parse_space_template_display_name(value: Any) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    display_name = str(value).strip()
    if not display_name:
        return None, "display_name cannot be empty"
    if len(display_name) < 2:
        return None, "display_name must be at least 2 characters"
    if len(display_name) > 80:
        return None, "display_name is too long"
    return display_name, None


def normalize_space_notification_mode(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "default":
        normalized = DEFAULT_SPACE_NOTIFICATION_MODE
    if normalized not in VALID_SPACE_NOTIFICATION_MODES:
        return DEFAULT_SPACE_NOTIFICATION_MODE
    return normalized


def parse_space_notification_mode(value: Any) -> tuple[str | None, str | None]:
    if value is None or value == "":
        return None, None
    normalized = str(value).strip().lower()
    if normalized == "default":
        normalized = DEFAULT_SPACE_NOTIFICATION_MODE
    if normalized not in VALID_SPACE_NOTIFICATION_MODES:
        allowed = ", ".join(sorted(VALID_SPACE_NOTIFICATION_MODES))
        return None, f"mode must be one of: {allowed}"
    return normalized, None


def normalize_space_quiet_hour(value: Any, *, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    if parsed < 0 or parsed > 23:
        return fallback
    return parsed


def resolve_space_notification_quiet_hours(space: Space | None) -> dict[str, Any]:
    if space is None:
        enabled = False
        start_hour = SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC
        end_hour = SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC
    else:
        enabled = bool(getattr(space, "notification_quiet_hours_enabled", False))
        start_hour = normalize_space_quiet_hour(
            getattr(space, "notification_quiet_hours_start_utc", SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC),
            fallback=SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC,
        )
        end_hour = normalize_space_quiet_hour(
            getattr(space, "notification_quiet_hours_end_utc", SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC),
            fallback=SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC,
        )

    return {
        "enabled": bool(enabled),
        "start_hour_utc": start_hour,
        "end_hour_utc": end_hour,
    }


def is_space_notification_quiet_hours_active(space: Space | None, now_utc: datetime | None = None) -> bool:
    quiet_hours = resolve_space_notification_quiet_hours(space)
    if not quiet_hours["enabled"]:
        return False

    start_hour = int(quiet_hours["start_hour_utc"])
    end_hour = int(quiet_hours["end_hour_utc"])
    if start_hour == end_hour:
        return False

    current_hour = (now_utc or datetime.utcnow()).hour
    if start_hour < end_hour:
        return start_hour <= current_hour < end_hour
    return current_hour >= start_hour or current_hour < end_hour


def resolve_space_member_default_notification_mode(space: Space | None) -> str:
    if space is None:
        return DEFAULT_SPACE_NOTIFICATION_MODE
    return normalize_space_notification_mode(getattr(space, "default_member_notification_mode", DEFAULT_SPACE_NOTIFICATION_MODE))


def serialize_task(task: Task) -> dict[str, Any]:
    effective_xp, _ = calculate_task_completion_xp(task)
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "task_type": task.task_type,
        "task_type_label": TASK_TYPE_LABELS.get(task.task_type, "Task"),
        "xp_reward": task.xp_reward,
        "xp_effective": effective_xp,
        "priority": task.priority,
        "due_on": task.due_on.isoformat() if task.due_on else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "recurrence_rule_id": task.recurrence_rule_id,
        "created_at": task.created_at.isoformat(),
    }


def serialize_habit(habit: Habit) -> dict[str, Any]:
    return {
        "id": habit.id,
        "name": habit.name,
        "current_streak": habit.current_streak,
        "longest_streak": habit.longest_streak,
        "last_completed_on": habit.last_completed_on.isoformat() if habit.last_completed_on else None,
        "created_at": habit.created_at.isoformat(),
    }


def serialize_goal(goal: Goal) -> dict[str, Any]:
    progress = round((goal.current_value / goal.target_value) * 100, 1) if goal.target_value else 0
    return {
        "id": goal.id,
        "title": goal.title,
        "target_value": goal.target_value,
        "current_value": goal.current_value,
        "progress": progress,
        "deadline": goal.deadline.isoformat() if goal.deadline else None,
        "created_at": goal.created_at.isoformat(),
    }


def normalize_avatar_choice(slot: str, value: Any) -> str:
    options_by_key = AVATAR_OPTION_INDEX.get(slot, {})
    fallback = DEFAULT_AVATAR_PROFILE.get(slot) or (next(iter(options_by_key)) if options_by_key else "")
    candidate = str(value or "").strip().lower()
    if candidate in options_by_key:
        return candidate
    return fallback


def ensure_avatar_profile(user: User) -> AvatarProfile:
    row = AvatarProfile.query.filter_by(user_id=user.id).first()
    if row is None:
        row = AvatarProfile(
            user_id=user.id,
            body_type=DEFAULT_AVATAR_PROFILE["body_type"],
            style=DEFAULT_AVATAR_PROFILE["style"],
            top=DEFAULT_AVATAR_PROFILE["top"],
            bottom=DEFAULT_AVATAR_PROFILE["bottom"],
            accessory=DEFAULT_AVATAR_PROFILE["accessory"],
            palette=DEFAULT_AVATAR_PROFILE["palette"],
        )
        db.session.add(row)
        db.session.flush()
        return row

    normalized_values = {
        "body_type": normalize_avatar_choice("body_type", row.body_type),
        "style": normalize_avatar_choice("style", row.style),
        "top": normalize_avatar_choice("top", row.top),
        "bottom": normalize_avatar_choice("bottom", row.bottom),
        "accessory": normalize_avatar_choice("accessory", row.accessory),
        "palette": normalize_avatar_choice("palette", row.palette),
    }
    dirty = False
    for field_name, normalized in normalized_values.items():
        if getattr(row, field_name) != normalized:
            setattr(row, field_name, normalized)
            dirty = True
    if dirty:
        db.session.add(row)
    return row


def serialize_avatar_profile(row: AvatarProfile) -> dict[str, Any]:
    return {
        "body_type": normalize_avatar_choice("body_type", row.body_type),
        "style": normalize_avatar_choice("style", row.style),
        "top": normalize_avatar_choice("top", row.top),
        "bottom": normalize_avatar_choice("bottom", row.bottom),
        "accessory": normalize_avatar_choice("accessory", row.accessory),
        "palette": normalize_avatar_choice("palette", row.palette),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def serialize_shop_purchase(row: ShopPurchase) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if row.metadata_json:
        try:
            raw_value = json.loads(row.metadata_json)
            if isinstance(raw_value, dict):
                metadata = raw_value
        except (TypeError, ValueError, json.JSONDecodeError):
            metadata = {}
    item_snapshot = SHOP_ITEMS_BY_KEY.get(str(row.item_key or "").strip().lower(), {})
    reward_type = str(item_snapshot.get("reward_type", metadata.get("reward_type", "self_reward"))).strip().lower()
    rarity = normalize_shop_rarity(str(item_snapshot.get("rarity", "common")))
    unlock_slot = metadata.get("unlock_slot") or item_snapshot.get("unlock_slot")
    unlock_value = metadata.get("unlock_value") or item_snapshot.get("unlock_value")
    unlock_set_key = metadata.get("unlock_set_key") or item_snapshot.get("unlock_set_key")
    set_key = metadata.get("set_key") or item_snapshot.get("set_key")
    repeatable = bool(item_snapshot.get("repeatable", metadata.get("repeatable", False)))
    return {
        "id": row.id,
        "item_key": row.item_key,
        "category": row.category,
        "title": row.title,
        "price_coins": int(row.price_coins or 0),
        "reward_type": reward_type,
        "rarity": rarity,
        "rarity_label": SHOP_RARITY_LABELS.get(rarity, "Common"),
        "repeatable": repeatable,
        "unlock_slot": unlock_slot,
        "unlock_value": unlock_value,
        "unlock_set_key": unlock_set_key,
        "set_key": set_key,
        "is_claimed": row.claimed_at is not None,
        "claimed_at": row.claimed_at.isoformat() if row.claimed_at else None,
        "claimed_note": row.claimed_note,
        "metadata": metadata,
        "purchased_at": row.purchased_at.isoformat() if row.purchased_at else None,
    }


def user_owned_shop_item_keys(user_id: int) -> set[str]:
    rows = (
        db.session.query(ShopPurchase.item_key)
        .filter(ShopPurchase.user_id == user_id)
        .group_by(ShopPurchase.item_key)
        .all()
    )
    return {str(row[0]) for row in rows if row and row[0]}


def normalize_shop_rarity(value: str | None) -> str:
    candidate = str(value or "common").strip().lower()
    return candidate if candidate in SHOP_RARITY_LABELS else "common"


def shop_day_window(now_utc: datetime | None = None) -> tuple[datetime, datetime, datetime, str]:
    current = now_utc or datetime.utcnow()
    day_start = datetime.combine(current.date(), datetime.min.time())
    day_end = day_start + timedelta(days=1)
    return current, day_start, day_end, day_start.date().isoformat()


def build_shop_rotation_active_keys(day_key: str) -> set[str]:
    normalized_day_key = str(day_key or date.today().isoformat())
    always_available_keys = {
        str(item.get("item_key", "")).strip()
        for item in SHOP_ITEMS
        if str(item.get("item_key", "")).strip() and bool(item.get("always_available", False))
    }
    grouped_candidates: dict[str, list[dict[str, Any]]] = {}
    for item in SHOP_ITEMS:
        item_key = str(item.get("item_key", "")).strip()
        if not item_key or item_key in always_available_keys:
            continue
        category_key = str(item.get("category", "self_reward")).strip().lower() or "self_reward"
        grouped_candidates.setdefault(category_key, []).append(item)

    active_keys = set(always_available_keys)
    for category_key, candidates in grouped_candidates.items():
        slots = max(int(SHOP_ROTATION_CATEGORY_SLOTS.get(category_key, SHOP_ROTATION_FALLBACK_SLOTS) or 0), 0)
        if slots < 1:
            continue
        scored_candidates: list[tuple[int, str]] = []
        for item in candidates:
            item_key = str(item.get("item_key", "")).strip()
            if not item_key:
                continue
            rarity = normalize_shop_rarity(str(item.get("rarity", "common")))
            rarity_bias = int(SHOP_RARITY_ROTATION_BIAS.get(rarity, 0) or 0)
            digest_value = hashlib.sha1(f"{normalized_day_key}:{item_key}".encode("utf-8")).hexdigest()
            score = int(digest_value[:8], 16) + rarity_bias
            scored_candidates.append((score, item_key))
        scored_candidates.sort(key=lambda entry: (entry[0], entry[1]))
        for _, item_key in scored_candidates[:slots]:
            active_keys.add(item_key)
    return active_keys


def load_shop_purchase_counts_since(day_start: datetime, *, user_id: int | None = None) -> dict[str, int]:
    query = db.session.query(ShopPurchase.item_key, func.count(ShopPurchase.id)).filter(ShopPurchase.purchased_at >= day_start)
    if user_id is not None:
        query = query.filter(ShopPurchase.user_id == int(user_id))
    rows = query.group_by(ShopPurchase.item_key).all()
    counts: dict[str, int] = {}
    for item_key, count in rows:
        safe_item_key = str(item_key or "").strip()
        if not safe_item_key:
            continue
        counts[safe_item_key] = max(int(count or 0), 0)
    return counts


def avatar_option_unlock_keys(option: dict[str, Any] | None) -> list[str]:
    if not option or not isinstance(option, dict):
        return []
    raw_keys: list[str] = []
    single_key = str(option.get("unlock_item_key", "")).strip()
    if single_key:
        raw_keys.append(single_key)
    multi_keys = option.get("unlock_item_keys")
    if isinstance(multi_keys, (list, tuple, set)):
        for value in multi_keys:
            candidate = str(value or "").strip()
            if candidate:
                raw_keys.append(candidate)
    return sorted(set(raw_keys))


def is_avatar_option_unlocked(option: dict[str, Any] | None, owned_item_keys: set[str]) -> bool:
    unlock_keys = avatar_option_unlock_keys(option)
    if not unlock_keys:
        return True
    return any(unlock_key in owned_item_keys for unlock_key in unlock_keys)


def avatar_set_status(set_key: str, owned_item_keys: set[str]) -> tuple[bool, bool, list[str]]:
    normalized_set_key = str(set_key or "").strip().lower()
    if not normalized_set_key:
        return False, False, []
    preset = AVATAR_SET_PRESETS_BY_KEY.get(normalized_set_key)
    if not preset:
        return False, False, []

    set_item_key = str(preset.get("set_item_key", "")).strip().lower()
    set_owned = bool(set_item_key and set_item_key in owned_item_keys)
    slots = preset.get("slots", {})
    if not isinstance(slots, dict):
        return set_owned, set_owned, []
    missing_slots: list[str] = []
    for slot, option_key in slots.items():
        option = AVATAR_OPTION_INDEX.get(str(slot), {}).get(str(option_key))
        if not is_avatar_option_unlocked(option, owned_item_keys):
            missing_slots.append(str(slot))
    unlocked = bool(set_owned or len(missing_slots) == 0)
    return unlocked, set_owned, missing_slots


def serialize_avatar_options_for_user(user: User, owned_item_keys: set[str] | None = None) -> dict[str, list[dict[str, Any]]]:
    owned = owned_item_keys if owned_item_keys is not None else user_owned_shop_item_keys(user.id)
    payload: dict[str, list[dict[str, Any]]] = {}
    for slot, options in AVATAR_OPTION_GROUPS.items():
        slot_rows: list[dict[str, Any]] = []
        for option in options:
            unlock_keys = avatar_option_unlock_keys(option)
            unlock_item_key = unlock_keys[0] if unlock_keys else None
            unlocked = is_avatar_option_unlocked(option, owned)
            slot_rows.append(
                {
                    "key": option["key"],
                    "label": option["label"],
                    "icon": option.get("icon"),
                    "unlock_item_key": unlock_item_key,
                    "unlock_item_keys": unlock_keys,
                    "set_key": option.get("set_key"),
                    "unlocked": bool(unlocked),
                }
            )
        payload[slot] = slot_rows
    return payload


def serialize_avatar_set_presets_for_user(user: User, owned_item_keys: set[str] | None = None) -> list[dict[str, Any]]:
    owned = owned_item_keys if owned_item_keys is not None else user_owned_shop_item_keys(user.id)
    rows: list[dict[str, Any]] = []
    for preset in AVATAR_SET_PRESETS:
        if not isinstance(preset, dict):
            continue
        set_key = str(preset.get("key", "")).strip().lower()
        if not set_key:
            continue
        slots = preset.get("slots", {})
        if not isinstance(slots, dict):
            slots = {}
        unlocked, set_owned, missing_slots = avatar_set_status(set_key, owned)
        rows.append(
            {
                "key": set_key,
                "label": str(preset.get("label", set_key)).strip() or set_key,
                "icon": str(preset.get("icon", "\u2728")).strip() or "\u2728",
                "description": str(preset.get("description", "")).strip(),
                "set_item_key": str(preset.get("set_item_key", "")).strip().lower() or None,
                "slots": {str(slot): str(value) for slot, value in slots.items()},
                "unlocked": bool(unlocked),
                "set_owned": bool(set_owned),
                "missing_slots": missing_slots,
            }
        )
    return rows


def serialize_shop_item_for_user(
    item: dict[str, Any],
    *,
    owned_item_keys: set[str],
    coins_balance: int,
    active_item_keys: set[str],
    global_daily_purchases: dict[str, int],
    user_daily_purchases: dict[str, int],
) -> dict[str, Any]:
    price = max(int(item.get("price_coins", 0) or 0), 0)
    item_key = str(item.get("item_key", "")).strip()
    repeatable = bool(item.get("repeatable", False))
    reward_type = str(item.get("reward_type", "self_reward")).strip().lower()
    owned = item_key in owned_item_keys
    if not owned and reward_type == "avatar_unlock":
        unlock_slot = str(item.get("unlock_slot", "")).strip().lower()
        unlock_value = str(item.get("unlock_value", "")).strip().lower()
        if unlock_slot and unlock_value:
            option = AVATAR_OPTION_INDEX.get(unlock_slot, {}).get(unlock_value)
            owned = is_avatar_option_unlocked(option, owned_item_keys)
    if not owned and reward_type == "avatar_set_unlock":
        set_key_value = str(item.get("unlock_set_key", "")).strip().lower()
        if not set_key_value and item_key.startswith("avatar_set_"):
            set_key_value = item_key.removeprefix("avatar_set_")
        set_unlocked, _set_owned, _missing_slots = avatar_set_status(set_key_value, owned_item_keys)
        owned = bool(set_unlocked)
    rarity = normalize_shop_rarity(str(item.get("rarity", "common")))
    always_available = bool(item.get("always_available", False))
    available_by_rotation = bool(always_available or item_key in active_item_keys)

    daily_stock = max(int(item.get("daily_stock", 0) or 0), 0)
    sold_today = max(int(global_daily_purchases.get(item_key, 0) or 0), 0)
    sold_out = daily_stock > 0 and sold_today >= daily_stock
    daily_remaining = max(daily_stock - sold_today, 0) if daily_stock > 0 else None

    user_daily_limit = max(int(item.get("user_daily_limit", 0) or 0), 0)
    user_purchased_today = max(int(user_daily_purchases.get(item_key, 0) or 0), 0)
    user_limit_reached = user_daily_limit > 0 and user_purchased_today >= user_daily_limit
    user_daily_remaining = max(user_daily_limit - user_purchased_today, 0) if user_daily_limit > 0 else None

    availability_reason: str | None = None
    if not available_by_rotation:
        availability_reason = "Not in today's rotation"
    elif sold_out:
        availability_reason = "Sold out for today"
    elif user_limit_reached:
        availability_reason = "Daily limit reached"

    can_purchase_today = bool(available_by_rotation and not sold_out and not user_limit_reached)
    coin_affordable = int(coins_balance or 0) >= price
    return {
        "item_key": item_key,
        "title": str(item.get("title", "")).strip(),
        "description": str(item.get("description", "")).strip(),
        "category": str(item.get("category", "self_reward")).strip().lower(),
        "category_label": SHOP_CATEGORY_LABELS.get(str(item.get("category", "self_reward")).strip().lower(), "Shop"),
        "price_coins": price,
        "rarity": rarity,
        "rarity_label": SHOP_RARITY_LABELS.get(rarity, "Common"),
        "repeatable": repeatable,
        "reward_type": reward_type,
        "unlock_slot": item.get("unlock_slot"),
        "unlock_value": item.get("unlock_value"),
        "unlock_set_key": item.get("unlock_set_key"),
        "set_key": item.get("set_key"),
        "owned": bool(owned),
        "always_available": always_available,
        "available_today": bool(available_by_rotation),
        "availability_reason": availability_reason,
        "can_purchase_today": can_purchase_today,
        "daily_stock": int(daily_stock) if daily_stock > 0 else None,
        "daily_sold": int(sold_today) if daily_stock > 0 else None,
        "daily_remaining": int(daily_remaining) if daily_remaining is not None else None,
        "user_daily_limit": int(user_daily_limit) if user_daily_limit > 0 else None,
        "user_daily_purchases": int(user_purchased_today) if user_daily_limit > 0 else None,
        "user_daily_remaining": int(user_daily_remaining) if user_daily_remaining is not None else None,
        "coin_affordable": bool(coin_affordable),
        "affordable": bool(coin_affordable and can_purchase_today),
    }


def ensure_reminder_settings(user: User) -> ReminderChannelSettings:
    row = ReminderChannelSettings.query.filter_by(user_id=user.id).first()
    if row is None:
        row = ReminderChannelSettings(
            user_id=user.id,
            in_app_enabled=True,
            email_enabled=False,
            sms_enabled=False,
            email_address=user.email,
            phone_number=None,
            digest_hour_utc=REMINDER_DEFAULT_DIGEST_HOUR_UTC,
        )
        db.session.add(row)
        db.session.flush()
    return row


def serialize_reminder_settings(row: ReminderChannelSettings, user: User) -> dict[str, Any]:
    email_address = row.email_address or user.email
    return {
        "user_id": row.user_id,
        "in_app_enabled": bool(row.in_app_enabled),
        "email_enabled": bool(row.email_enabled),
        "sms_enabled": bool(row.sms_enabled),
        "email_address": email_address,
        "phone_number": row.phone_number,
        "digest_hour_utc": int(row.digest_hour_utc),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def serialize_reminder_delivery_log(row: ReminderDeliveryLog) -> dict[str, Any]:
    return {
        "id": row.id,
        "channel": row.channel,
        "recipient": row.recipient,
        "provider": row.provider,
        "status": row.status,
        "subject": row.subject,
        "body": row.body,
        "notification_count": row.notification_count,
        "dedupe_key": row.dedupe_key,
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def reminder_log(
    *,
    user_id: int,
    channel: str,
    recipient: str,
    provider: str,
    status: str,
    subject: str,
    body: str,
    notification_count: int = 0,
    dedupe_key: str | None = None,
    error_message: str | None = None,
) -> ReminderDeliveryLog:
    entry = ReminderDeliveryLog(
        user_id=user_id,
        channel=channel,
        recipient=recipient,
        provider=provider,
        status=status,
        subject=subject[:180],
        body=body[:4000],
        notification_count=max(int(notification_count or 0), 0),
        dedupe_key=dedupe_key,
        error_message=(error_message or "")[:255] or None,
    )
    db.session.add(entry)
    return entry


def prune_reminder_delivery_logs(user_id: int | None = None) -> None:
    if REMINDER_LOG_MAX_ROWS <= 0:
        return
    query = ReminderDeliveryLog.query
    if user_id is not None:
        query = query.filter(ReminderDeliveryLog.user_id == user_id)
    total_rows = query.count()
    overflow = total_rows - REMINDER_LOG_MAX_ROWS
    if overflow <= 0:
        return
    stale_rows = query.order_by(ReminderDeliveryLog.created_at.asc(), ReminderDeliveryLog.id.asc()).limit(overflow).all()
    for row in stale_rows:
        db.session.delete(row)


def build_notification_digest(payload: dict[str, Any]) -> tuple[str, str]:
    generated_at = str(payload.get("generated_at", ""))[:19]
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    total = int(counts.get("total", 0) or 0)
    overdue = int(counts.get("overdue_tasks", 0) or 0)
    streak = int(counts.get("streak_risk_habits", 0) or 0)
    goals = int(counts.get("goals_due_soon", 0) or 0)
    due_today = int(counts.get("due_today", 0) or 0)
    space_updates = int(counts.get("space_updates", 0) or 0)
    invite_expiring = int(counts.get("space_invites_expiring", 0) or 0)

    subject = f"LifeOS Reminder Digest ({generated_at.split('T', 1)[0] or date.today().isoformat()})"
    lines = [
        "LifeOS reminder digest",
        f"Generated at: {generated_at or datetime.utcnow().isoformat()}",
        "",
        f"Active reminders: {total}",
        f"- Overdue tasks: {overdue}",
        f"- Streak risks: {streak}",
        f"- Goal deadlines: {goals}",
        f"- Due today: {due_today}",
        f"- Shared queue updates: {space_updates}",
        f"- Invite links expiring soon: {invite_expiring}",
        "",
        "Top reminders:",
    ]

    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    top_items = items[:6]
    if not top_items:
        lines.append("- You're all caught up.")
    else:
        for idx, item in enumerate(top_items, start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "Reminder")).strip() or "Reminder"
            message = str(item.get("message", "")).strip()
            lines.append(f"{idx}. {title}: {message}")

    lines.extend(["", "Open LifeOS to review and complete these items."])
    return subject, "\n".join(lines)


def send_email_message(recipient: str, subject: str, body: str) -> tuple[bool, str, str | None]:
    provider = REMINDER_EMAIL_PROVIDER or "console"
    if provider in {"disabled", "none", "off"}:
        return False, provider, "Email provider is disabled"

    if provider == "smtp":
        if not SMTP_HOST:
            return False, "smtp", "SMTP host is not configured"
        try:
            message = EmailMessage()
            message["From"] = SMTP_FROM_EMAIL
            message["To"] = recipient
            message["Subject"] = subject
            message.set_content(body)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
                if SMTP_USE_TLS:
                    smtp.starttls()
                if SMTP_USERNAME:
                    smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
                smtp.send_message(message)
            return True, "smtp", None
        except Exception as exc:
            return False, "smtp", str(exc)

    print(f"[LifeOS reminder email] to={recipient} subject={subject}\n{body}\n")
    return True, "console", None


def send_sms_message(recipient: str, body: str) -> tuple[bool, str, str | None]:
    provider = REMINDER_SMS_PROVIDER or "console"
    if provider in {"disabled", "none", "off"}:
        return False, provider, "SMS provider is disabled"

    if provider == "twilio":
        if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER):
            return False, "twilio", "Twilio credentials are not fully configured"
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        payload = urlencode({"To": recipient, "From": TWILIO_FROM_NUMBER, "Body": body}).encode("utf-8")
        credentials = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode("utf-8")
        basic_token = base64.b64encode(credentials).decode("ascii")
        req = Request(url, data=payload, method="POST")
        req.add_header("Authorization", f"Basic {basic_token}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urlopen(req, timeout=20) as response:  # noqa: S310
                status_code = int(getattr(response, "status", 200))
                if 200 <= status_code < 300:
                    return True, "twilio", None
                return False, "twilio", f"Twilio request failed with status {status_code}"
        except HTTPError as exc:
            return False, "twilio", f"Twilio HTTP error {exc.code}"
        except URLError as exc:
            return False, "twilio", str(exc.reason)
        except Exception as exc:
            return False, "twilio", str(exc)

    print(f"[LifeOS reminder sms] to={recipient}\n{body}\n")
    return True, "console", None


def send_digest_to_user(
    user: User,
    settings_row: ReminderChannelSettings,
    notifications_payload: dict[str, Any],
    *,
    force_send: bool = False,
    source: str = "worker",
) -> dict[str, Any]:
    now = datetime.utcnow()
    digest_day = now.date()
    subject, body = build_notification_digest(notifications_payload)
    notification_total = int((notifications_payload.get("counts") or {}).get("total", 0) or 0)
    summary = {"email": "skipped", "sms": "skipped", "sent": 0, "errors": 0, "notification_total": notification_total}

    if notification_total <= 0 and not force_send:
        return summary

    for channel in ("email", "sms"):
        is_enabled = bool(getattr(settings_row, f"{channel}_enabled", False))
        if not is_enabled:
            continue

        digest_hour = int(settings_row.digest_hour_utc or REMINDER_DEFAULT_DIGEST_HOUR_UTC)
        if not force_send and now.hour < digest_hour:
            continue

        recipient = (settings_row.email_address or user.email) if channel == "email" else settings_row.phone_number
        recipient = (recipient or "").strip()
        if not recipient:
            reminder_log(
                user_id=user.id,
                channel=channel,
                recipient="(missing)",
                provider=REMINDER_EMAIL_PROVIDER if channel == "email" else REMINDER_SMS_PROVIDER,
                status="error",
                subject=subject,
                body=body,
                notification_count=notification_total,
                error_message="Missing recipient",
            )
            summary[channel] = "error"
            summary["errors"] += 1
            continue

        dedupe_key = None
        if not force_send:
            dedupe_key = f"digest:{channel}:{digest_day.isoformat()}:{digest_hour}"
            existing_sent = ReminderDeliveryLog.query.filter_by(
                user_id=user.id,
                channel=channel,
                dedupe_key=dedupe_key,
                status="sent",
            ).first()
            if existing_sent is not None:
                continue

        if channel == "email":
            success, provider, send_error = send_email_message(recipient, subject, body)
        else:
            success, provider, send_error = send_sms_message(recipient, body)

        reminder_log(
            user_id=user.id,
            channel=channel,
            recipient=recipient,
            provider=provider,
            status="sent" if success else "error",
            subject=subject,
            body=body,
            notification_count=notification_total,
            dedupe_key=dedupe_key,
            error_message=send_error,
        )
        if success:
            summary[channel] = "sent"
            summary["sent"] += 1
        else:
            summary[channel] = "error"
            summary["errors"] += 1

    return summary


def run_reminder_delivery_cycle(
    *,
    user_id: int | None = None,
    force_send: bool = False,
    source: str = "worker",
    commit: bool = True,
) -> dict[str, Any]:
    if not REMINDER_DELIVERY_ENABLED and not force_send:
        return {"users_checked": 0, "sent": 0, "errors": 0, "source": source, "deliveries": []}

    query = ReminderChannelSettings.query
    if user_id is not None:
        query = query.filter(ReminderChannelSettings.user_id == user_id)
    else:
        query = query.filter(or_(ReminderChannelSettings.email_enabled.is_(True), ReminderChannelSettings.sms_enabled.is_(True)))
    settings_rows = query.order_by(ReminderChannelSettings.user_id.asc()).all()

    if not settings_rows and user_id is not None:
        user = db.session.get(User, user_id)
        if user is not None:
            settings_rows = [ensure_reminder_settings(user)]

    sent = 0
    errors = 0
    delivery_rows: list[dict[str, Any]] = []

    try:
        for settings_row in settings_rows:
            user = db.session.get(User, settings_row.user_id)
            if user is None:
                continue
            notifications_payload = build_notifications_payload(user, delivery_context="digest")
            user_summary = send_digest_to_user(
                user,
                settings_row,
                notifications_payload,
                force_send=force_send,
                source=source,
            )
            sent += int(user_summary.get("sent", 0) or 0)
            errors += int(user_summary.get("errors", 0) or 0)
            delivery_rows.append({"user_id": user.id, **user_summary})

        prune_reminder_delivery_logs(user_id=user_id)
        if commit:
            db.session.commit()
    except Exception:
        db.session.rollback()
        if source == "worker":
            return {"users_checked": len(settings_rows), "sent": sent, "errors": errors + 1, "source": source, "deliveries": delivery_rows}
        raise

    return {"users_checked": len(settings_rows), "sent": sent, "errors": errors, "source": source, "deliveries": delivery_rows}


def recurring_schedule_label(rule: RecurringRule) -> str:
    interval = max(int(rule.interval or 1), 1)
    if rule.frequency == "weekly":
        days = decode_weekdays(rule.days_of_week)
        day_names = ", ".join(WEEKDAY_LABELS[day] for day in days) if days else "selected days"
        if interval == 1:
            return f"Every week on {day_names}"
        return f"Every {interval} weeks on {day_names}"
    if interval == 1:
        return "Every day"
    return f"Every {interval} days"


def serialize_recurring_rule(rule: RecurringRule) -> dict[str, Any]:
    return {
        "id": rule.id,
        "user_id": rule.user_id,
        "title": rule.title,
        "task_type": rule.task_type,
        "priority": rule.priority,
        "xp_reward": rule.xp_reward,
        "frequency": rule.frequency,
        "interval": rule.interval,
        "days_of_week": decode_weekdays(rule.days_of_week),
        "start_on": rule.start_on.isoformat() if rule.start_on else None,
        "end_on": rule.end_on.isoformat() if rule.end_on else None,
        "active": bool(rule.active),
        "last_generated_on": rule.last_generated_on.isoformat() if rule.last_generated_on else None,
        "created_at": rule.created_at.isoformat(),
        "schedule_label": recurring_schedule_label(rule),
    }


def recurring_rule_applies_on_day(rule: RecurringRule, day_value: date) -> bool:
    if not rule.active:
        return False
    if rule.start_on and day_value < rule.start_on:
        return False
    if rule.end_on and day_value > rule.end_on:
        return False

    interval = max(int(rule.interval or 1), 1)
    anchor_day = rule.start_on or (rule.created_at.date() if rule.created_at else day_value)
    if day_value < anchor_day:
        return False

    if rule.frequency == "weekly":
        days = decode_weekdays(rule.days_of_week)
        if days and day_value.weekday() not in days:
            return False
        elapsed_weeks = (day_value - anchor_day).days // 7
        return elapsed_weeks % interval == 0

    elapsed_days = (day_value - anchor_day).days
    return elapsed_days % interval == 0


def run_recurring_generation(
    *,
    user_id: int | None = None,
    backfill_days: int | None = None,
    source: str = "manual",
    commit: bool = True,
) -> dict[str, Any]:
    resolved_backfill_days = RECURRING_DEFAULT_BACKFILL_DAYS if backfill_days is None else int(backfill_days)
    safe_backfill_days = max(1, min(resolved_backfill_days, RECURRING_MAX_BACKFILL_DAYS))
    today = date.today()
    start_day = today - timedelta(days=safe_backfill_days - 1)

    query = RecurringRule.query.filter(RecurringRule.active.is_(True))
    if user_id is not None:
        query = query.filter(RecurringRule.user_id == user_id)
    rules = query.order_by(RecurringRule.user_id.asc(), RecurringRule.created_at.asc(), RecurringRule.id.asc()).all()

    created_count = 0
    skipped_existing = 0
    errors_count = 0

    try:
        for offset in range(safe_backfill_days):
            target_day = start_day + timedelta(days=offset)
            for rule in rules:
                if not recurring_rule_applies_on_day(rule, target_day):
                    continue

                existing_task = Task.query.filter(
                    Task.user_id == rule.user_id,
                    Task.due_on == target_day,
                    or_(
                        Task.recurrence_rule_id == rule.id,
                        and_(
                            Task.recurrence_rule_id.is_(None),
                            Task.title == rule.title,
                            Task.task_type == rule.task_type,
                        ),
                    ),
                ).first()
                if existing_task is not None:
                    skipped_existing += 1
                    continue

                db.session.add(
                    Task(
                        user_id=rule.user_id,
                        title=rule.title,
                        status="todo",
                        task_type=rule.task_type,
                        xp_reward=max(int(rule.xp_reward or 20), 1),
                        priority=rule.priority if rule.priority in VALID_TASK_PRIORITIES else "medium",
                        due_on=target_day,
                        recurrence_rule_id=rule.id,
                        created_at=datetime.utcnow(),
                    )
                )
                if rule.last_generated_on is None or rule.last_generated_on < target_day:
                    rule.last_generated_on = target_day
                    db.session.add(rule)
                created_count += 1

        if commit:
            db.session.commit()
    except Exception:
        db.session.rollback()
        errors_count += 1
        if source == "worker":
            return {
                "source": source,
                "created": created_count,
                "skipped_existing": skipped_existing,
                "errors": errors_count,
                "range": {"start": start_day.isoformat(), "end": today.isoformat(), "days": safe_backfill_days},
                "rules_evaluated": len(rules),
            }
        raise

    return {
        "source": source,
        "created": created_count,
        "skipped_existing": skipped_existing,
        "errors": errors_count,
        "range": {"start": start_day.isoformat(), "end": today.isoformat(), "days": safe_backfill_days},
        "rules_evaluated": len(rules),
    }


def refresh_recurring_for_user(user: User, source: str = "request") -> dict[str, Any]:
    try:
        return run_recurring_generation(user_id=user.id, source=source, commit=True)
    except Exception:
        db.session.rollback()
        return {
            "source": source,
            "created": 0,
            "skipped_existing": 0,
            "errors": 1,
            "range": {"start": date.today().isoformat(), "end": date.today().isoformat(), "days": 1},
            "rules_evaluated": 0,
        }


def default_space_permissions_for_role(role: str | None) -> dict[str, bool]:
    normalized_role = (role or "").strip().lower()
    if normalized_role not in VALID_SPACE_ROLES:
        normalized_role = "member"
    defaults = DEFAULT_SPACE_ROLE_PERMISSIONS.get(normalized_role, DEFAULT_SPACE_ROLE_PERMISSIONS["member"])
    return {key: bool(defaults.get(key, False)) for key in SPACE_PERMISSION_KEYS}


def normalize_space_permissions(raw_permissions: dict[str, Any], role: str | None) -> dict[str, bool]:
    role_normalized = (role or "").strip().lower()
    base = default_space_permissions_for_role(role_normalized)
    for key in SPACE_PERMISSION_KEYS:
        if key in raw_permissions:
            base[key] = bool(raw_permissions[key])

    if role_normalized == "owner":
        return default_space_permissions_for_role("owner")

    if base["can_delete_space"]:
        base["can_manage_space"] = True
    if base["can_assign_admin"]:
        base["can_manage_members"] = True
    if not base["can_manage_members"]:
        base["can_assign_admin"] = False

    return base


def load_space_role_templates_map(space_id: int) -> dict[str, SpaceRoleTemplate]:
    rows = SpaceRoleTemplate.query.filter_by(space_id=space_id).all()
    return {row.role: row for row in rows if row.role in VALID_SPACE_ROLES}


def ensure_space_role_templates(space: Space) -> dict[str, SpaceRoleTemplate]:
    templates_by_role = load_space_role_templates_map(space.id)
    for role in SPACE_TEMPLATE_ROLES:
        if role in templates_by_role:
            continue
        defaults = default_space_permissions_for_role(role)
        row = SpaceRoleTemplate(
            space_id=space.id,
            role=role,
            display_name=DEFAULT_SPACE_ROLE_DISPLAY_NAMES.get(role, role.title()),
            can_manage_space=defaults["can_manage_space"],
            can_manage_members=defaults["can_manage_members"],
            can_assign_admin=defaults["can_assign_admin"],
            can_delete_space=defaults["can_delete_space"],
            can_create_tasks=defaults["can_create_tasks"],
            can_complete_tasks=defaults["can_complete_tasks"],
            can_manage_tasks=defaults["can_manage_tasks"],
            can_manage_invites=defaults["can_manage_invites"],
        )
        db.session.add(row)
        db.session.flush()
        templates_by_role[role] = row
    return templates_by_role


def space_permissions_for_role(
    role: str | None,
    template: SpaceRoleTemplate | None = None,
) -> dict[str, bool]:
    normalized_role = (role or "").strip().lower()
    if normalized_role not in VALID_SPACE_ROLES:
        normalized_role = "member"

    base = default_space_permissions_for_role(normalized_role)
    if template is not None and template.role == normalized_role and normalized_role != "owner":
        overrides = {
            "can_manage_space": bool(template.can_manage_space),
            "can_manage_members": bool(template.can_manage_members),
            "can_assign_admin": bool(template.can_assign_admin),
            "can_delete_space": bool(template.can_delete_space),
            "can_create_tasks": bool(template.can_create_tasks),
            "can_complete_tasks": bool(template.can_complete_tasks),
            "can_manage_tasks": bool(template.can_manage_tasks),
            "can_manage_invites": bool(template.can_manage_invites),
        }
        base = normalize_space_permissions(overrides, normalized_role)
    return base


def resolve_space_permissions(
    space_id: int,
    membership: SpaceMember,
    templates_by_role: dict[str, SpaceRoleTemplate] | None = None,
) -> dict[str, bool]:
    if templates_by_role is None:
        templates_by_role = load_space_role_templates_map(space_id)
    return space_permissions_for_role(membership.role, template=templates_by_role.get(membership.role))


def serialize_space_role_template(
    role: str,
    template: SpaceRoleTemplate | None = None,
) -> dict[str, Any]:
    normalized_role = (role or "").strip().lower()
    permissions = space_permissions_for_role(normalized_role, template=template)
    default_permissions = default_space_permissions_for_role(normalized_role)
    default_display_name = DEFAULT_SPACE_ROLE_DISPLAY_NAMES.get(normalized_role, normalized_role.title())
    resolved_display_name = (
        template.display_name.strip()
        if template is not None and str(template.display_name or "").strip()
        else default_display_name
    )
    is_custom = False
    if template is not None:
        permission_delta = any(bool(permissions.get(key)) != bool(default_permissions.get(key)) for key in SPACE_PERMISSION_KEYS)
        is_custom = permission_delta or resolved_display_name != default_display_name
    return {
        "role": normalized_role,
        "display_name": resolved_display_name,
        "editable": normalized_role in EDITABLE_SPACE_TEMPLATE_ROLES,
        "is_custom": is_custom,
        **permissions,
    }


def space_notification_mode_options() -> list[dict[str, str]]:
    return [
        {
            "mode": mode,
            "label": SPACE_NOTIFICATION_MODE_LABELS[mode],
            "description": SPACE_NOTIFICATION_MODE_DESCRIPTIONS.get(mode, ""),
        }
        for mode in ("all", "priority_only", "digest_only", "muted")
    ]


def load_user_space_notification_mode_map(
    user_id: int,
    space_ids: list[int] | set[int] | tuple[int, ...] | None = None,
) -> dict[int, str]:
    query = SpaceNotificationPreference.query.filter_by(user_id=user_id)
    if space_ids is not None:
        normalized_space_ids = sorted({int(space_id) for space_id in space_ids if isinstance(space_id, int)})
        if not normalized_space_ids:
            return {}
        query = query.filter(SpaceNotificationPreference.space_id.in_(normalized_space_ids))
    rows = query.all()
    return {row.space_id: normalize_space_notification_mode(row.mode) for row in rows}


def resolve_space_notification_mode(
    space_id: int,
    user_id: int,
    *,
    modes_by_space: dict[int, str] | None = None,
) -> str:
    if modes_by_space is not None:
        return normalize_space_notification_mode(modes_by_space.get(space_id))
    row = SpaceNotificationPreference.query.filter_by(space_id=space_id, user_id=user_id).first()
    if row is None:
        return DEFAULT_SPACE_NOTIFICATION_MODE
    return normalize_space_notification_mode(row.mode)


def serialize_space_notification_preference(
    space_id: int,
    user_id: int,
    mode: str,
    *,
    default_mode: str | None = None,
) -> dict[str, Any]:
    normalized_mode = normalize_space_notification_mode(mode)
    normalized_default = normalize_space_notification_mode(default_mode)
    return {
        "space_id": space_id,
        "user_id": user_id,
        "mode": normalized_mode,
        "label": SPACE_NOTIFICATION_MODE_LABELS.get(normalized_mode, SPACE_NOTIFICATION_MODE_LABELS[DEFAULT_SPACE_NOTIFICATION_MODE]),
        "description": SPACE_NOTIFICATION_MODE_DESCRIPTIONS.get(
            normalized_mode,
            SPACE_NOTIFICATION_MODE_DESCRIPTIONS[DEFAULT_SPACE_NOTIFICATION_MODE],
        ),
        "is_default": normalized_mode == normalized_default,
        "default_mode": normalized_default,
        "options": space_notification_mode_options(),
    }


def serialize_space_notification_default(space: Space) -> dict[str, Any]:
    mode = resolve_space_member_default_notification_mode(space)
    return {
        "space_id": space.id,
        "mode": mode,
        "label": SPACE_NOTIFICATION_MODE_LABELS.get(mode, SPACE_NOTIFICATION_MODE_LABELS[DEFAULT_SPACE_NOTIFICATION_MODE]),
        "description": SPACE_NOTIFICATION_MODE_DESCRIPTIONS.get(mode, SPACE_NOTIFICATION_MODE_DESCRIPTIONS[DEFAULT_SPACE_NOTIFICATION_MODE]),
        "options": space_notification_mode_options(),
    }


def serialize_space_notification_quiet_hours(space: Space, *, now_utc: datetime | None = None) -> dict[str, Any]:
    quiet_hours = resolve_space_notification_quiet_hours(space)
    start_hour = int(quiet_hours["start_hour_utc"])
    end_hour = int(quiet_hours["end_hour_utc"])
    return {
        "space_id": space.id,
        "enabled": bool(quiet_hours["enabled"]),
        "start_hour_utc": start_hour,
        "end_hour_utc": end_hour,
        "window_label": f"{start_hour:02d}:00-{end_hour:02d}:00 UTC",
        "is_active_now": is_space_notification_quiet_hours_active(space, now_utc=now_utc),
    }


def ensure_space_member_notification_preference(space: Space, user_id: int) -> SpaceNotificationPreference:
    row = SpaceNotificationPreference.query.filter_by(space_id=space.id, user_id=user_id).first()
    if row is None:
        row = SpaceNotificationPreference(
            space_id=space.id,
            user_id=user_id,
            mode=resolve_space_member_default_notification_mode(space),
        )
    else:
        row.mode = normalize_space_notification_mode(row.mode)
    db.session.add(row)
    db.session.flush()
    return row


def apply_space_notification_default_to_members(
    space: Space,
    *,
    include_owner: bool = False,
) -> dict[str, int]:
    target_rows = SpaceMember.query.filter_by(space_id=space.id).all()
    target_user_ids = {
        row.user_id
        for row in target_rows
        if isinstance(row.user_id, int) and (include_owner or row.user_id != space.owner_user_id)
    }
    if include_owner and isinstance(space.owner_user_id, int):
        target_user_ids.add(space.owner_user_id)

    if not target_user_ids:
        return {"targeted": 0, "applied": 0, "created": 0, "updated": 0, "removed": 0, "unchanged": 0}

    default_mode = resolve_space_member_default_notification_mode(space)
    existing_rows = SpaceNotificationPreference.query.filter(
        SpaceNotificationPreference.space_id == space.id,
        SpaceNotificationPreference.user_id.in_(sorted(target_user_ids)),
    ).all()
    preference_by_user_id = {row.user_id: row for row in existing_rows}

    created = 0
    updated = 0
    removed = 0
    unchanged = 0

    for user_id in sorted(target_user_ids):
        row = preference_by_user_id.get(user_id)
        current_mode = normalize_space_notification_mode(row.mode if row is not None else DEFAULT_SPACE_NOTIFICATION_MODE)
        if current_mode == default_mode:
            if default_mode == DEFAULT_SPACE_NOTIFICATION_MODE and row is not None:
                db.session.delete(row)
                removed += 1
            else:
                unchanged += 1
            continue

        if default_mode == DEFAULT_SPACE_NOTIFICATION_MODE:
            if row is not None:
                db.session.delete(row)
                removed += 1
            else:
                unchanged += 1
            continue

        if row is None:
            row = SpaceNotificationPreference(space_id=space.id, user_id=user_id, mode=default_mode)
            created += 1
        else:
            row.mode = default_mode
            updated += 1
        db.session.add(row)

    applied = created + updated + removed
    return {
        "targeted": len(target_user_ids),
        "applied": applied,
        "created": created,
        "updated": updated,
        "removed": removed,
        "unchanged": unchanged,
    }


def serialize_space(
    space: Space,
    current_role: str | None = None,
    member_count: int | None = None,
    permissions: dict[str, bool] | None = None,
    notification_mode: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": space.id,
        "name": space.name,
        "owner_user_id": space.owner_user_id,
        "default_member_notification_mode": resolve_space_member_default_notification_mode(space),
        "notification_quiet_hours_enabled": bool(getattr(space, "notification_quiet_hours_enabled", False)),
        "notification_quiet_hours_start_utc": normalize_space_quiet_hour(
            getattr(space, "notification_quiet_hours_start_utc", SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC),
            fallback=SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC,
        ),
        "notification_quiet_hours_end_utc": normalize_space_quiet_hour(
            getattr(space, "notification_quiet_hours_end_utc", SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC),
            fallback=SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC,
        ),
        "created_at": space.created_at.isoformat(),
    }
    if current_role is not None:
        payload["current_role"] = current_role
        payload["permissions"] = permissions if permissions is not None else space_permissions_for_role(current_role)
    if member_count is not None:
        payload["member_count"] = int(member_count)
    if notification_mode is not None:
        payload["notification_mode"] = normalize_space_notification_mode(notification_mode)
    return payload


def serialize_space_member(member: SpaceMember, user: User | None, auth_user_id: int) -> dict[str, Any]:
    display_name = user.display_name if user else f"User {member.user_id}"
    username = user.username if user else None
    email = user.email if user else None
    return {
        "user_id": member.user_id,
        "display_name": display_name,
        "username": username,
        "email": email,
        "role": member.role,
        "is_owner": member.role == "owner",
        "is_self": member.user_id == auth_user_id,
        "joined_at": member.created_at.isoformat(),
    }


def serialize_space_task(task: SpaceTask, users_by_id: dict[int, User] | None = None) -> dict[str, Any]:
    users_by_id = users_by_id or {}
    created_by = users_by_id.get(task.created_by_user_id)
    completed_by = users_by_id.get(task.completed_by_user_id) if task.completed_by_user_id else None
    return {
        "id": task.id,
        "space_id": task.space_id,
        "title": task.title,
        "status": task.status,
        "task_type": task.task_type,
        "task_type_label": TASK_TYPE_LABELS.get(task.task_type, "Task"),
        "xp_reward": task.xp_reward,
        "priority": task.priority,
        "due_on": task.due_on.isoformat() if task.due_on else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat(),
        "created_by_user_id": task.created_by_user_id,
        "created_by_display_name": created_by.display_name if created_by else None,
        "completed_by_user_id": task.completed_by_user_id,
        "completed_by_display_name": completed_by.display_name if completed_by else None,
    }


def is_space_invite_expired(invite: SpaceInvite, now: datetime | None = None) -> bool:
    if invite.expires_at is None:
        return False
    current = now or datetime.utcnow()
    return invite.expires_at <= current


def is_space_invite_active(invite: SpaceInvite, now: datetime | None = None) -> bool:
    if invite.revoked_at is not None:
        return False
    if invite.accepted_at is not None:
        return False
    return not is_space_invite_expired(invite, now=now)


def invite_status(invite: SpaceInvite, now: datetime | None = None) -> str:
    if invite.revoked_at is not None:
        return "revoked"
    if invite.accepted_at is not None:
        return "accepted"
    if is_space_invite_expired(invite, now=now):
        return "expired"
    return "active"


def serialize_space_invite(
    invite: SpaceInvite,
    users_by_id: dict[int, User] | None = None,
    *,
    include_token: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    users_by_id = users_by_id or {}
    created_by = users_by_id.get(invite.created_by_user_id)
    accepted_by = users_by_id.get(invite.accepted_by_user_id) if invite.accepted_by_user_id else None
    payload: dict[str, Any] = {
        "id": invite.id,
        "space_id": invite.space_id,
        "role": invite.role,
        "status": invite_status(invite, now=now),
        "is_active": is_space_invite_active(invite, now=now),
        "is_expired": is_space_invite_expired(invite, now=now),
        "created_by_user_id": invite.created_by_user_id,
        "created_by_display_name": created_by.display_name if created_by else None,
        "accepted_by_user_id": invite.accepted_by_user_id,
        "accepted_by_display_name": accepted_by.display_name if accepted_by else None,
        "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
        "accepted_at": invite.accepted_at.isoformat() if invite.accepted_at else None,
        "revoked_at": invite.revoked_at.isoformat() if invite.revoked_at else None,
        "created_at": invite.created_at.isoformat(),
    }
    if include_token:
        payload["invite_token"] = invite.invite_token
    return payload


def log_space_activity(
    *,
    space_id: int,
    actor_user_id: int | None,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    summary: str,
    details: dict[str, Any] | None = None,
    created_at: datetime | None = None,
) -> None:
    safe_summary = str(summary or "").strip()
    if not safe_summary:
        return
    details_json = None
    if isinstance(details, dict) and details:
        try:
            details_json = json.dumps(details, separators=(",", ":"), ensure_ascii=True)
        except (TypeError, ValueError):
            details_json = None
    db.session.add(
        SpaceActivityEvent(
            space_id=space_id,
            actor_user_id=actor_user_id,
            event_type=str(event_type or "").strip().lower() or "space_event",
            entity_type=str(entity_type or "").strip().lower() or "space",
            entity_id=entity_id,
            summary=safe_summary[:255],
            details_json=details_json,
            created_at=created_at or datetime.utcnow(),
        )
    )


def parse_space_activity_details(event: SpaceActivityEvent) -> dict[str, Any] | None:
    raw = (event.details_json or "").strip()
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        return payload
    return None


def serialize_space_activity_event(
    event: SpaceActivityEvent,
    *,
    users_by_id: dict[int, User] | None = None,
    include_details: bool = True,
) -> dict[str, Any]:
    users_by_id = users_by_id or {}
    actor = users_by_id.get(event.actor_user_id) if isinstance(event.actor_user_id, int) else None
    payload: dict[str, Any] = {
        "id": event.id,
        "space_id": event.space_id,
        "event_type": event.event_type,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "summary": event.summary,
        "actor_user_id": event.actor_user_id,
        "actor_display_name": actor.display_name if actor else None,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "category": "audit" if event.event_type in SPACE_ACTIVITY_AUDIT_EVENT_TYPES else "activity",
    }
    if include_details:
        payload["details"] = parse_space_activity_details(event)
    return payload


def query_space_activity_events(
    space_id: int,
    *,
    event_types: set[str] | tuple[str, ...] | list[str] | None = None,
    limit: int = SPACE_AUDIT_LOG_DEFAULT_LIMIT,
) -> list[SpaceActivityEvent]:
    query = SpaceActivityEvent.query.filter_by(space_id=space_id)
    if event_types:
        normalized_event_types = {
            str(event_type or "").strip().lower()
            for event_type in event_types
            if str(event_type or "").strip()
        }
        if normalized_event_types:
            query = query.filter(SpaceActivityEvent.event_type.in_(normalized_event_types))
    return (
        query.order_by(SpaceActivityEvent.created_at.desc(), SpaceActivityEvent.id.desc())
        .limit(max(int(limit), 1))
        .all()
    )


def summarize_space_audit_events(rows: list[SpaceActivityEvent]) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    for row in rows:
        key = str(row.event_type or "").strip().lower()
        if not key:
            continue
        by_type[key] = by_type.get(key, 0) + 1
    return {"total": len(rows), "by_type": by_type}


def include_space_activity_for_mode(mode: str, severity: str, delivery_context: str) -> bool:
    normalized_mode = normalize_space_notification_mode(mode)
    safe_context = str(delivery_context or "in_app").strip().lower() or "in_app"
    if normalized_mode == "muted":
        return False
    if normalized_mode == "digest_only":
        return safe_context == "digest"
    if normalized_mode == "priority_only":
        return severity in {"high", "medium"}
    return True


def build_space_activity_notification_items(
    user: User,
    severity_rank: dict[str, int],
    *,
    delivery_context: str = "in_app",
) -> tuple[list[dict[str, Any]], int]:
    memberships = SpaceMember.query.filter_by(user_id=user.id).all()
    if not memberships:
        return [], 0

    membership_by_space = {member.space_id: member for member in memberships}
    space_ids = list(membership_by_space.keys())
    if not space_ids:
        return [], 0
    notification_mode_by_space = load_user_space_notification_mode_map(user.id, space_ids)

    now_utc = datetime.utcnow()
    window_start = now_utc - timedelta(hours=SPACE_ACTIVITY_NOTIFICATION_WINDOW_HOURS)
    rows = (
        SpaceActivityEvent.query.filter(
            SpaceActivityEvent.space_id.in_(space_ids),
            SpaceActivityEvent.created_at >= window_start,
            SpaceActivityEvent.event_type.in_(SPACE_ACTIVITY_TASK_EVENT_TYPES),
        )
        .order_by(SpaceActivityEvent.created_at.desc(), SpaceActivityEvent.id.desc())
        .limit(SPACE_ACTIVITY_NOTIFICATION_MAX_EVENTS)
        .all()
    )
    if not rows:
        return [], 0

    spaces = Space.query.filter(Space.id.in_({row.space_id for row in rows})).all()
    spaces_by_id = {space.id: space for space in spaces}
    space_names = {space.id: space.name for space in spaces}
    grouped: dict[int, dict[str, Any]] = {}
    for row in rows:
        bucket = grouped.get(row.space_id)
        if bucket is None:
            bucket = {
                "latest_created_at": row.created_at,
                "latest_id": row.id,
                "counts": {event_type: 0 for event_type in SPACE_ACTIVITY_TASK_EVENT_TYPES},
            }
            grouped[row.space_id] = bucket
        if row.created_at > bucket["latest_created_at"]:
            bucket["latest_created_at"] = row.created_at
            bucket["latest_id"] = row.id
        if row.event_type in bucket["counts"]:
            bucket["counts"][row.event_type] += 1

    ordered_space_updates = sorted(
        grouped.items(),
        key=lambda entry: (entry[1]["latest_created_at"], entry[1]["latest_id"]),
        reverse=True,
    )[:SPACE_ACTIVITY_NOTIFICATION_MAX_SPACES]

    items: list[dict[str, Any]] = []
    included_updates_total = 0
    for space_id, payload in ordered_space_updates:
        if is_space_notification_quiet_hours_active(spaces_by_id.get(space_id), now_utc=now_utc):
            continue
        counts = payload.get("counts") or {}
        parts: list[str] = []
        for event_type in ("space_task_created", "space_task_completed", "space_task_updated", "space_task_reopened", "space_task_deleted"):
            count_value = int(counts.get(event_type, 0) or 0)
            if count_value <= 0:
                continue
            parts.append(f"{count_value} {SPACE_ACTIVITY_EVENT_LABELS.get(event_type, event_type)}")
        if not parts:
            continue

        updates_total = sum(int(value or 0) for value in counts.values())
        severity = "medium" if updates_total >= 4 or int(counts.get("space_task_deleted", 0) or 0) > 0 else "low"
        mode = notification_mode_by_space.get(space_id, DEFAULT_SPACE_NOTIFICATION_MODE)
        if not include_space_activity_for_mode(mode, severity, delivery_context):
            continue
        space_name = space_names.get(space_id, f"Space {space_id}")
        included_updates_total += updates_total
        items.append(
            {
                "id": f"space-updates-{space_id}-{payload['latest_id']}",
                "category": "space_updates",
                "severity": severity,
                "title": "Shared queue updates",
                "message": f"{space_name}: {', '.join(parts)} in the last {SPACE_ACTIVITY_NOTIFICATION_WINDOW_HOURS}h.",
                "related": {"entity": "space", "id": space_id, "path": "/spaces"},
                "date": payload["latest_created_at"].isoformat(),
                "_severity_rank": severity_rank[severity],
            }
        )

    return items, included_updates_total


def build_space_invite_expiry_notification_items(
    user: User,
    severity_rank: dict[str, int],
) -> tuple[list[dict[str, Any]], int]:
    memberships = SpaceMember.query.filter_by(user_id=user.id).all()
    if not memberships:
        return [], 0

    manageable_space_ids: list[int] = []
    for membership in memberships:
        templates_by_role = load_space_role_templates_map(membership.space_id)
        permissions = resolve_space_permissions(
            membership.space_id,
            membership,
            templates_by_role=templates_by_role,
        )
        if permissions.get("can_manage_invites"):
            manageable_space_ids.append(membership.space_id)

    if not manageable_space_ids:
        return [], 0

    now = datetime.utcnow()
    window_end = now + timedelta(hours=SPACE_INVITE_EXPIRY_ALERT_WINDOW_HOURS)
    managed_spaces = Space.query.filter(Space.id.in_(set(manageable_space_ids))).all()
    managed_spaces_by_id = {space.id: space for space in managed_spaces}
    eligible_space_ids = [
        space_id
        for space_id in manageable_space_ids
        if not is_space_notification_quiet_hours_active(managed_spaces_by_id.get(space_id), now_utc=now)
    ]
    if not eligible_space_ids:
        return [], 0

    expiring_total = (
        db.session.query(func.count(SpaceInvite.id))
        .filter(
            SpaceInvite.space_id.in_(eligible_space_ids),
            SpaceInvite.revoked_at.is_(None),
            SpaceInvite.accepted_at.is_(None),
            SpaceInvite.expires_at.isnot(None),
            SpaceInvite.expires_at > now,
            SpaceInvite.expires_at <= window_end,
        )
        .scalar()
        or 0
    )
    if expiring_total <= 0:
        return [], 0

    rows = (
        SpaceInvite.query.filter(
            SpaceInvite.space_id.in_(eligible_space_ids),
            SpaceInvite.revoked_at.is_(None),
            SpaceInvite.accepted_at.is_(None),
            SpaceInvite.expires_at.isnot(None),
            SpaceInvite.expires_at > now,
            SpaceInvite.expires_at <= window_end,
        )
        .order_by(SpaceInvite.expires_at.asc(), SpaceInvite.id.asc())
        .limit(SPACE_INVITE_EXPIRY_ALERT_MAX_ITEMS)
        .all()
    )
    if not rows:
        return [], int(expiring_total)

    spaces = Space.query.filter(Space.id.in_({row.space_id for row in rows})).all()
    space_names = {space.id: space.name for space in spaces}

    items: list[dict[str, Any]] = []
    for invite in rows:
        expires_at = invite.expires_at or window_end
        seconds_left = max(int((expires_at - now).total_seconds()), 0)
        if seconds_left < 3600:
            remaining_label = "less than 1 hour"
        else:
            hours_left = max(int((seconds_left + 3599) // 3600), 1)
            remaining_label = f"{hours_left} hour(s)"

        severity = "high" if seconds_left <= 6 * 3600 else "medium"
        role_bucket = normalize_space_invite_analytics_role(invite.role)
        role_label = SPACE_INVITE_ANALYTICS_ROLE_LABELS.get(role_bucket, "Invite")
        space_name = space_names.get(invite.space_id, f"Space {invite.space_id}")
        items.append(
            {
                "id": f"space-invite-expiry-{invite.id}",
                "category": "space_invite_expiry",
                "severity": severity,
                "title": "Invite expiring soon",
                "message": f"{space_name}: {role_label} expires in {remaining_label}.",
                "related": {"entity": "space", "id": invite.space_id, "path": "/spaces"},
                "date": expires_at.isoformat(),
                "_severity_rank": severity_rank[severity],
            }
        )

    return items, int(expiring_total)


def resolve_space_access(
    space_id: int,
    user_id: int,
) -> tuple[Space | None, SpaceMember | None, tuple[dict[str, Any], int] | None]:
    space = db.session.get(Space, space_id)
    if space is None:
        return None, None, ({"error": "Space not found"}, 404)

    membership = SpaceMember.query.filter_by(space_id=space_id, user_id=user_id).first()
    if membership is None:
        return space, None, auth_error("Forbidden", 403)
    return space, membership, None


def query_space_tasks(space_id: int, limit: int = 120) -> list[SpaceTask]:
    status_rank = case((SpaceTask.status == "todo", 0), (SpaceTask.status == "done", 1), else_=2)
    return (
        SpaceTask.query.filter_by(space_id=space_id)
        .order_by(status_rank.asc(), SpaceTask.due_on.is_(None), SpaceTask.due_on.asc(), SpaceTask.created_at.desc())
        .limit(max(int(limit), 1))
        .all()
    )


def summarize_space_tasks(task_rows: list[SpaceTask]) -> dict[str, int]:
    return {
        "total": len(task_rows),
        "todo": sum(1 for task in task_rows if task.status == "todo"),
        "done": sum(1 for task in task_rows if task.status == "done"),
    }


def query_space_invites(space_id: int, limit: int | None = 50) -> list[SpaceInvite]:
    query = (
        SpaceInvite.query.filter_by(space_id=space_id)
        .order_by(SpaceInvite.created_at.desc(), SpaceInvite.id.desc())
    )
    if isinstance(limit, int):
        query = query.limit(max(int(limit), 1))
    return query.all()


def summarize_space_invites(invite_rows: list[SpaceInvite], now: datetime | None = None) -> dict[str, int]:
    current = now or datetime.utcnow()
    statuses = [invite_status(invite, now=current) for invite in invite_rows]
    return {
        "total": len(invite_rows),
        "active": sum(1 for status in statuses if status == "active"),
        "accepted": sum(1 for status in statuses if status == "accepted"),
        "revoked": sum(1 for status in statuses if status == "revoked"),
        "expired": sum(1 for status in statuses if status == "expired"),
    }


def calculate_percent(numerator: int, denominator: int, precision: int = 1) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, precision)


def normalize_space_invite_analytics_role(role_value: Any) -> str:
    normalized = str(role_value or "").strip().lower()
    if normalized in ASSIGNABLE_SPACE_ROLES:
        return normalized
    return "other"


def empty_space_invite_role_breakdown_entry() -> dict[str, Any]:
    return {
        "created": 0,
        "accepted": 0,
        "revoked": 0,
        "expired": 0,
        "active": 0,
        "accepted_events": 0,
        "revoked_events": 0,
        "conversion_rate_percent": 0.0,
    }


def empty_space_invite_role_breakdown() -> dict[str, dict[str, Any]]:
    return {
        role: empty_space_invite_role_breakdown_entry()
        for role in SPACE_INVITE_ANALYTICS_ROLE_BUCKETS
    }


def summarize_space_invite_role_breakdown(
    invite_rows: list[SpaceInvite],
    *,
    now: datetime | None = None,
    window_start: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    current = now or datetime.utcnow()
    scoped_rows = (
        [invite for invite in invite_rows if invite.created_at >= window_start]
        if window_start is not None
        else list(invite_rows)
    )
    breakdown = empty_space_invite_role_breakdown()

    for invite in scoped_rows:
        role_key = normalize_space_invite_analytics_role(invite.role)
        bucket = breakdown[role_key]
        bucket["created"] = int(bucket["created"]) + 1
        if invite.accepted_at is not None:
            bucket["accepted"] = int(bucket["accepted"]) + 1
        if invite.revoked_at is not None:
            bucket["revoked"] = int(bucket["revoked"]) + 1
        status = invite_status(invite, now=current)
        if status == "active":
            bucket["active"] = int(bucket["active"]) + 1
        elif status == "expired":
            bucket["expired"] = int(bucket["expired"]) + 1

    if window_start is None:
        for role_key in breakdown:
            bucket = breakdown[role_key]
            bucket["accepted_events"] = int(bucket["accepted"])
            bucket["revoked_events"] = int(bucket["revoked"])
    else:
        for invite in invite_rows:
            role_key = normalize_space_invite_analytics_role(invite.role)
            bucket = breakdown[role_key]
            if invite.accepted_at is not None and invite.accepted_at >= window_start:
                bucket["accepted_events"] = int(bucket["accepted_events"]) + 1
            if invite.revoked_at is not None and invite.revoked_at >= window_start:
                bucket["revoked_events"] = int(bucket["revoked_events"]) + 1

    for role_key in breakdown:
        bucket = breakdown[role_key]
        bucket["conversion_rate_percent"] = calculate_percent(int(bucket["accepted"]), int(bucket["created"]))

    return breakdown


def summarize_space_invite_window(
    invite_rows: list[SpaceInvite],
    *,
    days: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.utcnow()
    safe_days = max(int(days), 1)
    window_start = current - timedelta(days=safe_days)
    created_rows = [invite for invite in invite_rows if invite.created_at >= window_start]
    created_count = len(created_rows)
    accepted_count = sum(1 for invite in created_rows if invite.accepted_at is not None)
    revoked_count = sum(1 for invite in created_rows if invite.revoked_at is not None)
    accepted_event_count = sum(
        1
        for invite in invite_rows
        if invite.accepted_at is not None and invite.accepted_at >= window_start
    )
    revoked_event_count = sum(
        1
        for invite in invite_rows
        if invite.revoked_at is not None and invite.revoked_at >= window_start
    )
    role_breakdown = summarize_space_invite_role_breakdown(
        invite_rows,
        now=current,
        window_start=window_start,
    )

    return {
        "window_days": safe_days,
        "window_start": window_start.isoformat(),
        "created": created_count,
        "accepted": accepted_count,
        "revoked": revoked_count,
        "accepted_events": accepted_event_count,
        "revoked_events": revoked_event_count,
        "conversion_rate_percent": calculate_percent(accepted_count, created_count),
        "role_breakdown": role_breakdown,
    }


def summarize_space_invite_analytics(invite_rows: list[SpaceInvite], now: datetime | None = None) -> dict[str, Any]:
    current = now or datetime.utcnow()
    lifetime_summary = summarize_space_invites(invite_rows, now=current)
    created_count = lifetime_summary["total"]
    accepted_count = lifetime_summary["accepted"]
    role_breakdown = summarize_space_invite_role_breakdown(invite_rows, now=current, window_start=None)

    return {
        "generated_at": current.isoformat(),
        "role_labels": SPACE_INVITE_ANALYTICS_ROLE_LABELS,
        "lifetime": {
            "created": created_count,
            "accepted": accepted_count,
            "revoked": lifetime_summary["revoked"],
            "expired": lifetime_summary["expired"],
            "active": lifetime_summary["active"],
            "conversion_rate_percent": calculate_percent(accepted_count, created_count),
            "role_breakdown": role_breakdown,
        },
        "recent": {
            "last_7_days": summarize_space_invite_window(invite_rows, days=7, now=current),
            "last_30_days": summarize_space_invite_window(invite_rows, days=30, now=current),
        },
    }


def generate_space_invite_token() -> str:
    for _ in range(12):
        token = secrets.token_urlsafe(24)
        exists = SpaceInvite.query.filter_by(invite_token=token).first()
        if exists is None:
            return token
    return f"{secrets.token_urlsafe(32)}{int(time.time())}"


def user_can_manage_space_task(task: SpaceTask, permissions: dict[str, bool], auth_user_id: int) -> bool:
    return bool(permissions.get("can_manage_tasks")) or task.created_by_user_id == auth_user_id


def build_space_detail_payload(space: Space, membership: SpaceMember, auth_user: User) -> dict[str, Any]:
    templates_by_role = load_space_role_templates_map(space.id)
    member_permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    current = datetime.utcnow()
    default_notification_mode = resolve_space_member_default_notification_mode(space)
    notification_mode_by_space = load_user_space_notification_mode_map(auth_user.id, [space.id])
    notification_mode = resolve_space_notification_mode(space.id, auth_user.id, modes_by_space=notification_mode_by_space)
    member_rows = SpaceMember.query.filter_by(space_id=space.id).all()
    member_count = len(member_rows)
    user_ids = [member.user_id for member in member_rows]
    task_rows = query_space_tasks(space.id, limit=120)
    task_user_ids = {
        user_id
        for user_id in [task.created_by_user_id for task in task_rows]
        if isinstance(user_id, int)
    }
    task_user_ids.update(
        {
            user_id
            for user_id in [task.completed_by_user_id for task in task_rows]
            if isinstance(user_id, int)
        }
    )
    invite_rows: list[SpaceInvite] = []
    invite_analytics: dict[str, Any] | None = None
    if member_permissions.get("can_manage_invites"):
        all_invite_rows = query_space_invites(space.id, limit=None)
        invite_rows = all_invite_rows[:50]
        invite_analytics = summarize_space_invite_analytics(all_invite_rows, now=current)
    audit_rows = query_space_activity_events(
        space.id,
        event_types=SPACE_ACTIVITY_AUDIT_EVENT_TYPES,
        limit=SPACE_AUDIT_LOG_DEFAULT_LIMIT,
    )
    invite_user_ids = {
        user_id
        for user_id in [invite.created_by_user_id for invite in invite_rows]
        if isinstance(user_id, int)
    }
    invite_user_ids.update(
        {
            user_id
            for user_id in [invite.accepted_by_user_id for invite in invite_rows]
            if isinstance(user_id, int)
        }
    )
    audit_actor_ids = {
        row.actor_user_id
        for row in audit_rows
        if isinstance(row.actor_user_id, int)
    }
    if task_user_ids or invite_user_ids or audit_actor_ids:
        user_ids = sorted(set(user_ids).union(task_user_ids).union(invite_user_ids).union(audit_actor_ids))
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    users_by_id = {user.id: user for user in users}
    role_rank = {"owner": 0, "admin": 1, "member": 2}
    ordered_members = sorted(
        member_rows,
        key=lambda row: (
            role_rank.get(row.role, 9),
            (users_by_id.get(row.user_id).display_name.lower() if users_by_id.get(row.user_id) else ""),
            row.user_id,
        ),
    )

    return {
        "space": serialize_space(
            space,
            current_role=membership.role,
            member_count=member_count,
            permissions=member_permissions,
            notification_mode=notification_mode,
        ),
        "notification_preference": serialize_space_notification_preference(
            space.id,
            auth_user.id,
            notification_mode,
            default_mode=default_notification_mode,
        ),
        "notification_default": serialize_space_notification_default(space),
        "notification_quiet_hours": serialize_space_notification_quiet_hours(space, now_utc=current),
        "permissions": member_permissions,
        "role_templates": [
            serialize_space_role_template(role, template=templates_by_role.get(role))
            for role in SPACE_TEMPLATE_ROLES
        ],
        "members": [serialize_space_member(row, users_by_id.get(row.user_id), auth_user.id) for row in ordered_members],
        "tasks": [serialize_space_task(task, users_by_id=users_by_id) for task in task_rows],
        "task_summary": summarize_space_tasks(task_rows),
        "invites": [
            serialize_space_invite(invite, users_by_id=users_by_id, include_token=True, now=current)
            for invite in invite_rows
        ],
        "invite_summary": summarize_space_invites(invite_rows, now=current),
        "invite_analytics": invite_analytics,
        "audit_events": [
            serialize_space_activity_event(event, users_by_id=users_by_id)
            for event in audit_rows
        ],
        "audit_summary": summarize_space_audit_events(audit_rows),
        "audit_available_event_types": sorted(SPACE_ACTIVITY_AUDIT_EVENT_TYPES),
    }


def award_xp(user_id: int, source: str, points: int, created_at: datetime | None = None) -> int:
    safe_points = max(int(points), 1)
    db.session.add(
        XpLedger(
            user_id=user_id,
            source=source,
            points=safe_points,
            created_at=created_at or datetime.utcnow(),
        )
    )
    return safe_points


def award_action_xp(
    user_id: int,
    action: str,
    source: str,
    fallback_points: int,
    created_at: datetime | None = None,
) -> int:
    points = xp_rule_value(action, fallback_points)
    return award_xp(user_id, source, points, created_at)


def award_coins(user_id: int, source: str, amount: int, created_at: datetime | None = None) -> int:
    safe_amount = max(int(amount), 0)
    if safe_amount < 1:
        return 0

    user = db.session.get(User, user_id)
    if user is None:
        return 0

    user.coins = max(int(user.coins or 0), 0) + safe_amount
    db.session.add(user)
    db.session.add(
        CoinLedger(
            user_id=user_id,
            source=source,
            amount=safe_amount,
            created_at=created_at or datetime.utcnow(),
        )
    )
    return safe_amount


def award_action_coins(
    user_id: int,
    action: str,
    source: str,
    fallback_amount: int,
    created_at: datetime | None = None,
) -> int:
    amount = coin_rule_value(action, fallback_amount)
    return award_coins(user_id, source, amount, created_at)


def spend_coins(user: User, source: str, amount: int, created_at: datetime | None = None) -> int:
    safe_amount = max(int(amount), 1)
    current_balance = max(int(user.coins or 0), 0)
    if current_balance < safe_amount:
        return 0
    user.coins = current_balance - safe_amount
    db.session.add(user)
    db.session.add(
        CoinLedger(
            user_id=user.id,
            source=source,
            amount=-safe_amount,
            created_at=created_at or datetime.utcnow(),
        )
    )
    return safe_amount


def apply_task_completion_effects(task: Task, completed_at: datetime) -> tuple[int, int]:
    if task.status == "done":
        return 0, 0

    task.status = "done"
    task.completed_at = completed_at
    db.session.add(task)

    task_xp, _ = calculate_task_completion_xp(task)
    xp_gained = award_xp(task.user_id, f"{task.task_type.title()} complete: {task.title}", task_xp, completed_at)
    task_coin_action = f"task.complete.{task.task_type}"
    coin_fallback = DEFAULT_COIN_RULES.get(task_coin_action, DEFAULT_COIN_RULES["task.complete.task"])
    coins_gained = award_action_coins(
        task.user_id,
        task_coin_action,
        f"{task.task_type.title()} complete coins: {task.title}",
        coin_fallback,
        completed_at,
    )

    if task.task_type == "habit":
        apply_habit_completion(task.user_id, task.title, completed_at.date())
    elif task.task_type == "quest":
        goal_xp, goal_coins = nudge_goal_progress(task.user_id, source_reason="quest")
        xp_gained += goal_xp
        coins_gained += goal_coins

    return xp_gained, coins_gained


def apply_space_task_completion(
    space: Space,
    task: SpaceTask,
    completed_by_user: User,
    completed_at: datetime,
) -> tuple[int, int]:
    if task.status == "done":
        return 0, 0

    task.status = "done"
    task.completed_at = completed_at
    task.completed_by_user_id = completed_by_user.id
    db.session.add(task)

    task_xp = max(int(task.xp_reward or 25), 1)
    xp_gained = award_xp(
        completed_by_user.id,
        f"Space {task.task_type.title()} complete ({space.name}): {task.title}",
        task_xp,
        completed_at,
    )
    space_coin_action = f"space.complete.{task.task_type if task.task_type in {'task', 'quest'} else 'task'}"
    coin_fallback = DEFAULT_COIN_RULES.get(space_coin_action, DEFAULT_COIN_RULES["space.complete.task"])
    coins_gained = award_action_coins(
        completed_by_user.id,
        space_coin_action,
        f"Space {task.task_type.title()} complete coins ({space.name}): {task.title}",
        coin_fallback,
        completed_at,
    )

    if task.task_type == "quest":
        goal_xp, goal_coins = nudge_goal_progress(completed_by_user.id, source_reason="space_quest")
        xp_gained += goal_xp
        coins_gained += goal_coins

    return xp_gained, coins_gained


def migrate_schema() -> None:
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())

    if "users" in table_names:
        user_columns = {col["name"] for col in inspector.get_columns("users")}
        if "username" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(40)"))
        if "password_hash" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
        if "coins" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN coins INTEGER"))
        if "season_pass_premium" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN season_pass_premium BOOLEAN"))
        rows = db.session.execute(text("SELECT id, email, username, coins, season_pass_premium FROM users")).mappings()
        for row in rows:
            email_value = row["email"] or f"user{row['id']}@lifeos.app"
            username = (row["username"] or "").strip().lower() or email_value.split("@", 1)[0].strip().lower() or f"user{row['id']}"
            try:
                coins_value = max(int(row.get("coins") or 0), 0)
            except (TypeError, ValueError):
                coins_value = 0
            premium_value = bool(row.get("season_pass_premium"))
            db.session.execute(
                text(
                    "UPDATE users SET username = :username, coins = :coins, "
                    "season_pass_premium = :season_pass_premium WHERE id = :user_id"
                ),
                {
                    "username": username,
                    "coins": coins_value,
                    "season_pass_premium": premium_value,
                    "user_id": row["id"],
                },
            )

    if "tasks" in table_names:
        task_columns = {col["name"] for col in inspector.get_columns("tasks")}
        if "task_type" not in task_columns:
            db.session.execute(text("ALTER TABLE tasks ADD COLUMN task_type VARCHAR(20)"))
        if "xp_reward" not in task_columns:
            db.session.execute(text("ALTER TABLE tasks ADD COLUMN xp_reward INTEGER"))
        if "completed_at" not in task_columns:
            db.session.execute(text("ALTER TABLE tasks ADD COLUMN completed_at DATETIME"))
        if "recurrence_rule_id" not in task_columns:
            db.session.execute(text("ALTER TABLE tasks ADD COLUMN recurrence_rule_id INTEGER"))
        db.session.execute(text("UPDATE tasks SET task_type = 'task' WHERE task_type IS NULL OR task_type = ''"))
        db.session.execute(text("UPDATE tasks SET xp_reward = 20 WHERE xp_reward IS NULL OR xp_reward < 1"))
        db.session.execute(text("UPDATE tasks SET completed_at = created_at WHERE status = 'done' AND completed_at IS NULL"))

    if "habits" in table_names:
        habit_columns = {col["name"] for col in inspector.get_columns("habits")}
        if "longest_streak" not in habit_columns:
            db.session.execute(text("ALTER TABLE habits ADD COLUMN longest_streak INTEGER"))
        db.session.execute(
            text(
                "UPDATE habits SET longest_streak = CASE "
                "WHEN longest_streak IS NULL OR longest_streak < current_streak THEN current_streak "
                "ELSE longest_streak END"
            )
        )

    if "spaces" in table_names:
        space_columns = {col["name"] for col in inspector.get_columns("spaces")}
        if "default_member_notification_mode" not in space_columns:
            db.session.execute(text("ALTER TABLE spaces ADD COLUMN default_member_notification_mode VARCHAR(24)"))
        if "notification_quiet_hours_enabled" not in space_columns:
            db.session.execute(text("ALTER TABLE spaces ADD COLUMN notification_quiet_hours_enabled BOOLEAN"))
        if "notification_quiet_hours_start_utc" not in space_columns:
            db.session.execute(text("ALTER TABLE spaces ADD COLUMN notification_quiet_hours_start_utc INTEGER"))
        if "notification_quiet_hours_end_utc" not in space_columns:
            db.session.execute(text("ALTER TABLE spaces ADD COLUMN notification_quiet_hours_end_utc INTEGER"))

        rows = db.session.execute(
            text(
                "SELECT id, default_member_notification_mode, notification_quiet_hours_enabled, "
                "notification_quiet_hours_start_utc, notification_quiet_hours_end_utc "
                "FROM spaces"
            )
        ).mappings()
        for row in rows:
            normalized_mode = normalize_space_notification_mode(row.get("default_member_notification_mode"))
            quiet_enabled = bool(row.get("notification_quiet_hours_enabled"))
            quiet_start = normalize_space_quiet_hour(
                row.get("notification_quiet_hours_start_utc"),
                fallback=SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC,
            )
            quiet_end = normalize_space_quiet_hour(
                row.get("notification_quiet_hours_end_utc"),
                fallback=SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC,
            )

            if (
                (row.get("default_member_notification_mode") or "") != normalized_mode
                or row.get("notification_quiet_hours_enabled") != quiet_enabled
                or row.get("notification_quiet_hours_start_utc") != quiet_start
                or row.get("notification_quiet_hours_end_utc") != quiet_end
            ):
                db.session.execute(
                    text(
                        "UPDATE spaces SET default_member_notification_mode = :mode, "
                        "notification_quiet_hours_enabled = :quiet_enabled, "
                        "notification_quiet_hours_start_utc = :quiet_start, "
                        "notification_quiet_hours_end_utc = :quiet_end "
                        "WHERE id = :space_id"
                    ),
                    {
                        "mode": normalized_mode,
                        "quiet_enabled": quiet_enabled,
                        "quiet_start": quiet_start,
                        "quiet_end": quiet_end,
                        "space_id": row["id"],
                    },
                )

    if "shop_purchases" in table_names:
        purchase_columns = {col["name"] for col in inspector.get_columns("shop_purchases")}
        if "claimed_at" not in purchase_columns:
            db.session.execute(text("ALTER TABLE shop_purchases ADD COLUMN claimed_at DATETIME"))
        if "claimed_note" not in purchase_columns:
            db.session.execute(text("ALTER TABLE shop_purchases ADD COLUMN claimed_note VARCHAR(255)"))

    db.session.commit()


def ensure_user(username: str, display_name: str, email: str, password: str | None = None) -> User:
    normalized_username = normalize_username(username)
    normalized_email = normalize_email(email)

    user = User.query.filter(func.lower(User.username) == normalized_username).first()
    if user is None:
        user = User.query.filter(func.lower(User.email) == normalized_email).first()

    if user is None:
        user = User(
            username=normalized_username,
            email=normalized_email,
            display_name=display_name,
            password_hash=generate_password_hash(password) if password else None,
        )
        db.session.add(user)
        db.session.flush()
    else:
        user.username = normalized_username
        user.email = normalized_email
        user.display_name = display_name
        if password and not user.password_hash:
            user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.flush()

    return user


def seed_user_data(user: User, include_richer_data: bool) -> None:
    today = date.today()
    now = datetime.utcnow()
    rng = random.Random(20260209 + user.id)

    if Task.query.filter_by(user_id=user.id).count() == 0:
        todo_rows = [
            ("Morning Workout", "habit", 20, "high", 0),
            ("Read 10 Pages", "habit", 10, "medium", 0),
            ("Finish Project Proposal", "quest", 100, "high", 0),
            ("Review sprint board", "task", 25, "medium", 0),
            ("Plan meals for the week", "task", 20, "low", 1),
            ("Call accountability partner", "habit", 15, "medium", 1),
        ]
        if not include_richer_data:
            todo_rows = todo_rows[:3]

        for title, task_type, xp_reward, priority, due_offset in todo_rows:
            db.session.add(
                Task(
                    user_id=user.id,
                    title=title,
                    status="todo",
                    task_type=task_type,
                    xp_reward=xp_reward,
                    priority=priority,
                    due_on=today + timedelta(days=due_offset),
                    created_at=now - timedelta(hours=rng.randint(1, 24)),
                )
            )

        completed_rows = [
            ("Evening Meditation", "habit", 5, "low", 0),
            ("Submit Report", "quest", 100, "high", 1),
            ("Clean email inbox", "task", 20, "medium", 2),
        ]
        for idx, (title, task_type, xp_reward, priority, days_ago) in enumerate(completed_rows):
            completed_day = today - timedelta(days=days_ago)
            completed_at = datetime.combine(completed_day, datetime.min.time()) + timedelta(hours=17 + idx)
            db.session.add(
                Task(
                    user_id=user.id,
                    title=title,
                    status="done",
                    task_type=task_type,
                    xp_reward=xp_reward,
                    priority=priority,
                    due_on=completed_day,
                    completed_at=completed_at,
                    created_at=completed_at - timedelta(hours=6),
                )
            )

    if Habit.query.filter_by(user_id=user.id).count() == 0:
        habits = [
            Habit(user_id=user.id, name="Morning Workout", current_streak=7, longest_streak=15, last_completed_on=today),
            Habit(user_id=user.id, name="Read 10 Pages", current_streak=6, longest_streak=12, last_completed_on=today),
            Habit(user_id=user.id, name="Evening Meditation", current_streak=3, longest_streak=9, last_completed_on=today),
        ]
        db.session.add_all(habits)
        db.session.flush()

    if HabitLog.query.filter_by(user_id=user.id).count() == 0:
        for habit in Habit.query.filter_by(user_id=user.id).all():
            for offset in range(habit.current_streak):
                db.session.add(
                    HabitLog(
                        user_id=user.id,
                        habit_id=habit.id,
                        completed_on=habit.last_completed_on - timedelta(days=offset),
                    )
                )

    if Goal.query.filter_by(user_id=user.id).count() == 0:
        goals = [
            Goal(user_id=user.id, title="Ship LifeOS v0.1", target_value=10, current_value=6, deadline=today + timedelta(days=21)),
            Goal(user_id=user.id, title="Complete 30 workouts", target_value=30, current_value=14, deadline=today + timedelta(days=35)),
        ]
        if include_richer_data:
            goals.append(
                Goal(user_id=user.id, title="Read 12 books this year", target_value=12, current_value=4, deadline=today + timedelta(days=140))
            )
        db.session.add_all(goals)

    if XpLedger.query.filter_by(user_id=user.id).count() == 0:
        completed_tasks = Task.query.filter_by(user_id=user.id, status="done").all()
        for task in completed_tasks:
            db.session.add(
                XpLedger(
                    user_id=user.id,
                    source=f"{task.task_type.title()} complete: {task.title}",
                    points=task.xp_reward,
                    created_at=task.completed_at or task.created_at,
                )
            )
        if include_richer_data:
            for day_offset in range(25, 2, -1):
                if rng.random() < 0.7:
                    db.session.add(
                        XpLedger(
                            user_id=user.id,
                            source=rng.choice(["Habit streak bonus", "Goal checkpoint", "Focus session complete"]),
                            points=rng.randint(35, 120),
                            created_at=now - timedelta(days=day_offset, hours=rng.randint(0, 20)),
                        )
                    )

    if CoinLedger.query.filter_by(user_id=user.id).count() == 0:
        completed_tasks = Task.query.filter_by(user_id=user.id, status="done").all()
        earned_total = 0
        for task in completed_tasks:
            action_key = f"task.complete.{task.task_type}"
            fallback = DEFAULT_COIN_RULES.get(action_key, DEFAULT_COIN_RULES["task.complete.task"])
            amount = coin_rule_value(action_key, fallback)
            if amount < 1:
                continue
            db.session.add(
                CoinLedger(
                    user_id=user.id,
                    source=f"{task.task_type.title()} complete coins: {task.title}",
                    amount=amount,
                    created_at=task.completed_at or task.created_at or now,
                )
            )
            earned_total += amount

        if include_richer_data:
            for day_offset in range(25, 2, -1):
                if rng.random() < 0.65:
                    amount = rng.randint(6, 28)
                    db.session.add(
                        CoinLedger(
                            user_id=user.id,
                            source=rng.choice(["Consistency bonus", "Focus block", "Milestone checkpoint"]),
                            amount=amount,
                            created_at=now - timedelta(days=day_offset, hours=rng.randint(0, 20)),
                        )
                    )
                    earned_total += amount

            starter_bonus = 180
            db.session.add(
                CoinLedger(
                    user_id=user.id,
                    source="Starter wallet bonus",
                    amount=starter_bonus,
                    created_at=now - timedelta(days=1, minutes=15),
                )
            )
            earned_total += starter_bonus

            if ShopPurchase.query.filter_by(user_id=user.id).count() == 0:
                seeded_entries = [
                    ("avatar_set_unicorn", False),
                    ("avatar_style_cyber", False),
                    ("avatar_palette_neon", False),
                    ("reward_coffee_break", True),
                ]
                if bool(user.season_pass_premium):
                    seeded_entries.insert(0, (SEASON_PASS_PREMIUM_SHOP_ITEM_KEY, False))
                for item_key, mark_claimed in seeded_entries:
                    item = SHOP_ITEMS_BY_KEY.get(item_key)
                    if item is None:
                        continue
                    price = max(int(item.get("price_coins", 0) or 0), 0)
                    if price < 1 or earned_total < price:
                        continue
                    purchased_at = now - timedelta(hours=rng.randint(4, 36))
                    claimed_at = purchased_at + timedelta(hours=2) if mark_claimed else None
                    db.session.add(
                        ShopPurchase(
                            user_id=user.id,
                            item_key=item_key,
                            category=str(item.get("category", "avatar")),
                            title=str(item.get("title", item_key)),
                            price_coins=price,
                            metadata_json=json.dumps(
                                {
                                    "seeded": True,
                                    "reward_type": str(item.get("reward_type", "self_reward")).strip().lower(),
                                }
                            ),
                            purchased_at=purchased_at,
                            claimed_at=claimed_at,
                            claimed_note="Seeded redemption" if claimed_at else None,
                        )
                    )
                    db.session.add(
                        CoinLedger(
                            user_id=user.id,
                            source=f"Shop purchase: {item.get('title', item_key)} (seeded)",
                            amount=-price,
                            created_at=purchased_at,
                        )
                    )
                    earned_total -= price

        user.coins = max(int(earned_total), 0)
        db.session.add(user)
    else:
        ledger_balance = (
            db.session.query(func.coalesce(func.sum(CoinLedger.amount), 0))
            .filter(CoinLedger.user_id == user.id)
            .scalar()
            or 0
        )
        user.coins = max(int(ledger_balance), 0)
        db.session.add(user)

    avatar_profile = ensure_avatar_profile(user)
    if include_richer_data:
        avatar_profile.body_type = "female"
        avatar_profile.style = "cyber"
        avatar_profile.top = "jacket_black"
        avatar_profile.bottom = "jeans_dark"
        avatar_profile.accessory = "glasses_round"
        avatar_profile.palette = "neon"
    db.session.add(avatar_profile)


def seed_recurring_rules(user: User, include_richer_data: bool) -> None:
    if RecurringRule.query.filter_by(user_id=user.id).count() > 0:
        return

    today = date.today()
    rules = [
        RecurringRule(
            user_id=user.id,
            title="Morning Workout",
            task_type="habit",
            priority="high",
            xp_reward=20,
            frequency="daily",
            interval=1,
            start_on=today,
            active=True,
        ),
        RecurringRule(
            user_id=user.id,
            title="Read 10 Pages",
            task_type="habit",
            priority="medium",
            xp_reward=12,
            frequency="daily",
            interval=1,
            start_on=today,
            active=True,
        ),
    ]

    if include_richer_data:
        rules.append(
            RecurringRule(
                user_id=user.id,
                title="Weekly Planning Session",
                task_type="task",
                priority="medium",
                xp_reward=30,
                frequency="weekly",
                interval=1,
                days_of_week=encode_weekdays([0]),
                start_on=today,
                active=True,
            )
        )

    db.session.add_all(rules)


def seed_reminder_settings(user: User, enable_delivery: bool) -> None:
    settings_row = ensure_reminder_settings(user)
    if enable_delivery:
        settings_row.email_enabled = True
        settings_row.sms_enabled = False
        settings_row.email_address = user.email
        if not settings_row.phone_number:
            settings_row.phone_number = "+15550000000"
    db.session.add(settings_row)


def ensure_space_member(space: Space, user: User, role: str) -> SpaceMember:
    existing = SpaceMember.query.filter_by(space_id=space.id, user_id=user.id).first()
    if existing is None:
        existing = SpaceMember(space_id=space.id, user_id=user.id, role=role)
    else:
        existing.role = role
    db.session.add(existing)
    db.session.flush()
    return existing


def seed_shared_spaces(owner_user: User, admin_user: User, member_user: User) -> None:
    space = Space.query.filter_by(owner_user_id=owner_user.id, name="LifeOS Guild Alpha").first()
    if space is None:
        space = Space(name="LifeOS Guild Alpha", owner_user_id=owner_user.id)
        db.session.add(space)
        db.session.flush()
    else:
        space.owner_user_id = owner_user.id
        db.session.add(space)
        db.session.flush()

    ensure_space_member(space, owner_user, "owner")
    ensure_space_member(space, admin_user, "admin")
    ensure_space_member(space, member_user, "member")
    ensure_space_role_templates(space)

    if SpaceTask.query.filter_by(space_id=space.id).count() == 0:
        today = date.today()
        now = datetime.utcnow()
        rows = [
            ("Finalize product roadmap", "quest", "high", 120, today),
            ("Weekly engineering sync notes", "task", "medium", 30, today),
            ("Update onboarding checklist", "task", "low", 20, today + timedelta(days=1)),
            ("Prepare release candidate scope", "quest", "high", 100, today + timedelta(days=2)),
        ]
        creator_cycle = [owner_user.id, admin_user.id, member_user.id, owner_user.id]
        for idx, (title, task_type, priority, xp_reward, due_on) in enumerate(rows):
            db.session.add(
                SpaceTask(
                    space_id=space.id,
                    created_by_user_id=creator_cycle[idx % len(creator_cycle)],
                    title=title,
                    status="todo",
                    task_type=task_type,
                    priority=priority,
                    xp_reward=xp_reward,
                    due_on=due_on,
                    created_at=now - timedelta(hours=8 - idx),
                )
            )


def init_db() -> None:
    db.create_all()
    migrate_schema()

    demo_user = ensure_user("demo", "Demo User", "demo@lifeos.app", DEFAULT_DEMO_PASSWORD)
    test_user = ensure_user("testuser1", "Test User 1", "testuser1@lifeos.app", DEFAULT_TESTUSER1_PASSWORD)
    ally_user = ensure_user("allydev", "Ally Dev", "allydev@lifeos.app", DEFAULT_ALLYDEV_PASSWORD)
    test_user.season_pass_premium = True
    demo_user.season_pass_premium = False
    ally_user.season_pass_premium = False
    db.session.add(demo_user)
    db.session.add(test_user)
    db.session.add(ally_user)

    seed_user_data(demo_user, include_richer_data=False)
    seed_user_data(test_user, include_richer_data=True)
    seed_user_data(ally_user, include_richer_data=False)
    seed_recurring_rules(demo_user, include_richer_data=False)
    seed_recurring_rules(test_user, include_richer_data=True)
    seed_recurring_rules(ally_user, include_richer_data=False)
    seed_reminder_settings(demo_user, enable_delivery=False)
    seed_reminder_settings(test_user, enable_delivery=True)
    seed_reminder_settings(ally_user, enable_delivery=False)
    seed_shared_spaces(test_user, ally_user, demo_user)
    for existing_space in Space.query.all():
        ensure_space_role_templates(existing_space)
    db.session.commit()
    run_recurring_generation(source="init", commit=True)


def apply_habit_completion(user_id: int, task_title: str, completed_on: date) -> None:
    habit = Habit.query.filter_by(user_id=user_id, name=task_title).first()
    if habit is None:
        habit = Habit(user_id=user_id, name=task_title, current_streak=1, longest_streak=1, last_completed_on=completed_on)
        db.session.add(habit)
        db.session.flush()
    elif habit.last_completed_on != completed_on:
        if habit.last_completed_on == completed_on - timedelta(days=1):
            habit.current_streak += 1
        elif habit.last_completed_on is None or habit.last_completed_on < completed_on - timedelta(days=1):
            habit.current_streak = 1
        habit.last_completed_on = completed_on
        habit.longest_streak = max(habit.longest_streak, habit.current_streak)
        db.session.add(habit)

    existing_log = HabitLog.query.filter_by(user_id=user_id, habit_id=habit.id, completed_on=completed_on).first()
    if existing_log is None:
        db.session.add(HabitLog(user_id=user_id, habit_id=habit.id, completed_on=completed_on))


def nudge_goal_progress(user_id: int, source_reason: str = "manual") -> tuple[int, int]:
    goal = (
        Goal.query.filter(Goal.user_id == user_id, Goal.current_value < Goal.target_value)
        .order_by(Goal.deadline.is_(None), Goal.deadline.asc())
        .first()
    )
    if goal is None:
        return 0, 0

    before_value = goal.current_value
    goal.current_value = min(goal.current_value + 1, goal.target_value)
    db.session.add(goal)

    if goal.current_value <= before_value:
        return 0, 0

    xp_total = award_action_xp(
        user_id,
        "goal.progress.increment",
        f"Goal progress: {goal.title}",
        8,
    )
    coin_total = award_action_coins(
        user_id,
        "goal.progress.increment",
        f"Goal progress coins: {goal.title}",
        4,
    )

    if goal.current_value >= goal.target_value:
        xp_total += award_action_xp(
            user_id,
            "goal.progress.complete_bonus",
            f"Goal completed: {goal.title}",
            60,
        )
        coin_total += award_action_coins(
            user_id,
            "goal.progress.complete_bonus",
            f"Goal completed coins: {goal.title}",
            20,
        )

    return xp_total, coin_total


def build_dashboard_payload(user: User) -> dict[str, Any]:
    today = date.today()
    priority_rank = case(
        (Task.priority == "high", 0),
        (Task.priority == "medium", 1),
        (Task.priority == "low", 2),
        else_=3,
    )

    xp_total = (
        db.session.query(func.coalesce(func.sum(XpLedger.points), 0))
        .filter(XpLedger.user_id == user.id)
        .scalar()
        or 0
    )
    coins_balance = max(int(user.coins or 0), 0)
    level, xp_into_level, xp_for_next_level = level_progress(xp_total)

    current_streak = (
        db.session.query(func.coalesce(func.max(Habit.current_streak), 0))
        .filter(Habit.user_id == user.id)
        .scalar()
        or 0
    )
    longest_streak = (
        db.session.query(func.coalesce(func.max(Habit.longest_streak), 0))
        .filter(Habit.user_id == user.id)
        .scalar()
        or 0
    )

    today_tasks = (
        Task.query.filter(Task.user_id == user.id, Task.status == "todo", Task.due_on <= today)
        .order_by(priority_rank.asc(), Task.created_at.asc())
        .limit(8)
        .all()
    )
    if not today_tasks:
        today_tasks = (
            Task.query.filter(Task.user_id == user.id, Task.status == "todo")
            .order_by(priority_rank.asc(), Task.created_at.asc())
            .limit(8)
            .all()
        )

    completed_rows = (
        Task.query.filter(Task.user_id == user.id, Task.status == "done")
        .order_by(Task.completed_at.is_(None), Task.completed_at.desc(), Task.created_at.desc())
        .limit(8)
        .all()
    )
    goal_rows = Goal.query.filter_by(user_id=user.id).order_by(Goal.deadline.is_(None), Goal.deadline.asc()).all()

    open_quests = Task.query.filter_by(user_id=user.id, status="todo", task_type="quest").count()
    tasks_due_today = Task.query.filter_by(user_id=user.id, status="todo", due_on=today).count()
    completed_today = Task.query.filter(
        Task.user_id == user.id,
        Task.status == "done",
        func.date(func.coalesce(Task.completed_at, Task.created_at)) == today.isoformat(),
    ).count()
    goals_in_progress = Goal.query.filter(Goal.user_id == user.id, Goal.current_value < Goal.target_value).count()
    achievement_summary = build_achievements_payload(user, grant_new=False).get("summary", {})
    challenge_summary = build_challenges_payload(user).get("summary", {})
    season_pass_summary = build_season_pass_payload(user).get("summary", {})

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "coins": coins_balance,
            "level": level,
            "xp_total": xp_total,
            "xp_into_level": xp_into_level,
            "xp_for_next_level": xp_for_next_level,
        },
        "stats": {
            "tasks_due_today": tasks_due_today,
            "completed_today": completed_today,
            "open_quests": open_quests,
            "goals_in_progress": goals_in_progress,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "achievements_unlocked": int(achievement_summary.get("unlocked", 0)),
            "achievements_total": int(achievement_summary.get("total", 0)),
            "challenge_claimable": int(challenge_summary.get("claimable", 0)),
            "season_tier": int(season_pass_summary.get("current_tier", 1)),
            "season_pass_claimable": int(season_pass_summary.get("claimable", 0)),
        },
        "today_label": today.strftime("%b %d"),
        "today_tasks": [
            {
                "id": task.id,
                "title": task.title,
                "task_type": task.task_type,
                "task_type_label": TASK_TYPE_LABELS.get(task.task_type, "Task"),
                "xp_reward": task.xp_reward,
                "xp_effective": calculate_task_completion_xp(task)[0],
                "priority": task.priority,
                "status": task.status,
                "due_on": task.due_on.isoformat() if task.due_on else None,
            }
            for task in today_tasks
        ],
        "recent_completions": [
            {
                "id": task.id,
                "title": task.title,
                "task_type": task.task_type,
                "xp_earned": calculate_task_completion_xp(task)[0],
                "completed_on": (task.completed_at or task.created_at).date().isoformat(),
                "completed_label": relative_day_label((task.completed_at or task.created_at).date(), today),
            }
            for task in completed_rows
        ],
        "goals": [
            {
                "id": goal.id,
                "title": goal.title,
                "target_value": goal.target_value,
                "current_value": goal.current_value,
                "progress": round((goal.current_value / goal.target_value) * 100, 1)
                if goal.target_value
                else 0,
                "deadline": goal.deadline.isoformat() if goal.deadline else None,
            }
            for goal in goal_rows
        ],
        "quote": daily_quote_for_user(user, today),
    }


def build_shop_payload(user: User) -> dict[str, Any]:
    now_utc, day_start, next_reset, day_key = shop_day_window()
    active_item_keys = build_shop_rotation_active_keys(day_key)
    owned_item_keys = user_owned_shop_item_keys(user.id)
    if bool(user.season_pass_premium):
        owned_item_keys.add(SEASON_PASS_PREMIUM_SHOP_ITEM_KEY)
    coins_balance = max(int(user.coins or 0), 0)
    global_daily_purchases = load_shop_purchase_counts_since(day_start)
    user_daily_purchases = load_shop_purchase_counts_since(day_start, user_id=user.id)
    catalog_rows = [
        serialize_shop_item_for_user(
            item,
            owned_item_keys=owned_item_keys,
            coins_balance=coins_balance,
            active_item_keys=active_item_keys,
            global_daily_purchases=global_daily_purchases,
            user_daily_purchases=user_daily_purchases,
        )
        for item in SHOP_ITEMS
    ]
    catalog_rows.sort(
        key=lambda row: (
            int(SHOP_CATEGORY_ORDER.get(str(row.get("category", "shop")), 99)),
            0 if row.get("available_today") else 1,
            -int(SHOP_RARITY_ORDER.get(str(row.get("rarity", "common")), 0)),
            int(row.get("price_coins", 0)),
            str(row.get("title", "")).lower(),
        )
    )
    category_counts: dict[str, dict[str, int]] = {}
    for row in catalog_rows:
        category_key = row["category"]
        if category_key not in category_counts:
            category_counts[category_key] = {"count": 0, "available_count": 0}
        category_counts[category_key]["count"] += 1
        if bool(row.get("available_today", False)):
            category_counts[category_key]["available_count"] += 1

    recent_purchases = (
        ShopPurchase.query.filter_by(user_id=user.id)
        .order_by(ShopPurchase.purchased_at.desc(), ShopPurchase.id.desc())
        .limit(24)
        .all()
    )
    seconds_until_reset = max(int((next_reset - now_utc).total_seconds()), 0)
    return {
        "coins_balance": coins_balance,
        "rotation": {
            "day_key": day_key,
            "generated_at": now_utc.isoformat(),
            "reset_at": next_reset.isoformat(),
            "seconds_until_reset": seconds_until_reset,
            "daily_slots": {key: int(value) for key, value in SHOP_ROTATION_CATEGORY_SLOTS.items()},
            "active_item_keys": sorted(active_item_keys),
        },
        "categories": [
            {
                "key": key,
                "label": SHOP_CATEGORY_LABELS.get(key, key.replace("_", " ").title()),
                "count": int(counters.get("count", 0)),
                "available_count": int(counters.get("available_count", 0)),
            }
            for key, counters in sorted(
                category_counts.items(),
                key=lambda entry: (
                    int(SHOP_CATEGORY_ORDER.get(str(entry[0]), 99)),
                    str(entry[0]),
                ),
            )
        ],
        "items": catalog_rows,
        "owned_item_keys": sorted(owned_item_keys),
        "recent_purchases": [serialize_shop_purchase(row) for row in recent_purchases],
    }


def build_inventory_payload(user: User, history_limit: int = 240) -> dict[str, Any]:
    safe_limit = min(max(int(history_limit or 240), 24), 500)
    coins_balance = max(int(user.coins or 0), 0)
    total_purchases = ShopPurchase.query.filter_by(user_id=user.id).count()
    total_spent = (
        db.session.query(func.coalesce(func.sum(ShopPurchase.price_coins), 0))
        .filter(ShopPurchase.user_id == user.id)
        .scalar()
    )
    total_spent_value = max(int(total_spent or 0), 0)

    category_rows = (
        db.session.query(ShopPurchase.category, func.count(ShopPurchase.id), func.coalesce(func.sum(ShopPurchase.price_coins), 0))
        .filter(ShopPurchase.user_id == user.id)
        .group_by(ShopPurchase.category)
        .all()
    )
    category_summaries = [
        {
            "key": str(category or "shop").strip().lower(),
            "label": SHOP_CATEGORY_LABELS.get(str(category or "shop").strip().lower(), str(category or "shop").replace("_", " ").title()),
            "count": int(count or 0),
            "coins_spent": max(int(spent or 0), 0),
        }
        for category, count, spent in category_rows
    ]
    category_summaries.sort(key=lambda row: row["label"].lower())

    purchase_rows = (
        ShopPurchase.query.filter_by(user_id=user.id)
        .order_by(ShopPurchase.purchased_at.desc(), ShopPurchase.id.desc())
        .limit(safe_limit)
        .all()
    )
    purchase_history = [serialize_shop_purchase(row) for row in purchase_rows]
    avatar_unlock_by_key: dict[str, dict[str, Any]] = {}
    reward_redemptions: list[dict[str, Any]] = []
    for row in purchase_history:
        reward_type = str(row.get("reward_type", "self_reward")).strip().lower()
        item_key = str(row.get("item_key", "")).strip().lower()
        if reward_type == "avatar_unlock" and item_key and item_key not in avatar_unlock_by_key:
            avatar_unlock_by_key[item_key] = row
        if reward_type == "self_reward":
            reward_redemptions.append(row)
    avatar_unlocks = sorted(
        avatar_unlock_by_key.values(),
        key=lambda row: str(row.get("purchased_at") or ""),
        reverse=True,
    )

    lookback_days = 14
    today = date.today()
    start_day = today - timedelta(days=lookback_days - 1)
    start_dt = datetime.combine(start_day, datetime.min.time())
    purchase_day_expr = func.date(ShopPurchase.purchased_at)
    daily_rows = (
        db.session.query(
            purchase_day_expr.label("day"),
            func.count(ShopPurchase.id).label("count"),
            func.coalesce(func.sum(ShopPurchase.price_coins), 0).label("coins"),
        )
        .filter(ShopPurchase.user_id == user.id, ShopPurchase.purchased_at >= start_dt)
        .group_by(purchase_day_expr)
        .order_by(purchase_day_expr.asc())
        .all()
    )
    daily_index = {
        str(day or ""): {"count": int(count or 0), "coins": max(int(coins or 0), 0)}
        for day, count, coins in daily_rows
    }
    spending_by_day = []
    for offset in range(lookback_days):
        day_value = start_day + timedelta(days=offset)
        key = day_value.isoformat()
        bucket = daily_index.get(key, {"count": 0, "coins": 0})
        spending_by_day.append(
            {
                "date": key,
                "label": day_value.strftime("%b %d"),
                "purchase_count": int(bucket["count"]),
                "coins_spent": int(bucket["coins"]),
            }
        )

    unique_owned_item_keys = user_owned_shop_item_keys(user.id)
    claimed_rewards = sum(1 for row in reward_redemptions if row.get("is_claimed"))
    unclaimed_rewards = max(len(reward_redemptions) - claimed_rewards, 0)
    return {
        "coins_balance": coins_balance,
        "summary": {
            "total_purchases": int(total_purchases or 0),
            "total_coins_spent": total_spent_value,
            "avatar_unlocks_owned": int(len([key for key in unique_owned_item_keys if key.startswith("avatar_")])),
            "self_rewards_redeemed": int(
                db.session.query(func.count(ShopPurchase.id))
                .filter(ShopPurchase.user_id == user.id, ShopPurchase.category == "self_reward")
                .scalar()
                or 0
            ),
            "self_rewards_claimed": int(claimed_rewards),
            "self_rewards_unclaimed": int(unclaimed_rewards),
            "recent_purchases_loaded": int(len(purchase_history)),
        },
        "filters": {
            "categories": category_summaries,
            "reward_types": [
                {"key": "avatar_unlock", "label": "Avatar Unlocks"},
                {"key": "season_pass_premium_unlock", "label": "Season Pass Unlocks"},
                {"key": "self_reward", "label": "Self Rewards"},
            ],
            "history_limit": safe_limit,
        },
        "avatar_unlocks": avatar_unlocks,
        "reward_redemptions": reward_redemptions,
        "purchase_history": purchase_history,
        "spending_by_day": spending_by_day,
    }


def collect_achievement_metrics(user_id: int) -> dict[str, int]:
    xp_total = (
        db.session.query(func.coalesce(func.sum(XpLedger.points), 0))
        .filter(XpLedger.user_id == user_id)
        .scalar()
        or 0
    )
    task_done_total = Task.query.filter(Task.user_id == user_id, Task.status == "done").count()
    quest_done_total = Task.query.filter(Task.user_id == user_id, Task.status == "done", Task.task_type == "quest").count()
    habit_done_total = HabitLog.query.filter(HabitLog.user_id == user_id).count()
    goal_completed_total = Goal.query.filter(Goal.user_id == user_id, Goal.current_value >= Goal.target_value).count()
    habit_streak_best = (
        db.session.query(func.coalesce(func.max(Habit.longest_streak), 0))
        .filter(Habit.user_id == user_id)
        .scalar()
        or 0
    )
    coins_earned_total = (
        db.session.query(func.coalesce(func.sum(CoinLedger.amount), 0))
        .filter(CoinLedger.user_id == user_id, CoinLedger.amount > 0)
        .scalar()
        or 0
    )
    coins_spent_total = (
        db.session.query(func.coalesce(func.sum(ShopPurchase.price_coins), 0))
        .filter(ShopPurchase.user_id == user_id)
        .scalar()
        or 0
    )
    avatar_unlock_owned_total = (
        db.session.query(func.count(func.distinct(ShopPurchase.item_key)))
        .filter(ShopPurchase.user_id == user_id, ShopPurchase.category == "avatar")
        .scalar()
        or 0
    )
    return {
        "xp_total": max(int(xp_total or 0), 0),
        "task_done_total": max(int(task_done_total or 0), 0),
        "quest_done_total": max(int(quest_done_total or 0), 0),
        "habit_done_total": max(int(habit_done_total or 0), 0),
        "goal_completed_total": max(int(goal_completed_total or 0), 0),
        "habit_streak_best": max(int(habit_streak_best or 0), 0),
        "coins_earned_total": max(int(coins_earned_total or 0), 0),
        "coins_spent_total": max(int(coins_spent_total or 0), 0),
        "avatar_unlock_owned_total": max(int(avatar_unlock_owned_total or 0), 0),
        "completion_total": max(int(task_done_total or 0) + int(habit_done_total or 0), 0),
    }


def build_achievements_payload(user: User, *, grant_new: bool = False, unlock_time: datetime | None = None) -> dict[str, Any]:
    metrics = collect_achievement_metrics(user.id)
    existing_rows = UserAchievement.query.filter_by(user_id=user.id).all()
    existing_by_key = {str(row.achievement_key): row for row in existing_rows}
    unlocked_now: list[dict[str, Any]] = []
    now_utc = unlock_time or datetime.utcnow()

    rows: list[dict[str, Any]] = []
    for definition in ACHIEVEMENT_DEFINITIONS:
        achievement_key = str(definition.get("key", "")).strip().lower()
        if not achievement_key:
            continue
        metric_key = str(definition.get("metric", "")).strip()
        metric_value = max(int(metrics.get(metric_key, 0) or 0), 0)
        target_value = max(int(definition.get("target", 1) or 1), 1)
        progress_value = min(metric_value, target_value)
        unlocked = metric_value >= target_value

        existing_row = existing_by_key.get(achievement_key)
        if unlocked and existing_row is None and grant_new:
            reward_xp = max(int(definition.get("reward_xp", 0) or 0), 0)
            reward_coins = max(int(definition.get("reward_coins", 0) or 0), 0)
            if reward_xp > 0:
                award_xp(user.id, f"Achievement unlocked: {definition.get('title', achievement_key)}", reward_xp, now_utc)
            if reward_coins > 0:
                award_coins(user.id, f"Achievement unlocked coins: {definition.get('title', achievement_key)}", reward_coins, now_utc)
            existing_row = UserAchievement(
                user_id=user.id,
                achievement_key=achievement_key,
                title=str(definition.get("title", achievement_key)).strip(),
                description=str(definition.get("description", "")).strip(),
                icon=str(definition.get("icon", "\U0001F3C5")).strip() or "\U0001F3C5",
                rarity=str(definition.get("rarity", "common")).strip().lower() or "common",
                target_value=target_value,
                unlocked_value=metric_value,
                reward_xp=reward_xp,
                reward_coins=reward_coins,
                unlocked_at=now_utc,
            )
            db.session.add(existing_row)
            db.session.flush()
            existing_by_key[achievement_key] = existing_row
            unlocked_now.append(
                {
                    "key": achievement_key,
                    "title": existing_row.title,
                    "reward_xp": int(existing_row.reward_xp or 0),
                    "reward_coins": int(existing_row.reward_coins or 0),
                    "icon": existing_row.icon,
                }
            )

        persisted_row = existing_by_key.get(achievement_key)
        rows.append(
            {
                "key": achievement_key,
                "title": str(definition.get("title", achievement_key)).strip(),
                "description": str(definition.get("description", "")).strip(),
                "icon": str(definition.get("icon", "\U0001F3C5")).strip() or "\U0001F3C5",
                "rarity": str(definition.get("rarity", "common")).strip().lower() or "common",
                "rarity_label": SHOP_RARITY_LABELS.get(str(definition.get("rarity", "common")).strip().lower(), "Common"),
                "metric_key": metric_key,
                "target_value": target_value,
                "progress_value": progress_value,
                "current_value": metric_value,
                "progress_percent": round((progress_value / target_value) * 100, 1) if target_value > 0 else 0,
                "reward_xp": max(int(definition.get("reward_xp", 0) or 0), 0),
                "reward_coins": max(int(definition.get("reward_coins", 0) or 0), 0),
                "unlocked": bool(persisted_row is not None or unlocked),
                "unlocked_at": persisted_row.unlocked_at.isoformat() if persisted_row and persisted_row.unlocked_at else None,
            }
        )

    rows.sort(
        key=lambda row: (
            0 if row.get("unlocked") else 1,
            -int(ACHIEVEMENT_RARITY_ORDER.get(str(row.get("rarity", "common")), 0)),
            str(row.get("title", "")).lower(),
        )
    )
    unlocked_count = sum(1 for row in rows if row.get("unlocked"))
    return {
        "summary": {
            "total": int(len(rows)),
            "unlocked": int(unlocked_count),
            "locked": int(max(len(rows) - unlocked_count, 0)),
            "completion_rate": round((unlocked_count / max(len(rows), 1)) * 100, 1),
            "newly_unlocked": int(len(unlocked_now)),
        },
        "recent_unlocks": unlocked_now,
        "items": rows,
    }


def challenge_window_context(window_type: str, now_utc: datetime | None = None) -> dict[str, Any]:
    normalized_type = str(window_type or "").strip().lower()
    if normalized_type not in CHALLENGE_WINDOW_TYPES:
        raise ValueError("window_type must be daily or weekly")

    current = now_utc or datetime.utcnow()
    today = current.date()
    if normalized_type == "daily":
        start_day = today
        end_day = today
        start_dt = datetime.combine(start_day, datetime.min.time())
        reset_dt = start_dt + timedelta(days=1)
        window_key = start_day.isoformat()
        label = start_day.strftime("%b %d")
    else:
        start_day = today - timedelta(days=today.weekday())
        end_day = start_day + timedelta(days=6)
        start_dt = datetime.combine(start_day, datetime.min.time())
        reset_dt = start_dt + timedelta(days=7)
        window_key = f"{start_day.isoformat()}_{end_day.isoformat()}"
        label = f"Week of {start_day.strftime('%b %d')}"

    return {
        "window_type": normalized_type,
        "window_key": window_key,
        "label": label,
        "start_day": start_day,
        "end_day": end_day,
        "start_dt": start_dt,
        "reset_at": reset_dt,
        "seconds_until_reset": max(int((reset_dt - current).total_seconds()), 0),
    }


def select_active_challenge_templates(templates: list[dict[str, Any]], *, window_type: str, window_key: str) -> list[dict[str, Any]]:
    if not templates:
        return []
    active_count = max(int(CHALLENGE_ROTATION_COUNT_BY_WINDOW.get(window_type, len(templates)) or len(templates)), 1)
    scored_rows: list[tuple[int, dict[str, Any]]] = []
    for template in templates:
        challenge_key = str(template.get("key", "")).strip().lower()
        if not challenge_key:
            continue
        digest = hashlib.sha1(f"{window_type}:{window_key}:{challenge_key}".encode("utf-8")).hexdigest()
        score = int(digest[:8], 16)
        scored_rows.append((score, template))
    scored_rows.sort(key=lambda row: (row[0], str(row[1].get("key", ""))))
    return [row[1] for row in scored_rows[: min(active_count, len(scored_rows))]]


def collect_challenge_metrics(user_id: int, *, start_dt: datetime, start_day: date) -> dict[str, int]:
    task_completion_moment = func.coalesce(Task.completed_at, Task.created_at)
    task_done_total = Task.query.filter(
        Task.user_id == user_id,
        Task.status == "done",
        task_completion_moment >= start_dt,
    ).count()
    quest_done_total = Task.query.filter(
        Task.user_id == user_id,
        Task.status == "done",
        Task.task_type == "quest",
        task_completion_moment >= start_dt,
    ).count()
    habit_done_total = HabitLog.query.filter(HabitLog.user_id == user_id, HabitLog.completed_on >= start_day).count()
    xp_earned_total = (
        db.session.query(func.coalesce(func.sum(XpLedger.points), 0))
        .filter(XpLedger.user_id == user_id, XpLedger.created_at >= start_dt)
        .scalar()
        or 0
    )
    coins_earned_total = (
        db.session.query(func.coalesce(func.sum(CoinLedger.amount), 0))
        .filter(CoinLedger.user_id == user_id, CoinLedger.created_at >= start_dt, CoinLedger.amount > 0)
        .scalar()
        or 0
    )
    coins_spent_total = (
        db.session.query(func.coalesce(func.sum(-CoinLedger.amount), 0))
        .filter(CoinLedger.user_id == user_id, CoinLedger.created_at >= start_dt, CoinLedger.amount < 0)
        .scalar()
        or 0
    )
    completion_total = max(int(task_done_total or 0) + int(habit_done_total or 0), 0)
    return {
        "task_done_total": max(int(task_done_total or 0), 0),
        "quest_done_total": max(int(quest_done_total or 0), 0),
        "habit_done_total": max(int(habit_done_total or 0), 0),
        "xp_earned_total": max(int(xp_earned_total or 0), 0),
        "coins_earned_total": max(int(coins_earned_total or 0), 0),
        "coins_spent_total": max(int(coins_spent_total or 0), 0),
        "completion_total": completion_total,
    }


def build_challenges_payload(user: User, *, now_utc: datetime | None = None, only_window: str | None = None) -> dict[str, Any]:
    current = now_utc or datetime.utcnow()
    window_types = [only_window] if only_window else ["daily", "weekly"]
    payload: dict[str, Any] = {}
    claimable_total = 0
    completed_total = 0
    challenge_total = 0

    for window_type in window_types:
        context = challenge_window_context(window_type, now_utc=current)
        templates = CHALLENGE_DAILY_TEMPLATES if context["window_type"] == "daily" else CHALLENGE_WEEKLY_TEMPLATES
        active_templates = select_active_challenge_templates(
            templates,
            window_type=context["window_type"],
            window_key=context["window_key"],
        )
        metrics = collect_challenge_metrics(user.id, start_dt=context["start_dt"], start_day=context["start_day"])
        claim_rows = ChallengeClaim.query.filter_by(
            user_id=user.id,
            window_type=context["window_type"],
            window_key=context["window_key"],
        ).all()
        claims_by_key = {str(row.challenge_key): row for row in claim_rows}

        challenge_rows: list[dict[str, Any]] = []
        for template in active_templates:
            challenge_key = str(template.get("key", "")).strip().lower()
            if not challenge_key:
                continue
            metric_key = str(template.get("metric", "")).strip()
            target_value = max(int(template.get("target", 1) or 1), 1)
            current_value = max(int(metrics.get(metric_key, 0) or 0), 0)
            progress_value = min(current_value, target_value)
            completed = current_value >= target_value
            claim_row = claims_by_key.get(challenge_key)
            claimed = claim_row is not None
            claimable = bool(completed and not claimed)
            challenge_rows.append(
                {
                    "key": challenge_key,
                    "title": str(template.get("title", challenge_key)).strip(),
                    "description": str(template.get("description", "")).strip(),
                    "metric_key": metric_key,
                    "target_value": target_value,
                    "current_value": current_value,
                    "progress_value": progress_value,
                    "progress_percent": round((progress_value / target_value) * 100, 1) if target_value > 0 else 0,
                    "reward_xp": max(int(template.get("reward_xp", 0) or 0), 0),
                    "reward_coins": max(int(template.get("reward_coins", 0) or 0), 0),
                    "completed": bool(completed),
                    "claimed": bool(claimed),
                    "claimable": claimable,
                    "claimed_at": claim_row.claimed_at.isoformat() if claim_row and claim_row.claimed_at else None,
                }
            )
        challenge_rows.sort(
            key=lambda row: (
                0 if row.get("claimable") else 1,
                0 if row.get("completed") else 1,
                str(row.get("title", "")).lower(),
            )
        )
        window_completed = sum(1 for row in challenge_rows if row.get("completed"))
        window_claimed = sum(1 for row in challenge_rows if row.get("claimed"))
        window_claimable = sum(1 for row in challenge_rows if row.get("claimable"))

        challenge_total += len(challenge_rows)
        completed_total += window_completed
        claimable_total += window_claimable
        payload[context["window_type"]] = {
            "window_type": context["window_type"],
            "window_key": context["window_key"],
            "label": context["label"],
            "start": context["start_day"].isoformat(),
            "end": context["end_day"].isoformat(),
            "reset_at": context["reset_at"].isoformat(),
            "seconds_until_reset": int(context["seconds_until_reset"]),
            "summary": {
                "total": int(len(challenge_rows)),
                "completed": int(window_completed),
                "claimed": int(window_claimed),
                "claimable": int(window_claimable),
            },
            "challenges": challenge_rows,
        }

    payload["summary"] = {
        "total": int(challenge_total),
        "completed": int(completed_total),
        "claimable": int(claimable_total),
    }
    return payload


def clamp_timeline_days(raw_days: int | None) -> int:
    return clamp_day_window(raw_days, default=TIMELINE_DEFAULT_DAYS, minimum=TIMELINE_DAY_RANGE_MIN, maximum=TIMELINE_DAY_RANGE_MAX)


def build_timeline_payload(user: User, days: int | None = None) -> dict[str, Any]:
    window_days = clamp_timeline_days(days)
    today = date.today()
    start_day = today - timedelta(days=window_days - 1)
    start_dt = datetime.combine(start_day, datetime.min.time())
    task_completion_moment = func.coalesce(Task.completed_at, Task.created_at)

    events: list[dict[str, Any]] = []
    done_tasks = (
        Task.query.filter(Task.user_id == user.id, Task.status == "done", task_completion_moment >= start_dt)
        .order_by(task_completion_moment.desc())
        .limit(260)
        .all()
    )
    for task in done_tasks:
        completed_at = task.completed_at or task.created_at
        if completed_at is None:
            continue
        events.append(
            {
                "id": f"task-{task.id}",
                "event_type": "task_completed",
                "title": f"Completed {TASK_TYPE_LABELS.get(task.task_type, 'Task').lower()}: {task.title}",
                "detail": f"{calculate_task_completion_xp(task)[0]} XP potential",
                "timestamp": completed_at.isoformat(),
                "source": "tasks",
            }
        )

    habit_rows = (
        db.session.query(HabitLog, Habit.name)
        .join(Habit, Habit.id == HabitLog.habit_id)
        .filter(HabitLog.user_id == user.id, HabitLog.completed_on >= start_day)
        .order_by(HabitLog.completed_on.desc(), HabitLog.id.desc())
        .limit(260)
        .all()
    )
    for row, habit_name in habit_rows:
        completed_at = datetime.combine(row.completed_on, datetime.min.time()) + timedelta(hours=12)
        events.append(
            {
                "id": f"habit-{row.id}",
                "event_type": "habit_completed",
                "title": f"Habit check-in: {habit_name}",
                "detail": "Habit completed",
                "timestamp": completed_at.isoformat(),
                "source": "habits",
            }
        )

    purchase_rows = (
        ShopPurchase.query.filter(ShopPurchase.user_id == user.id, ShopPurchase.purchased_at >= start_dt)
        .order_by(ShopPurchase.purchased_at.desc(), ShopPurchase.id.desc())
        .limit(220)
        .all()
    )
    for purchase in purchase_rows:
        events.append(
            {
                "id": f"shop-purchase-{purchase.id}",
                "event_type": "shop_purchase",
                "title": f"Purchased: {purchase.title}",
                "detail": f"Spent {int(purchase.price_coins or 0)} coins",
                "timestamp": purchase.purchased_at.isoformat() if purchase.purchased_at else None,
                "source": "shop",
            }
        )
        if purchase.claimed_at:
            events.append(
                {
                    "id": f"shop-claim-{purchase.id}",
                    "event_type": "reward_claimed",
                    "title": f"Redeemed reward: {purchase.title}",
                    "detail": purchase.claimed_note or "Marked as claimed",
                    "timestamp": purchase.claimed_at.isoformat(),
                    "source": "inventory",
                }
            )

    achievement_rows = (
        UserAchievement.query.filter(UserAchievement.user_id == user.id, UserAchievement.unlocked_at >= start_dt)
        .order_by(UserAchievement.unlocked_at.desc(), UserAchievement.id.desc())
        .limit(120)
        .all()
    )
    for achievement in achievement_rows:
        events.append(
            {
                "id": f"achievement-{achievement.id}",
                "event_type": "achievement_unlocked",
                "title": f"{achievement.icon} Achievement unlocked: {achievement.title}",
                "detail": achievement.description,
                "timestamp": achievement.unlocked_at.isoformat() if achievement.unlocked_at else None,
                "source": "achievements",
            }
        )

    challenge_rows = (
        ChallengeClaim.query.filter(ChallengeClaim.user_id == user.id, ChallengeClaim.claimed_at >= start_dt)
        .order_by(ChallengeClaim.claimed_at.desc(), ChallengeClaim.id.desc())
        .limit(120)
        .all()
    )
    for challenge_claim in challenge_rows:
        reward_label = []
        if challenge_claim.reward_xp:
            reward_label.append(f"+{int(challenge_claim.reward_xp)} XP")
        if challenge_claim.reward_coins:
            reward_label.append(f"+{int(challenge_claim.reward_coins)} coins")
        events.append(
            {
                "id": f"challenge-{challenge_claim.id}",
                "event_type": "challenge_claimed",
                "title": f"Challenge reward claimed: {challenge_claim.challenge_title}",
                "detail": ", ".join(reward_label) if reward_label else "Claim completed",
                "timestamp": challenge_claim.claimed_at.isoformat() if challenge_claim.claimed_at else None,
                "source": "challenges",
            }
        )

    events = [row for row in events if row.get("timestamp")]
    events.sort(key=lambda row: (str(row.get("timestamp", "")), str(row.get("id", ""))), reverse=True)
    events = events[:500]

    day_buckets: dict[str, dict[str, Any]] = {}
    for row in events:
        day_key = str(row.get("timestamp", ""))[:10]
        if not day_key:
            continue
        if day_key not in day_buckets:
            day_buckets[day_key] = {
                "date": day_key,
                "label": datetime.fromisoformat(day_key).strftime("%b %d, %Y"),
                "count": 0,
            }
        day_buckets[day_key]["count"] += 1

    ordered_day_buckets = sorted(day_buckets.values(), key=lambda row: row["date"], reverse=True)
    return {
        "range": {
            "days": int(window_days),
            "start": start_day.isoformat(),
            "end": today.isoformat(),
        },
        "summary": {
            "event_count": int(len(events)),
            "active_days": int(len(ordered_day_buckets)),
        },
        "day_buckets": ordered_day_buckets,
        "events": events,
    }


def season_pass_window_context(now_utc: datetime | None = None) -> dict[str, Any]:
    current = now_utc or datetime.utcnow()
    start_day = date(current.year, current.month, 1)
    if current.month == 12:
        next_start_day = date(current.year + 1, 1, 1)
    else:
        next_start_day = date(current.year, current.month + 1, 1)
    start_dt = datetime.combine(start_day, datetime.min.time())
    reset_dt = datetime.combine(next_start_day, datetime.min.time())
    season_key = start_day.strftime("%Y-%m")
    return {
        "season_key": season_key,
        "label": start_day.strftime("%B %Y"),
        "start_day": start_day,
        "end_day": next_start_day - timedelta(days=1),
        "start_dt": start_dt,
        "reset_at": reset_dt,
        "seconds_until_reset": max(int((reset_dt - current).total_seconds()), 0),
    }


def season_pass_tier_reward(tier: int) -> dict[str, Any]:
    safe_tier = max(min(int(tier or 1), SEASON_PASS_MAX_TIER), 1)
    free_reward_coins = max(SEASON_PASS_COIN_BASE + ((safe_tier - 1) * SEASON_PASS_COIN_STEP), 0)
    free_reward_xp = 0
    if safe_tier % 5 == 0:
        free_reward_xp += 45 * (safe_tier // 5)
    if safe_tier == SEASON_PASS_MAX_TIER:
        free_reward_xp += 120

    premium_reward_coins = max(10 + ((safe_tier - 1) * 2), 0)
    premium_reward_xp = 10
    if safe_tier % 3 == 0:
        premium_reward_xp += 10
    if safe_tier % 5 == 0:
        premium_reward_xp += 25
    if safe_tier == SEASON_PASS_MAX_TIER:
        premium_reward_xp += 75

    return {
        "tier": safe_tier,
        "required_xp": max((safe_tier - 1) * SEASON_PASS_XP_PER_TIER, 0),
        "free": {
            "reward_title": f"Tier {safe_tier} Free Reward",
            "reward_description": (
                f"Claim {free_reward_coins} coins"
                + (f" and {free_reward_xp} XP" if free_reward_xp > 0 else "")
                + "."
            ),
            "reward_coins": int(free_reward_coins),
            "reward_xp": int(free_reward_xp),
        },
        "premium": {
            "reward_title": f"Tier {safe_tier} Premium Reward",
            "reward_description": f"Claim {premium_reward_coins} bonus coins and {premium_reward_xp} bonus XP.",
            "reward_coins": int(premium_reward_coins),
            "reward_xp": int(premium_reward_xp),
        },
    }


def build_season_pass_payload(user: User, *, now_utc: datetime | None = None) -> dict[str, Any]:
    current = now_utc or datetime.utcnow()
    context = season_pass_window_context(now_utc=current)
    season_key = str(context["season_key"])
    start_dt = context["start_dt"]
    reset_dt = context["reset_at"]

    season_xp_earned = (
        db.session.query(func.coalesce(func.sum(XpLedger.points), 0))
        .filter(XpLedger.user_id == user.id, XpLedger.created_at >= start_dt, XpLedger.created_at < reset_dt)
        .scalar()
        or 0
    )
    season_xp = max(int(season_xp_earned or 0), 0)
    current_tier = min((season_xp // SEASON_PASS_XP_PER_TIER) + 1, SEASON_PASS_MAX_TIER)
    tier_floor_xp = (current_tier - 1) * SEASON_PASS_XP_PER_TIER
    xp_into_tier = max(season_xp - tier_floor_xp, 0)
    next_tier = min(current_tier + 1, SEASON_PASS_MAX_TIER)
    next_tier_threshold = (next_tier - 1) * SEASON_PASS_XP_PER_TIER
    xp_needed_for_next = max(next_tier_threshold - season_xp, 0) if current_tier < SEASON_PASS_MAX_TIER else 0
    progress_percent = (
        100.0
        if current_tier >= SEASON_PASS_MAX_TIER
        else round((xp_into_tier / max(SEASON_PASS_XP_PER_TIER, 1)) * 100, 1)
    )

    premium_enabled = bool(user.season_pass_premium)
    free_claim_rows = SeasonPassClaim.query.filter_by(user_id=user.id, season_key=season_key).all()
    premium_claim_rows = SeasonPassPremiumClaim.query.filter_by(user_id=user.id, season_key=season_key).all()
    free_claims_by_tier = {int(row.tier): row for row in free_claim_rows}
    premium_claims_by_tier = {int(row.tier): row for row in premium_claim_rows}

    tiers: list[dict[str, Any]] = []
    claimable_free = 0
    claimable_premium = 0
    for tier in range(1, SEASON_PASS_MAX_TIER + 1):
        reward = season_pass_tier_reward(tier)
        required_xp = int(reward["required_xp"])
        unlocked = season_xp >= required_xp

        free_reward = reward.get("free", {})
        premium_reward = reward.get("premium", {})
        free_claim_row = free_claims_by_tier.get(tier)
        premium_claim_row = premium_claims_by_tier.get(tier)

        free_claimed = free_claim_row is not None
        premium_claimed = premium_claim_row is not None
        free_claimable = bool(unlocked and not free_claimed)
        premium_claimable = bool(premium_enabled and unlocked and not premium_claimed)
        if free_claimable:
            claimable_free += 1
        if premium_claimable:
            claimable_premium += 1

        tiers.append(
            {
                "tier": tier,
                "required_xp": required_xp,
                "unlocked": bool(unlocked),
                "free": {
                    "reward_title": str(free_reward.get("reward_title", f"Tier {tier} Free Reward")),
                    "reward_description": str(free_reward.get("reward_description", "")).strip(),
                    "reward_xp": int(free_reward.get("reward_xp", 0) or 0),
                    "reward_coins": int(free_reward.get("reward_coins", 0) or 0),
                    "claimed": bool(free_claimed),
                    "claimable": bool(free_claimable),
                    "claimed_at": free_claim_row.claimed_at.isoformat() if free_claim_row and free_claim_row.claimed_at else None,
                },
                "premium": {
                    "available": bool(premium_enabled),
                    "reward_title": str(premium_reward.get("reward_title", f"Tier {tier} Premium Reward")),
                    "reward_description": str(premium_reward.get("reward_description", "")).strip(),
                    "reward_xp": int(premium_reward.get("reward_xp", 0) or 0),
                    "reward_coins": int(premium_reward.get("reward_coins", 0) or 0),
                    "claimed": bool(premium_claimed),
                    "claimable": bool(premium_claimable),
                    "claimed_at": premium_claim_row.claimed_at.isoformat() if premium_claim_row and premium_claim_row.claimed_at else None,
                },
            }
        )

    claimed_free = len(free_claim_rows)
    claimed_premium = len(premium_claim_rows)
    claimable_total = claimable_free + claimable_premium
    claimed_total = claimed_free + claimed_premium
    return {
        "season": {
            "season_key": season_key,
            "label": context["label"],
            "start": context["start_day"].isoformat(),
            "end": context["end_day"].isoformat(),
            "reset_at": context["reset_at"].isoformat(),
            "seconds_until_reset": int(context["seconds_until_reset"]),
            "premium_enabled": bool(premium_enabled),
        },
        "summary": {
            "xp_per_tier": int(SEASON_PASS_XP_PER_TIER),
            "max_tier": int(SEASON_PASS_MAX_TIER),
            "current_tier": int(current_tier),
            "xp_earned": int(season_xp),
            "xp_into_tier": int(xp_into_tier),
            "xp_needed_for_next_tier": int(xp_needed_for_next),
            "progress_percent": float(progress_percent),
            "premium_enabled": bool(premium_enabled),
            "claimable": int(claimable_total),
            "claimable_free": int(claimable_free),
            "claimable_premium": int(claimable_premium),
            "claimed": int(claimed_total),
            "claimed_free": int(claimed_free),
            "claimed_premium": int(claimed_premium),
        },
        "tiers": tiers,
    }


def clamp_leaderboard_limit(raw_limit: int | None) -> int:
    try:
        numeric_limit = int(raw_limit or LEADERBOARD_DEFAULT_LIMIT)
    except (TypeError, ValueError):
        numeric_limit = LEADERBOARD_DEFAULT_LIMIT
    return max(min(numeric_limit, LEADERBOARD_MAX_LIMIT), LEADERBOARD_MIN_LIMIT)


def normalize_leaderboard_scope(value: Any) -> str:
    scope = str(value or "global").strip().lower() or "global"
    return scope if scope in LEADERBOARD_SCOPES else "global"


def leaderboard_scope_user_ids(viewer_user_id: int, scope: str) -> set[int] | None:
    safe_scope = normalize_leaderboard_scope(scope)
    if safe_scope == "global":
        return None

    viewer_space_rows = db.session.query(SpaceMember.space_id).filter(SpaceMember.user_id == viewer_user_id).all()
    viewer_space_ids = sorted({int(row[0]) for row in viewer_space_rows if row and row[0] is not None})
    if not viewer_space_ids:
        return {int(viewer_user_id)}

    member_rows = db.session.query(SpaceMember.user_id).filter(SpaceMember.space_id.in_(viewer_space_ids)).all()
    user_ids = {int(viewer_user_id)}
    user_ids.update(int(row[0]) for row in member_rows if row and row[0] is not None)
    return user_ids


def load_total_xp_by_user(allowed_user_ids: set[int] | None = None) -> dict[int, int]:
    query = db.session.query(XpLedger.user_id, func.coalesce(func.sum(XpLedger.points), 0))
    if allowed_user_ids is not None:
        allowed_rows = sorted({int(user_id) for user_id in allowed_user_ids if int(user_id) > 0})
        if not allowed_rows:
            return {}
        query = query.filter(XpLedger.user_id.in_(allowed_rows))
    rows = query.group_by(XpLedger.user_id).all()
    return {int(user_id): max(int(total_xp or 0), 0) for user_id, total_xp in rows}


def build_xp_leaderboard_board(
    *,
    key: str,
    label: str,
    viewer_user_id: int,
    limit: int,
    total_xp_by_user: dict[int, int],
    allowed_user_ids: set[int] | None = None,
    start_dt: datetime | None = None,
    end_dt: datetime | None = None,
) -> dict[str, Any]:
    join_condition = XpLedger.user_id == User.id
    if start_dt is not None:
        join_condition = and_(join_condition, XpLedger.created_at >= start_dt)
    if end_dt is not None:
        join_condition = and_(join_condition, XpLedger.created_at < end_dt)
    score_expr = func.coalesce(func.sum(XpLedger.points), 0)
    query = db.session.query(
        User.id.label("user_id"),
        User.username.label("username"),
        User.display_name.label("display_name"),
        User.coins.label("coins"),
        score_expr.label("score"),
    )
    if allowed_user_ids is not None:
        allowed_rows = sorted({int(user_id) for user_id in allowed_user_ids if int(user_id) > 0})
        if not allowed_rows:
            return {
                "key": key,
                "label": label,
                "metric": "xp",
                "viewer_rank": 0,
                "viewer_score": 0,
                "entries": [],
            }
        query = query.filter(User.id.in_(allowed_rows))

    rows = (
        query.outerjoin(XpLedger, join_condition)
        .group_by(User.id)
        .order_by(score_expr.desc(), func.lower(User.username).asc(), User.id.asc())
        .all()
    )

    viewer_rank = None
    viewer_score = 0
    entries: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        score_value = max(int(row.score or 0), 0)
        level_value, _, _ = level_progress(int(total_xp_by_user.get(int(row.user_id), 0)))
        if row.user_id == viewer_user_id:
            viewer_rank = index
            viewer_score = score_value
        if index > limit:
            continue
        entries.append(
            {
                "rank": int(index),
                "user_id": int(row.user_id),
                "username": row.username,
                "display_name": row.display_name,
                "level": int(level_value),
                "score": int(score_value),
                "coins_balance": max(int(row.coins or 0), 0),
                "is_viewer": bool(row.user_id == viewer_user_id),
            }
        )

    return {
        "key": key,
        "label": label,
        "metric": "xp",
        "viewer_rank": int(viewer_rank or 0),
        "viewer_score": int(viewer_score),
        "entries": entries,
    }


def build_coin_leaderboard_board(
    *,
    viewer_user_id: int,
    limit: int,
    total_xp_by_user: dict[int, int],
    allowed_user_ids: set[int] | None = None,
) -> dict[str, Any]:
    query = User.query
    if allowed_user_ids is not None:
        allowed_rows = sorted({int(user_id) for user_id in allowed_user_ids if int(user_id) > 0})
        if not allowed_rows:
            return {
                "key": "coins_balance",
                "label": "Top Coin Balance",
                "metric": "coins",
                "viewer_rank": 0,
                "viewer_score": 0,
                "entries": [],
            }
        query = query.filter(User.id.in_(allowed_rows))
    rows = query.order_by(User.coins.desc(), func.lower(User.username).asc(), User.id.asc()).all()
    viewer_rank = None
    viewer_score = 0
    entries: list[dict[str, Any]] = []
    for index, user in enumerate(rows, start=1):
        score_value = max(int(user.coins or 0), 0)
        total_xp = int(total_xp_by_user.get(int(user.id), 0))
        level_value, _, _ = level_progress(total_xp)
        if user.id == viewer_user_id:
            viewer_rank = index
            viewer_score = score_value
        if index > limit:
            continue
        entries.append(
            {
                "rank": int(index),
                "user_id": int(user.id),
                "username": user.username,
                "display_name": user.display_name,
                "level": int(level_value),
                "score": int(score_value),
                "coins_balance": int(score_value),
                "is_viewer": bool(user.id == viewer_user_id),
            }
        )
    return {
        "key": "coins_balance",
        "label": "Top Coin Balance",
        "metric": "coins",
        "viewer_rank": int(viewer_rank or 0),
        "viewer_score": int(viewer_score),
        "entries": entries,
    }


def build_streak_leaderboard_board(
    *,
    viewer_user_id: int,
    limit: int,
    total_xp_by_user: dict[int, int],
    allowed_user_ids: set[int] | None = None,
) -> dict[str, Any]:
    streak_expr = func.coalesce(func.max(Habit.current_streak), 0)
    query = db.session.query(
        User.id.label("user_id"),
        User.username.label("username"),
        User.display_name.label("display_name"),
        User.coins.label("coins"),
        streak_expr.label("score"),
    )
    if allowed_user_ids is not None:
        allowed_rows = sorted({int(user_id) for user_id in allowed_user_ids if int(user_id) > 0})
        if not allowed_rows:
            return {
                "key": "current_streak",
                "label": "Longest Active Streak",
                "metric": "streak",
                "viewer_rank": 0,
                "viewer_score": 0,
                "entries": [],
            }
        query = query.filter(User.id.in_(allowed_rows))
    rows = (
        query.outerjoin(Habit, Habit.user_id == User.id)
        .group_by(User.id)
        .order_by(streak_expr.desc(), func.lower(User.username).asc(), User.id.asc())
        .all()
    )
    viewer_rank = None
    viewer_score = 0
    entries: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        score_value = max(int(row.score or 0), 0)
        total_xp = int(total_xp_by_user.get(int(row.user_id), 0))
        level_value, _, _ = level_progress(total_xp)
        if row.user_id == viewer_user_id:
            viewer_rank = index
            viewer_score = score_value
        if index > limit:
            continue
        entries.append(
            {
                "rank": int(index),
                "user_id": int(row.user_id),
                "username": row.username,
                "display_name": row.display_name,
                "level": int(level_value),
                "score": int(score_value),
                "coins_balance": max(int(row.coins or 0), 0),
                "is_viewer": bool(row.user_id == viewer_user_id),
            }
        )

    return {
        "key": "current_streak",
        "label": "Longest Active Streak",
        "metric": "streak",
        "viewer_rank": int(viewer_rank or 0),
        "viewer_score": int(viewer_score),
        "entries": entries,
    }


def build_leaderboard_payload(user: User, limit: int | None = None, scope: str | None = None) -> dict[str, Any]:
    safe_limit = clamp_leaderboard_limit(limit)
    safe_scope = normalize_leaderboard_scope(scope)
    allowed_user_ids = leaderboard_scope_user_ids(user.id, safe_scope)
    now_utc = datetime.utcnow()
    xp_7d_start = now_utc - timedelta(days=7)
    xp_30d_start = now_utc - timedelta(days=30)
    total_xp_by_user = load_total_xp_by_user(allowed_user_ids=allowed_user_ids)
    boards = [
        build_xp_leaderboard_board(
            key="xp_7d",
            label="XP - Last 7 Days",
            viewer_user_id=user.id,
            limit=safe_limit,
            total_xp_by_user=total_xp_by_user,
            allowed_user_ids=allowed_user_ids,
            start_dt=xp_7d_start,
            end_dt=now_utc,
        ),
        build_xp_leaderboard_board(
            key="xp_30d",
            label="XP - Last 30 Days",
            viewer_user_id=user.id,
            limit=safe_limit,
            total_xp_by_user=total_xp_by_user,
            allowed_user_ids=allowed_user_ids,
            start_dt=xp_30d_start,
            end_dt=now_utc,
        ),
        build_xp_leaderboard_board(
            key="xp_all_time",
            label="XP - All Time",
            viewer_user_id=user.id,
            limit=safe_limit,
            total_xp_by_user=total_xp_by_user,
            allowed_user_ids=allowed_user_ids,
        ),
        build_coin_leaderboard_board(
            viewer_user_id=user.id,
            limit=safe_limit,
            total_xp_by_user=total_xp_by_user,
            allowed_user_ids=allowed_user_ids,
        ),
        build_streak_leaderboard_board(
            viewer_user_id=user.id,
            limit=safe_limit,
            total_xp_by_user=total_xp_by_user,
            allowed_user_ids=allowed_user_ids,
        ),
    ]
    scope_user_count = (
        len(allowed_user_ids)
        if allowed_user_ids is not None
        else int(User.query.count())
    )
    return {
        "generated_at": now_utc.isoformat(),
        "limit": int(safe_limit),
        "scope": safe_scope,
        "scope_label": "Network" if safe_scope == "network" else "Global",
        "scope_user_count": int(scope_user_count),
        "boards": boards,
    }


def build_avatar_payload(user: User) -> dict[str, Any]:
    profile = ensure_avatar_profile(user)
    owned_item_keys = user_owned_shop_item_keys(user.id)
    return {
        "coins_balance": max(int(user.coins or 0), 0),
        "avatar": serialize_avatar_profile(profile),
        "options": serialize_avatar_options_for_user(user, owned_item_keys),
        "set_presets": serialize_avatar_set_presets_for_user(user, owned_item_keys),
        "owned_item_keys": sorted(owned_item_keys),
    }


def clamp_day_window(raw_days: int | None, default: int = 30, minimum: int = 7, maximum: int = 180) -> int:
    if raw_days is None:
        return default
    try:
        parsed = int(raw_days)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


def build_stats_payload(user: User, days: int | None = 30) -> dict[str, Any]:
    window_days = clamp_day_window(days)
    today = date.today()
    start_day = today - timedelta(days=window_days - 1)
    start_dt = datetime.combine(start_day, datetime.min.time())

    task_completion_moment = func.coalesce(Task.completed_at, Task.created_at)
    xp_day_expr = func.date(XpLedger.created_at)
    task_day_expr = func.date(task_completion_moment)

    xp_day_rows = (
        db.session.query(xp_day_expr, func.coalesce(func.sum(XpLedger.points), 0))
        .filter(XpLedger.user_id == user.id, XpLedger.created_at >= start_dt)
        .group_by(xp_day_expr)
        .all()
    )
    xp_by_day_map = {str(row[0]): int(row[1] or 0) for row in xp_day_rows if row[0] is not None}

    task_completion_rows = (
        db.session.query(task_day_expr, func.count(Task.id))
        .filter(Task.user_id == user.id, Task.status == "done", task_completion_moment >= start_dt)
        .group_by(task_day_expr)
        .all()
    )
    task_by_day_map = {str(row[0]): int(row[1] or 0) for row in task_completion_rows if row[0] is not None}

    habit_completion_rows = (
        db.session.query(HabitLog.completed_on, func.count(HabitLog.id))
        .filter(HabitLog.user_id == user.id, HabitLog.completed_on >= start_day)
        .group_by(HabitLog.completed_on)
        .all()
    )
    habit_by_day_map = {row[0].isoformat(): int(row[1] or 0) for row in habit_completion_rows if row[0] is not None}

    xp_by_day: list[dict[str, Any]] = []
    completion_by_day: list[dict[str, Any]] = []
    running_xp = 0
    for offset in range(window_days):
        day_value = start_day + timedelta(days=offset)
        iso_day = day_value.isoformat()
        daily_xp = xp_by_day_map.get(iso_day, 0)
        task_count = task_by_day_map.get(iso_day, 0)
        habit_count = habit_by_day_map.get(iso_day, 0)
        total_count = task_count + habit_count

        running_xp += daily_xp
        xp_by_day.append(
            {
                "date": iso_day,
                "label": day_value.strftime("%b %d"),
                "xp": daily_xp,
                "cumulative_xp": running_xp,
            }
        )
        completion_by_day.append(
            {
                "date": iso_day,
                "label": day_value.strftime("%b %d"),
                "task_completions": task_count,
                "habit_completions": habit_count,
                "total_completions": total_count,
            }
        )

    xp_total = (
        db.session.query(func.coalesce(func.sum(XpLedger.points), 0))
        .filter(XpLedger.user_id == user.id)
        .scalar()
        or 0
    )
    coins_balance = max(int(user.coins or 0), 0)
    coins_earned_in_range = (
        db.session.query(func.coalesce(func.sum(CoinLedger.amount), 0))
        .filter(CoinLedger.user_id == user.id, CoinLedger.created_at >= start_dt, CoinLedger.amount > 0)
        .scalar()
        or 0
    )
    coins_spent_in_range = (
        db.session.query(func.coalesce(func.sum(-CoinLedger.amount), 0))
        .filter(CoinLedger.user_id == user.id, CoinLedger.created_at >= start_dt, CoinLedger.amount < 0)
        .scalar()
        or 0
    )
    level, xp_into_level, xp_for_next_level = level_progress(xp_total)

    total_window_xp = sum(item["xp"] for item in xp_by_day)
    total_window_task_completions = sum(item["task_completions"] for item in completion_by_day)
    total_window_habit_completions = sum(item["habit_completions"] for item in completion_by_day)

    trailing_seven_xp = sum(item["xp"] for item in xp_by_day[-7:])
    trailing_seven_tasks = sum(item["task_completions"] for item in completion_by_day[-7:])
    trailing_seven_habits = sum(item["habit_completions"] for item in completion_by_day[-7:])

    active_days = sum(1 for item in completion_by_day if item["total_completions"] > 0)
    activity_rate = round((active_days / max(window_days, 1)) * 100, 1)

    best_xp_day = max(xp_by_day, key=lambda item: item["xp"]) if xp_by_day else None
    top_day_payload = (
        {"date": best_xp_day["date"], "xp": best_xp_day["xp"], "label": best_xp_day["label"]}
        if best_xp_day and best_xp_day["xp"] > 0
        else None
    )

    task_type_rows = (
        db.session.query(Task.task_type, func.count(Task.id))
        .filter(Task.user_id == user.id, Task.status == "done", task_completion_moment >= start_dt)
        .group_by(Task.task_type)
        .all()
    )
    task_type_counts = {str(row[0] or "task"): int(row[1] or 0) for row in task_type_rows}
    total_completed_tasks = sum(task_type_counts.values())
    task_type_breakdown = []
    for task_type in ("task", "habit", "quest"):
        count = task_type_counts.get(task_type, 0)
        percentage = round((count / total_completed_tasks) * 100, 1) if total_completed_tasks else 0
        task_type_breakdown.append(
            {
                "task_type": task_type,
                "label": TASK_TYPE_LABELS.get(task_type, "Task"),
                "count": count,
                "percentage": percentage,
            }
        )

    xp_source_rows = (
        db.session.query(XpLedger.source, func.coalesce(func.sum(XpLedger.points), 0).label("points"))
        .filter(XpLedger.user_id == user.id, XpLedger.created_at >= start_dt)
        .group_by(XpLedger.source)
        .order_by(func.sum(XpLedger.points).desc(), XpLedger.source.asc())
        .limit(8)
        .all()
    )
    xp_source_breakdown = [{"source": str(row[0]), "points": int(row[1] or 0)} for row in xp_source_rows if row[0]]

    goals = Goal.query.filter_by(user_id=user.id).all()
    goal_total = len(goals)
    goal_completed = sum(1 for goal in goals if goal.current_value >= goal.target_value)
    goal_in_progress = sum(1 for goal in goals if goal.current_value < goal.target_value)
    goal_completion_rate = round((goal_completed / goal_total) * 100, 1) if goal_total else 0
    average_goal_progress = (
        round(
            sum((goal.current_value / goal.target_value) * 100 for goal in goals if goal.target_value > 0)
            / max(sum(1 for goal in goals if goal.target_value > 0), 1),
            1,
        )
        if goals
        else 0
    )

    current_streak = (
        db.session.query(func.coalesce(func.max(Habit.current_streak), 0))
        .filter(Habit.user_id == user.id)
        .scalar()
        or 0
    )
    longest_streak = (
        db.session.query(func.coalesce(func.max(Habit.longest_streak), 0))
        .filter(Habit.user_id == user.id)
        .scalar()
        or 0
    )

    return {
        "range": {
            "days": window_days,
            "start": start_day.isoformat(),
            "end": today.isoformat(),
        },
        "summary": {
            "level": level,
            "xp_total": int(xp_total),
            "coins_balance": int(coins_balance),
            "coins_earned_in_range": int(coins_earned_in_range),
            "coins_spent_in_range": int(coins_spent_in_range),
            "xp_into_level": xp_into_level,
            "xp_for_next_level": xp_for_next_level,
            "xp_in_range": int(total_window_xp),
            "xp_last_7_days": int(trailing_seven_xp),
            "tasks_completed_in_range": int(total_window_task_completions),
            "tasks_completed_last_7_days": int(trailing_seven_tasks),
            "habit_checks_in_range": int(total_window_habit_completions),
            "habit_checks_last_7_days": int(trailing_seven_habits),
            "active_days_in_range": active_days,
            "activity_rate": activity_rate,
            "current_streak": int(current_streak),
            "longest_streak": int(longest_streak),
            "top_xp_day": top_day_payload,
        },
        "goal_status": {
            "total": goal_total,
            "completed": goal_completed,
            "in_progress": goal_in_progress,
            "completion_rate": goal_completion_rate,
            "average_progress": average_goal_progress,
        },
        "xp_by_day": xp_by_day,
        "completion_by_day": completion_by_day,
        "task_type_breakdown": task_type_breakdown,
        "xp_source_breakdown": xp_source_breakdown,
    }


def build_notifications_payload(user: User, *, delivery_context: str = "in_app") -> dict[str, Any]:
    today = date.today()
    due_soon_cutoff = today + timedelta(days=max(NOTIFICATION_GOAL_WINDOW_DAYS, 1))
    priority_rank = case(
        (Task.priority == "high", 0),
        (Task.priority == "medium", 1),
        (Task.priority == "low", 2),
        else_=3,
    )
    severity_rank = {"high": 0, "medium": 1, "low": 2}

    items: list[dict[str, Any]] = []

    overdue_tasks = (
        Task.query.filter(
            Task.user_id == user.id,
            Task.status == "todo",
            Task.due_on.isnot(None),
            Task.due_on < today,
        )
        .order_by(Task.due_on.asc(), priority_rank.asc(), Task.created_at.asc())
        .limit(10)
        .all()
    )
    for task in overdue_tasks:
        days_overdue = (today - task.due_on).days if task.due_on else 0
        items.append(
            {
                "id": f"overdue-task-{task.id}",
                "category": "overdue_task",
                "severity": "high" if days_overdue >= 2 or task.priority == "high" else "medium",
                "title": "Task overdue",
                "message": f"{task.title} is {days_overdue} day(s) overdue.",
                "related": {"entity": "task", "id": task.id, "path": "/tasks"},
                "date": task.due_on.isoformat() if task.due_on else today.isoformat(),
                "_severity_rank": severity_rank["high" if days_overdue >= 2 or task.priority == "high" else "medium"],
            }
        )

    habits = Habit.query.filter_by(user_id=user.id).order_by(Habit.current_streak.desc(), Habit.name.asc()).all()
    streak_risk_count = 0
    for habit in habits:
        if habit.last_completed_on == today:
            continue
        if habit.current_streak <= 0:
            continue

        streak_risk_count += 1
        if habit.last_completed_on == today - timedelta(days=1):
            severity = "high"
            message = f"Complete {habit.name} today to protect your {habit.current_streak}-day streak."
        else:
            severity = "medium"
            message = f"{habit.name} streak needs attention ({habit.current_streak} days before break)."

        items.append(
            {
                "id": f"streak-habit-{habit.id}",
                "category": "streak_risk",
                "severity": severity,
                "title": "Streak at risk",
                "message": message,
                "related": {"entity": "habit", "id": habit.id, "path": "/tasks"},
                "date": today.isoformat(),
                "_severity_rank": severity_rank[severity],
            }
        )

    goals_due_soon = (
        Goal.query.filter(
            Goal.user_id == user.id,
            Goal.current_value < Goal.target_value,
            Goal.deadline.isnot(None),
            Goal.deadline <= due_soon_cutoff,
        )
        .order_by(Goal.deadline.asc(), Goal.created_at.asc())
        .limit(8)
        .all()
    )
    for goal in goals_due_soon:
        if goal.deadline is None:
            continue
        days_left = (goal.deadline - today).days
        if days_left < 0:
            severity = "high"
            message = f"{goal.title} is overdue by {abs(days_left)} day(s)."
        elif days_left == 0:
            severity = "high"
            message = f"{goal.title} is due today."
        elif days_left <= 2:
            severity = "medium"
            message = f"{goal.title} is due in {days_left} day(s)."
        else:
            severity = "low"
            message = f"{goal.title} is due in {days_left} day(s)."

        items.append(
            {
                "id": f"goal-deadline-{goal.id}",
                "category": "goal_deadline",
                "severity": severity,
                "title": "Goal deadline",
                "message": message,
                "related": {"entity": "goal", "id": goal.id, "path": "/quests"},
                "date": goal.deadline.isoformat(),
                "_severity_rank": severity_rank[severity],
            }
        )

    due_today_count = Task.query.filter_by(user_id=user.id, status="todo", due_on=today).count()
    if due_today_count > 0:
        items.append(
            {
                "id": "due-today-summary",
                "category": "due_today",
                "severity": "medium",
                "title": "Tasks due today",
                "message": f"You have {due_today_count} task(s) due today.",
                "related": {"entity": "task", "id": None, "path": "/dashboard"},
                "date": today.isoformat(),
                "_severity_rank": severity_rank["medium"],
            }
        )

    space_activity_items, space_updates_count = build_space_activity_notification_items(
        user,
        severity_rank,
        delivery_context=delivery_context,
    )
    if space_activity_items:
        items.extend(space_activity_items)

    invite_expiry_items, invite_expiring_count = build_space_invite_expiry_notification_items(
        user,
        severity_rank,
    )
    if invite_expiry_items:
        items.extend(invite_expiry_items)

    items.sort(key=lambda item: (item.get("_severity_rank", 9), item.get("date", today.isoformat()), item.get("id", "")))
    max_items = max(NOTIFICATION_MAX_ITEMS, 1)
    trimmed_items = items[:max_items]
    for item in trimmed_items:
        item.pop("_severity_rank", None)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "counts": {
            "total": len(trimmed_items),
            "overdue_tasks": len(overdue_tasks),
            "streak_risk_habits": streak_risk_count,
            "goals_due_soon": len(goals_due_soon),
            "due_today": due_today_count,
            "space_updates": space_updates_count,
            "space_invites_expiring": invite_expiring_count,
        },
        "items": trimmed_items,
    }


def build_account_snapshot(user: User) -> dict[str, Any]:
    tasks = (
        Task.query.filter_by(user_id=user.id)
        .order_by(Task.created_at.asc(), Task.id.asc())
        .all()
    )
    habits = (
        Habit.query.filter_by(user_id=user.id)
        .order_by(Habit.created_at.asc(), Habit.id.asc())
        .all()
    )
    habit_logs = (
        HabitLog.query.filter_by(user_id=user.id)
        .order_by(HabitLog.completed_on.asc(), HabitLog.id.asc())
        .all()
    )
    goals = (
        Goal.query.filter_by(user_id=user.id)
        .order_by(Goal.created_at.asc(), Goal.id.asc())
        .all()
    )
    recurring_rules = (
        RecurringRule.query.filter_by(user_id=user.id)
        .order_by(RecurringRule.created_at.asc(), RecurringRule.id.asc())
        .all()
    )
    reminder_settings = ensure_reminder_settings(user)
    xp_entries = (
        XpLedger.query.filter_by(user_id=user.id)
        .order_by(XpLedger.created_at.asc(), XpLedger.id.asc())
        .all()
    )

    habit_name_by_id = {habit.id: habit.name for habit in habits}

    return {
        "meta": {
            "schema_version": 2,
            "source": "LifeOS",
            "exported_at": datetime.utcnow().isoformat(),
        },
        "user": {
            "display_name": user.display_name,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "data": {
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "task_type": task.task_type,
                    "priority": task.priority,
                    "xp_reward": task.xp_reward,
                    "due_on": task.due_on.isoformat() if task.due_on else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "recurrence_rule_id": task.recurrence_rule_id,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                }
                for task in tasks
            ],
            "habits": [
                {
                    "id": habit.id,
                    "name": habit.name,
                    "current_streak": habit.current_streak,
                    "longest_streak": habit.longest_streak,
                    "last_completed_on": habit.last_completed_on.isoformat() if habit.last_completed_on else None,
                    "created_at": habit.created_at.isoformat() if habit.created_at else None,
                }
                for habit in habits
            ],
            "habit_logs": [
                {
                    "id": log.id,
                    "habit_id": log.habit_id,
                    "habit_name": habit_name_by_id.get(log.habit_id),
                    "completed_on": log.completed_on.isoformat(),
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in habit_logs
            ],
            "goals": [
                {
                    "id": goal.id,
                    "title": goal.title,
                    "target_value": goal.target_value,
                    "current_value": goal.current_value,
                    "deadline": goal.deadline.isoformat() if goal.deadline else None,
                    "created_at": goal.created_at.isoformat() if goal.created_at else None,
                }
                for goal in goals
            ],
            "recurring_rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "task_type": rule.task_type,
                    "priority": rule.priority,
                    "xp_reward": rule.xp_reward,
                    "frequency": rule.frequency,
                    "interval": rule.interval,
                    "days_of_week": decode_weekdays(rule.days_of_week),
                    "start_on": rule.start_on.isoformat() if rule.start_on else None,
                    "end_on": rule.end_on.isoformat() if rule.end_on else None,
                    "active": bool(rule.active),
                    "last_generated_on": rule.last_generated_on.isoformat() if rule.last_generated_on else None,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                }
                for rule in recurring_rules
            ],
            "reminder_channels": {
                "in_app_enabled": bool(reminder_settings.in_app_enabled),
                "email_enabled": bool(reminder_settings.email_enabled),
                "sms_enabled": bool(reminder_settings.sms_enabled),
                "email_address": reminder_settings.email_address,
                "phone_number": reminder_settings.phone_number,
                "digest_hour_utc": int(reminder_settings.digest_hour_utc),
                "updated_at": reminder_settings.updated_at.isoformat() if reminder_settings.updated_at else None,
            },
            "xp_ledger": [
                {
                    "id": entry.id,
                    "source": entry.source,
                    "points": entry.points,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                }
                for entry in xp_entries
            ],
        },
    }


def import_account_snapshot(user: User, snapshot_payload: dict[str, Any], mode: str, apply_profile: bool) -> dict[str, Any]:
    data_payload = snapshot_payload.get("data", snapshot_payload)
    if not isinstance(data_payload, dict):
        raise ValueError("snapshot data must be an object")

    tasks_payload = data_payload.get("tasks", [])
    habits_payload = data_payload.get("habits", [])
    habit_logs_payload = data_payload.get("habit_logs", [])
    goals_payload = data_payload.get("goals", [])
    recurring_rules_payload = data_payload.get("recurring_rules", [])
    reminder_channels_payload = data_payload.get("reminder_channels")
    xp_payload = data_payload.get("xp_ledger", data_payload.get("xp_entries", []))

    for field_name, value in (
        ("tasks", tasks_payload),
        ("habits", habits_payload),
        ("habit_logs", habit_logs_payload),
        ("goals", goals_payload),
        ("recurring_rules", recurring_rules_payload),
        ("xp_ledger", xp_payload),
    ):
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be an array")
    if reminder_channels_payload is not None and not isinstance(reminder_channels_payload, dict):
        raise ValueError("reminder_channels must be an object")

    imported = {"tasks": 0, "habits": 0, "habit_logs": 0, "goals": 0, "recurring_rules": 0, "reminder_channels": 0, "xp_ledger": 0}
    skipped = {"tasks": 0, "habits": 0, "habit_logs": 0, "goals": 0, "recurring_rules": 0, "reminder_channels": 0, "xp_ledger": 0}

    if mode == "replace":
        HabitLog.query.filter_by(user_id=user.id).delete()
        Task.query.filter_by(user_id=user.id).delete()
        Habit.query.filter_by(user_id=user.id).delete()
        Goal.query.filter_by(user_id=user.id).delete()
        RecurringRule.query.filter_by(user_id=user.id).delete()
        ReminderDeliveryLog.query.filter_by(user_id=user.id).delete()
        XpLedger.query.filter_by(user_id=user.id).delete()
        db.session.flush()

    if apply_profile:
        snapshot_user = snapshot_payload.get("user")
        if isinstance(snapshot_user, dict):
            display_name = str(snapshot_user.get("display_name", "")).strip()
            if display_name:
                user.display_name = display_name
                db.session.add(user)

    existing_habits_by_name = (
        {habit.name.lower(): habit for habit in Habit.query.filter_by(user_id=user.id).all()} if mode == "merge" else {}
    )
    habit_id_map: dict[str, int] = {}

    for raw in habits_payload:
        if not isinstance(raw, dict):
            skipped["habits"] += 1
            continue

        name = str(raw.get("name", "")).strip()
        if not name:
            skipped["habits"] += 1
            continue

        current_streak, _ = parse_int_value(raw.get("current_streak"), "current_streak", 0)
        longest_streak, _ = parse_int_value(raw.get("longest_streak"), "longest_streak", 0)
        last_completed_on, _ = parse_date_value(raw.get("last_completed_on"), "last_completed_on")
        created_at, _ = parse_datetime_value(raw.get("created_at"), "created_at")

        current_value = current_streak or 0
        longest_value = max(longest_streak or 0, current_value)

        habit = existing_habits_by_name.get(name.lower())
        if habit is None:
            habit = Habit(
                user_id=user.id,
                name=name,
                current_streak=current_value,
                longest_streak=longest_value,
                last_completed_on=last_completed_on,
                created_at=created_at or datetime.utcnow(),
            )
            db.session.add(habit)
            db.session.flush()
            existing_habits_by_name[name.lower()] = habit
        else:
            habit.current_streak = max(habit.current_streak, current_value)
            habit.longest_streak = max(habit.longest_streak, longest_value, habit.current_streak)
            if last_completed_on and (habit.last_completed_on is None or last_completed_on > habit.last_completed_on):
                habit.last_completed_on = last_completed_on
            if created_at and created_at < habit.created_at:
                habit.created_at = created_at
            db.session.add(habit)

        raw_habit_id = raw.get("id")
        if raw_habit_id is not None:
            habit_id_map[str(raw_habit_id)] = habit.id
        habit_id_map[name.lower()] = habit.id
        imported["habits"] += 1

    existing_log_keys = (
        {
            (log.habit_id, log.completed_on.isoformat())
            for log in HabitLog.query.filter_by(user_id=user.id).all()
        }
        if mode == "merge"
        else set()
    )

    for raw in habit_logs_payload:
        if not isinstance(raw, dict):
            skipped["habit_logs"] += 1
            continue

        completed_on, _ = parse_date_value(raw.get("completed_on"), "completed_on")
        if completed_on is None:
            skipped["habit_logs"] += 1
            continue

        mapped_habit_id = None
        raw_habit_id = raw.get("habit_id")
        if raw_habit_id is not None:
            mapped_habit_id = habit_id_map.get(str(raw_habit_id))

        habit_name = str(raw.get("habit_name", "")).strip()
        if mapped_habit_id is None and habit_name:
            mapped_habit_id = habit_id_map.get(habit_name.lower())
            if mapped_habit_id is None and mode == "merge":
                matched_habit = existing_habits_by_name.get(habit_name.lower())
                if matched_habit is not None:
                    mapped_habit_id = matched_habit.id

        if mapped_habit_id is None:
            skipped["habit_logs"] += 1
            continue

        dedupe_key = (mapped_habit_id, completed_on.isoformat())
        if dedupe_key in existing_log_keys:
            skipped["habit_logs"] += 1
            continue

        created_at, _ = parse_datetime_value(raw.get("created_at"), "created_at")
        db.session.add(
            HabitLog(
                user_id=user.id,
                habit_id=mapped_habit_id,
                completed_on=completed_on,
                created_at=created_at or datetime.utcnow(),
            )
        )
        existing_log_keys.add(dedupe_key)
        imported["habit_logs"] += 1

    for raw in tasks_payload:
        if not isinstance(raw, dict):
            skipped["tasks"] += 1
            continue

        title = str(raw.get("title", "")).strip()
        if not title:
            skipped["tasks"] += 1
            continue

        task_type, _ = parse_task_type(raw.get("task_type"))
        priority, _ = parse_task_priority(raw.get("priority"))
        status, _ = parse_task_status(raw.get("status"))
        xp_reward, _ = parse_int_value(raw.get("xp_reward"), "xp_reward", 1)
        due_on, _ = parse_date_value(raw.get("due_on"), "due_on")
        completed_at, _ = parse_datetime_value(raw.get("completed_at"), "completed_at")
        created_at, _ = parse_datetime_value(raw.get("created_at"), "created_at")

        task_created_at = created_at or datetime.utcnow()
        task_status = status or "todo"
        if task_status == "done" and completed_at is None:
            completed_at = task_created_at

        db.session.add(
            Task(
                user_id=user.id,
                title=title,
                status=task_status,
                task_type=task_type or "task",
                xp_reward=xp_reward or 20,
                priority=priority or "medium",
                due_on=due_on,
                completed_at=completed_at,
                created_at=task_created_at,
            )
        )
        imported["tasks"] += 1

    for raw in goals_payload:
        if not isinstance(raw, dict):
            skipped["goals"] += 1
            continue

        title = str(raw.get("title", "")).strip()
        if not title:
            skipped["goals"] += 1
            continue

        target_value, _ = parse_int_value(raw.get("target_value"), "target_value", 1)
        current_value, _ = parse_int_value(raw.get("current_value"), "current_value", 0)
        deadline, _ = parse_date_value(raw.get("deadline"), "deadline")
        created_at, _ = parse_datetime_value(raw.get("created_at"), "created_at")

        safe_target = target_value or 1
        safe_current = min(current_value or 0, safe_target)

        db.session.add(
            Goal(
                user_id=user.id,
                title=title,
                target_value=safe_target,
                current_value=safe_current,
                deadline=deadline,
                created_at=created_at or datetime.utcnow(),
            )
        )
        imported["goals"] += 1

    existing_rule_signatures = (
        {
            (
                rule.title.lower(),
                rule.task_type,
                rule.frequency,
                max(int(rule.interval or 1), 1),
                tuple(decode_weekdays(rule.days_of_week)),
            )
            for rule in RecurringRule.query.filter_by(user_id=user.id).all()
        }
        if mode == "merge"
        else set()
    )

    for raw in recurring_rules_payload:
        if not isinstance(raw, dict):
            skipped["recurring_rules"] += 1
            continue

        title = str(raw.get("title", "")).strip()
        if not title:
            skipped["recurring_rules"] += 1
            continue

        task_type, _ = parse_task_type(raw.get("task_type"))
        priority, _ = parse_task_priority(raw.get("priority"))
        xp_reward, _ = parse_int_value(raw.get("xp_reward"), "xp_reward", 1)
        frequency, _ = parse_recurrence_frequency(raw.get("frequency"))
        interval, _ = parse_int_value(raw.get("interval"), "interval", 1)
        start_on, _ = parse_date_value(raw.get("start_on"), "start_on")
        end_on, _ = parse_date_value(raw.get("end_on"), "end_on")
        last_generated_on, _ = parse_date_value(raw.get("last_generated_on"), "last_generated_on")
        active, _ = parse_bool_value(raw.get("active"), "active")
        created_at, _ = parse_datetime_value(raw.get("created_at"), "created_at")
        weekdays, weekday_error = parse_weekday_values(raw.get("days_of_week"))
        if weekday_error:
            skipped["recurring_rules"] += 1
            continue

        resolved_frequency = frequency or "daily"
        resolved_interval = interval or 1
        resolved_days = weekdays
        if resolved_frequency == "weekly" and not resolved_days:
            inferred_weekday = start_on.weekday() if start_on else date.today().weekday()
            resolved_days = [inferred_weekday]

        signature = (
            title.lower(),
            task_type or "task",
            resolved_frequency,
            resolved_interval,
            tuple(sorted(set(resolved_days))),
        )
        if signature in existing_rule_signatures:
            skipped["recurring_rules"] += 1
            continue

        db.session.add(
            RecurringRule(
                user_id=user.id,
                title=title,
                task_type=task_type or "task",
                priority=priority or "medium",
                xp_reward=xp_reward or 20,
                frequency=resolved_frequency,
                interval=resolved_interval,
                days_of_week=encode_weekdays(resolved_days),
                start_on=start_on,
                end_on=end_on,
                active=True if active is None else active,
                last_generated_on=last_generated_on,
                created_at=created_at or datetime.utcnow(),
            )
        )
        existing_rule_signatures.add(signature)
        imported["recurring_rules"] += 1

    if reminder_channels_payload is not None:
        settings_row = ensure_reminder_settings(user)
        email_enabled, _ = parse_bool_value(reminder_channels_payload.get("email_enabled"), "email_enabled")
        sms_enabled, _ = parse_bool_value(reminder_channels_payload.get("sms_enabled"), "sms_enabled")
        in_app_enabled, _ = parse_bool_value(reminder_channels_payload.get("in_app_enabled"), "in_app_enabled")
        email_address, _ = parse_email_address(reminder_channels_payload.get("email_address"), "email_address")
        phone_number, _ = parse_phone_number(reminder_channels_payload.get("phone_number"), "phone_number")
        digest_hour, _ = parse_hour_value(reminder_channels_payload.get("digest_hour_utc"), "digest_hour_utc")

        if in_app_enabled is not None:
            settings_row.in_app_enabled = in_app_enabled
        if email_enabled is not None:
            settings_row.email_enabled = email_enabled
        if sms_enabled is not None:
            settings_row.sms_enabled = sms_enabled
        if email_address is not None:
            settings_row.email_address = email_address
        if phone_number is not None:
            settings_row.phone_number = phone_number
        if digest_hour is not None:
            settings_row.digest_hour_utc = digest_hour
        db.session.add(settings_row)
        imported["reminder_channels"] += 1

    for raw in xp_payload:
        if not isinstance(raw, dict):
            skipped["xp_ledger"] += 1
            continue

        source = str(raw.get("source", "")).strip() or "Imported XP"
        points, _ = parse_int_value(raw.get("points"), "points", 1)
        created_at, _ = parse_datetime_value(raw.get("created_at"), "created_at")

        db.session.add(
            XpLedger(
                user_id=user.id,
                source=source,
                points=points or 1,
                created_at=created_at or datetime.utcnow(),
            )
        )
        imported["xp_ledger"] += 1

    return {"imported": imported, "skipped": skipped}


def snapshot_user_identity(user: User | None, fallback_user_id: int | None = None) -> dict[str, Any]:
    return {
        "user_id": user.id if user is not None else fallback_user_id,
        "username": user.username if user is not None else None,
        "email": user.email if user is not None else None,
        "display_name": user.display_name if user is not None else None,
    }


def build_space_snapshot(space: Space) -> dict[str, Any]:
    member_rows = (
        SpaceMember.query.filter_by(space_id=space.id)
        .order_by(SpaceMember.created_at.asc(), SpaceMember.id.asc())
        .all()
    )
    task_rows = (
        SpaceTask.query.filter_by(space_id=space.id)
        .order_by(SpaceTask.created_at.asc(), SpaceTask.id.asc())
        .all()
    )
    preference_rows = (
        SpaceNotificationPreference.query.filter_by(space_id=space.id)
        .order_by(SpaceNotificationPreference.created_at.asc(), SpaceNotificationPreference.id.asc())
        .all()
    )
    templates_by_role = ensure_space_role_templates(space)

    user_ids: set[int] = {
        user_id
        for user_id in [row.user_id for row in member_rows]
        if isinstance(user_id, int)
    }
    user_ids.update(
        {
            user_id
            for user_id in [row.created_by_user_id for row in task_rows]
            if isinstance(user_id, int)
        }
    )
    user_ids.update(
        {
            user_id
            for user_id in [row.completed_by_user_id for row in task_rows]
            if isinstance(user_id, int)
        }
    )
    user_ids.update(
        {
            user_id
            for user_id in [row.user_id for row in preference_rows]
            if isinstance(user_id, int)
        }
    )

    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    users_by_id = {user.id: user for user in users}
    owner_user = users_by_id.get(space.owner_user_id) or db.session.get(User, space.owner_user_id)

    members_payload: list[dict[str, Any]] = []
    for row in member_rows:
        identity = snapshot_user_identity(users_by_id.get(row.user_id), row.user_id)
        members_payload.append(
            {
                **identity,
                "role": row.role,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )

    tasks_payload: list[dict[str, Any]] = []
    for row in task_rows:
        created_by_identity = snapshot_user_identity(users_by_id.get(row.created_by_user_id), row.created_by_user_id)
        completed_by_identity = (
            snapshot_user_identity(users_by_id.get(row.completed_by_user_id), row.completed_by_user_id)
            if row.completed_by_user_id is not None
            else None
        )
        tasks_payload.append(
            {
                "id": row.id,
                "title": row.title,
                "status": row.status,
                "task_type": row.task_type,
                "priority": row.priority,
                "xp_reward": row.xp_reward,
                "due_on": row.due_on.isoformat() if row.due_on else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "created_by": created_by_identity,
                "completed_by": completed_by_identity,
            }
        )

    preferences_payload: list[dict[str, Any]] = []
    for row in preference_rows:
        identity = snapshot_user_identity(users_by_id.get(row.user_id), row.user_id)
        mode = normalize_space_notification_mode(row.mode)
        preferences_payload.append(
            {
                **identity,
                "mode": mode,
                "mode_label": SPACE_NOTIFICATION_MODE_LABELS.get(mode, SPACE_NOTIFICATION_MODE_LABELS[DEFAULT_SPACE_NOTIFICATION_MODE]),
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        )

    quiet_hours = resolve_space_notification_quiet_hours(space)

    return {
        "meta": {
            "schema_version": 1,
            "source": "LifeOS",
            "exported_at": datetime.utcnow().isoformat(),
            "scope": "space",
        },
        "space": {
            "id": space.id,
            "name": space.name,
            "owner_user_id": space.owner_user_id,
            "owner": snapshot_user_identity(owner_user, space.owner_user_id),
            "default_member_notification_mode": resolve_space_member_default_notification_mode(space),
            "notification_quiet_hours": {
                "enabled": bool(quiet_hours["enabled"]),
                "start_hour_utc": int(quiet_hours["start_hour_utc"]),
                "end_hour_utc": int(quiet_hours["end_hour_utc"]),
            },
            "notification_quiet_hours_enabled": bool(quiet_hours["enabled"]),
            "notification_quiet_hours_start_utc": int(quiet_hours["start_hour_utc"]),
            "notification_quiet_hours_end_utc": int(quiet_hours["end_hour_utc"]),
            "created_at": space.created_at.isoformat() if space.created_at else None,
        },
        "data": {
            "members": members_payload,
            "tasks": tasks_payload,
            "role_templates": [
                serialize_space_role_template(role, template=templates_by_role.get(role))
                for role in SPACE_TEMPLATE_ROLES
            ],
            "notification_preferences": preferences_payload,
        },
    }


def resolve_space_snapshot_user(raw_value: Any) -> User | None:
    if raw_value is None or raw_value == "":
        return None
    if isinstance(raw_value, User):
        return raw_value
    if isinstance(raw_value, int):
        return db.session.get(User, raw_value)
    if isinstance(raw_value, str):
        candidate = raw_value.strip()
        if not candidate:
            return None
        if candidate.isdigit():
            user_by_id = db.session.get(User, int(candidate))
            if user_by_id is not None:
                return user_by_id
        return resolve_user_by_identifier(candidate)
    if isinstance(raw_value, dict):
        user_id_raw = raw_value.get("user_id")
        if isinstance(user_id_raw, int):
            user_by_id = db.session.get(User, user_id_raw)
            if user_by_id is not None:
                return user_by_id
        if isinstance(user_id_raw, str) and user_id_raw.strip().isdigit():
            user_by_id = db.session.get(User, int(user_id_raw.strip()))
            if user_by_id is not None:
                return user_by_id
        for field_name in ("username", "email", "identifier"):
            candidate = raw_value.get(field_name)
            if candidate is None:
                continue
            resolved = resolve_space_snapshot_user(candidate)
            if resolved is not None:
                return resolved
    return None


def resolve_space_snapshot_user_from_payload(payload: dict[str, Any], key_prefix: str) -> User | None:
    for key in (
        key_prefix,
        f"{key_prefix}_user",
        f"{key_prefix}_user_id",
        f"{key_prefix}_username",
        f"{key_prefix}_email",
    ):
        if key not in payload:
            continue
        resolved = resolve_space_snapshot_user(payload.get(key))
        if resolved is not None:
            return resolved
    return None


def import_space_snapshot(
    space: Space,
    snapshot_payload: dict[str, Any],
    *,
    mode: str,
    actor_user: User,
    detail_limit: int = 0,
) -> dict[str, Any]:
    space_payload = snapshot_payload.get("space")
    if isinstance(space_payload, dict):
        space_updates_applied = False

        mode_source_value = None
        for key in ("default_member_notification_mode", "default_notification_mode", "new_member_notification_mode"):
            if key in space_payload:
                mode_source_value = space_payload.get(key)
                break
        if mode_source_value is not None:
            parsed_default_mode, parsed_default_mode_error = parse_space_notification_mode(mode_source_value)
            if parsed_default_mode_error:
                raise ValueError(f"space.default_member_notification_mode: {parsed_default_mode_error}")
            if parsed_default_mode is not None:
                space.default_member_notification_mode = normalize_space_notification_mode(parsed_default_mode)
                space_updates_applied = True

        quiet_hours_payload = space_payload.get("notification_quiet_hours")
        quiet_enabled_value = None
        quiet_start_value = None
        quiet_end_value = None
        if isinstance(quiet_hours_payload, dict):
            if "enabled" in quiet_hours_payload:
                quiet_enabled_value = quiet_hours_payload.get("enabled")
            if "start_hour_utc" in quiet_hours_payload:
                quiet_start_value = quiet_hours_payload.get("start_hour_utc")
            elif "start" in quiet_hours_payload:
                quiet_start_value = quiet_hours_payload.get("start")
            if "end_hour_utc" in quiet_hours_payload:
                quiet_end_value = quiet_hours_payload.get("end_hour_utc")
            elif "end" in quiet_hours_payload:
                quiet_end_value = quiet_hours_payload.get("end")
        elif quiet_hours_payload is not None:
            raise ValueError("space.notification_quiet_hours must be an object")

        for key in ("notification_quiet_hours_enabled", "quiet_hours_enabled"):
            if key in space_payload:
                quiet_enabled_value = space_payload.get(key)
                break
        for key in ("notification_quiet_hours_start_utc", "quiet_hours_start_utc", "quiet_hours_start"):
            if key in space_payload:
                quiet_start_value = space_payload.get(key)
                break
        for key in ("notification_quiet_hours_end_utc", "quiet_hours_end_utc", "quiet_hours_end"):
            if key in space_payload:
                quiet_end_value = space_payload.get(key)
                break

        current_quiet_hours = resolve_space_notification_quiet_hours(space)
        next_quiet_enabled = bool(current_quiet_hours["enabled"])
        next_quiet_start = int(current_quiet_hours["start_hour_utc"])
        next_quiet_end = int(current_quiet_hours["end_hour_utc"])

        if quiet_enabled_value is not None:
            parsed_quiet_enabled, parsed_quiet_enabled_error = parse_bool_value(
                quiet_enabled_value,
                "space.notification_quiet_hours.enabled",
            )
            if parsed_quiet_enabled_error:
                raise ValueError(parsed_quiet_enabled_error)
            if parsed_quiet_enabled is not None:
                next_quiet_enabled = bool(parsed_quiet_enabled)

        if quiet_start_value is not None:
            parsed_quiet_start, parsed_quiet_start_error = parse_hour_value(
                quiet_start_value,
                "space.notification_quiet_hours.start_hour_utc",
            )
            if parsed_quiet_start_error:
                raise ValueError(parsed_quiet_start_error)
            if parsed_quiet_start is not None:
                next_quiet_start = int(parsed_quiet_start)

        if quiet_end_value is not None:
            parsed_quiet_end, parsed_quiet_end_error = parse_hour_value(
                quiet_end_value,
                "space.notification_quiet_hours.end_hour_utc",
            )
            if parsed_quiet_end_error:
                raise ValueError(parsed_quiet_end_error)
            if parsed_quiet_end is not None:
                next_quiet_end = int(parsed_quiet_end)

        if (
            quiet_enabled_value is not None
            or quiet_start_value is not None
            or quiet_end_value is not None
        ):
            if next_quiet_enabled and next_quiet_start == next_quiet_end:
                raise ValueError("space.notification_quiet_hours window cannot have matching start/end when enabled")
            space.notification_quiet_hours_enabled = bool(next_quiet_enabled)
            space.notification_quiet_hours_start_utc = int(next_quiet_start)
            space.notification_quiet_hours_end_utc = int(next_quiet_end)
            space_updates_applied = True

        if space_updates_applied:
            db.session.add(space)

    data_payload = snapshot_payload.get("data", snapshot_payload)
    if not isinstance(data_payload, dict):
        raise ValueError("snapshot data must be an object")

    members_payload = data_payload.get("members", [])
    tasks_payload = data_payload.get("tasks", [])
    templates_payload = data_payload.get("role_templates", [])
    preferences_payload = data_payload.get("notification_preferences", [])

    for field_name, value in (
        ("members", members_payload),
        ("tasks", tasks_payload),
        ("role_templates", templates_payload),
        ("notification_preferences", preferences_payload),
    ):
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be an array")

    imported = {"members": 0, "tasks": 0, "role_templates": 0, "notification_preferences": 0}
    skipped = {"members": 0, "tasks": 0, "role_templates": 0, "notification_preferences": 0}
    safe_detail_limit = max(int(detail_limit or 0), 0)
    skip_details: dict[str, list[dict[str, Any]]] = {key: [] for key in skipped}

    def summarize_skip_item(raw_value: Any) -> dict[str, Any] | None:
        if not isinstance(raw_value, dict):
            if raw_value is None:
                return None
            text_value = str(raw_value).strip()
            return {"value": text_value[:120]} if text_value else None

        summary: dict[str, Any] = {}
        for key in (
            "title",
            "name",
            "username",
            "email",
            "role",
            "display_name",
            "mode",
            "status",
            "task_type",
            "priority",
            "user_id",
            "id",
        ):
            if key not in raw_value:
                continue
            value = raw_value.get(key)
            if value is None or value == "":
                continue
            summary[key] = str(value)[:120]
            if len(summary) >= 3:
                break
        return summary or None

    def record_skip(bucket_key: str, reason: str, raw_value: Any = None) -> None:
        skipped[bucket_key] = int(skipped[bucket_key]) + 1
        if safe_detail_limit <= 0:
            return
        bucket_details = skip_details.get(bucket_key)
        if bucket_details is None or len(bucket_details) >= safe_detail_limit:
            return
        detail_payload: dict[str, Any] = {"reason": str(reason or "Skipped")}
        item_summary = summarize_skip_item(raw_value)
        if item_summary:
            detail_payload["item"] = item_summary
        bucket_details.append(detail_payload)

    templates_by_role = ensure_space_role_templates(space)

    if mode == "replace":
        SpaceTask.query.filter_by(space_id=space.id).delete()
        SpaceNotificationPreference.query.filter_by(space_id=space.id).delete()
        member_rows_to_remove = (
            SpaceMember.query.filter(
                SpaceMember.space_id == space.id,
                SpaceMember.user_id != space.owner_user_id,
            ).all()
        )
        for row in member_rows_to_remove:
            db.session.delete(row)

        for role in EDITABLE_SPACE_TEMPLATE_ROLES:
            defaults = default_space_permissions_for_role(role)
            template = templates_by_role.get(role)
            if template is None:
                template = SpaceRoleTemplate(
                    space_id=space.id,
                    role=role,
                    display_name=DEFAULT_SPACE_ROLE_DISPLAY_NAMES.get(role, role.title()),
                    can_manage_space=defaults["can_manage_space"],
                    can_manage_members=defaults["can_manage_members"],
                    can_assign_admin=defaults["can_assign_admin"],
                    can_delete_space=defaults["can_delete_space"],
                    can_create_tasks=defaults["can_create_tasks"],
                    can_complete_tasks=defaults["can_complete_tasks"],
                    can_manage_tasks=defaults["can_manage_tasks"],
                    can_manage_invites=defaults["can_manage_invites"],
                )
                templates_by_role[role] = template
            template.display_name = DEFAULT_SPACE_ROLE_DISPLAY_NAMES.get(role, role.title())
            template.can_manage_space = bool(defaults["can_manage_space"])
            template.can_manage_members = bool(defaults["can_manage_members"])
            template.can_assign_admin = bool(defaults["can_assign_admin"])
            template.can_delete_space = bool(defaults["can_delete_space"])
            template.can_create_tasks = bool(defaults["can_create_tasks"])
            template.can_complete_tasks = bool(defaults["can_complete_tasks"])
            template.can_manage_tasks = bool(defaults["can_manage_tasks"])
            template.can_manage_invites = bool(defaults["can_manage_invites"])
            db.session.add(template)

        db.session.flush()

    membership_rows = SpaceMember.query.filter_by(space_id=space.id).all()
    memberships_by_user_id = {row.user_id: row for row in membership_rows}
    processed_member_user_ids: set[int] = set()

    for raw in members_payload:
        if not isinstance(raw, dict):
            record_skip("members", "Member row must be an object", raw)
            continue

        role, role_error = parse_space_role(raw.get("role"))
        if role_error:
            record_skip("members", role_error, raw)
            continue
        target_role = role or "member"

        user = (
            resolve_space_snapshot_user_from_payload(raw, "user")
            or resolve_space_snapshot_user(raw.get("username"))
            or resolve_space_snapshot_user(raw.get("email"))
            or resolve_space_snapshot_user(raw.get("user_id"))
        )
        if user is None:
            record_skip("members", "Could not resolve member user from snapshot", raw)
            continue
        if user.id == space.owner_user_id:
            record_skip("members", "Owner cannot be imported as a non-owner member", raw)
            continue
        if user.id in processed_member_user_ids:
            record_skip("members", "Duplicate member entry in snapshot", raw)
            continue

        created_at, _ = parse_datetime_value(raw.get("created_at"), "created_at")
        member_row = memberships_by_user_id.get(user.id)
        if member_row is None:
            member_row = SpaceMember(
                space_id=space.id,
                user_id=user.id,
                role=target_role,
                created_at=created_at or datetime.utcnow(),
            )
        else:
            if member_row.role == "owner":
                record_skip("members", "Owner membership cannot be modified", raw)
                continue
            member_row.role = target_role
            if created_at and (member_row.created_at is None or created_at < member_row.created_at):
                member_row.created_at = created_at

        db.session.add(member_row)
        memberships_by_user_id[user.id] = member_row
        processed_member_user_ids.add(user.id)
        imported["members"] += 1

    db.session.flush()
    membership_user_ids = set(memberships_by_user_id.keys())
    membership_user_ids.add(space.owner_user_id)

    existing_task_signatures: set[tuple[str, str, str, str, str, int]] = set()
    if mode == "merge":
        existing_rows = SpaceTask.query.filter_by(space_id=space.id).all()
        existing_task_signatures = {
            (
                str(row.title or "").strip().lower(),
                str(row.task_type or "task"),
                str(row.status or "todo"),
                str(row.priority or "medium"),
                row.due_on.isoformat() if row.due_on else "",
                max(int(row.xp_reward or 0), 0),
            )
            for row in existing_rows
        }

    for raw in tasks_payload:
        if not isinstance(raw, dict):
            record_skip("tasks", "Task row must be an object", raw)
            continue

        title = str(raw.get("title", "")).strip()
        if not title:
            record_skip("tasks", "title is required", raw)
            continue

        task_type, task_type_error = parse_space_task_type(raw.get("task_type"))
        priority, priority_error = parse_task_priority(raw.get("priority"))
        status, status_error = parse_task_status(raw.get("status"))
        xp_reward, xp_error = parse_int_value(raw.get("xp_reward"), "xp_reward", 1)
        due_on, due_error = parse_date_value(raw.get("due_on"), "due_on")
        completed_at, completed_at_error = parse_datetime_value(raw.get("completed_at"), "completed_at")
        created_at, created_at_error = parse_datetime_value(raw.get("created_at"), "created_at")

        if any(
            error is not None
            for error in (
                task_type_error,
                priority_error,
                status_error,
                xp_error,
                due_error,
                completed_at_error,
                created_at_error,
            )
        ):
            task_error = next(
                (
                    error
                    for error in (
                        task_type_error,
                        priority_error,
                        status_error,
                        xp_error,
                        due_error,
                        completed_at_error,
                        created_at_error,
                    )
                    if error is not None
                ),
                "Task row is invalid",
            )
            record_skip("tasks", task_error, raw)
            continue

        resolved_type = task_type or "task"
        resolved_priority = priority or "medium"
        resolved_status = status or "todo"
        resolved_xp = xp_reward or 25
        resolved_created_at = created_at or datetime.utcnow()
        resolved_completed_at = completed_at
        if resolved_status == "done" and resolved_completed_at is None:
            resolved_completed_at = resolved_created_at

        created_by_user = resolve_space_snapshot_user_from_payload(raw, "created_by")
        completed_by_user = resolve_space_snapshot_user_from_payload(raw, "completed_by")
        created_by_user_id = (
            created_by_user.id
            if created_by_user is not None and created_by_user.id in membership_user_ids
            else actor_user.id
        )
        completed_by_user_id = (
            completed_by_user.id
            if completed_by_user is not None and completed_by_user.id in membership_user_ids
            else None
        )
        if resolved_status == "done" and completed_by_user_id is None:
            completed_by_user_id = created_by_user_id

        signature = (
            title.lower(),
            resolved_type,
            resolved_status,
            resolved_priority,
            due_on.isoformat() if due_on else "",
            resolved_xp,
        )
        if signature in existing_task_signatures:
            record_skip("tasks", "Task duplicates existing task signature", raw)
            continue

        db.session.add(
            SpaceTask(
                space_id=space.id,
                created_by_user_id=created_by_user_id,
                completed_by_user_id=completed_by_user_id if resolved_status == "done" else None,
                title=title,
                status=resolved_status,
                task_type=resolved_type,
                xp_reward=resolved_xp,
                priority=resolved_priority,
                due_on=due_on,
                completed_at=resolved_completed_at if resolved_status == "done" else None,
                created_at=resolved_created_at,
            )
        )
        existing_task_signatures.add(signature)
        imported["tasks"] += 1

    for raw in templates_payload:
        if not isinstance(raw, dict):
            record_skip("role_templates", "Role template row must be an object", raw)
            continue

        role = str(raw.get("role", "")).strip().lower()
        if role not in EDITABLE_SPACE_TEMPLATE_ROLES:
            record_skip("role_templates", "role must be admin or member", raw)
            continue

        template = templates_by_role.get(role)
        if template is None:
            defaults = default_space_permissions_for_role(role)
            template = SpaceRoleTemplate(
                space_id=space.id,
                role=role,
                display_name=DEFAULT_SPACE_ROLE_DISPLAY_NAMES.get(role, role.title()),
                can_manage_space=defaults["can_manage_space"],
                can_manage_members=defaults["can_manage_members"],
                can_assign_admin=defaults["can_assign_admin"],
                can_delete_space=defaults["can_delete_space"],
                can_create_tasks=defaults["can_create_tasks"],
                can_complete_tasks=defaults["can_complete_tasks"],
                can_manage_tasks=defaults["can_manage_tasks"],
                can_manage_invites=defaults["can_manage_invites"],
            )
            templates_by_role[role] = template

        display_name, display_name_error = parse_space_template_display_name(raw.get("display_name"))
        if display_name_error:
            record_skip("role_templates", display_name_error, raw)
            continue

        permission_updates: dict[str, bool] = {}
        permission_error: str | None = None
        for key in SPACE_PERMISSION_KEYS:
            if key not in raw:
                continue
            parsed_bool, parsed_error = parse_bool_value(raw.get(key), key)
            if parsed_error or parsed_bool is None:
                permission_error = parsed_error or f"{key} must be a boolean value"
                break
            permission_updates[key] = bool(parsed_bool)
        if permission_error is not None:
            record_skip("role_templates", permission_error, raw)
            continue

        if display_name is None and not permission_updates:
            record_skip("role_templates", "No role template fields were provided", raw)
            continue

        next_permissions = space_permissions_for_role(role, template=template)
        for key, value in permission_updates.items():
            next_permissions[key] = bool(value)
        next_permissions = normalize_space_permissions(next_permissions, role)
        if role == "member":
            next_permissions["can_assign_admin"] = False
            next_permissions["can_delete_space"] = False

        if display_name:
            template.display_name = display_name
        template.can_manage_space = bool(next_permissions["can_manage_space"])
        template.can_manage_members = bool(next_permissions["can_manage_members"])
        template.can_assign_admin = bool(next_permissions["can_assign_admin"])
        template.can_delete_space = bool(next_permissions["can_delete_space"])
        template.can_create_tasks = bool(next_permissions["can_create_tasks"])
        template.can_complete_tasks = bool(next_permissions["can_complete_tasks"])
        template.can_manage_tasks = bool(next_permissions["can_manage_tasks"])
        template.can_manage_invites = bool(next_permissions["can_manage_invites"])
        db.session.add(template)
        imported["role_templates"] += 1

    db.session.flush()
    membership_user_ids = {
        row.user_id
        for row in SpaceMember.query.filter_by(space_id=space.id).all()
        if isinstance(row.user_id, int)
    }

    for raw in preferences_payload:
        if not isinstance(raw, dict):
            record_skip("notification_preferences", "Notification preference row must be an object", raw)
            continue

        mode_value, mode_error = parse_space_notification_mode(raw.get("mode"))
        if mode_error:
            record_skip("notification_preferences", mode_error, raw)
            continue
        normalized_mode = normalize_space_notification_mode(mode_value)

        user = (
            resolve_space_snapshot_user_from_payload(raw, "user")
            or resolve_space_snapshot_user(raw.get("username"))
            or resolve_space_snapshot_user(raw.get("email"))
            or resolve_space_snapshot_user(raw.get("user_id"))
        )
        if user is None or user.id not in membership_user_ids:
            record_skip(
                "notification_preferences",
                "Preference user was not found or is not a member of this space",
                raw,
            )
            continue

        created_at, created_at_error = parse_datetime_value(raw.get("created_at"), "created_at")
        updated_at, updated_at_error = parse_datetime_value(raw.get("updated_at"), "updated_at")
        if created_at_error or updated_at_error:
            record_skip(
                "notification_preferences",
                created_at_error or updated_at_error or "Invalid preference datetime value",
                raw,
            )
            continue

        row = SpaceNotificationPreference.query.filter_by(space_id=space.id, user_id=user.id).first()
        if row is None:
            row = SpaceNotificationPreference(
                space_id=space.id,
                user_id=user.id,
                mode=normalized_mode,
            )
            if created_at is not None:
                row.created_at = created_at

        row.mode = normalized_mode
        if updated_at is not None:
            row.updated_at = updated_at

        db.session.add(row)
        imported["notification_preferences"] += 1

    result: dict[str, Any] = {"imported": imported, "skipped": skipped}
    if safe_detail_limit > 0:
        truncated = {
            key: max(int(skipped.get(key, 0)) - len(skip_details.get(key, [])), 0)
            for key in skipped
        }
        result["details"] = {
            "detail_limit": safe_detail_limit,
            "skipped": skip_details,
            "truncated": truncated,
        }
    return result


def normalize_space_snapshot_import_count_map(raw_value: Any) -> dict[str, int]:
    if not isinstance(raw_value, dict):
        return {}
    normalized: dict[str, int] = {}
    for raw_key, raw_count in raw_value.items():
        key = str(raw_key or "").strip().lower()
        if not key:
            continue
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            count = 0
        normalized[key] = max(count, 0)
    return normalized


def build_space_snapshot_import_audit_details(
    summary: dict[str, Any],
    snapshot_payload: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    imported = normalize_space_snapshot_import_count_map(summary.get("imported"))
    skipped = normalize_space_snapshot_import_count_map(summary.get("skipped"))

    details: dict[str, Any] = {
        "mode": str(mode or "merge").strip().lower() or "merge",
        "imported": imported,
        "skipped": skipped,
        "totals": {
            "imported": sum(imported.values()),
            "skipped": sum(skipped.values()),
        },
    }

    snapshot_meta = snapshot_payload.get("meta") if isinstance(snapshot_payload, dict) else None
    if isinstance(snapshot_meta, dict):
        meta_payload: dict[str, Any] = {}
        for key in ("schema_version", "source", "scope", "exported_at"):
            if key not in snapshot_meta:
                continue
            value = snapshot_meta.get(key)
            if value is None or value == "":
                continue
            meta_payload[key] = value
        if meta_payload:
            details["snapshot_meta"] = meta_payload

    source_space = snapshot_payload.get("space") if isinstance(snapshot_payload, dict) else None
    if isinstance(source_space, dict):
        source_payload: dict[str, Any] = {}
        source_id = source_space.get("id")
        if source_id is not None and source_id != "":
            source_payload["id"] = source_id
        source_name = str(source_space.get("name", "")).strip()
        if source_name:
            source_payload["name"] = source_name
        if source_payload:
            details["source_space"] = source_payload

    return details


def summarize_space_snapshot_counts(space_id: int) -> dict[str, int]:
    return {
        "members": int(SpaceMember.query.filter_by(space_id=space_id).count()),
        "tasks": int(SpaceTask.query.filter_by(space_id=space_id).count()),
        "role_templates": int(
            SpaceRoleTemplate.query.filter(
                SpaceRoleTemplate.space_id == space_id,
                SpaceRoleTemplate.role.in_(SPACE_TEMPLATE_ROLES),
            ).count()
        ),
        "notification_preferences": int(SpaceNotificationPreference.query.filter_by(space_id=space_id).count()),
    }


def required_space_replace_confirmation_phrase(space_id: int) -> str:
    safe_space_id = int(space_id)
    return f"{SPACE_IMPORT_REPLACE_CONFIRM_PREFIX} {safe_space_id}"


def build_space_snapshot_import_preview(
    space: Space,
    snapshot_payload: dict[str, Any],
    *,
    mode: str,
    actor_user: User,
) -> dict[str, Any]:
    current_counts = summarize_space_snapshot_counts(space.id)
    savepoint = db.session.begin_nested()
    try:
        summary = import_space_snapshot(
            space,
            snapshot_payload,
            mode=mode,
            actor_user=actor_user,
            detail_limit=SPACE_IMPORT_PREVIEW_DETAIL_LIMIT,
        )
        projected_counts = summarize_space_snapshot_counts(space.id)
    finally:
        savepoint.rollback()
        db.session.expire_all()

    diff_counts = {key: int(projected_counts.get(key, 0)) - int(current_counts.get(key, 0)) for key in current_counts}
    replace_confirmation_phrase = required_space_replace_confirmation_phrase(space.id)

    warnings: list[str] = []
    if mode == "replace":
        warnings.append(
            "Replace mode will overwrite shared tasks, non-owner memberships, role templates, "
            "notification preferences, and space reminder defaults/quiet hours."
        )
        warnings.append(
            f"Replace mode requires confirmation_phrase: {replace_confirmation_phrase}"
        )
    for bucket_key, skipped_count in (summary.get("skipped") or {}).items():
        safe_skipped = int(skipped_count or 0)
        if safe_skipped > 0:
            warnings.append(f"{safe_skipped} {bucket_key.replace('_', ' ')} item(s) would be skipped.")
    details_meta = summary.get("details")
    truncated_map = details_meta.get("truncated") if isinstance(details_meta, dict) else {}
    if isinstance(truncated_map, dict):
        omitted_total = sum(max(int(value or 0), 0) for value in truncated_map.values())
        if omitted_total > 0:
            warnings.append(
                f"{omitted_total} additional skipped item detail(s) are omitted from preview."
            )

    return {
        "mode": mode,
        "summary": summary,
        "current": current_counts,
        "projected": projected_counts,
        "diff": diff_counts,
        "warnings": warnings,
        "confirmation": {
            "required": mode == "replace",
            "phrase": replace_confirmation_phrase if mode == "replace" else None,
        },
    }


@app.get("/api/health")
def health() -> tuple[dict[str, Any], int]:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "auth": "token"}, 200


@app.post("/api/auth/register")
def register() -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return auth_error("Request body must be an object", 400)
    username = normalize_username(str(payload.get("username", "")))
    email = normalize_email(str(payload.get("email", "")))
    display_name = str(payload.get("display_name", "")).strip()
    password = str(payload.get("password", ""))

    if not USERNAME_PATTERN.match(username):
        return auth_error("Username must be 3-24 chars (letters, numbers, underscore)", 400)
    if "@" not in email or "." not in email.split("@")[-1]:
        return auth_error("Enter a valid email", 400)
    if not display_name:
        return auth_error("Display name is required", 400)
    password_error = validate_password(password)
    if password_error:
        return auth_error(password_error, 400)

    existing = User.query.filter(
        or_(func.lower(User.username) == username, func.lower(User.email) == email)
    ).first()
    if existing is not None:
        return auth_error("Username or email already exists", 409)

    user = User(
        username=username,
        email=email,
        display_name=display_name,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.flush()
    ensure_reminder_settings(user)
    ensure_avatar_profile(user)
    db.session.commit()

    return {"message": "Registration successful", "token": issue_token(user), "user": serialize_user(user)}, 201


@app.post("/api/auth/login")
def login() -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    identifier = normalize_username(str(payload.get("identifier", "")))
    password = str(payload.get("password", ""))

    if not identifier or not password:
        return auth_error("identifier and password are required", 400)

    user = User.query.filter(
        or_(func.lower(User.username) == identifier, func.lower(User.email) == identifier)
    ).first()
    if user is None or not user.password_hash or not check_password_hash(user.password_hash, password):
        return auth_error("Invalid credentials", 401)

    return {"message": "Login successful", "token": issue_token(user), "user": serialize_user(user)}, 200


@app.get("/api/auth/me")
@require_auth
def me(auth_user: User) -> tuple[dict[str, Any], int]:
    return {"user": serialize_user(auth_user)}, 200


@app.post("/api/auth/logout")
@require_auth
def logout(auth_user: User) -> tuple[dict[str, str], int]:
    token_value = extract_bearer_token(request.headers.get("Authorization", ""))
    if token_value:
        revoke_auth_token(token_value, user_id=auth_user.id)
        db.session.commit()
    return {"message": "Logged out"}, 200


@app.get("/api/account/export")
@require_auth
def export_account_snapshot(auth_user: User) -> tuple[dict[str, Any], int]:
    return {"snapshot": build_account_snapshot(auth_user)}, 200


@app.post("/api/account/import")
@require_auth
def import_account_data(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "merge")).strip().lower()
    if mode not in {"merge", "replace"}:
        return auth_error("mode must be merge or replace", 400)

    snapshot_payload = payload.get("snapshot", payload)
    if not isinstance(snapshot_payload, dict):
        return auth_error("snapshot must be an object", 400)

    apply_profile = bool(payload.get("apply_profile", False))
    try:
        summary = import_account_snapshot(auth_user, snapshot_payload, mode=mode, apply_profile=apply_profile)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return auth_error(str(exc), 400)

    refreshed_user = db.session.get(User, auth_user.id) or auth_user
    return {
        "message": "Import completed",
        "mode": mode,
        "summary": summary,
        "user": serialize_user(refreshed_user),
        "dashboard": build_dashboard_payload(refreshed_user),
    }, 200


@app.patch("/api/account/profile")
@require_auth
def update_account_profile(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    if not any(field in payload for field in ("display_name", "username", "email")):
        return auth_error("No profile fields were provided", 400)
    previous_email = auth_user.email

    if "display_name" in payload:
        display_name = str(payload.get("display_name", "")).strip()
        if not display_name:
            return auth_error("Display name is required", 400)
        if len(display_name) > 80:
            return auth_error("Display name is too long", 400)
        auth_user.display_name = display_name

    if "username" in payload:
        username = normalize_username(str(payload.get("username", "")))
        if not USERNAME_PATTERN.match(username):
            return auth_error("Username must be 3-24 chars (letters, numbers, underscore)", 400)
        existing_user = User.query.filter(
            func.lower(User.username) == username,
            User.id != auth_user.id,
        ).first()
        if existing_user is not None:
            return auth_error("Username already exists", 409)
        auth_user.username = username

    if "email" in payload:
        email = normalize_email(str(payload.get("email", "")))
        if "@" not in email or "." not in email.split("@")[-1]:
            return auth_error("Enter a valid email", 400)
        existing_user = User.query.filter(
            func.lower(User.email) == email,
            User.id != auth_user.id,
        ).first()
        if existing_user is not None:
            return auth_error("Email already exists", 409)
        auth_user.email = email

    settings_row = ReminderChannelSettings.query.filter_by(user_id=auth_user.id).first()
    if settings_row is not None:
        if not settings_row.email_address or settings_row.email_address == previous_email:
            settings_row.email_address = auth_user.email
            db.session.add(settings_row)

    db.session.add(auth_user)
    db.session.commit()
    return {"message": "Profile updated", "user": serialize_user(auth_user)}, 200


@app.post("/api/account/password")
@require_auth
def update_account_password(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    current_password = str(payload.get("current_password", ""))
    new_password = str(payload.get("new_password", ""))

    if not current_password or not new_password:
        return auth_error("current_password and new_password are required", 400)
    if not auth_user.password_hash or not check_password_hash(auth_user.password_hash, current_password):
        return auth_error("Current password is incorrect", 400)

    password_error = validate_password(new_password)
    if password_error:
        return auth_error(password_error, 400)
    if check_password_hash(auth_user.password_hash, new_password):
        return auth_error("New password must be different from current password", 400)

    auth_user.password_hash = generate_password_hash(new_password)
    db.session.add(auth_user)
    db.session.commit()
    return {"message": "Password updated"}, 200


@app.get("/api/account/reminder-channels")
@require_auth
def get_reminder_channels(auth_user: User) -> tuple[dict[str, Any], int]:
    settings_row = ensure_reminder_settings(auth_user)
    recent_rows = (
        ReminderDeliveryLog.query.filter_by(user_id=auth_user.id)
        .order_by(ReminderDeliveryLog.created_at.desc(), ReminderDeliveryLog.id.desc())
        .limit(20)
        .all()
    )
    return {
        "settings": serialize_reminder_settings(settings_row, auth_user),
        "recent_deliveries": [serialize_reminder_delivery_log(row) for row in recent_rows],
        "providers": {"email": REMINDER_EMAIL_PROVIDER, "sms": REMINDER_SMS_PROVIDER},
    }, 200


@app.patch("/api/account/reminder-channels")
@require_auth
def update_reminder_channels(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    settings_row = ensure_reminder_settings(auth_user)

    if "in_app_enabled" in payload:
        in_app_enabled, in_app_error = parse_bool_value(payload.get("in_app_enabled"), "in_app_enabled")
        if in_app_error:
            return auth_error(in_app_error, 400)
        if in_app_enabled is None:
            return auth_error("in_app_enabled is required", 400)
        settings_row.in_app_enabled = in_app_enabled

    if "email_enabled" in payload:
        email_enabled, email_enabled_error = parse_bool_value(payload.get("email_enabled"), "email_enabled")
        if email_enabled_error:
            return auth_error(email_enabled_error, 400)
        if email_enabled is None:
            return auth_error("email_enabled is required", 400)
        settings_row.email_enabled = email_enabled

    if "sms_enabled" in payload:
        sms_enabled, sms_enabled_error = parse_bool_value(payload.get("sms_enabled"), "sms_enabled")
        if sms_enabled_error:
            return auth_error(sms_enabled_error, 400)
        if sms_enabled is None:
            return auth_error("sms_enabled is required", 400)
        settings_row.sms_enabled = sms_enabled

    if "email_address" in payload:
        email_address, email_address_error = parse_email_address(payload.get("email_address"), "email_address")
        if email_address_error:
            return auth_error(email_address_error, 400)
        settings_row.email_address = email_address

    if "phone_number" in payload:
        phone_number, phone_number_error = parse_phone_number(payload.get("phone_number"), "phone_number")
        if phone_number_error:
            return auth_error(phone_number_error, 400)
        settings_row.phone_number = phone_number

    if "digest_hour_utc" in payload:
        digest_hour, digest_error = parse_hour_value(payload.get("digest_hour_utc"), "digest_hour_utc")
        if digest_error:
            return auth_error(digest_error, 400)
        if digest_hour is None:
            return auth_error("digest_hour_utc is required", 400)
        settings_row.digest_hour_utc = digest_hour

    if settings_row.email_enabled and not (settings_row.email_address or auth_user.email):
        return auth_error("Set an email address before enabling email reminders", 400)
    if settings_row.sms_enabled and not settings_row.phone_number:
        return auth_error("Set a phone number before enabling SMS reminders", 400)

    db.session.add(settings_row)
    db.session.commit()
    return {"message": "Reminder channels updated", "settings": serialize_reminder_settings(settings_row, auth_user)}, 200


@app.post("/api/account/reminder-channels/test")
@require_auth
def send_test_reminder(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    channel, channel_error = parse_reminder_channel(payload.get("channel"))
    if channel_error:
        return auth_error(channel_error, 400)
    target_channel = channel or "all"

    settings_row = ensure_reminder_settings(auth_user)
    message = str(payload.get("message", "")).strip() or "This is a test reminder from LifeOS."
    subject = "LifeOS Reminder Test"
    sent = 0
    errors = 0
    details: list[dict[str, Any]] = []

    channels_to_send = ["email", "sms"] if target_channel == "all" else [target_channel]
    for current_channel in channels_to_send:
        recipient = (settings_row.email_address or auth_user.email) if current_channel == "email" else settings_row.phone_number
        recipient = (recipient or "").strip()
        if not recipient:
            reminder_log(
                user_id=auth_user.id,
                channel=current_channel,
                recipient="(missing)",
                provider=REMINDER_EMAIL_PROVIDER if current_channel == "email" else REMINDER_SMS_PROVIDER,
                status="error",
                subject=subject,
                body=message,
                notification_count=0,
                error_message="Missing recipient",
            )
            details.append({"channel": current_channel, "status": "error", "error": "Missing recipient"})
            errors += 1
            continue

        if current_channel == "email":
            ok, provider, err_msg = send_email_message(recipient, subject, message)
        else:
            ok, provider, err_msg = send_sms_message(recipient, message)

        reminder_log(
            user_id=auth_user.id,
            channel=current_channel,
            recipient=recipient,
            provider=provider,
            status="sent" if ok else "error",
            subject=subject,
            body=message,
            notification_count=0,
            dedupe_key=None,
            error_message=err_msg,
        )
        details.append({"channel": current_channel, "status": "sent" if ok else "error", "provider": provider, "error": err_msg})
        if ok:
            sent += 1
        else:
            errors += 1

    prune_reminder_delivery_logs(user_id=auth_user.id)
    db.session.commit()
    status_code = 200 if errors == 0 else 207
    return {"message": "Test reminder sent" if errors == 0 else "Test reminder completed with errors", "sent": sent, "errors": errors, "details": details}, status_code


@app.post("/api/account/reminder-channels/run")
@require_auth
def run_reminder_delivery_for_user(auth_user: User) -> tuple[dict[str, Any], int]:
    summary = run_reminder_delivery_cycle(user_id=auth_user.id, force_send=True, source="manual_run", commit=True)
    return {"message": "Reminder delivery run complete", "summary": summary}, 200


@app.get("/api/account/reminder-deliveries")
@require_auth
def list_reminder_deliveries(auth_user: User) -> tuple[dict[str, Any], int]:
    limit = request.args.get("limit", type=int) or 30
    safe_limit = max(1, min(limit, 100))
    rows = (
        ReminderDeliveryLog.query.filter_by(user_id=auth_user.id)
        .order_by(ReminderDeliveryLog.created_at.desc(), ReminderDeliveryLog.id.desc())
        .limit(safe_limit)
        .all()
    )
    return {"deliveries": [serialize_reminder_delivery_log(row) for row in rows]}, 200


@app.post("/api/account/recovery/request")
def request_password_recovery() -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    identifier = str(payload.get("identifier", "")).strip()
    if not identifier:
        return auth_error("identifier is required", 400)

    user = resolve_user_by_identifier(identifier)
    response_payload: dict[str, Any] = {"message": "If the account exists, reset instructions were generated."}
    if user is not None and user.password_hash:
        reset_token = password_reset_serializer().dumps({"user_id": user.id, "purpose": "password_reset"})
        if EXPOSE_RESET_TOKEN:
            response_payload["reset_token"] = reset_token
            response_payload["expires_in_seconds"] = RESET_TOKEN_MAX_AGE_SECONDS

    return response_payload, 200


@app.post("/api/account/recovery/confirm")
def confirm_password_recovery() -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    token_value = str(payload.get("token", "")).strip()
    new_password = str(payload.get("new_password", ""))

    if not token_value or not new_password:
        return auth_error("token and new_password are required", 400)

    password_error = validate_password(new_password)
    if password_error:
        return auth_error(password_error, 400)

    try:
        reset_payload = password_reset_serializer().loads(token_value, max_age=RESET_TOKEN_MAX_AGE_SECONDS)
    except SignatureExpired:
        return auth_error("Recovery token expired", 400)
    except BadSignature:
        return auth_error("Invalid recovery token", 400)

    if not isinstance(reset_payload, dict) or reset_payload.get("purpose") != "password_reset":
        return auth_error("Invalid recovery token", 400)
    user_id = reset_payload.get("user_id")
    if not isinstance(user_id, int):
        return auth_error("Invalid recovery token", 400)

    user = db.session.get(User, user_id)
    if user is None:
        return auth_error("User not found", 404)
    if user.password_hash and check_password_hash(user.password_hash, new_password):
        return auth_error("New password must be different from current password", 400)

    user.password_hash = generate_password_hash(new_password)
    db.session.add(user)
    db.session.commit()
    return {"message": "Password reset successful"}, 200


@app.get("/api/dashboard")
@require_auth
def dashboard(auth_user: User) -> tuple[dict[str, Any], int]:
    refresh_recurring_for_user(auth_user, source="dashboard")
    requested_user_id = request.args.get("user_id", type=int)
    if requested_user_id is not None and requested_user_id != auth_user.id:
        return auth_error("Forbidden", 403)
    return jsonify(build_dashboard_payload(auth_user)), 200


@app.get("/api/shop")
@require_auth
def get_shop(auth_user: User) -> tuple[dict[str, Any], int]:
    return jsonify(build_shop_payload(auth_user)), 200


@app.get("/api/inventory")
@require_auth
def get_inventory(auth_user: User) -> tuple[dict[str, Any], int]:
    limit_value = request.args.get("limit", type=int)
    return jsonify(build_inventory_payload(auth_user, history_limit=limit_value or 240)), 200


@app.post("/api/inventory/redeem/<int:purchase_id>")
@require_auth
def redeem_inventory_purchase(purchase_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    purchase = db.session.get(ShopPurchase, purchase_id)
    if purchase is None:
        return auth_error("Purchase not found", 404)
    if purchase.user_id != auth_user.id:
        return auth_error("Purchase does not belong to authenticated user", 403)

    serialized_purchase = serialize_shop_purchase(purchase)
    reward_type = str(serialized_purchase.get("reward_type", "")).strip().lower()
    if reward_type != "self_reward":
        return auth_error("Only self-reward purchases can be redeemed", 400)
    if purchase.claimed_at is not None:
        return {
            "message": "Reward already redeemed",
            "purchase": serialize_shop_purchase(purchase),
            "inventory": build_inventory_payload(auth_user, history_limit=240),
        }, 200

    payload = request.get_json(silent=True) or {}
    claim_note = ""
    if isinstance(payload, dict):
        claim_note = str(payload.get("claim_note", "")).strip()
    if len(claim_note) > 255:
        claim_note = claim_note[:255]

    claim_time = datetime.utcnow()
    purchase.claimed_at = claim_time
    purchase.claimed_note = claim_note or None
    db.session.add(purchase)

    xp_gained = award_action_xp(
        auth_user.id,
        "reward.claim",
        f"Reward redeemed: {purchase.title}",
        10,
        claim_time,
    )
    coins_gained = award_action_coins(
        auth_user.id,
        "reward.claim",
        f"Reward redeemed coins: {purchase.title}",
        4,
        claim_time,
    )
    achievements_payload = build_achievements_payload(auth_user, grant_new=True, unlock_time=claim_time)
    db.session.commit()

    refreshed_user = db.session.get(User, auth_user.id) or auth_user
    return {
        "message": "Reward redeemed",
        "purchase": serialize_shop_purchase(purchase),
        "xp_gained": int(xp_gained),
        "coins_gained": int(coins_gained),
        "achievements": achievements_payload,
        "inventory": build_inventory_payload(refreshed_user, history_limit=240),
        "dashboard": build_dashboard_payload(refreshed_user),
    }, 200


@app.get("/api/achievements")
@require_auth
def get_achievements(auth_user: User) -> tuple[dict[str, Any], int]:
    refresh_param = str(request.args.get("refresh", "1")).strip().lower()
    grant_new = refresh_param not in {"0", "false", "no", "off"}
    payload = build_achievements_payload(auth_user, grant_new=grant_new, unlock_time=datetime.utcnow())
    if grant_new and payload.get("summary", {}).get("newly_unlocked", 0):
        db.session.commit()
    return jsonify(payload), 200


@app.get("/api/challenges")
@require_auth
def get_challenges(auth_user: User) -> tuple[dict[str, Any], int]:
    window_type = str(request.args.get("window_type", "")).strip().lower()
    selected_window = window_type if window_type in CHALLENGE_WINDOW_TYPES else None
    return jsonify(build_challenges_payload(auth_user, only_window=selected_window)), 200


@app.post("/api/challenges/claim")
@require_auth
def claim_challenge_reward(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return auth_error("Request body must be an object", 400)

    window_type = str(payload.get("window_type", "daily")).strip().lower() or "daily"
    if window_type not in CHALLENGE_WINDOW_TYPES:
        return auth_error("window_type must be daily or weekly", 400)
    challenge_key = str(payload.get("challenge_key", "")).strip().lower()
    if not challenge_key:
        return auth_error("challenge_key is required", 400)

    challenge_payload = build_challenges_payload(auth_user, only_window=window_type)
    window_payload = challenge_payload.get(window_type) if isinstance(challenge_payload, dict) else None
    if not isinstance(window_payload, dict):
        return auth_error("Challenge window unavailable", 404)
    challenge_rows = window_payload.get("challenges", [])
    challenge_row = next((row for row in challenge_rows if str(row.get("key", "")).strip().lower() == challenge_key), None)
    if challenge_row is None:
        return auth_error("Challenge not found in active rotation", 404)
    if challenge_row.get("claimed"):
        return auth_error("Challenge reward already claimed", 409)
    if not challenge_row.get("completed"):
        return auth_error("Challenge is not completed yet", 400)

    window_key = str(window_payload.get("window_key", "")).strip()
    if not window_key:
        return auth_error("Challenge window key missing", 500)

    existing_claim = ChallengeClaim.query.filter_by(
        user_id=auth_user.id,
        challenge_key=challenge_key,
        window_type=window_type,
        window_key=window_key,
    ).first()
    if existing_claim is not None:
        return auth_error("Challenge reward already claimed", 409)

    claim_time = datetime.utcnow()
    reward_xp = max(int(challenge_row.get("reward_xp", 0) or 0), 0)
    reward_coins = max(int(challenge_row.get("reward_coins", 0) or 0), 0)
    if reward_xp > 0:
        award_xp(
            auth_user.id,
            f"Challenge claimed ({window_type}): {challenge_row.get('title', challenge_key)}",
            reward_xp,
            claim_time,
        )
    if reward_coins > 0:
        award_coins(
            auth_user.id,
            f"Challenge claimed coins ({window_type}): {challenge_row.get('title', challenge_key)}",
            reward_coins,
            claim_time,
        )

    claim_row = ChallengeClaim(
        user_id=auth_user.id,
        challenge_key=challenge_key,
        window_type=window_type,
        window_key=window_key,
        challenge_title=str(challenge_row.get("title", challenge_key)).strip(),
        reward_xp=reward_xp,
        reward_coins=reward_coins,
        claimed_at=claim_time,
    )
    db.session.add(claim_row)
    achievements_payload = build_achievements_payload(auth_user, grant_new=True, unlock_time=claim_time)
    db.session.commit()

    refreshed_user = db.session.get(User, auth_user.id) or auth_user
    refreshed_challenges = build_challenges_payload(refreshed_user, only_window=window_type)
    return {
        "message": "Challenge reward claimed",
        "claim": {
            "id": claim_row.id,
            "challenge_key": claim_row.challenge_key,
            "window_type": claim_row.window_type,
            "window_key": claim_row.window_key,
            "challenge_title": claim_row.challenge_title,
            "reward_xp": int(claim_row.reward_xp or 0),
            "reward_coins": int(claim_row.reward_coins or 0),
            "claimed_at": claim_row.claimed_at.isoformat() if claim_row.claimed_at else None,
        },
        "achievements": achievements_payload,
        "challenges": refreshed_challenges,
        "dashboard": build_dashboard_payload(refreshed_user),
    }, 200


@app.get("/api/timeline")
@require_auth
def get_timeline(auth_user: User) -> tuple[dict[str, Any], int]:
    requested_user_id = request.args.get("user_id", type=int)
    if requested_user_id is not None and requested_user_id != auth_user.id:
        return auth_error("Forbidden", 403)
    days_value = request.args.get("days", type=int)
    return jsonify(build_timeline_payload(auth_user, days=days_value)), 200


@app.get("/api/leaderboard")
@require_auth
def get_leaderboard(auth_user: User) -> tuple[dict[str, Any], int]:
    requested_user_id = request.args.get("user_id", type=int)
    if requested_user_id is not None and requested_user_id != auth_user.id:
        return auth_error("Forbidden", 403)
    limit_value = request.args.get("limit", type=int)
    scope_value = normalize_leaderboard_scope(request.args.get("scope"))
    return jsonify(build_leaderboard_payload(auth_user, limit=limit_value, scope=scope_value)), 200


@app.get("/api/season-pass")
@require_auth
def get_season_pass(auth_user: User) -> tuple[dict[str, Any], int]:
    requested_user_id = request.args.get("user_id", type=int)
    if requested_user_id is not None and requested_user_id != auth_user.id:
        return auth_error("Forbidden", 403)
    return jsonify(build_season_pass_payload(auth_user)), 200


@app.get("/api/season-pass/premium")
@require_auth
def get_season_pass_premium(auth_user: User) -> tuple[dict[str, Any], int]:
    return {
        "enabled": bool(auth_user.season_pass_premium),
        "message": "Premium track enabled" if auth_user.season_pass_premium else "Premium track disabled",
    }, 200


@app.patch("/api/season-pass/premium")
@require_auth
def update_season_pass_premium(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    enabled, enabled_error = parse_bool_value(payload.get("enabled"), "enabled")
    if enabled_error:
        return auth_error(enabled_error, 400)
    if enabled is None:
        return auth_error("enabled is required", 400)

    auth_user.season_pass_premium = bool(enabled)
    db.session.add(auth_user)
    db.session.commit()

    refreshed_user = db.session.get(User, auth_user.id) or auth_user
    return {
        "message": "Premium track enabled" if refreshed_user.season_pass_premium else "Premium track disabled",
        "user": serialize_user(refreshed_user),
        "season_pass": build_season_pass_payload(refreshed_user),
        "dashboard": build_dashboard_payload(refreshed_user),
    }, 200


@app.post("/api/season-pass/claim")
@require_auth
def claim_season_pass_tier(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return auth_error("Request body must be an object", 400)

    tier_value, tier_error = parse_int_value(payload.get("tier"), "tier", minimum=1)
    if tier_error:
        return auth_error(tier_error, 400)
    if tier_value is None:
        return auth_error("tier is required", 400)
    safe_tier = int(tier_value)
    if safe_tier > SEASON_PASS_MAX_TIER:
        return auth_error(f"tier cannot exceed {SEASON_PASS_MAX_TIER}", 400)
    track = str(payload.get("track", "free")).strip().lower() or "free"
    if track not in {"free", "premium"}:
        return auth_error("track must be free or premium", 400)

    season_payload = build_season_pass_payload(auth_user)
    season_meta = season_payload.get("season", {}) if isinstance(season_payload, dict) else {}
    season_key = str(season_meta.get("season_key", "")).strip()
    if not season_key:
        return auth_error("Season is unavailable", 500)

    tier_rows = season_payload.get("tiers", []) if isinstance(season_payload, dict) else []
    tier_row = next((row for row in tier_rows if int(row.get("tier", 0) or 0) == safe_tier), None)
    if tier_row is None:
        return auth_error("Season pass tier not found", 404)
    if not tier_row.get("unlocked"):
        return auth_error("Season pass tier is not unlocked yet", 400)

    free_tier = tier_row.get("free", {}) if isinstance(tier_row, dict) else {}
    premium_tier = tier_row.get("premium", {}) if isinstance(tier_row, dict) else {}
    selected_tier = free_tier if track == "free" else premium_tier
    if not isinstance(selected_tier, dict):
        return auth_error("Season pass tier reward unavailable", 404)
    if track == "premium" and not bool(auth_user.season_pass_premium):
        return auth_error("Premium track is disabled for this account", 403)
    if bool(selected_tier.get("claimed")):
        return auth_error("Season pass tier already claimed", 409)
    if not bool(selected_tier.get("claimable")):
        return auth_error("Season pass tier reward is not claimable", 400)

    claim_time = datetime.utcnow()
    reward_xp = max(int(selected_tier.get("reward_xp", 0) or 0), 0)
    reward_coins = max(int(selected_tier.get("reward_coins", 0) or 0), 0)
    if reward_xp > 0:
        award_xp(
            auth_user.id,
            f"Season pass {track} tier {safe_tier} claimed ({season_key})",
            reward_xp,
            claim_time,
        )
    if reward_coins > 0:
        award_coins(
            auth_user.id,
            f"Season pass {track} tier {safe_tier} coins claimed ({season_key})",
            reward_coins,
            claim_time,
        )

    if track == "free":
        existing_claim = SeasonPassClaim.query.filter_by(
            user_id=auth_user.id,
            season_key=season_key,
            tier=safe_tier,
        ).first()
        if existing_claim is not None:
            return auth_error("Season pass tier already claimed", 409)
        claim_row = SeasonPassClaim(
            user_id=auth_user.id,
            season_key=season_key,
            tier=safe_tier,
            reward_xp=reward_xp,
            reward_coins=reward_coins,
            claimed_at=claim_time,
        )
    else:
        existing_claim = SeasonPassPremiumClaim.query.filter_by(
            user_id=auth_user.id,
            season_key=season_key,
            tier=safe_tier,
        ).first()
        if existing_claim is not None:
            return auth_error("Season pass tier already claimed", 409)
        claim_row = SeasonPassPremiumClaim(
            user_id=auth_user.id,
            season_key=season_key,
            tier=safe_tier,
            reward_xp=reward_xp,
            reward_coins=reward_coins,
            claimed_at=claim_time,
        )
    db.session.add(claim_row)
    achievements_payload = build_achievements_payload(auth_user, grant_new=True, unlock_time=claim_time)
    db.session.commit()

    refreshed_user = db.session.get(User, auth_user.id) or auth_user
    return {
        "message": f"Season pass {track} tier {safe_tier} claimed",
        "claim": {
            "id": claim_row.id,
            "track": track,
            "season_key": claim_row.season_key,
            "tier": int(claim_row.tier),
            "reward_xp": int(claim_row.reward_xp or 0),
            "reward_coins": int(claim_row.reward_coins or 0),
            "claimed_at": claim_row.claimed_at.isoformat() if claim_row.claimed_at else None,
        },
        "achievements": achievements_payload,
        "season_pass": build_season_pass_payload(refreshed_user),
        "leaderboard": build_leaderboard_payload(refreshed_user, scope="global"),
        "dashboard": build_dashboard_payload(refreshed_user),
    }, 200


@app.post("/api/shop/purchase")
@require_auth
def purchase_shop_item(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return auth_error("Request body must be an object", 400)

    item_key = str(payload.get("item_key", "")).strip().lower()
    if not item_key:
        return auth_error("item_key is required", 400)

    shop_payload = build_shop_payload(auth_user)
    item_state_by_key = {
        str(row.get("item_key", "")).strip().lower(): row
        for row in shop_payload.get("items", [])
        if isinstance(row, dict)
    }
    item_state = item_state_by_key.get(item_key)
    if item_state is None:
        return auth_error("Shop item not found", 404)

    item = SHOP_ITEMS_BY_KEY.get(item_key)
    if item is None:
        return auth_error("Shop item not found", 404)

    repeatable = bool(item.get("repeatable", False))
    if not repeatable and bool(item_state.get("owned", False)):
        return auth_error("Item already owned", 409)

    if not bool(item_state.get("can_purchase_today", True)):
        blocked_message = str(item_state.get("availability_reason") or "Item unavailable right now").strip()
        return auth_error(blocked_message or "Item unavailable right now", 409)

    price_coins = max(int(item_state.get("price_coins", item.get("price_coins", 0)) or 0), 0)
    if price_coins < 1:
        return auth_error("Item cannot be purchased", 400)
    if not bool(item_state.get("coin_affordable", int(auth_user.coins or 0) >= price_coins)):
        return auth_error("Not enough coins", 400)

    purchase_time = datetime.utcnow()
    coins_spent = spend_coins(auth_user, f"Shop purchase: {item.get('title', item_key)}", price_coins, purchase_time)
    if coins_spent < 1:
        return auth_error("Not enough coins", 400)

    reward_type = str(item.get("reward_type", "self_reward")).strip().lower()
    metadata = {
        "reward_type": reward_type,
        "repeatable": repeatable,
    }
    if item.get("unlock_slot"):
        metadata["unlock_slot"] = item.get("unlock_slot")
    if item.get("unlock_value"):
        metadata["unlock_value"] = item.get("unlock_value")
    if item.get("unlock_set_key"):
        metadata["unlock_set_key"] = item.get("unlock_set_key")
    if item.get("set_key"):
        metadata["set_key"] = item.get("set_key")
    if reward_type == "season_pass_premium_unlock":
        auth_user.season_pass_premium = True
        db.session.add(auth_user)
        metadata["season_pass_premium_enabled"] = True

    purchase_row = ShopPurchase(
        user_id=auth_user.id,
        item_key=item_key,
        category=str(item.get("category", "self_reward")).strip().lower(),
        title=str(item.get("title", item_key)).strip(),
        price_coins=price_coins,
        metadata_json=json.dumps(metadata),
        purchased_at=purchase_time,
    )
    db.session.add(purchase_row)
    achievements_payload = build_achievements_payload(auth_user, grant_new=True, unlock_time=purchase_time)
    db.session.commit()

    refreshed_user = db.session.get(User, auth_user.id) or auth_user
    return {
        "message": f"Purchased {item.get('title', item_key)}",
        "coins_spent": int(coins_spent),
        "coins_balance": max(int(refreshed_user.coins or 0), 0),
        "purchase": serialize_shop_purchase(purchase_row),
        "user": serialize_user(refreshed_user),
        "achievements": achievements_payload,
        "shop": build_shop_payload(refreshed_user),
        "inventory": build_inventory_payload(refreshed_user, history_limit=240),
        "challenges": build_challenges_payload(refreshed_user),
        "season_pass": build_season_pass_payload(refreshed_user),
        "avatar": build_avatar_payload(refreshed_user),
        "dashboard": build_dashboard_payload(refreshed_user),
    }, 200


@app.get("/api/avatar")
@require_auth
def get_avatar(auth_user: User) -> tuple[dict[str, Any], int]:
    return jsonify(build_avatar_payload(auth_user)), 200


@app.patch("/api/avatar")
@require_auth
def update_avatar(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return auth_error("Request body must be an object", 400)

    slots = [slot for slot in DEFAULT_AVATAR_PROFILE if slot in payload]
    if not slots:
        return auth_error("Provide at least one avatar field to update", 400)

    owned_item_keys = user_owned_shop_item_keys(auth_user.id)
    profile = ensure_avatar_profile(auth_user)
    has_changes = False
    for slot in slots:
        candidate = str(payload.get(slot, "")).strip().lower()
        option = AVATAR_OPTION_INDEX.get(slot, {}).get(candidate)
        if option is None:
            return auth_error(f"{slot} option is invalid", 400)
        if not is_avatar_option_unlocked(option, owned_item_keys):
            return auth_error(f"{slot} option is locked. Buy it in Shop first.", 403)
        if getattr(profile, slot) != candidate:
            setattr(profile, slot, candidate)
            has_changes = True

    if has_changes:
        db.session.add(profile)
        db.session.commit()

    refreshed_user = db.session.get(User, auth_user.id) or auth_user
    response_payload = build_avatar_payload(refreshed_user)
    response_payload["message"] = "Avatar updated" if has_changes else "Avatar unchanged"
    response_payload["dashboard"] = build_dashboard_payload(refreshed_user)
    return response_payload, 200


@app.get("/api/xp/rules")
@require_auth
def get_xp_rules(auth_user: User) -> tuple[dict[str, Any], int]:
    _ = auth_user
    ordered_rules = {key: XP_RULES[key] for key in sorted(XP_RULES.keys())}
    return {"rules": ordered_rules}, 200


@app.get("/api/stats")
@require_auth
def stats(auth_user: User) -> tuple[dict[str, Any], int]:
    requested_user_id = request.args.get("user_id", type=int)
    if requested_user_id is not None and requested_user_id != auth_user.id:
        return auth_error("Forbidden", 403)
    return jsonify(build_stats_payload(auth_user, request.args.get("days", type=int))), 200


@app.get("/api/notifications")
@require_auth
def notifications(auth_user: User) -> tuple[dict[str, Any], int]:
    refresh_recurring_for_user(auth_user, source="notifications")
    requested_user_id = request.args.get("user_id", type=int)
    if requested_user_id is not None and requested_user_id != auth_user.id:
        return auth_error("Forbidden", 403)
    payload = build_notifications_payload(auth_user, delivery_context="in_app")
    settings_row = ReminderChannelSettings.query.filter_by(user_id=auth_user.id).first()
    if settings_row is not None and not settings_row.in_app_enabled:
        payload["counts"]["total"] = 0
        payload["items"] = []
    return jsonify(payload), 200


@app.get("/api/recurring-rules")
@require_auth
def list_recurring_rules(auth_user: User) -> tuple[dict[str, Any], int]:
    status_filter = request.args.get("active")
    query = RecurringRule.query.filter(RecurringRule.user_id == auth_user.id)
    if status_filter is not None:
        active_flag, active_error = parse_bool_value(status_filter, "active")
        if active_error:
            return auth_error(active_error, 400)
        if active_flag is not None:
            query = query.filter(RecurringRule.active.is_(active_flag))
    rows = query.order_by(RecurringRule.active.desc(), RecurringRule.created_at.desc(), RecurringRule.id.desc()).all()
    return {"rules": [serialize_recurring_rule(row) for row in rows]}, 200


@app.post("/api/recurring-rules")
@require_auth
def create_recurring_rule(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return auth_error("title is required", 400)

    task_type, task_type_error = parse_task_type(payload.get("task_type"))
    if task_type_error:
        return auth_error(task_type_error, 400)
    safe_task_type = task_type or "task"
    if safe_task_type not in {"task", "habit"}:
        return auth_error("task_type must be task or habit", 400)

    priority, priority_error = parse_task_priority(payload.get("priority"))
    if priority_error:
        return auth_error(priority_error, 400)

    xp_reward, xp_error = parse_int_value(payload.get("xp_reward"), "xp_reward", 1)
    if xp_error:
        return auth_error(xp_error, 400)

    frequency, frequency_error = parse_recurrence_frequency(payload.get("frequency"))
    if frequency_error:
        return auth_error(frequency_error, 400)

    interval, interval_error = parse_int_value(payload.get("interval"), "interval", 1)
    if interval_error:
        return auth_error(interval_error, 400)
    if interval and interval > 30:
        return auth_error("interval must be 30 or less", 400)

    start_on, start_error = parse_date_value(payload.get("start_on"), "start_on")
    if start_error:
        return auth_error(start_error, 400)
    end_on, end_error = parse_date_value(payload.get("end_on"), "end_on")
    if end_error:
        return auth_error(end_error, 400)
    if start_on and end_on and end_on < start_on:
        return auth_error("end_on must be on or after start_on", 400)

    active, active_error = parse_bool_value(payload.get("active"), "active")
    if active_error:
        return auth_error(active_error, 400)

    weekdays, weekday_error = parse_weekday_values(payload.get("days_of_week"))
    if weekday_error:
        return auth_error(weekday_error, 400)
    resolved_frequency = frequency or "daily"
    if resolved_frequency == "weekly" and not weekdays:
        inferred_weekday = (start_on or date.today()).weekday()
        weekdays = [inferred_weekday]

    rule = RecurringRule(
        user_id=auth_user.id,
        title=title,
        task_type=safe_task_type,
        priority=priority or "medium",
        xp_reward=xp_reward or 20,
        frequency=resolved_frequency,
        interval=interval or 1,
        days_of_week=encode_weekdays(weekdays),
        start_on=start_on,
        end_on=end_on,
        active=True if active is None else active,
    )
    db.session.add(rule)
    db.session.commit()
    return {"message": "Recurring rule created", "rule": serialize_recurring_rule(rule)}, 201


@app.patch("/api/recurring-rules/<int:rule_id>")
@require_auth
def update_recurring_rule(rule_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    rule = db.session.get(RecurringRule, rule_id)
    if rule is None:
        return {"error": "Recurring rule not found"}, 404
    if rule.user_id != auth_user.id:
        return {"error": "Recurring rule does not belong to authenticated user"}, 403

    payload = request.get_json(silent=True) or {}

    if "title" in payload:
        title = str(payload.get("title", "")).strip()
        if not title:
            return auth_error("title is required", 400)
        rule.title = title

    if "task_type" in payload:
        task_type, task_type_error = parse_task_type(payload.get("task_type"))
        if task_type_error:
            return auth_error(task_type_error, 400)
        if task_type is None or task_type not in {"task", "habit"}:
            return auth_error("task_type must be task or habit", 400)
        rule.task_type = task_type

    if "priority" in payload:
        priority, priority_error = parse_task_priority(payload.get("priority"))
        if priority_error:
            return auth_error(priority_error, 400)
        if priority is None:
            return auth_error("priority is required", 400)
        rule.priority = priority

    if "xp_reward" in payload:
        xp_reward, xp_error = parse_int_value(payload.get("xp_reward"), "xp_reward", 1)
        if xp_error:
            return auth_error(xp_error, 400)
        if xp_reward is None:
            return auth_error("xp_reward is required", 400)
        rule.xp_reward = xp_reward

    if "frequency" in payload:
        frequency, frequency_error = parse_recurrence_frequency(payload.get("frequency"))
        if frequency_error:
            return auth_error(frequency_error, 400)
        if frequency is None:
            return auth_error("frequency is required", 400)
        rule.frequency = frequency

    if "interval" in payload:
        interval, interval_error = parse_int_value(payload.get("interval"), "interval", 1)
        if interval_error:
            return auth_error(interval_error, 400)
        if interval is None:
            return auth_error("interval is required", 400)
        if interval > 30:
            return auth_error("interval must be 30 or less", 400)
        rule.interval = interval

    if "days_of_week" in payload:
        weekdays, weekday_error = parse_weekday_values(payload.get("days_of_week"))
        if weekday_error:
            return auth_error(weekday_error, 400)
        rule.days_of_week = encode_weekdays(weekdays)

    if "start_on" in payload:
        start_on, start_error = parse_date_value(payload.get("start_on"), "start_on")
        if start_error:
            return auth_error(start_error, 400)
        rule.start_on = start_on

    if "end_on" in payload:
        end_on, end_error = parse_date_value(payload.get("end_on"), "end_on")
        if end_error:
            return auth_error(end_error, 400)
        rule.end_on = end_on

    if rule.start_on and rule.end_on and rule.end_on < rule.start_on:
        return auth_error("end_on must be on or after start_on", 400)

    if "active" in payload:
        active, active_error = parse_bool_value(payload.get("active"), "active")
        if active_error:
            return auth_error(active_error, 400)
        if active is None:
            return auth_error("active is required", 400)
        rule.active = active

    if rule.frequency == "weekly" and not decode_weekdays(rule.days_of_week):
        inferred_weekday = (rule.start_on or date.today()).weekday()
        rule.days_of_week = encode_weekdays([inferred_weekday])

    db.session.add(rule)
    db.session.commit()
    return {"message": "Recurring rule updated", "rule": serialize_recurring_rule(rule)}, 200


@app.delete("/api/recurring-rules/<int:rule_id>")
@require_auth
def delete_recurring_rule(rule_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    rule = db.session.get(RecurringRule, rule_id)
    if rule is None:
        return {"error": "Recurring rule not found"}, 404
    if rule.user_id != auth_user.id:
        return {"error": "Recurring rule does not belong to authenticated user"}, 403

    Task.query.filter_by(user_id=auth_user.id, recurrence_rule_id=rule.id, status="todo").delete()
    db.session.delete(rule)
    db.session.commit()
    return {"message": "Recurring rule deleted", "rule_id": rule_id}, 200


@app.post("/api/recurring-rules/run")
@require_auth
def run_recurring_rules(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    backfill_days, backfill_error = parse_int_value(payload.get("backfill_days"), "backfill_days", 1)
    if backfill_error:
        return auth_error(backfill_error, 400)
    if backfill_days and backfill_days > RECURRING_MAX_BACKFILL_DAYS:
        return auth_error(f"backfill_days cannot exceed {RECURRING_MAX_BACKFILL_DAYS}", 400)

    summary = run_recurring_generation(
        user_id=auth_user.id,
        backfill_days=backfill_days,
        source="manual_run",
        commit=True,
    )
    return {"message": "Recurring generation complete", "summary": summary}, 200


@app.get("/api/spaces")
@require_auth
def list_spaces(auth_user: User) -> tuple[dict[str, Any], int]:
    memberships = SpaceMember.query.filter_by(user_id=auth_user.id).all()
    if not memberships:
        return {"spaces": []}, 200

    membership_by_space = {membership.space_id: membership for membership in memberships}
    space_ids = list(membership_by_space.keys())
    spaces = Space.query.filter(Space.id.in_(space_ids)).order_by(Space.created_at.desc(), Space.id.desc()).all()

    count_rows = (
        db.session.query(SpaceMember.space_id, func.count(SpaceMember.id))
        .filter(SpaceMember.space_id.in_(space_ids))
        .group_by(SpaceMember.space_id)
        .all()
    )
    count_by_space = {space_id: int(count) for space_id, count in count_rows}
    notification_mode_by_space = load_user_space_notification_mode_map(auth_user.id, space_ids)

    return {
        "spaces": [
            serialize_space(
                space,
                current_role=membership_by_space[space.id].role,
                member_count=count_by_space.get(space.id, 1),
                notification_mode=resolve_space_notification_mode(
                    space.id,
                    auth_user.id,
                    modes_by_space=notification_mode_by_space,
                ),
            )
            for space in spaces
        ]
    }, 200


@app.post("/api/spaces")
@require_auth
def create_space(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    name, name_error = parse_space_name(payload.get("name"))
    if name_error:
        return auth_error(name_error, 400)

    space = Space(name=name or "New Space", owner_user_id=auth_user.id)
    db.session.add(space)
    db.session.flush()
    owner_membership = SpaceMember(space_id=space.id, user_id=auth_user.id, role="owner")
    db.session.add(owner_membership)
    templates_by_role = ensure_space_role_templates(space)
    db.session.commit()

    owner_permissions = resolve_space_permissions(space.id, owner_membership, templates_by_role=templates_by_role)
    return {
        "message": "Space created",
        "space": serialize_space(space, current_role="owner", member_count=1, permissions=owner_permissions),
    }, 201


@app.get("/api/spaces/<int:space_id>")
@require_auth
def get_space(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)

    return build_space_detail_payload(space, membership, auth_user), 200


@app.get("/api/spaces/<int:space_id>/export")
@require_auth
def export_space_data(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)

    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_space"):
        return auth_error("Forbidden", 403)

    return {"snapshot": build_space_snapshot(space)}, 200


@app.post("/api/spaces/<int:space_id>/import/preview")
@require_auth
def preview_space_data_import(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    if membership.role != "owner":
        return auth_error("Only the space owner can preview snapshot imports", 403)

    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "merge")).strip().lower()
    if mode not in {"merge", "replace"}:
        return auth_error("mode must be merge or replace", 400)

    snapshot_payload = payload.get("snapshot", payload)
    if not isinstance(snapshot_payload, dict):
        return auth_error("snapshot must be an object", 400)

    try:
        preview = build_space_snapshot_import_preview(
            space,
            snapshot_payload,
            mode=mode,
            actor_user=auth_user,
        )
    except ValueError as exc:
        db.session.rollback()
        return auth_error(str(exc), 400)

    return {"message": "Space snapshot preview generated", **preview}, 200


@app.post("/api/spaces/<int:space_id>/import")
@require_auth
def import_space_data(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    if membership.role != "owner":
        return auth_error("Only the space owner can import snapshots", 403)

    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "merge")).strip().lower()
    if mode not in {"merge", "replace"}:
        return auth_error("mode must be merge or replace", 400)
    if mode == "replace":
        required_phrase = required_space_replace_confirmation_phrase(space.id)
        confirmation_phrase = str(payload.get("confirmation_phrase", "")).strip()
        if confirmation_phrase != required_phrase:
            return auth_error(f"confirmation_phrase must exactly match: {required_phrase}", 400)

    snapshot_payload = payload.get("snapshot", payload)
    if not isinstance(snapshot_payload, dict):
        return auth_error("snapshot must be an object", 400)

    try:
        summary = import_space_snapshot(space, snapshot_payload, mode=mode, actor_user=auth_user)
        audit_details = build_space_snapshot_import_audit_details(summary, snapshot_payload, mode=mode)
        imported_total = int((audit_details.get("totals") or {}).get("imported", 0))
        skipped_total = int((audit_details.get("totals") or {}).get("skipped", 0))
        log_space_activity(
            space_id=space.id,
            actor_user_id=auth_user.id,
            event_type="space_snapshot_imported",
            entity_type="space",
            entity_id=space.id,
            summary=(
                f"{auth_user.display_name} imported a {mode} snapshot into {space.name} "
                f"({imported_total} imported, {skipped_total} skipped)"
            ),
            details=audit_details,
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return auth_error(str(exc), 400)

    refreshed_membership = SpaceMember.query.filter_by(space_id=space.id, user_id=auth_user.id).first() or membership
    return {
        "message": "Space snapshot imported",
        "mode": mode,
        "summary": summary,
        **build_space_detail_payload(space, refreshed_membership, auth_user),
    }, 200


@app.patch("/api/spaces/<int:space_id>")
@require_auth
def update_space(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_space"):
        return auth_error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    if "name" not in payload:
        return auth_error("name is required", 400)

    name, name_error = parse_space_name(payload.get("name"))
    if name_error:
        return auth_error(name_error, 400)

    space.name = name or space.name
    db.session.add(space)
    db.session.commit()
    refreshed_membership = SpaceMember.query.filter_by(space_id=space.id, user_id=auth_user.id).first() or membership
    return {"message": "Space updated", **build_space_detail_payload(space, refreshed_membership, auth_user)}, 200


@app.delete("/api/spaces/<int:space_id>")
@require_auth
def delete_space(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_delete_space"):
        return auth_error("You do not have permission to delete this space", 403)

    SpaceActivityEvent.query.filter_by(space_id=space.id).delete()
    SpaceNotificationPreference.query.filter_by(space_id=space.id).delete()
    SpaceRoleTemplate.query.filter_by(space_id=space.id).delete()
    SpaceInvite.query.filter_by(space_id=space.id).delete()
    SpaceTask.query.filter_by(space_id=space.id).delete()
    SpaceMember.query.filter_by(space_id=space.id).delete()
    db.session.delete(space)
    db.session.commit()
    return {"message": "Space deleted", "space_id": space_id}, 200


@app.post("/api/spaces/<int:space_id>/members")
@require_auth
def add_space_member(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_members"):
        return auth_error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    identifier = str(payload.get("identifier", "")).strip()
    if not identifier:
        return auth_error("identifier is required", 400)

    role, role_error = parse_space_role(payload.get("role"))
    if role_error:
        return auth_error(role_error, 400)
    target_role = role or "member"
    if target_role == "admin" and not permissions.get("can_assign_admin"):
        return auth_error("You do not have permission to assign admin role", 403)
    if target_role not in ASSIGNABLE_SPACE_ROLES:
        return auth_error("role must be admin or member", 400)

    invited_user = resolve_user_by_identifier(identifier)
    if invited_user is None:
        return auth_error("User not found", 404)

    existing_member = SpaceMember.query.filter_by(space_id=space.id, user_id=invited_user.id).first()
    if existing_member is not None:
        return auth_error("User is already in this space", 409)

    member = SpaceMember(space_id=space.id, user_id=invited_user.id, role=target_role)
    db.session.add(member)
    ensure_space_member_notification_preference(space, invited_user.id)
    db.session.commit()

    return {"message": "Member added", "member": serialize_space_member(member, invited_user, auth_user.id)}, 201


@app.patch("/api/spaces/<int:space_id>/members/<int:member_user_id>")
@require_auth
def update_space_member_role(space_id: int, member_user_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_members"):
        return auth_error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    role, role_error = parse_space_role(payload.get("role"))
    if role_error:
        return auth_error(role_error, 400)
    if role is None:
        return auth_error("role is required", 400)
    if role not in ASSIGNABLE_SPACE_ROLES:
        return auth_error("role must be admin or member", 400)
    if role == "admin" and not permissions.get("can_assign_admin"):
        return auth_error("You do not have permission to assign admin role", 403)

    target_member = SpaceMember.query.filter_by(space_id=space.id, user_id=member_user_id).first()
    if target_member is None:
        return {"error": "Space member not found"}, 404
    if target_member.role == "owner":
        return auth_error("Owner role cannot be changed", 400)
    if target_member.role == "admin" and not permissions.get("can_assign_admin"):
        return auth_error("You do not have permission to update admin roles", 403)

    previous_role = target_member.role
    target_user = db.session.get(User, member_user_id)
    if previous_role == role:
        return {"message": "Member role unchanged", "member": serialize_space_member(target_member, target_user, auth_user.id)}, 200

    target_member.role = role
    db.session.add(target_member)
    target_name = target_user.display_name if target_user else f"User {member_user_id}"
    log_space_activity(
        space_id=space.id,
        actor_user_id=auth_user.id,
        event_type="space_member_role_updated",
        entity_type="space_member",
        entity_id=target_member.id,
        summary=f"{auth_user.display_name} changed {target_name} role: {previous_role} -> {role}",
        details={
            "member_user_id": member_user_id,
            "member_display_name": target_name,
            "from_role": previous_role,
            "to_role": role,
        },
    )
    db.session.commit()
    return {"message": "Member role updated", "member": serialize_space_member(target_member, target_user, auth_user.id)}, 200


@app.delete("/api/spaces/<int:space_id>/members/<int:member_user_id>")
@require_auth
def remove_space_member(space_id: int, member_user_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)

    target_member = SpaceMember.query.filter_by(space_id=space.id, user_id=member_user_id).first()
    if target_member is None:
        return {"error": "Space member not found"}, 404

    if target_member.role == "owner":
        return auth_error("Owner cannot be removed from the space", 400)

    is_self = target_member.user_id == auth_user.id
    if not is_self and not permissions.get("can_manage_members"):
        return auth_error("Forbidden", 403)

    if not is_self and target_member.role == "admin" and not permissions.get("can_assign_admin"):
        return auth_error("You do not have permission to remove admins", 403)

    SpaceNotificationPreference.query.filter_by(space_id=space.id, user_id=target_member.user_id).delete()
    db.session.delete(target_member)
    db.session.commit()
    return {
        "message": "Left space" if is_self else "Member removed",
        "space_id": space_id,
        "user_id": member_user_id,
    }, 200


@app.get("/api/spaces/<int:space_id>/role-templates")
@require_auth
def list_space_role_templates(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)

    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    return {
        "templates": [
            serialize_space_role_template(role, template=templates_by_role.get(role))
            for role in SPACE_TEMPLATE_ROLES
        ],
        "permissions": permissions,
        "can_edit": membership.role == "owner",
    }, 200


@app.patch("/api/spaces/<int:space_id>/role-templates/<string:role_name>")
@require_auth
def update_space_role_template(space_id: int, role_name: str, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    if membership.role != "owner":
        return auth_error("Only the owner can update role templates", 403)

    normalized_role = str(role_name or "").strip().lower()
    if normalized_role not in EDITABLE_SPACE_TEMPLATE_ROLES:
        return auth_error("role_name must be admin or member", 400)

    payload = request.get_json(silent=True) or {}
    display_name: str | None = None
    updated_fields: dict[str, Any] = {}

    if "display_name" in payload:
        display_name, display_name_error = parse_space_template_display_name(payload.get("display_name"))
        if display_name_error:
            return auth_error(display_name_error, 400)
        updated_fields["display_name"] = display_name

    permission_updates: dict[str, bool] = {}
    for key in SPACE_PERMISSION_KEYS:
        if key not in payload:
            continue
        parsed_bool, parsed_error = parse_bool_value(payload.get(key), key)
        if parsed_error:
            return auth_error(parsed_error, 400)
        if parsed_bool is None:
            return auth_error(f"{key} is required", 400)
        permission_updates[key] = parsed_bool

    if not updated_fields and not permission_updates:
        return auth_error("No role template fields were provided", 400)

    templates_by_role = load_space_role_templates_map(space.id)
    template = templates_by_role.get(normalized_role)
    if template is None:
        defaults = default_space_permissions_for_role(normalized_role)
        template = SpaceRoleTemplate(
            space_id=space.id,
            role=normalized_role,
            display_name=DEFAULT_SPACE_ROLE_DISPLAY_NAMES.get(normalized_role, normalized_role.title()),
            can_manage_space=defaults["can_manage_space"],
            can_manage_members=defaults["can_manage_members"],
            can_assign_admin=defaults["can_assign_admin"],
            can_delete_space=defaults["can_delete_space"],
            can_create_tasks=defaults["can_create_tasks"],
            can_complete_tasks=defaults["can_complete_tasks"],
            can_manage_tasks=defaults["can_manage_tasks"],
            can_manage_invites=defaults["can_manage_invites"],
        )

    previous_permissions = space_permissions_for_role(normalized_role, template=template)
    previous_display_name = template.display_name

    next_permissions = space_permissions_for_role(normalized_role, template=template)
    for key, value in permission_updates.items():
        next_permissions[key] = bool(value)
    next_permissions = normalize_space_permissions(next_permissions, normalized_role)
    if normalized_role == "member":
        next_permissions["can_assign_admin"] = False
        next_permissions["can_delete_space"] = False

    permission_changes = {
        key: {"before": bool(previous_permissions.get(key)), "after": bool(next_permissions.get(key))}
        for key in SPACE_PERMISSION_KEYS
        if bool(previous_permissions.get(key)) != bool(next_permissions.get(key))
    }

    template.can_manage_space = bool(next_permissions["can_manage_space"])
    template.can_manage_members = bool(next_permissions["can_manage_members"])
    template.can_assign_admin = bool(next_permissions["can_assign_admin"])
    template.can_delete_space = bool(next_permissions["can_delete_space"])
    template.can_create_tasks = bool(next_permissions["can_create_tasks"])
    template.can_complete_tasks = bool(next_permissions["can_complete_tasks"])
    template.can_manage_tasks = bool(next_permissions["can_manage_tasks"])
    template.can_manage_invites = bool(next_permissions["can_manage_invites"])
    if display_name:
        template.display_name = display_name

    next_display_name = template.display_name
    display_name_changed = bool(display_name) and previous_display_name != next_display_name

    db.session.add(template)
    db.session.flush()
    if permission_changes or display_name_changed:
        summary_parts: list[str] = []
        if display_name_changed:
            summary_parts.append("display name")
        if permission_changes:
            permission_label = "permission" if len(permission_changes) == 1 else "permissions"
            summary_parts.append(f"{len(permission_changes)} {permission_label}")

        details_payload: dict[str, Any] = {
            "role": normalized_role,
            "permissions": permission_changes,
            "changed_permission_keys": sorted(permission_changes.keys()),
        }
        if display_name_changed:
            details_payload["display_name"] = {"before": previous_display_name, "after": next_display_name}

        log_space_activity(
            space_id=space.id,
            actor_user_id=auth_user.id,
            event_type="space_role_template_updated",
            entity_type="space_role_template",
            entity_id=template.id,
            summary=(
                f"{auth_user.display_name} updated {normalized_role} template"
                + (f" ({', '.join(summary_parts)})" if summary_parts else "")
            ),
            details=details_payload,
        )
    db.session.commit()

    refreshed_templates = load_space_role_templates_map(space.id)
    return {
        "message": "Role template updated",
        "template": serialize_space_role_template(normalized_role, template=refreshed_templates.get(normalized_role)),
        "templates": [
            serialize_space_role_template(role, template=refreshed_templates.get(role))
            for role in SPACE_TEMPLATE_ROLES
        ],
    }, 200


@app.get("/api/spaces/<int:space_id>/notification-preference")
@require_auth
def get_space_notification_preference(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)

    default_mode = resolve_space_member_default_notification_mode(space)
    mode = resolve_space_notification_mode(space.id, auth_user.id)
    return {
        "preference": serialize_space_notification_preference(
            space.id,
            auth_user.id,
            mode,
            default_mode=default_mode,
        ),
        "default": serialize_space_notification_default(space),
    }, 200


@app.patch("/api/spaces/<int:space_id>/notification-preference")
@require_auth
def update_space_notification_preference(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    mode, mode_error = parse_space_notification_mode(payload.get("mode"))
    if mode_error:
        return auth_error(mode_error, 400)
    if mode is None:
        return auth_error("mode is required", 400)
    normalized_mode = normalize_space_notification_mode(mode)

    row = SpaceNotificationPreference.query.filter_by(space_id=space.id, user_id=auth_user.id).first()
    if normalized_mode == DEFAULT_SPACE_NOTIFICATION_MODE:
        if row is not None:
            db.session.delete(row)
    else:
        if row is None:
            row = SpaceNotificationPreference(space_id=space.id, user_id=auth_user.id, mode=normalized_mode)
        else:
            row.mode = normalized_mode
        db.session.add(row)

    db.session.commit()
    return {
        "message": "Space notification preference updated",
        "preference": serialize_space_notification_preference(
            space.id,
            auth_user.id,
            normalized_mode,
            default_mode=resolve_space_member_default_notification_mode(space),
        ),
        "default": serialize_space_notification_default(space),
    }, 200


@app.get("/api/spaces/<int:space_id>/notification-default")
@require_auth
def get_space_notification_default(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    return {"default": serialize_space_notification_default(space)}, 200


@app.patch("/api/spaces/<int:space_id>/notification-default")
@require_auth
def update_space_notification_default(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    if membership.role != "owner":
        return auth_error("Only the space owner can change the default reminder mode", 403)

    payload = request.get_json(silent=True) or {}
    mode, mode_error = parse_space_notification_mode(payload.get("mode"))
    if mode_error:
        return auth_error(mode_error, 400)
    if mode is None:
        return auth_error("mode is required", 400)

    normalized_mode = normalize_space_notification_mode(mode)
    previous_mode = resolve_space_member_default_notification_mode(space)
    space.default_member_notification_mode = normalized_mode
    db.session.add(space)
    if previous_mode != normalized_mode:
        log_space_activity(
            space_id=space.id,
            actor_user_id=auth_user.id,
            event_type="space_notification_default_updated",
            entity_type="space",
            entity_id=space.id,
            summary=(
                f"{auth_user.display_name} changed new-member reminder mode default "
                f"from {previous_mode} to {normalized_mode}."
            ),
            details={
                "space_id": space.id,
                "previous_mode": previous_mode,
                "next_mode": normalized_mode,
            },
        )
    db.session.commit()
    return {
        "message": "Default reminder mode for new members updated",
        "default": serialize_space_notification_default(space),
    }, 200


@app.post("/api/spaces/<int:space_id>/notification-default/apply")
@require_auth
def apply_space_notification_default(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    if membership.role != "owner":
        return auth_error("Only the space owner can apply the default reminder mode to existing members", 403)

    payload = request.get_json(silent=True) or {}
    include_owner_raw = payload.get("include_owner", False)
    include_owner, include_owner_error = parse_bool_value(include_owner_raw, "include_owner")
    if include_owner_error:
        return auth_error(include_owner_error, 400)

    default_mode = resolve_space_member_default_notification_mode(space)
    summary = apply_space_notification_default_to_members(space, include_owner=bool(include_owner))
    if int(summary.get("applied", 0)) > 0:
        log_space_activity(
            space_id=space.id,
            actor_user_id=auth_user.id,
            event_type="space_notification_default_applied",
            entity_type="space",
            entity_id=space.id,
            summary=(
                f"{auth_user.display_name} applied {default_mode} reminder mode to existing members "
                f"({summary.get('applied', 0)} changed)."
            ),
            details={
                "space_id": space.id,
                "default_mode": default_mode,
                "include_owner": bool(include_owner),
                **summary,
            },
        )
    db.session.commit()

    return {
        "message": "Default reminder mode applied to existing members",
        "default": serialize_space_notification_default(space),
        "summary": summary,
    }, 200


@app.get("/api/spaces/<int:space_id>/notification-quiet-hours")
@require_auth
def get_space_notification_quiet_hours(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    return {"quiet_hours": serialize_space_notification_quiet_hours(space, now_utc=datetime.utcnow())}, 200


@app.patch("/api/spaces/<int:space_id>/notification-quiet-hours")
@require_auth
def update_space_notification_quiet_hours(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)

    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_space"):
        return auth_error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return auth_error("Request body must be an object", 400)

    has_enabled = "enabled" in payload
    has_start = "start_hour_utc" in payload
    has_end = "end_hour_utc" in payload
    if not (has_enabled or has_start or has_end):
        return auth_error("At least one field must be provided: enabled, start_hour_utc, end_hour_utc", 400)

    current_quiet_hours = resolve_space_notification_quiet_hours(space)
    next_enabled = bool(current_quiet_hours["enabled"])
    next_start = int(current_quiet_hours["start_hour_utc"])
    next_end = int(current_quiet_hours["end_hour_utc"])

    if has_enabled:
        parsed_enabled, parsed_enabled_error = parse_bool_value(payload.get("enabled"), "enabled")
        if parsed_enabled_error:
            return auth_error(parsed_enabled_error, 400)
        next_enabled = bool(parsed_enabled)

    if has_start:
        parsed_start, parsed_start_error = parse_hour_value(payload.get("start_hour_utc"), "start_hour_utc")
        if parsed_start_error:
            return auth_error(parsed_start_error, 400)
        if parsed_start is None:
            return auth_error("start_hour_utc is required", 400)
        next_start = int(parsed_start)

    if has_end:
        parsed_end, parsed_end_error = parse_hour_value(payload.get("end_hour_utc"), "end_hour_utc")
        if parsed_end_error:
            return auth_error(parsed_end_error, 400)
        if parsed_end is None:
            return auth_error("end_hour_utc is required", 400)
        next_end = int(parsed_end)

    if next_enabled and next_start == next_end:
        return auth_error("start_hour_utc and end_hour_utc cannot match when quiet hours are enabled", 400)

    previous_quiet_hours = {
        "enabled": bool(current_quiet_hours["enabled"]),
        "start_hour_utc": int(current_quiet_hours["start_hour_utc"]),
        "end_hour_utc": int(current_quiet_hours["end_hour_utc"]),
    }
    next_quiet_hours = {
        "enabled": bool(next_enabled),
        "start_hour_utc": int(next_start),
        "end_hour_utc": int(next_end),
    }

    if previous_quiet_hours != next_quiet_hours:
        space.notification_quiet_hours_enabled = bool(next_enabled)
        space.notification_quiet_hours_start_utc = int(next_start)
        space.notification_quiet_hours_end_utc = int(next_end)
        db.session.add(space)
        log_space_activity(
            space_id=space.id,
            actor_user_id=auth_user.id,
            event_type="space_notification_quiet_hours_updated",
            entity_type="space",
            entity_id=space.id,
            summary=(
                f"{auth_user.display_name} updated reminder quiet hours "
                f"to {next_start:02d}:00-{next_end:02d}:00 UTC ({'enabled' if next_enabled else 'disabled'})."
            ),
            details={
                "space_id": space.id,
                "previous": previous_quiet_hours,
                "next": next_quiet_hours,
            },
        )

    db.session.commit()
    return {
        "message": "Space quiet hours updated",
        "quiet_hours": serialize_space_notification_quiet_hours(space, now_utc=datetime.utcnow()),
    }, 200


@app.get("/api/spaces/<int:space_id>/audit-events")
@require_auth
def list_space_audit_events(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)

    requested_limit, limit_error = parse_int_value(request.args.get("limit"), "limit", 1)
    if limit_error:
        return auth_error(limit_error, 400)
    limit = requested_limit if requested_limit is not None else SPACE_AUDIT_LOG_DEFAULT_LIMIT
    limit = min(max(limit, 1), 100)

    raw_event_type = str(request.args.get("event_type", "")).strip().lower()
    selected_event_type = "all"
    selected_event_types = set(SPACE_ACTIVITY_AUDIT_EVENT_TYPES)
    if raw_event_type and raw_event_type != "all":
        if raw_event_type not in SPACE_ACTIVITY_AUDIT_EVENT_TYPES:
            return auth_error("event_type is invalid", 400)
        selected_event_type = raw_event_type
        selected_event_types = {raw_event_type}

    days = None
    days_raw = request.args.get("days")
    if days_raw is not None and str(days_raw).strip() != "":
        parsed_days, days_error = parse_int_value(days_raw, "days", 1)
        if days_error:
            return auth_error(days_error, 400)
        days = parsed_days

    search_text = str(request.args.get("query", "")).strip()
    search_text = search_text[:120]

    query = SpaceActivityEvent.query.filter_by(space_id=space.id)
    query = query.filter(SpaceActivityEvent.event_type.in_(selected_event_types))
    if days is not None:
        window_start = datetime.utcnow() - timedelta(days=max(int(days), 1))
        query = query.filter(SpaceActivityEvent.created_at >= window_start)
    if search_text:
        query_token = f"%{search_text.lower()}%"
        query = query.filter(
            or_(
                func.lower(SpaceActivityEvent.summary).like(query_token),
                func.lower(SpaceActivityEvent.event_type).like(query_token),
                func.lower(SpaceActivityEvent.entity_type).like(query_token),
                func.lower(SpaceActivityEvent.details_json).like(query_token),
            )
        )
    rows = query.order_by(SpaceActivityEvent.created_at.desc(), SpaceActivityEvent.id.desc()).limit(limit).all()

    actor_user_ids = {row.actor_user_id for row in rows if isinstance(row.actor_user_id, int)}
    actor_users = User.query.filter(User.id.in_(actor_user_ids)).all() if actor_user_ids else []
    users_by_id = {user.id: user for user in actor_users}

    return {
        "events": [serialize_space_activity_event(row, users_by_id=users_by_id) for row in rows],
        "summary": summarize_space_audit_events(rows),
        "limit": limit,
        "filters": {
            "event_type": selected_event_type,
            "days": days,
            "query": search_text,
        },
        "available_event_types": sorted(SPACE_ACTIVITY_AUDIT_EVENT_TYPES),
    }, 200


@app.get("/api/spaces/<int:space_id>/invites")
@require_auth
def list_space_invites(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_invites"):
        return auth_error("Forbidden", 403)

    include_inactive_raw = request.args.get("include_inactive")
    include_inactive = True
    if include_inactive_raw is not None:
        parsed_include, parsed_error = parse_bool_value(include_inactive_raw, "include_inactive")
        if parsed_error:
            return auth_error(parsed_error, 400)
        include_inactive = bool(parsed_include) if parsed_include is not None else True

    rows = query_space_invites(space.id, limit=100)
    now = datetime.utcnow()
    if not include_inactive:
        rows = [row for row in rows if is_space_invite_active(row, now=now)]

    user_ids = {invite.created_by_user_id for invite in rows if isinstance(invite.created_by_user_id, int)}
    user_ids.update({invite.accepted_by_user_id for invite in rows if isinstance(invite.accepted_by_user_id, int)})
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    users_by_id = {user.id: user for user in users}

    return {
        "invites": [serialize_space_invite(invite, users_by_id=users_by_id, include_token=True, now=now) for invite in rows],
        "invite_summary": summarize_space_invites(rows, now=now),
    }, 200


@app.get("/api/spaces/<int:space_id>/invite-analytics")
@require_auth
def get_space_invite_analytics(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_invites"):
        return auth_error("Forbidden", 403)

    now = datetime.utcnow()
    rows = query_space_invites(space.id, limit=None)
    return {
        "space_id": space.id,
        "analytics": summarize_space_invite_analytics(rows, now=now),
    }, 200


@app.post("/api/spaces/<int:space_id>/invites")
@require_auth
def create_space_invite(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_invites"):
        return auth_error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    role, role_error = parse_space_role(payload.get("role"))
    if role_error:
        return auth_error(role_error, 400)
    target_role = role or "member"
    if target_role not in ASSIGNABLE_SPACE_ROLES:
        return auth_error("role must be admin or member", 400)
    if target_role == "admin" and not permissions.get("can_assign_admin"):
        return auth_error("You do not have permission to create admin invites", 403)

    expires_in_hours, expires_error = parse_space_invite_hours(payload.get("expires_in_hours"))
    if expires_error:
        return auth_error(expires_error, 400)

    now = datetime.utcnow()
    invite = SpaceInvite(
        space_id=space.id,
        created_by_user_id=auth_user.id,
        role=target_role,
        invite_token=generate_space_invite_token(),
        expires_at=now + timedelta(hours=expires_in_hours),
    )
    db.session.add(invite)
    db.session.commit()

    users_by_id = {auth_user.id: auth_user}
    return {
        "message": "Invite created",
        "invite": serialize_space_invite(invite, users_by_id=users_by_id, include_token=True, now=now),
        "expires_in_hours": expires_in_hours,
    }, 201


@app.delete("/api/spaces/<int:space_id>/invites/<int:invite_id>")
@require_auth
def revoke_space_invite(space_id: int, invite_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_manage_invites"):
        return auth_error("Forbidden", 403)

    invite = SpaceInvite.query.filter_by(id=invite_id, space_id=space.id).first()
    if invite is None:
        return {"error": "Space invite not found"}, 404

    if invite.revoked_at is None:
        invite.revoked_at = datetime.utcnow()
        db.session.add(invite)
        db.session.commit()

    user_ids = {invite.created_by_user_id}
    if invite.accepted_by_user_id:
        user_ids.add(invite.accepted_by_user_id)
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    users_by_id = {user.id: user for user in users}
    return {
        "message": "Invite revoked",
        "invite": serialize_space_invite(invite, users_by_id=users_by_id, include_token=True),
    }, 200


@app.post("/api/spaces/invites/accept")
@require_auth
def accept_space_invite(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    token_value = str(payload.get("token", "")).strip()
    if not token_value:
        return auth_error("token is required", 400)

    invite = SpaceInvite.query.filter_by(invite_token=token_value).first()
    if invite is None:
        return auth_error("Invite not found", 404)

    now = datetime.utcnow()
    if invite.revoked_at is not None:
        return auth_error("Invite has been revoked", 410)
    if invite.accepted_at is not None:
        return auth_error("Invite has already been used", 409)
    if is_space_invite_expired(invite, now=now):
        return auth_error("Invite has expired", 410)

    space = db.session.get(Space, invite.space_id)
    if space is None:
        return auth_error("Space not found", 404)

    existing_member = SpaceMember.query.filter_by(space_id=space.id, user_id=auth_user.id).first()
    if existing_member is not None:
        return auth_error("You are already a member of this space", 409)

    target_role = invite.role if invite.role in ASSIGNABLE_SPACE_ROLES else "member"
    member = SpaceMember(space_id=space.id, user_id=auth_user.id, role=target_role)
    invite.accepted_by_user_id = auth_user.id
    invite.accepted_at = now
    db.session.add(member)
    db.session.add(invite)
    ensure_space_member_notification_preference(space, auth_user.id)
    db.session.commit()

    member_count = SpaceMember.query.filter_by(space_id=space.id).count()
    templates_by_role = load_space_role_templates_map(space.id)
    member_permissions = resolve_space_permissions(space.id, member, templates_by_role=templates_by_role)
    return {
        "message": f"You joined {space.name}",
        "space": serialize_space(space, current_role=member.role, member_count=member_count, permissions=member_permissions),
        "member": serialize_space_member(member, auth_user, auth_user.id),
    }, 200


@app.get("/api/spaces/<int:space_id>/tasks")
@require_auth
def list_space_tasks(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)

    status_filter = request.args.get("status", type=str)
    query = SpaceTask.query.filter(SpaceTask.space_id == space.id)
    if status_filter:
        status_value = status_filter.strip().lower()
        if status_value not in VALID_TASK_STATUSES:
            return auth_error("status must be todo or done", 400)
        query = query.filter(SpaceTask.status == status_value)

    status_rank = case((SpaceTask.status == "todo", 0), (SpaceTask.status == "done", 1), else_=2)
    task_rows = (
        query.order_by(status_rank.asc(), SpaceTask.due_on.is_(None), SpaceTask.due_on.asc(), SpaceTask.created_at.desc())
        .limit(200)
        .all()
    )
    user_ids: set[int] = {
        user_id
        for user_id in [task.created_by_user_id for task in task_rows]
        if isinstance(user_id, int)
    }
    user_ids.update(
        {
            user_id
            for user_id in [task.completed_by_user_id for task in task_rows]
            if isinstance(user_id, int)
        }
    )
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    users_by_id = {user.id: user for user in users}
    return {
        "tasks": [serialize_space_task(task, users_by_id=users_by_id) for task in task_rows],
        "task_summary": summarize_space_tasks(task_rows),
    }, 200


@app.post("/api/spaces/<int:space_id>/tasks")
@require_auth
def create_space_task(space_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_create_tasks"):
        return auth_error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return auth_error("title is required", 400)

    task_type, task_type_error = parse_space_task_type(payload.get("task_type"))
    if task_type_error:
        return auth_error(task_type_error, 400)

    priority, priority_error = parse_task_priority(payload.get("priority"))
    if priority_error:
        return auth_error(priority_error, 400)

    status, status_error = parse_task_status(payload.get("status"))
    if status_error:
        return auth_error(status_error, 400)

    xp_reward, xp_error = parse_int_value(payload.get("xp_reward"), "xp_reward", 1)
    if xp_error:
        return auth_error(xp_error, 400)

    due_on, due_error = parse_date_value(payload.get("due_on"), "due_on")
    if due_error:
        return auth_error(due_error, 400)

    task = SpaceTask(
        space_id=space.id,
        created_by_user_id=auth_user.id,
        title=title,
        status="todo",
        task_type=task_type or "task",
        xp_reward=xp_reward or 25,
        priority=priority or "medium",
        due_on=due_on,
    )
    db.session.add(task)
    db.session.flush()

    xp_gained = 0
    coins_gained = 0
    event_type = "space_task_created"
    event_summary = f"{auth_user.display_name} created shared {task.task_type}: {task.title}"
    if status == "done":
        xp_gained, coins_gained = apply_space_task_completion(space, task, auth_user, datetime.utcnow())
        event_type = "space_task_completed"
        event_summary = f"{auth_user.display_name} completed shared {task.task_type}: {task.title}"

    log_space_activity(
        space_id=space.id,
        actor_user_id=auth_user.id,
        event_type=event_type,
        entity_type="space_task",
        entity_id=task.id,
        summary=event_summary,
        details={
            "task_id": task.id,
            "task_type": task.task_type,
            "priority": task.priority,
            "status": task.status,
        },
    )

    achievements_payload = build_achievements_payload(auth_user, grant_new=True)
    db.session.commit()
    users_by_id = {auth_user.id: auth_user}
    payload_response: dict[str, Any] = {
        "message": "Space task created",
        "task": serialize_space_task(task, users_by_id=users_by_id),
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
    }
    if xp_gained or coins_gained:
        payload_response["dashboard"] = build_dashboard_payload(auth_user)
    return payload_response, 201


@app.patch("/api/spaces/<int:space_id>/tasks/<int:task_id>")
@require_auth
def update_space_task(space_id: int, task_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)

    task = SpaceTask.query.filter_by(id=task_id, space_id=space.id).first()
    if task is None:
        return {"error": "Space task not found"}, 404
    if not user_can_manage_space_task(task, permissions, auth_user.id):
        return auth_error("Forbidden", 403)

    payload = request.get_json(silent=True) or {}
    previous_status = task.status
    has_updates = False
    if "title" in payload:
        title = str(payload.get("title", "")).strip()
        if not title:
            return auth_error("title is required", 400)
        if task.title != title:
            task.title = title
            has_updates = True

    if "task_type" in payload:
        task_type, task_type_error = parse_space_task_type(payload.get("task_type"))
        if task_type_error:
            return auth_error(task_type_error, 400)
        if task_type and task.task_type != task_type:
            task.task_type = task_type
            has_updates = True

    if "priority" in payload:
        priority, priority_error = parse_task_priority(payload.get("priority"))
        if priority_error:
            return auth_error(priority_error, 400)
        if priority and task.priority != priority:
            task.priority = priority
            has_updates = True

    if "xp_reward" in payload:
        xp_reward, xp_error = parse_int_value(payload.get("xp_reward"), "xp_reward", 1)
        if xp_error:
            return auth_error(xp_error, 400)
        if xp_reward is not None and int(task.xp_reward or 0) != int(xp_reward):
            task.xp_reward = xp_reward
            has_updates = True

    if "due_on" in payload:
        due_on, due_error = parse_date_value(payload.get("due_on"), "due_on")
        if due_error:
            return auth_error(due_error, 400)
        if task.due_on != due_on:
            task.due_on = due_on
            has_updates = True

    xp_gained = 0
    coins_gained = 0
    event_type: str | None = None
    event_summary: str | None = None
    if "status" in payload:
        status, status_error = parse_task_status(payload.get("status"))
        if status_error:
            return auth_error(status_error, 400)
        if status == "done" and task.status != "done":
            xp_gained, coins_gained = apply_space_task_completion(space, task, auth_user, datetime.utcnow())
            event_type = "space_task_completed"
            event_summary = f"{auth_user.display_name} completed shared {task.task_type}: {task.title}"
            has_updates = True
        elif status == "todo" and task.status != "todo":
            task.status = "todo"
            task.completed_at = None
            task.completed_by_user_id = None
            db.session.add(task)
            event_type = "space_task_reopened"
            event_summary = f"{auth_user.display_name} reopened shared {task.task_type}: {task.title}"
            has_updates = True

    if event_type is None and has_updates:
        event_type = "space_task_updated"
        event_summary = f"{auth_user.display_name} updated shared {task.task_type}: {task.title}"

    db.session.add(task)
    if event_type and event_summary:
        log_space_activity(
            space_id=space.id,
            actor_user_id=auth_user.id,
            event_type=event_type,
            entity_type="space_task",
            entity_id=task.id,
            summary=event_summary,
            details={
                "task_id": task.id,
                "task_type": task.task_type,
                "priority": task.priority,
                "status_before": previous_status,
                "status_after": task.status,
            },
        )
    achievements_payload = build_achievements_payload(auth_user, grant_new=True)
    db.session.commit()

    user_ids = {task.created_by_user_id}
    if task.completed_by_user_id:
        user_ids.add(task.completed_by_user_id)
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    users_by_id = {user.id: user for user in users}

    response_payload: dict[str, Any] = {
        "message": "Space task updated",
        "task": serialize_space_task(task, users_by_id=users_by_id),
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
    }
    if xp_gained or coins_gained:
        response_payload["dashboard"] = build_dashboard_payload(auth_user)
    return response_payload, 200


@app.delete("/api/spaces/<int:space_id>/tasks/<int:task_id>")
@require_auth
def delete_space_task(space_id: int, task_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)

    task = SpaceTask.query.filter_by(id=task_id, space_id=space.id).first()
    if task is None:
        return {"error": "Space task not found"}, 404
    if not user_can_manage_space_task(task, permissions, auth_user.id):
        return auth_error("Forbidden", 403)

    log_space_activity(
        space_id=space.id,
        actor_user_id=auth_user.id,
        event_type="space_task_deleted",
        entity_type="space_task",
        entity_id=task.id,
        summary=f"{auth_user.display_name} deleted shared {task.task_type}: {task.title}",
        details={
            "task_id": task.id,
            "task_type": task.task_type,
            "priority": task.priority,
            "status": task.status,
        },
    )
    db.session.delete(task)
    db.session.commit()
    return {"message": "Space task deleted", "task_id": task_id}, 200


@app.post("/api/spaces/<int:space_id>/tasks/<int:task_id>/complete")
@require_auth
def complete_space_task(space_id: int, task_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    space, membership, access_error = resolve_space_access(space_id, auth_user.id)
    if access_error:
        return access_error
    if space is None or membership is None:
        return auth_error("Forbidden", 403)
    templates_by_role = load_space_role_templates_map(space.id)
    permissions = resolve_space_permissions(space.id, membership, templates_by_role=templates_by_role)
    if not permissions.get("can_complete_tasks"):
        return auth_error("Forbidden", 403)

    task = SpaceTask.query.filter_by(id=task_id, space_id=space.id).first()
    if task is None:
        return {"error": "Space task not found"}, 404

    if task.status == "done":
        user_ids = {task.created_by_user_id}
        if task.completed_by_user_id:
            user_ids.add(task.completed_by_user_id)
        users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
        users_by_id = {user.id: user for user in users}
        return {
            "message": "Space task already completed",
            "task": serialize_space_task(task, users_by_id=users_by_id),
            "xp_gained": 0,
            "coins_gained": 0,
            "dashboard": build_dashboard_payload(auth_user),
        }, 200

    completion_time = datetime.utcnow()
    xp_gained, coins_gained = apply_space_task_completion(space, task, auth_user, completion_time)
    achievements_payload = build_achievements_payload(auth_user, grant_new=True, unlock_time=completion_time)
    log_space_activity(
        space_id=space.id,
        actor_user_id=auth_user.id,
        event_type="space_task_completed",
        entity_type="space_task",
        entity_id=task.id,
        summary=f"{auth_user.display_name} completed shared {task.task_type}: {task.title}",
        details={
            "task_id": task.id,
            "task_type": task.task_type,
            "priority": task.priority,
            "status_after": task.status,
        },
        created_at=completion_time,
    )
    db.session.commit()

    user_ids = {task.created_by_user_id, auth_user.id}
    if task.completed_by_user_id:
        user_ids.add(task.completed_by_user_id)
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    users_by_id = {user.id: user for user in users}
    return {
        "message": "Space task completed",
        "task_id": task.id,
        "task": serialize_space_task(task, users_by_id=users_by_id),
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
        "dashboard": build_dashboard_payload(auth_user),
    }, 200


@app.get("/api/tasks")
@require_auth
def list_tasks(auth_user: User) -> tuple[dict[str, Any], int]:
    refresh_recurring_for_user(auth_user, source="tasks")
    status_filter = request.args.get("status", type=str)
    query = Task.query.filter(Task.user_id == auth_user.id)
    if status_filter:
        status_value = status_filter.strip().lower()
        if status_value not in VALID_TASK_STATUSES:
            return auth_error("status must be todo or done", 400)
        query = query.filter(Task.status == status_value)

    status_rank = case((Task.status == "todo", 0), (Task.status == "done", 1), else_=2)
    rows = query.order_by(status_rank.asc(), Task.due_on.is_(None), Task.due_on.asc(), Task.created_at.desc()).all()
    return {"tasks": [serialize_task(row) for row in rows]}, 200


@app.post("/api/tasks")
@require_auth
def create_task(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return auth_error("title is required", 400)

    task_type, type_error = parse_task_type(payload.get("task_type"))
    if type_error:
        return auth_error(type_error, 400)

    priority, priority_error = parse_task_priority(payload.get("priority"))
    if priority_error:
        return auth_error(priority_error, 400)

    status, status_error = parse_task_status(payload.get("status"))
    if status_error:
        return auth_error(status_error, 400)

    xp_reward, xp_error = parse_int_value(payload.get("xp_reward"), "xp_reward", 1)
    if xp_error:
        return auth_error(xp_error, 400)

    due_on, due_error = parse_date_value(payload.get("due_on"), "due_on")
    if due_error:
        return auth_error(due_error, 400)

    task = Task(
        user_id=auth_user.id,
        title=title,
        status="todo",
        task_type=task_type or "task",
        xp_reward=xp_reward or 20,
        priority=priority or "medium",
        due_on=due_on,
    )
    db.session.add(task)
    db.session.flush()

    xp_gained = 0
    coins_gained = 0
    if status == "done":
        xp_gained, coins_gained = apply_task_completion_effects(task, datetime.utcnow())

    achievements_payload = build_achievements_payload(auth_user, grant_new=True)
    db.session.commit()
    return {
        "task": serialize_task(task),
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
    }, 201


@app.patch("/api/tasks/<int:task_id>")
@require_auth
def update_task(task_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    task = db.session.get(Task, task_id)
    if task is None:
        return {"error": "Task not found"}, 404
    if task.user_id != auth_user.id:
        return {"error": "Task does not belong to authenticated user"}, 403

    payload = request.get_json(silent=True) or {}
    if "title" in payload:
        title = str(payload.get("title", "")).strip()
        if not title:
            return auth_error("title is required", 400)
        task.title = title

    if "task_type" in payload:
        task_type, type_error = parse_task_type(payload.get("task_type"))
        if type_error:
            return auth_error(type_error, 400)
        if task_type:
            task.task_type = task_type

    if "priority" in payload:
        priority, priority_error = parse_task_priority(payload.get("priority"))
        if priority_error:
            return auth_error(priority_error, 400)
        if priority:
            task.priority = priority

    if "xp_reward" in payload:
        xp_reward, xp_error = parse_int_value(payload.get("xp_reward"), "xp_reward", 1)
        if xp_error:
            return auth_error(xp_error, 400)
        if xp_reward is not None:
            task.xp_reward = xp_reward

    if "due_on" in payload:
        due_on, due_error = parse_date_value(payload.get("due_on"), "due_on")
        if due_error:
            return auth_error(due_error, 400)
        task.due_on = due_on

    xp_gained = 0
    coins_gained = 0
    if "status" in payload:
        status, status_error = parse_task_status(payload.get("status"))
        if status_error:
            return auth_error(status_error, 400)
        if status == "done" and task.status != "done":
            xp_gained, coins_gained = apply_task_completion_effects(task, datetime.utcnow())
        elif status == "todo" and task.status != "todo":
            task.status = "todo"
            task.completed_at = None
            db.session.add(task)

    achievements_payload = build_achievements_payload(auth_user, grant_new=True)
    db.session.commit()
    return {
        "task": serialize_task(task),
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
    }, 200


@app.delete("/api/tasks/<int:task_id>")
@require_auth
def delete_task(task_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    task = db.session.get(Task, task_id)
    if task is None:
        return {"error": "Task not found"}, 404
    if task.user_id != auth_user.id:
        return {"error": "Task does not belong to authenticated user"}, 403

    db.session.delete(task)
    db.session.commit()
    return {"message": "Task deleted", "task_id": task_id}, 200


@app.get("/api/habits")
@require_auth
def list_habits(auth_user: User) -> tuple[dict[str, Any], int]:
    rows = Habit.query.filter_by(user_id=auth_user.id).order_by(Habit.name.asc()).all()
    return {"habits": [serialize_habit(row) for row in rows]}, 200


@app.post("/api/habits")
@require_auth
def create_habit(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    if not name:
        return auth_error("name is required", 400)

    existing = Habit.query.filter(
        Habit.user_id == auth_user.id,
        func.lower(Habit.name) == name.lower(),
    ).first()
    if existing is not None:
        return auth_error("Habit already exists", 409)

    current_streak, current_error = parse_int_value(payload.get("current_streak"), "current_streak", 0)
    if current_error:
        return auth_error(current_error, 400)
    longest_streak, longest_error = parse_int_value(payload.get("longest_streak"), "longest_streak", 0)
    if longest_error:
        return auth_error(longest_error, 400)
    last_completed_on, last_error = parse_date_value(payload.get("last_completed_on"), "last_completed_on")
    if last_error:
        return auth_error(last_error, 400)

    current_value = current_streak or 0
    longest_value = max(longest_streak or 0, current_value)
    habit = Habit(
        user_id=auth_user.id,
        name=name,
        current_streak=current_value,
        longest_streak=longest_value,
        last_completed_on=last_completed_on,
    )
    db.session.add(habit)
    db.session.flush()

    if last_completed_on and current_value > 0:
        for offset in range(current_value):
            db.session.add(
                HabitLog(
                    user_id=auth_user.id,
                    habit_id=habit.id,
                    completed_on=last_completed_on - timedelta(days=offset),
                )
            )

    xp_gained = award_action_xp(
        auth_user.id,
        "habit.create",
        f"Habit created: {habit.name}",
        3,
    )
    coins_gained = award_action_coins(
        auth_user.id,
        "habit.create",
        f"Habit created coins: {habit.name}",
        2,
    )

    achievements_payload = build_achievements_payload(auth_user, grant_new=True)
    db.session.commit()
    return {
        "habit": serialize_habit(habit),
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
    }, 201


@app.patch("/api/habits/<int:habit_id>")
@require_auth
def update_habit(habit_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    habit = db.session.get(Habit, habit_id)
    if habit is None:
        return {"error": "Habit not found"}, 404
    if habit.user_id != auth_user.id:
        return {"error": "Habit does not belong to authenticated user"}, 403

    payload = request.get_json(silent=True) or {}
    if "name" in payload:
        name = str(payload.get("name", "")).strip()
        if not name:
            return auth_error("name is required", 400)
        existing = Habit.query.filter(
            Habit.user_id == auth_user.id,
            func.lower(Habit.name) == name.lower(),
            Habit.id != habit.id,
        ).first()
        if existing is not None:
            return auth_error("Habit with that name already exists", 409)
        habit.name = name

    if "current_streak" in payload:
        current_streak, current_error = parse_int_value(payload.get("current_streak"), "current_streak", 0)
        if current_error:
            return auth_error(current_error, 400)
        if current_streak is not None:
            habit.current_streak = current_streak

    if "longest_streak" in payload:
        longest_streak, longest_error = parse_int_value(payload.get("longest_streak"), "longest_streak", 0)
        if longest_error:
            return auth_error(longest_error, 400)
        if longest_streak is not None:
            habit.longest_streak = longest_streak

    if "last_completed_on" in payload:
        last_completed_on, last_error = parse_date_value(payload.get("last_completed_on"), "last_completed_on")
        if last_error:
            return auth_error(last_error, 400)
        habit.last_completed_on = last_completed_on

    habit.longest_streak = max(habit.longest_streak, habit.current_streak)
    db.session.add(habit)
    db.session.commit()
    return {"habit": serialize_habit(habit)}, 200


@app.post("/api/habits/<int:habit_id>/complete")
@require_auth
def complete_habit(habit_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    habit = db.session.get(Habit, habit_id)
    if habit is None:
        return {"error": "Habit not found"}, 404
    if habit.user_id != auth_user.id:
        return {"error": "Habit does not belong to authenticated user"}, 403

    payload = request.get_json(silent=True) or {}
    completed_on, completed_error = parse_date_value(payload.get("completed_on"), "completed_on")
    if completed_error:
        return auth_error(completed_error, 400)
    completed_on = completed_on or date.today()

    already_logged = HabitLog.query.filter_by(
        user_id=auth_user.id,
        habit_id=habit.id,
        completed_on=completed_on,
    ).first()

    apply_habit_completion(auth_user.id, habit.name, completed_on)

    xp_gained = 0
    coins_gained = 0
    if already_logged is None:
        completed_at = datetime.combine(completed_on, datetime.min.time()) + timedelta(hours=12)
        xp_gained = award_action_xp(
            auth_user.id,
            "habit.complete.manual",
            f"Habit complete: {habit.name}",
            10,
            completed_at,
        )
        coins_gained = award_action_coins(
            auth_user.id,
            "habit.complete.manual",
            f"Habit complete coins: {habit.name}",
            6,
            completed_at,
        )

    achievements_payload = build_achievements_payload(auth_user, grant_new=True)
    db.session.commit()

    refreshed = db.session.get(Habit, habit_id)
    return {
        "habit": serialize_habit(refreshed),
        "dashboard": build_dashboard_payload(auth_user),
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
    }, 200


@app.delete("/api/habits/<int:habit_id>")
@require_auth
def delete_habit(habit_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    habit = db.session.get(Habit, habit_id)
    if habit is None:
        return {"error": "Habit not found"}, 404
    if habit.user_id != auth_user.id:
        return {"error": "Habit does not belong to authenticated user"}, 403

    HabitLog.query.filter_by(user_id=auth_user.id, habit_id=habit.id).delete()
    db.session.delete(habit)
    db.session.commit()
    return {"message": "Habit deleted", "habit_id": habit_id}, 200


@app.get("/api/goals")
@require_auth
def list_goals(auth_user: User) -> tuple[dict[str, Any], int]:
    rows = Goal.query.filter_by(user_id=auth_user.id).order_by(Goal.deadline.is_(None), Goal.deadline.asc()).all()
    return {"goals": [serialize_goal(row) for row in rows]}, 200


@app.post("/api/goals")
@require_auth
def create_goal(auth_user: User) -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return auth_error("title is required", 400)

    target_value, target_error = parse_int_value(payload.get("target_value"), "target_value", 1)
    if target_error:
        return auth_error(target_error, 400)
    current_value, current_error = parse_int_value(payload.get("current_value"), "current_value", 0)
    if current_error:
        return auth_error(current_error, 400)
    deadline, deadline_error = parse_date_value(payload.get("deadline"), "deadline")
    if deadline_error:
        return auth_error(deadline_error, 400)

    safe_target = target_value or 1
    safe_current = min(current_value or 0, safe_target)
    goal = Goal(
        user_id=auth_user.id,
        title=title,
        target_value=safe_target,
        current_value=safe_current,
        deadline=deadline,
    )
    db.session.add(goal)

    xp_gained = award_action_xp(
        auth_user.id,
        "goal.create",
        f"Goal created: {goal.title}",
        8,
    )
    coins_gained = award_action_coins(
        auth_user.id,
        "goal.create",
        f"Goal created coins: {goal.title}",
        4,
    )

    achievements_payload = build_achievements_payload(auth_user, grant_new=True)
    db.session.commit()
    return {
        "goal": serialize_goal(goal),
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
    }, 201


@app.patch("/api/goals/<int:goal_id>")
@require_auth
def update_goal(goal_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    goal = db.session.get(Goal, goal_id)
    if goal is None:
        return {"error": "Goal not found"}, 404
    if goal.user_id != auth_user.id:
        return {"error": "Goal does not belong to authenticated user"}, 403

    payload = request.get_json(silent=True) or {}
    if "title" in payload:
        title = str(payload.get("title", "")).strip()
        if not title:
            return auth_error("title is required", 400)
        goal.title = title

    if "target_value" in payload:
        target_value, target_error = parse_int_value(payload.get("target_value"), "target_value", 1)
        if target_error:
            return auth_error(target_error, 400)
        if target_value is not None:
            goal.target_value = target_value

    if "current_value" in payload:
        current_value, current_error = parse_int_value(payload.get("current_value"), "current_value", 0)
        if current_error:
            return auth_error(current_error, 400)
        if current_value is not None:
            goal.current_value = current_value

    if "deadline" in payload:
        deadline, deadline_error = parse_date_value(payload.get("deadline"), "deadline")
        if deadline_error:
            return auth_error(deadline_error, 400)
        goal.deadline = deadline

    if goal.current_value > goal.target_value:
        goal.current_value = goal.target_value

    db.session.add(goal)
    db.session.commit()
    return {"goal": serialize_goal(goal)}, 200


@app.delete("/api/goals/<int:goal_id>")
@require_auth
def delete_goal(goal_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    goal = db.session.get(Goal, goal_id)
    if goal is None:
        return {"error": "Goal not found"}, 404
    if goal.user_id != auth_user.id:
        return {"error": "Goal does not belong to authenticated user"}, 403

    db.session.delete(goal)
    db.session.commit()
    return {"message": "Goal deleted", "goal_id": goal_id}, 200


@app.post("/api/tasks/<int:task_id>/complete")
@require_auth
def complete_task(task_id: int, auth_user: User) -> tuple[dict[str, Any], int]:
    task = db.session.get(Task, task_id)
    if task is None:
        return {"error": "Task not found"}, 404
    if task.user_id != auth_user.id:
        return {"error": "Task does not belong to authenticated user"}, 403

    if task.status == "done":
        return {"message": "Task already completed", "xp_gained": 0, "coins_gained": 0, "dashboard": build_dashboard_payload(auth_user)}, 200

    completion_time = datetime.utcnow()
    xp_gained, coins_gained = apply_task_completion_effects(task, completion_time)
    achievements_payload = build_achievements_payload(auth_user, grant_new=True, unlock_time=completion_time)

    db.session.commit()
    return {
        "message": "Task completed",
        "task_id": task.id,
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "achievements": achievements_payload,
        "dashboard": build_dashboard_payload(auth_user),
    }, 200


_recurring_worker_thread: threading.Thread | None = None


def recurring_worker_loop() -> None:
    last_recurring_run = datetime.min
    last_delivery_run = datetime.min
    tick_seconds = 30
    while True:
        try:
            with app.app_context():
                now = datetime.utcnow()
                if (now - last_recurring_run).total_seconds() >= RECURRING_WORKER_INTERVAL_SECONDS:
                    run_recurring_generation(source="worker", commit=True)
                    last_recurring_run = now
                if (now - last_delivery_run).total_seconds() >= REMINDER_DELIVERY_INTERVAL_SECONDS:
                    run_reminder_delivery_cycle(source="worker", commit=True)
                    last_delivery_run = now
        except Exception:
            with app.app_context():
                db.session.rollback()
        time.sleep(tick_seconds)


def start_recurring_worker() -> None:
    global _recurring_worker_thread
    if not RECURRING_WORKER_ENABLED:
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return
    if _recurring_worker_thread is not None and _recurring_worker_thread.is_alive():
        return

    worker = threading.Thread(target=recurring_worker_loop, daemon=True, name="lifeos-recurring-worker")
    worker.start()
    _recurring_worker_thread = worker


with app.app_context():
    init_db()


if __name__ == "__main__":
    start_recurring_worker()
    host_value = str(os.getenv("LIFEOS_HOST", "127.0.0.1")).strip() or "127.0.0.1"
    port_raw = str(os.getenv("LIFEOS_PORT", "5000")).strip()
    try:
        port_value = int(port_raw)
    except ValueError:
        port_value = 5000
    port_value = min(max(port_value, 1), 65535)
    debug_value = str(os.getenv("LIFEOS_DEBUG", "1")).strip().lower() in {"1", "true", "yes", "on"}
    reloader_value = str(os.getenv("LIFEOS_RELOADER", "0")).strip().lower() in {"1", "true", "yes", "on"}
    app.run(debug=debug_value, host=host_value, port=port_value, use_reloader=reloader_value)
