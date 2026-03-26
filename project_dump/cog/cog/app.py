from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
from markupsafe import escape
from flask_wtf.csrf import CSRFProtect
from core_ai import ask_core_ai, ask_for_code_change
from tools.safety import check_file_safety
from simulation import GRID_SIZE
import database, simulation
import os, time, difflib, glob, random, string, json
import html

# Flask app with security headers
app = Flask(__name__)
# prefer environment override for production use
app.secret_key = os.environ.get("COGNITIA_SECRET") or "dev-secret"
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour CSRF token lifetime

# Enable CSRF protection globally
csrf = CSRFProtect(app)

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

# Ensure DB and simulation initialized
database.init_db()
simulation.init_sim()

ALLOWED_FILES = [
    "simulation.py",
    "templates/home.html",
    "templates/logs.html",
    "templates/simulation.html",
    "templates/codex.html",
    "templates/base.html",
    "templates/debug.html",
    "templates/core_ai.html",
    "templates/sim_overview.html",
    "templates/sim_population.html",
    "templates/sim_society.html",
    "templates/metrics.html",
    "templates/events.html",
    "templates/tech.html",
    "templates/sandbox.html",
    "templates/lab.html",
    "templates/governance.html",
    "static/style.css",
    "app.py"
]

def atomic_write(path, content):
    project_root = os.path.dirname(__file__)
    backup_dir = os.path.join(project_root, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    if os.path.exists(path):
        ts = time.strftime("%Y%m%d_%H%M%S")
        base = os.path.basename(path)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                old = f.read()
        except Exception:
            old = ""
        with open(os.path.join(backup_dir, f"{base}.{ts}.bak"), "w", encoding="utf-8") as f:
            f.write(old)
        diff = "\n".join(difflib.unified_diff(old.splitlines(), content.splitlines(),
                                              fromfile=f"old/{base}", tofile=f"new/{base}", lineterm=""))
    else:
        diff = content
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return diff

@app.route("/")
def index():
    return redirect(url_for("core_ai"))

# --- Core AI Chat (persistent) ---
@app.route("/core", methods=["GET","POST"])
def core_ai():
    if request.method == "POST":
        msg = request.form.get("prompt","").strip()
        if msg:
            database.save_chat("user", msg)
            reply = ask_core_ai(msg)
            database.save_chat("assistant", reply)
        return redirect(url_for('core_ai'))
    history = database.get_chat(300)
    return render_template("core_ai.html", history=history)

# --- Codex self-modify ---
@app.route("/codex", methods=["GET", "POST"])
def codex():
    if request.method == "POST":
        instruction = request.form.get("instruction","").strip()
        if not instruction:
            flash("Please provide an instruction", "error")
            return redirect(url_for("codex"))
        result = ask_for_code_change(instruction, ALLOWED_FILES)
        filename = html.escape(result.get("filename",""))
        content = result.get("content","")
        summary = html.escape(result.get("summary",""))
        if not filename or not content:
            flash("AI did not return a valid change.", "error")
            return redirect(url_for("codex"))
        if filename not in ALLOWED_FILES:
            flash(f"File not allowed: {escape(filename)}", "error")
            return redirect(url_for("codex"))
            
        # Run safety checks on the generated code
        is_safe, errors = check_file_safety(filename, content)
        if not is_safe:
            flash(f"Safety check failed: {'; '.join(errors)}", "error")
            return redirect(url_for("codex"))
            
        diff = atomic_write(filename, content)
        database.save_code_change(filename, summary or "(no summary)", diff)
        flash(f"Applied change to {escape(filename)}", "ok")
        return redirect(url_for("codex"))
    changes = database.get_code_changes(50)
    return render_template("codex.html", changes=changes, allowed=ALLOWED_FILES)

@app.route("/rollback/<path:filename>", methods=["POST"])
def rollback(filename):
    backups = sorted(glob.glob(f"backups/{os.path.basename(filename)}.*.bak"))
    if not backups:
        flash("No backups found for "+filename, "error")
        return redirect(url_for("codex"))
    latest = backups[-1]
    with open(latest,"r",encoding="utf-8",errors="ignore") as f:
        content = f.read()
    with open(filename,"w",encoding="utf-8") as f:
        f.write(content)
    database.save_code_change(filename, "Rollback applied", "(rollback from "+latest+")")
    flash(f"Rolled back {filename}", "ok")
    return redirect(url_for("codex"))

# --- Simulation & sub-tabs ---
@app.route("/simulation")
def simulation_hub():
    return render_template("simulation.html")

@app.route("/sim/overview")
def sim_overview():
    return render_template("sim_overview.html")

@app.route("/sim/population")
def sim_population():
    agents = simulation.list_agents()
    return render_template("sim_population.html", agents=agents)

@app.route("/sim/society")
def sim_society():
    agents = simulation.list_agents()
    towns = max(1, len(agents)//10)
    families = max(1, len(agents)//3)
    return render_template("sim_society.html", towns=towns, families=families, pop=len(agents))

@app.route("/simdata")
def simdata():
    simulation.step()
    data = simulation.get_positions()
    return jsonify(data)

@app.route("/agent_at")
def agent_at():
    x = int(request.args.get("x", -1))
    y = int(request.args.get("y", -1))
    data = database.get_agent_at(x, y)
    return jsonify(data or {})

@app.route("/agent/goals/<int:agent_id>")
def agent_goals(agent_id):
    goals = database.get_agent_goals(agent_id)
    return jsonify([{
        'id': g['id'],
        'type': g['goal_type'],
        'progress': g['progress'],
        'priority': g['priority'],
        'target': json.loads(g['target_data'])
    } for g in goals])

@app.route("/agent/memories/<int:agent_id>")
def agent_memories(agent_id):
    memories = database.get_agent_memories(agent_id)
    return jsonify([{
        'timestamp': m['timestamp'],
        'type': m['memory_type'],
        'description': format_memory(m['memory_type'], json.loads(m['memory_data']))
    } for m in memories])

@app.route("/agent/relationships/<int:agent_id>")
def agent_relationships(agent_id):
    relationships = database.get_relationships(agent_id)
    return jsonify([{
        'target_id': r['target_id'],
        'target_name': database.get_agent_name(r['target_id']),
        'type': r['relationship_type'],
        'strength': r['strength']
    } for r in relationships])

@app.route("/environment")
def environment():
    env = database.get_current_environment()
    if not env:
        return jsonify({
            'weather': 'clear',
            'season': 'summer',
            'day_phase': 'day',
            'effects': {}
        })
    return jsonify({
        'weather': env['weather'],
        'season': env['season'],
        'day_phase': env['day_phase'],
        'effects': json.loads(env['effects'])
    })

@app.route("/resources")
def resources():
    resources = database.get_resources_in_range(0, 0, GRID_SIZE)
    return jsonify([{
        'x': r['x'],
        'y': r['y'],
        'type': r['resource_type'],
        'amount': r['amount']
    } for r in resources])

def format_memory(memory_type, data):
    """Format memory data into human-readable description."""
    if memory_type == 'interaction':
        target_name = database.get_agent_name(data['target_id'])
        return f"Had a {data['outcome']} interaction with {target_name}"
    elif memory_type == 'discovery':
        return f"Discovered {data['resource_type']} at ({data['x']}, {data['y']})"
    elif memory_type == 'resource':
        return f"{'Gathered' if data['amount'] > 0 else 'Failed to find'} {abs(data['amount'])} {data['resource_type']}"
    return str(data)

# --- Metrics ---
@app.route("/metrics")
def metrics():
    m = database.get_metrics(50)
    return render_template("metrics.html", metrics=m)

# --- Events ---
@app.route("/events")
def events():
    ev = database.get_events(100)
    return render_template("events.html", events=ev)

# --- Tech Tree ---
TECH_ORDER = [
    ("foraging","Foraging"),
    ("farming","Farming"),
    ("stone_tools","Stone Tools"),
    ("storage","Storage"),
    ("trade","Trade"),
    ("science","Science")
]

TECH_LABELS = {
    "foraging": "Foraging",
    "farming": "Farming",
    "stone_tools": "Stone Tools",
    "storage": "Storage",
    "trade": "Trade",
    "science": "Science"
}

@app.route("/tech", methods=["GET","POST"])
def tech():
    if request.method == "POST":
        action = request.form.get("action")
        tech_name = request.form.get("tech")
        
        if action == "research":
            if not database.can_research_tech(tech_name):
                flash("Prerequisites not met for this technology", "error")
                return redirect(url_for("tech"))
            
            # Simulate research points from agents
            agents = simulation.list_agents()
            scientists = [a for a in agents if a['role'] == 'scientist' and a['energy'] > 50]
            
            if not scientists:
                flash("No scientists available to research", "error")
                return redirect(url_for("tech"))
            
            # Each scientist contributes research points
            total_points = 0
            for scientist in scientists:
                points = random.randint(5, 15) * (1 + scientist['prestige'] / 100)
                database.add_research_points(scientist['id'], tech_name, int(points))
                total_points += points
            
            flash(f"Added {int(total_points)} research points to {tech_name}", "ok")
            return redirect(url_for("tech"))
    
    # Get tech tree data
    tech_data = database.get_tech()
    tech_info = {}
    
    for name, data in tech_data.items():
        tech_info[name] = {
            'label': TECH_LABELS.get(name, name),
            'unlocked': data['unlocked'],
            'progress': data['progress'],
            'prerequisites': data['prerequisites'],
            'effects': data['effects'],
            'can_research': database.can_research_tech(name),
            'discoverer_name': database.get_agent_name(data['discoverer']) if data['discoverer'] else None,
            'discovery_time': data['discovery_time']
        }
    
    # Get research statistics
    research_stats = []
    for agent in simulation.list_agents():
        if agent['role'] == 'scientist':
            progress = database.get_research_progress(agent['id'])
            research_stats.append({
                'name': agent['name'],
                'techs_researched': len(progress),
                'total_points': sum(p['total_points'] for p in progress)
            })
    
    research_stats.sort(key=lambda x: x['total_points'], reverse=True)
    
    return render_template("tech.html", 
                         tech=tech_info,
                         research_stats=research_stats)

# --- Sandbox Controls ---
@app.route("/sandbox", methods=["GET","POST"])
def sandbox():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "spawn":
            name = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
            x = random.randint(0,11); y = random.randint(0,11)
            database.add_agent(name, x, y, age=random.randint(16,40), energy=90, role="settler")
            database.log_event(f"Spawned new agent {name} at ({x},{y})")
            flash(f"Spawned agent {name}", "ok")
        elif action == "boost":
            database.update_energy_all(+10)
            database.log_event("Global energy boost +10")
            flash("Boosted energy for all agents", "ok")
        elif action == "rain":
            database.log_event("Weather event: Rain improves crop yield")
            flash("Triggered Rain event", "ok")
        return redirect(url_for("sandbox"))
    return render_template("sandbox.html")

# --- AI Lab & Governance (placeholders) ---
@app.route("/lab")
def lab():
    return render_template("lab.html")

@app.route("/governance")
def governance():
    return render_template("governance.html")

# --- Logs ---
@app.route("/logs")
def logs():
    logs = database.get_logs(50)
    return render_template("logs.html", logs=logs)

# --- Debug ---
@app.route("/debug")
def debug():
    log_path = "core_ai.log"
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-200:]
    except FileNotFoundError:
        lines = ["(no log yet)"]
    return render_template("debug.html", log_lines=lines, log_path=log_path)

if __name__ == "__main__":
    app.run(debug=True)
