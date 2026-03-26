# LifeOS (Starter Dashboard)

This is a first-pass `LifeOS` scaffold with:

- Flask API backend
- SQLite database (default)
- React dashboard frontend
- Seeded demo data including `testuser1`

## Stack

- Backend: Flask + SQLAlchemy + Flask-Cors
- Frontend: React + Vite + React Router
- Database: SQLite now, PostgreSQL-ready via `DATABASE_URL`

## Run Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend runs on `http://127.0.0.1:5000`.

Useful endpoints:

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `PATCH /api/account/profile` (requires bearer token)
- `POST /api/account/password` (requires bearer token)
- `GET /api/account/reminder-channels` (requires bearer token)
- `PATCH /api/account/reminder-channels` (requires bearer token)
- `POST /api/account/reminder-channels/test` (requires bearer token)
- `POST /api/account/reminder-channels/run` (requires bearer token)
- `GET /api/account/reminder-deliveries` (requires bearer token)
- `GET /api/account/export` (requires bearer token)
- `POST /api/account/import` (requires bearer token)
- `POST /api/account/recovery/request`
- `POST /api/account/recovery/confirm`
- `GET /api/dashboard` (requires bearer token)
- `GET /api/xp/rules`
- `GET /api/stats?days=30`
- `GET /api/notifications` (requires bearer token)
- `GET /api/recurring-rules` (requires bearer token)
- `POST /api/recurring-rules` (requires bearer token)
- `PATCH /api/recurring-rules/<rule_id>` (requires bearer token)
- `DELETE /api/recurring-rules/<rule_id>` (requires bearer token)
- `POST /api/recurring-rules/run` (requires bearer token)
- `GET /api/spaces` (requires bearer token)
- `POST /api/spaces` (requires bearer token)
- `GET /api/spaces/<space_id>` (requires bearer token)
- `PATCH /api/spaces/<space_id>` (requires bearer token + space permission)
- `DELETE /api/spaces/<space_id>` (requires bearer token + delete permission)
- `POST /api/spaces/<space_id>/members` (requires bearer token + member-manage permission)
- `PATCH /api/spaces/<space_id>/members/<user_id>` (requires bearer token + member-manage permission)
- `DELETE /api/spaces/<space_id>/members/<user_id>` (requires bearer token + member-manage permission or self leave)
- `GET /api/spaces/<space_id>/role-templates` (requires bearer token, space member)
- `PATCH /api/spaces/<space_id>/role-templates/<role_name>` (requires bearer token, owner only)
- `GET /api/spaces/<space_id>/notification-preference` (requires bearer token, space member)
- `PATCH /api/spaces/<space_id>/notification-preference` (requires bearer token, space member)
- `GET /api/spaces/<space_id>/notification-default` (requires bearer token, space member)
- `PATCH /api/spaces/<space_id>/notification-default` (requires bearer token, owner only)
- `POST /api/spaces/<space_id>/notification-default/apply` (requires bearer token, owner only)
- `GET /api/spaces/<space_id>/notification-quiet-hours` (requires bearer token, space member)
- `PATCH /api/spaces/<space_id>/notification-quiet-hours` (requires bearer token + manage-space permission)
- `GET /api/spaces/<space_id>/audit-events` (requires bearer token, space member)
- `GET /api/spaces/<space_id>/invites` (requires bearer token + invite-manage permission)
- `GET /api/spaces/<space_id>/invite-analytics` (requires bearer token + invite-manage permission)
- `POST /api/spaces/<space_id>/invites` (requires bearer token + invite-manage permission)
- `DELETE /api/spaces/<space_id>/invites/<invite_id>` (requires bearer token + invite-manage permission)
- `POST /api/spaces/invites/accept` (requires bearer token)
- `GET /api/spaces/<space_id>/tasks` (requires bearer token, space member)
- `POST /api/spaces/<space_id>/tasks` (requires bearer token + task-create permission)
- `PATCH /api/spaces/<space_id>/tasks/<task_id>` (requires bearer token + task-manage permission or creator)
- `DELETE /api/spaces/<space_id>/tasks/<task_id>` (requires bearer token + task-manage permission or creator)
- `POST /api/spaces/<space_id>/tasks/<task_id>/complete` (requires bearer token + task-complete permission)
- `GET /api/tasks`
- `POST /api/tasks`
- `PATCH /api/tasks/<task_id>`
- `DELETE /api/tasks/<task_id>`
- `POST /api/tasks/<task_id>/complete`
- `GET /api/habits`
- `POST /api/habits`
- `PATCH /api/habits/<habit_id>`
- `POST /api/habits/<habit_id>/complete`
- `DELETE /api/habits/<habit_id>`
- `GET /api/goals`
- `POST /api/goals`
- `PATCH /api/goals/<goal_id>`
- `DELETE /api/goals/<goal_id>`

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`.

The dashboard UI includes:

- Left sidebar (collapsed by default on desktop, slide-out on mobile)
- Login/register auth screen
- Task complete buttons that update XP, streaks, and goal progress in real time
- Mobile-friendly layout and responsive panels
- In-app CRUD management for tasks, habits, and goals
- Rule-driven XP engine (task type/priority, habit events, goal events)
- Stats view with daily XP/completion charts and breakdown cards
- Route-level pages: `/dashboard`, `/tasks`, `/quests`, `/spaces`, `/stats`, `/settings`
- Settings forms for profile + password update
- Snapshot export/import tools in Settings
- Password recovery flow (token request + reset) on the sign-in screen
- In-app reminder center for overdue tasks, streak risk, and goal deadlines
- Shared spaces with role-based member management (owner/admin/member)
- Per-space role templates with custom permissions for admin/member
- Per-space reminder preferences (all, priority-only, digest-only, muted)
- Owner-level default reminder mode for newly added/invited members
- Owner bulk-apply action to sync the current reminder default to existing members
- Per-space quiet hours for shared update and invite-expiry reminders
- Space audit trail for template permission changes and member role updates
- Invite-link join flow for spaces (create, revoke, accept token)
- Invite analytics for conversion and 7d/30d create/accept/revoke trends
- Invite analytics breakdown by link role type (member/admin/other)
- Invite lifecycle reminders for links expiring in the next 24h
- Shared-space task/quest queue with XP + goal progress on completion
- Space activity reminders and digest summaries for shared queue changes
- Recurring task/habit rules with background generation jobs
- Optional email/SMS reminder delivery channels with delivery logs

Seeded test credentials:

- Username: `testuser1`
- Password: `testuser123`

- Username: `allydev`
- Password: `allydev123`

To point the frontend to a different API URL:

```bash
$env:VITE_API_BASE_URL="http://127.0.0.1:5000"
```

## E2E Smoke Test (Playwright)

Run from `frontend`:

```bash
npm install
npx playwright install chromium
npm run test:e2e
```

What it covers:

- Sign in with `testuser1`
- Sidebar navigation across all menu views
- Dashboard-only panel visibility checks
- Add a quest from Tasks and complete it from Quests
- Cross-view navigation via in-app buttons

## XP Rules Configuration

Override XP rules at backend startup with `LIFEOS_XP_RULES_JSON`:

```bash
$env:LIFEOS_XP_RULES_JSON='{"task.complete.task":25,"task.priority_bonus.high":15,"goal.progress.complete_bonus":80}'
```

The active rules are available at `GET /api/xp/rules` (auth required).

## Recovery Token Configuration

Password recovery tokens default to a 1-hour expiry:

```bash
$env:LIFEOS_RESET_TOKEN_MAX_AGE_SECONDS="3600"
```

For local/dev convenience, reset tokens are returned from `/api/account/recovery/request`.
Set this to hide the token in responses:

```bash
$env:LIFEOS_EXPOSE_RESET_TOKEN="0"
```

## Reminder Configuration

```bash
$env:LIFEOS_NOTIFICATION_GOAL_WINDOW_DAYS="5"
$env:LIFEOS_NOTIFICATION_MAX_ITEMS="12"
```

## Reminder Delivery Channels

```bash
$env:LIFEOS_REMINDER_DELIVERY_ENABLED="1"
$env:LIFEOS_REMINDER_DELIVERY_INTERVAL_SECONDS="300"
$env:LIFEOS_REMINDER_DEFAULT_DIGEST_HOUR_UTC="14"
$env:LIFEOS_REMINDER_EMAIL_PROVIDER="console"   # console | smtp | disabled
$env:LIFEOS_REMINDER_SMS_PROVIDER="console"     # console | twilio | disabled
```

If using SMTP:

```bash
$env:LIFEOS_SMTP_HOST="smtp.example.com"
$env:LIFEOS_SMTP_PORT="587"
$env:LIFEOS_SMTP_USERNAME="smtp-user"
$env:LIFEOS_SMTP_PASSWORD="smtp-pass"
$env:LIFEOS_SMTP_USE_TLS="1"
$env:LIFEOS_SMTP_FROM_EMAIL="noreply@lifeos.app"
```

If using Twilio for SMS:

```bash
$env:LIFEOS_TWILIO_ACCOUNT_SID="ACxxxxxxxx"
$env:LIFEOS_TWILIO_AUTH_TOKEN="your_token"
$env:LIFEOS_TWILIO_FROM_NUMBER="+15551234567"
```

## Recurring Job Configuration

```bash
$env:LIFEOS_RECURRING_WORKER_ENABLED="1"
$env:LIFEOS_RECURRING_WORKER_INTERVAL_SECONDS="120"
$env:LIFEOS_RECURRING_DEFAULT_BACKFILL_DAYS="1"
$env:LIFEOS_RECURRING_MAX_BACKFILL_DAYS="7"
```

## Space Invite Configuration

```bash
$env:LIFEOS_SPACE_INVITE_DEFAULT_HOURS="72"
$env:LIFEOS_SPACE_INVITE_MAX_HOURS="720"
```

## Space Activity Reminder Configuration

```bash
$env:LIFEOS_SPACE_ACTIVITY_NOTIFICATION_WINDOW_HOURS="36"
$env:LIFEOS_SPACE_ACTIVITY_NOTIFICATION_MAX_EVENTS="120"
$env:LIFEOS_SPACE_ACTIVITY_NOTIFICATION_MAX_SPACES="6"
$env:LIFEOS_SPACE_INVITE_EXPIRY_ALERT_WINDOW_HOURS="24"
$env:LIFEOS_SPACE_INVITE_EXPIRY_ALERT_MAX_ITEMS="8"
$env:LIFEOS_SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_START_UTC="22"
$env:LIFEOS_SPACE_NOTIFICATION_QUIET_HOURS_DEFAULT_END_UTC="7"
$env:LIFEOS_SPACE_AUDIT_LOG_DEFAULT_LIMIT="30"
```

## One-Click Launcher (Windows)

Run:

```bash
run_lifeos.bat
```

This script:

- auto-locates project files from the script directory
- checks `python`/`py` and `npm`
- creates `.venv` if needed
- installs backend/frontend dependencies
- stops existing LifeOS backend/frontend processes for a clean restart
- auto-detects a LAN IP and free backend/frontend ports
- sets `VITE_API_BASE_URL` automatically for the frontend
- opens two terminals (backend + frontend)

Optional overrides before running:

```bash
$env:LIFEOS_BIND_HOST="0.0.0.0"
$env:LIFEOS_PUBLIC_IP="192.168.1.10"
$env:LIFEOS_BACKEND_PORT="5000"
$env:LIFEOS_FRONTEND_PORT="5173"
$env:LIFEOS_DEBUG="1"
$env:LIFEOS_RELOADER="0"
$env:LIFEOS_CLEAN_START="1"
```

Dry run (validates setup without launching terminals):

```bash
run_lifeos.bat --dry-run
```

Skip automatic process cleanup:

```bash
run_lifeos.bat --no-clean
```

Run automated E2E smoke checks (starts backend/frontend internally for test run and exits):

```bash
run_lifeos.bat --test
```

Run E2E smoke checks in headed mode:

```bash
run_lifeos.bat --test-headed
```

## PostgreSQL Later

Switch from SQLite to PostgreSQL by setting:

```bash
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/lifeos"
```

and restarting the Flask server.

## Next Build Steps

1. Add owner-level invite expiry escalation policy (e.g., 6h / 24h thresholds).
2. Add optional per-space locale support for reminder windows (timezone + local-hour labels).
3. Add scheduled reminder summary cadence per space role (owner/admin/member templates).
