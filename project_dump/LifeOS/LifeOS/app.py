import json
import json
import os
import threading
import time
from datetime import date, timedelta
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "sample_data.json"
TRACK_DEFAULT = [
    "projects_tasks",
    "events",
    "goals_habits",
    "daily_log",
    "fitness",
    "finance",
    "wishlist",
    "notes",
    "reminders",
]

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("LIFEOS_SECRET", "lifeos-secret")
WRITE_LOCK = threading.Lock()
# Default remember duration; non-remember uses session cookie
app.permanent_session_lifetime = timedelta(days=30)


def require_token():
    """Lightweight token guard for write endpoints. Set LIFEOS_TOKEN env var to enable."""
    token = os.environ.get("LIFEOS_TOKEN")
    if not token:
        return True
    header = request.headers.get("X-Auth-Token") or request.args.get("token")
    return header == token


def load_data():
    """Load sample data once. In a real backend, swap with a DB/service."""
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # assign ids to records that are missing them so UI actions can target them
    dirty = False

    def ensure_ids(key):
        nonlocal dirty
        arr = data.get(key)
        if isinstance(arr, list):
            for item in arr:
                if "id" not in item:
                    item["id"] = new_id()
                    dirty = True

    for key in ["tasks", "events", "reminders", "notes", "wishlist", "projects"]:
        ensure_ids(key)

    if dirty:
        # persist the newly assigned identifiers
        write_data(data)

    data.setdefault("users", [])
    if not data["users"]:
        data["users"] = [
            {
                "id": 1,
                "username": "demo",
                "password": "demo",
                "name": "Demo User",
                "focus": "Ship Life OS",
                "mood": "In the zone",
                "prefs": {
                    "modules": {
                        m: {"enabled": True, "prefs": {}}
                        for m in TRACK_DEFAULT
                    },
                    "dashboard": {"show": TRACK_DEFAULT, "top_priority": "projects_tasks"},
                },
            }
        ]
    # derive a few helper aggregates for the dashboard
    tasks = data.get("tasks", [])
    open_tasks = [t for t in tasks if t.get("status") in ("open", "in-progress")]
    overdue = [t for t in open_tasks if t.get("due") and t["due"] < str(date.today())]
    today_events = [
        e for e in data.get("events", []) if e.get("date") == str(date.today())
    ]
    data["meta"] = {
        "open_tasks": len(open_tasks),
        "overdue_tasks": len(overdue),
        "today_events": len(today_events),
    }
    # Finance aggregates
    finance = data.get("finances", {}) or {}
    txns = finance.get("transactions", [])
    by_cat = {}
    for t in txns:
        cat = t.get("category", "Other")
        by_cat.setdefault(cat, 0)
        by_cat[cat] += t.get("amount", 0)
    finance["by_category"] = by_cat
    data["finances"] = finance
    return data


def write_data(data: dict):
    """Persist the in-memory dict back to disk safely."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    with WRITE_LOCK:
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(DATA_FILE)


def normalize_profile(raw_prefs: dict):
    """Ensure prefs has modules/dash keys with defaults."""
    modules = raw_prefs.get("modules") or {}
    # migrate legacy flat prefs
    if "projects_tasks" in raw_prefs and "modules" not in raw_prefs:
        for k, v in raw_prefs.items():
            if k in TRACK_DEFAULT:
                enabled = True
                prefs = v if isinstance(v, dict) else {}
                modules[k] = {"enabled": enabled, "prefs": prefs}
    # fill missing modules
    for m in TRACK_DEFAULT:
        modules.setdefault(m, {"enabled": False, "prefs": {}})
        modules[m].setdefault("enabled", False)
        modules[m].setdefault("prefs", {})
    dashboard = raw_prefs.get("dashboard") or {}
    dashboard.setdefault("show", [m for m, cfg in modules.items() if cfg.get("enabled")])
    if not dashboard["show"]:
        dashboard["show"] = TRACK_DEFAULT
    dashboard.setdefault("top_priority", dashboard["show"][0] if dashboard["show"] else "projects_tasks")
    # layout / priority tiers can be added later; keep minimal shape
    return {"modules": modules, "dashboard": dashboard}


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    data = load_data()
    return next((u for u in data.get("users", []) if u.get("id") == uid), None)

def ensure_logged_in():
    if current_user():
        return None
    return redirect(url_for("login", next=request.path))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        remember = bool(request.form.get("remember"))
        data = load_data()
        user = next((u for u in data.get("users", []) if u.get("username") == username and u.get("password") == password), None)
        if user:
            session.permanent = remember
            session["user_id"] = user["id"]
            flash("Welcome back!", "success")
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        name = (request.form.get("name") or "").strip()
        if not username or not password or not name:
            flash("All fields required.", "danger")
            return render_template("signup.html", name=name, username=username)
        data = load_data()
        if any(u.get("username") == username for u in data.get("users", [])):
            flash("Username already exists.", "warning")
            return render_template("signup.html", name=name, username=username)
        new_user = {
            "id": int(time.time() * 1000),
            "username": username,
            "password": password,
            "name": name,
            "focus": "Set your focus",
            "mood": "Ready",
            "prefs": {"track": []},
        }
        data.setdefault("users", []).append(new_user)
        write_data(data)
        session["user_id"] = new_user["id"]
        flash("Account created. Let's tailor your Life OS.", "success")
        return redirect(url_for("onboarding"))
    return render_template("signup.html")

@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    guard = ensure_logged_in()
    if guard:
        return guard
    user = current_user()
    profile = normalize_profile((user or {}).get("prefs", {}))
    if request.method == "POST":
        track = request.form.getlist("track")
        focus = (request.form.get("focus") or "").strip() or "Stay organized"
        mood = (request.form.get("mood") or "").strip() or "Ready"
        data = load_data()
        for u in data.get("users", []):
            if u.get("id") == user["id"]:
                u["prefs"] = {
                    "projects_tasks": {
                        "enabled": "projects_tasks" in track,
                        "mode": request.form.get("proj_mode") or "simple",
                        "time_tracking": request.form.get("proj_time") == "yes",
                    },
                    "events": {"enabled": "events" in track},
                    "goals_habits": {
                        "enabled": "goals_habits" in track,
                        "detail": request.form.get("goals_detail") or "standard",
                    },
                    "daily_log": {
                        "enabled": "daily_log" in track,
                        "prompt_style": request.form.get("log_prompt") or "short",
                    },
                    "fitness": {
                        "enabled": "fitness" in track,
                        "main_focus": request.form.get("fit_focus") or "general",
                        "target_per_week": int(request.form.get("fit_target") or 3),
                    },
                    "finance": {
                        "enabled": "finance" in track,
                        "scope": request.form.get("fin_scope") or "personal_only",
                        "detail": request.form.get("fin_detail") or "light",
                    },
                    "wishlist": {"enabled": "wishlist" in track},
                    "notes": {"enabled": "notes" in track},
                    "reminders": {"enabled": "reminders" in track},
                }
                u["focus"] = focus
                u["mood"] = mood
                user = u
                break
        write_data(data)
        flash("Preferences saved.", "success")
        return redirect(url_for("dashboard"))
    track_options = ["projects", "tasks", "events", "habits", "finance", "health", "notes", "reminders", "wishlist"]
    return render_template("onboarding.html", track_options=track_options, user=user, profile=profile, mods=profile.get("modules"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def dashboard():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile((user or {}).get("prefs", {}))
    return render_template("dashboard.html", data=data, user=user, profile=profile)


@app.route("/api/data")
def api_data():
    if not current_user():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    return jsonify(load_data())


@app.route("/projects")
def projects_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["projects_tasks"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("projects.html", data=data, user=user, profile=profile)


@app.route("/tasks")
def tasks_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["projects_tasks"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("tasks.html", data=data, user=user, profile=profile)


@app.route("/events")
def events_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["events"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("events.html", data=data, user=user, profile=profile)


@app.route("/habits")
def habits_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["goals_habits"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("habits.html", data=data, user=user, profile=profile)


@app.route("/finance")
def finance_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["finance"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("finance.html", data=data, user=user, profile=profile)


@app.route("/health")
def health_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["fitness"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("health.html", data=data, user=user, profile=profile)


@app.route("/notes")
def notes_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["notes"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("notes.html", data=data, user=user, profile=profile)


@app.route("/reminders")
def reminders_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["reminders"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("reminders.html", data=data, user=user, profile=profile)


@app.route("/wishlist")
def wishlist_page():
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    user = current_user()
    profile = normalize_profile(user.get("prefs", {}))
    if not profile["modules"]["wishlist"]["enabled"]:
        return redirect(url_for("dashboard"))
    return render_template("wishlist.html", data=data, user=user, profile=profile)

@app.route("/about")
def about():
    guard = ensure_logged_in()
    if guard:
        return guard
    user = current_user()
    profile = normalize_profile((user or {}).get("prefs", {}))
    return render_template("about.html", user=user, profile=profile)

@app.route("/howto")
def howto():
    guard = ensure_logged_in()
    if guard:
        return guard
    user = current_user()
    profile = normalize_profile((user or {}).get("prefs", {}))
    return render_template("howto.html", user=user, profile=profile)


@app.route("/tailor/<module>", methods=["POST"])
def tailor_module(module):
    guard = ensure_logged_in()
    if guard:
        return guard
    payload = request.get_json(silent=True) or request.form
    enabled = payload.get("enabled")
    prefs = payload.get("prefs") or {}
    user = current_user()
    data = load_data()
    for u in data.get("users", []):
        if u.get("id") == user["id"]:
            profile = normalize_profile(u.get("prefs", {}))
            if module not in profile["modules"]:
                return jsonify({"ok": False, "error": "unknown_module"}), 400
            if enabled is not None:
                profile["modules"][module]["enabled"] = str(enabled).lower() in ("true", "1", "yes", "on")
            # merge prefs
            if isinstance(prefs, dict):
                profile["modules"][module]["prefs"].update(prefs)
            u["prefs"] = profile
            break
    write_data(data)
    flash(f"{module} preferences updated.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/tailor/profile", methods=["GET", "POST"])
def tailor_profile():
    guard = ensure_logged_in()
    if guard:
        return guard
    user = current_user()
    if request.method == "POST":
        data = load_data()
        for u in data.get("users", []):
            if u.get("id") == user["id"]:
                profile = normalize_profile(u.get("prefs", {}))
                dash_show = request.form.getlist("dash_show_list")
                dash_show = dash_show or profile["dashboard"]["show"]
                profile["dashboard"]["top_priority"] = request.form.get("dash_top") or profile["dashboard"]["top_priority"]
                if dash_show:
                    profile["dashboard"]["show"] = dash_show
                u["prefs"] = profile
                break
        write_data(data)
        flash("Profile updated.", "success")
        return redirect(url_for("dashboard"))
    profile = normalize_profile((user or {}).get("prefs", {}))
    return render_template("tailor_profile.html", user=user, profile=profile, modules=TRACK_DEFAULT)


def new_id() -> int:
    return int(time.time() * 1000)


@app.route("/api/notes", methods=["POST"])
def api_add_note():
    if not require_token():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    payload = request.get_json(force=True, silent=True) or {}
    title = (payload.get("title") or "").strip()
    excerpt = (payload.get("excerpt") or "").strip()
    tags = payload.get("tags") or []
    if not title and not excerpt:
        return jsonify({"ok": False, "error": "title_or_excerpt_required"}), 400
    data = load_data()
    note = {
        "id": new_id(),
        "title": title or "Untitled",
        "excerpt": excerpt or "",
        "tags": tags,
    }
    data.setdefault("notes", []).insert(0, note)
    write_data(data)
    return jsonify({"ok": True, "note": note})


@app.route("/api/reminders", methods=["POST"])
def api_add_reminder():
    if not require_token():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    payload = request.get_json(force=True, silent=True) or {}
    title = (payload.get("title") or "").strip()
    due = (payload.get("due") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "title_required"}), 400
    data = load_data()
    reminder = {"id": new_id(), "title": title, "due": due or "TBD"}
    data.setdefault("reminders", []).insert(0, reminder)
    write_data(data)
    return jsonify({"ok": True, "reminder": reminder})


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    if not require_token():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    payload = request.get_json(force=True, silent=True) or {}
    title = (payload.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "title_required"}), 400
    task = {
        "id": new_id(),
        "title": title,
        "due": (payload.get("due") or "").strip(),
        "status": payload.get("status") or "backlog",
        "project": payload.get("project") or "Personal",
        "priority": payload.get("priority") or "Medium",
    }
    data = load_data()
    data.setdefault("tasks", []).insert(0, task)
    write_data(data)
    return jsonify({"ok": True, "task": task})


@app.route("/tasks/add", methods=["POST"])
def tasks_add():
    guard = ensure_logged_in()
    if guard:
        return guard
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Task title is required.", "warning")
        return redirect(request.referrer or url_for("tasks_page"))
    task = {
        "id": new_id(),
        "title": title,
        "due": (request.form.get("due") or "").strip(),
        "status": request.form.get("status") or "backlog",
        "project": request.form.get("project") or "Personal",
        "priority": request.form.get("priority") or "Medium",
    }
    data = load_data()
    data.setdefault("tasks", []).insert(0, task)
    write_data(data)
    flash("Task added.", "success")
    return redirect(request.referrer or url_for("tasks_page"))


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def tasks_complete(task_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    for t in data.get("tasks", []):
        if int(t.get("id")) == task_id:
            t["status"] = "done"
            break
    write_data(data)
    flash("Task completed.", "success")
    return redirect(request.referrer or url_for("tasks_page"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def tasks_delete(task_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    data["tasks"] = [t for t in data.get("tasks", []) if int(t.get("id")) != task_id]
    write_data(data)
    flash("Task removed.", "info")
    return redirect(request.referrer or url_for("tasks_page"))


@app.route("/events/add", methods=["POST"])
def events_add():
    guard = ensure_logged_in()
    if guard:
        return guard
    title = (request.form.get("title") or "").strip()
    date_val = (request.form.get("date") or "").strip()
    if not title or not date_val:
        flash("Event title and date are required.", "warning")
        return redirect(request.referrer or url_for("events_page"))
    event = {
        "id": new_id(),
        "title": title,
        "date": date_val,
        "time": (request.form.get("time") or "").strip(),
        "type": (request.form.get("type") or "general").strip(),
        "status": request.form.get("status") or "upcoming",
    }
    data = load_data()
    data.setdefault("events", []).insert(0, event)
    write_data(data)
    flash("Event added.", "success")
    return redirect(request.referrer or url_for("events_page"))


@app.route("/events/<int:event_id>/complete", methods=["POST"])
def events_complete(event_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    for e in data.get("events", []):
        if int(e.get("id")) == event_id:
            e["status"] = "done"
            break
    write_data(data)
    flash("Event marked done.", "success")
    return redirect(request.referrer or url_for("events_page"))


@app.route("/events/<int:event_id>/delete", methods=["POST"])
def events_delete(event_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    data["events"] = [e for e in data.get("events", []) if int(e.get("id")) != event_id]
    write_data(data)
    flash("Event removed.", "info")
    return redirect(request.referrer or url_for("events_page"))


@app.route("/reminders/add", methods=["POST"])
def reminders_add():
    guard = ensure_logged_in()
    if guard:
        return guard
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Reminder title is required.", "warning")
        return redirect(request.referrer or url_for("reminders_page"))
    reminder = {
        "id": new_id(),
        "title": title,
        "due": (request.form.get("due") or "").strip() or "TBD",
        "status": request.form.get("status") or "open",
    }
    data = load_data()
    data.setdefault("reminders", []).insert(0, reminder)
    write_data(data)
    flash("Reminder added.", "success")
    return redirect(request.referrer or url_for("reminders_page"))


@app.route("/reminders/<int:reminder_id>/complete", methods=["POST"])
def reminders_complete(reminder_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    for r in data.get("reminders", []):
        if int(r.get("id")) == reminder_id:
            r["status"] = "done"
            break
    write_data(data)
    flash("Reminder completed.", "success")
    return redirect(request.referrer or url_for("reminders_page"))


@app.route("/reminders/<int:reminder_id>/delete", methods=["POST"])
def reminders_delete(reminder_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    data["reminders"] = [r for r in data.get("reminders", []) if int(r.get("id")) != reminder_id]
    write_data(data)
    flash("Reminder removed.", "info")
    return redirect(request.referrer or url_for("reminders_page"))


@app.route("/notes/add", methods=["POST"])
def notes_add():
    guard = ensure_logged_in()
    if guard:
        return guard
    title = (request.form.get("title") or "").strip()
    body = (request.form.get("excerpt") or "").strip()
    tags_raw = (request.form.get("tags") or "").strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    if not title and not body:
        flash("Note title or body is required.", "warning")
        return redirect(request.referrer or url_for("notes_page"))
    note = {"id": new_id(), "title": title or "Untitled", "excerpt": body, "tags": tags}
    data = load_data()
    data.setdefault("notes", []).insert(0, note)
    write_data(data)
    flash("Note saved.", "success")
    return redirect(request.referrer or url_for("notes_page"))


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def notes_delete(note_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    data["notes"] = [n for n in data.get("notes", []) if int(n.get("id")) != note_id]
    write_data(data)
    flash("Note deleted.", "info")
    return redirect(request.referrer or url_for("notes_page"))


@app.route("/tasks/<int:task_id>/update", methods=["POST"])
def tasks_update(task_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    title = (request.form.get("title") or "").strip()
    due = (request.form.get("due") or "").strip()
    status = (request.form.get("status") or "").strip() or None
    priority = (request.form.get("priority") or "").strip() or None
    project = (request.form.get("project") or "").strip() or None
    for t in data.get("tasks", []):
        if int(t.get("id")) == task_id:
            if title:
                t["title"] = title
            if due:
                t["due"] = due
            if status:
                t["status"] = status
            if priority:
                t["priority"] = priority
            if project:
                t["project"] = project
            break
    write_data(data)
    flash("Task updated.", "success")
    return redirect(request.referrer or url_for("tasks_page"))


@app.route("/events/<int:event_id>/update", methods=["POST"])
def events_update(event_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    title = (request.form.get("title") or "").strip()
    date_val = (request.form.get("date") or "").strip()
    time_val = (request.form.get("time") or "").strip()
    type_val = (request.form.get("type") or "").strip()
    status_val = (request.form.get("status") or "").strip()
    for e in data.get("events", []):
        if int(e.get("id")) == event_id:
            if title:
                e["title"] = title
            if date_val:
                e["date"] = date_val
            if time_val:
                e["time"] = time_val
            if type_val:
                e["type"] = type_val
            if status_val:
                e["status"] = status_val
            break
    write_data(data)
    flash("Event updated.", "success")
    return redirect(request.referrer or url_for("events_page"))


@app.route("/reminders/<int:reminder_id>/update", methods=["POST"])
def reminders_update(reminder_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    title = (request.form.get("title") or "").strip()
    due = (request.form.get("due") or "").strip()
    status_val = (request.form.get("status") or "").strip()
    for r in data.get("reminders", []):
        if int(r.get("id")) == reminder_id:
            if title:
                r["title"] = title
            if due:
                r["due"] = due
            if status_val:
                r["status"] = status_val
            break
    write_data(data)
    flash("Reminder updated.", "success")
    return redirect(request.referrer or url_for("reminders_page"))


@app.route("/notes/<int:note_id>/update", methods=["POST"])
def notes_update(note_id: int):
    guard = ensure_logged_in()
    if guard:
        return guard
    data = load_data()
    title = (request.form.get("title") or "").strip()
    excerpt = (request.form.get("excerpt") or "").strip()
    tags_raw = (request.form.get("tags") or "").strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else None
    for n in data.get("notes", []):
        if int(n.get("id")) == note_id:
            if title:
                n["title"] = title
            if excerpt:
                n["excerpt"] = excerpt
            if tags is not None:
                n["tags"] = tags
            break
    write_data(data)
    flash("Note updated.", "success")
    return redirect(request.referrer or url_for("notes_page"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
