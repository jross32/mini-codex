
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# get_db helper for context manager DB access
def get_db():
    return connect()

# Use the existing cognitia.db in workspace root for persistence
DB_NAME = os.path.join(os.path.dirname(__file__), "cognitia.db")

def connect():
    """Return a sqlite3 connection with row factory set."""
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_ai_scientist(name: str, x: int, y: int) -> int:
    """Create a new AI Scientist in the database."""
    with get_db() as db:
        cur = db.cursor()
        cur.execute("""
        INSERT INTO agents (name, x, y, energy, agent_type, access_level)
        VALUES (?, ?, ?, 100.0, 'scientist', 2)
        """, (name, x, y))
        return cur.lastrowid

def create_research_project(title: str, description: str, lead_scientist_id: int) -> int:
    """Create a new research project."""
    with get_db() as db:
        cur = db.cursor()
        cur.execute("""
        INSERT INTO research_projects (title, description, lead_scientist_id)
        VALUES (?, ?, ?)
        """, (title, description, lead_scientist_id))
        return cur.lastrowid

def add_project_finding(
    project_id: int,
    finding_type: str,
    description: str,
    code_change: Optional[str] = None
) -> int:
    """Add a new finding to a research project."""
    with get_db() as db:
        cur = db.cursor()
        cur.execute("""
        INSERT INTO research_findings 
        (project_id, finding_type, description, code_change)
        VALUES (?, ?, ?, ?)
        """, (project_id, finding_type, description, code_change))
        return cur.lastrowid

def get_recent_findings(limit: int = 10) -> List[Dict[str, Any]]:
    """Get the most recent research findings."""
    with get_db() as db:
        cur = db.cursor()
        cur.execute("""
        SELECT f.*, p.title as project_title, a.name as scientist_name
        FROM research_findings f
        JOIN research_projects p ON f.project_id = p.id
        JOIN agents a ON p.lead_scientist_id = a.id
        ORDER BY f.timestamp DESC
        LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]

def publish_news_article(title: str, content: str, access_level: int = 0) -> int:
    """Publish a news article to the information feed."""
    with get_db() as db:
        cur = db.cursor()
        cur.execute("""
        INSERT INTO news_feed (title, content, access_level)
        VALUES (?, ?, ?)
        """, (title, content, access_level))
        return cur.lastrowid

def get_news_feed(access_level: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent news articles up to the specified access level."""
    with get_db() as db:
        cur = db.cursor()
        cur.execute("""
        SELECT * FROM news_feed
        WHERE access_level <= ?
        ORDER BY timestamp DESC
        LIMIT ?
        """, (access_level, limit))
        return [dict(row) for row in cur.fetchall()]

def init_agent_tables(cur):
    """Initialize database tables for base agents."""
    cur.execute("DROP TABLE IF EXISTS agents")
    cur.execute("DROP TABLE IF EXISTS groups")
    cur.execute("DROP TABLE IF EXISTS agent_relationships")
    cur.execute("""
    CREATE TABLE agents (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        energy REAL NOT NULL
    )
    """)

# Add a new function to initialize all tables and indices
def init_db():
    conn = connect()
    cur = conn.cursor()
    # Meta University table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta_university (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        size INTEGER NOT NULL,
        access_level INTEGER DEFAULT 3
    )
    """)
    # Research projects table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS research_projects (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        lead_scientist_id INTEGER NOT NULL,
        start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_date DATETIME,
        status TEXT DEFAULT 'in_progress',
        FOREIGN KEY (lead_scientist_id) REFERENCES agents (id)
    )
    """)
    # Research findings table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS research_findings (
        id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        finding_type TEXT NOT NULL,
        description TEXT NOT NULL,
        code_change TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES research_projects (id)
    )
    """)
    # News/information feed table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news_feed (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        access_level INTEGER DEFAULT 0
    )
    """)
    # Create indices
    cur.execute("CREATE INDEX IF NOT EXISTS idx_research_findings_project ON research_findings(project_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_news_access ON news_feed(access_level)")
    # Initialize default access levels
    cur.execute("""
    CREATE TABLE IF NOT EXISTS access_levels (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """)
    # Insert default access levels if not exists
    cur.executemany(
        "INSERT OR IGNORE INTO access_levels (id, name, description) VALUES (?, ?, ?)",
        [
            (0, "Public", "General simulation information"),
            (1, "Restricted", "Limited access research data"),
            (2, "Scientific", "Full research access"),
            (3, "Core", "System level access")
        ]
    )
    # Project findings table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_findings (
        id INTEGER PRIMARY KEY,
        project_id INTEGER,
        finding_type TEXT NOT NULL,
        description TEXT,
        code_change TEXT,
        implementation_status TEXT DEFAULT 'pending',
        verification_status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES research_projects (id)
    )
    """)
    # News system table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            access_level INTEGER DEFAULT 0,
            publication_date TEXT DEFAULT CURRENT_TIMESTAMP,
            source TEXT,
            reliability REAL DEFAULT 1.0
        )
        """)

def save_chat(role, content):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO chat_messages (timestamp, role, content) VALUES (?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role, content))
    conn.commit(); conn.close()

def get_chat(limit=200):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT timestamp, role, content FROM chat_messages ORDER BY id ASC LIMIT ?", (limit,))
    rows = c.fetchall(); conn.close(); return rows

def save_log(user_input, ai_response):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, user_input, ai_response) VALUES (?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_input, ai_response))
    conn.commit(); conn.close()

def get_logs(limit=50):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT timestamp, user_input, ai_response FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall(); conn.close(); return rows

def save_code_change(filename, summary, diff):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO code_changes (timestamp, filename, summary, diff) VALUES (?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), filename, summary, diff))
    conn.commit(); conn.close()

def get_code_changes(limit=50):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT timestamp, filename, summary, diff FROM code_changes ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall(); conn.close(); return rows

def seed_agents(n=20, grid=12):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM agents")
    count = c.fetchone()[0]
    if count == 0:
        import random, string
        for _ in range(n):
            name = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
            c.execute("INSERT INTO agents (name, x, y, age, energy, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (name, random.randint(0,grid-1), random.randint(0,grid-1),
                       random.randint(16,60), random.randint(30,100), random.choice(["farmer","builder","miner","scientist"]), "ok"))
        conn.commit()
    conn.close()

def add_agent(name, x, y, age=20, energy=80, role="farmer", status="ok"):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO agents (name,x,y,age,energy,role,status) VALUES (?,?,?,?,?,?,?)",
              (name, x, y, age, energy, role, status))
    conn.commit(); conn.close()

def update_energy_all(delta=10):
    conn = connect(); c = conn.cursor()
    # SQLite doesn't have MIN/MAX in UPDATE expression in same way; use CASE to clamp
    c.execute("UPDATE agents SET energy = CASE WHEN energy + ? > 100 THEN 100 WHEN energy + ? < 0 THEN 0 ELSE energy + ? END", (delta, delta, delta))
    conn.commit(); conn.close()

def get_agent_at(x, y):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT id, name, x, y, age, energy, role, status FROM agents WHERE x=? AND y=? LIMIT 1", (x, y))
    row = c.fetchone(); conn.close()
    if not row: return None
    keys = ["id","name","x","y","age","energy","role","status"]
    return {k: row[k] for k in keys}

def log_event(message, access_level=0):
    """Log an event to the events table with access level control."""
    with get_db() as db:
        db.execute(
            "INSERT INTO events (message, access_level) VALUES (?, ?)",
            (message, access_level)
        )

def create_ai_scientist(name, x, y):
    """Create a new AI Scientist agent."""
    with get_db() as db:
        cur = db.execute(
            """INSERT INTO agents 
            (name, x, y, energy, role, prestige, agent_type, access_level) 
            VALUES (?, ?, ?, 100, 'scientist', 50, 'ai_scientist', 3)
            RETURNING id""",
            (name, x, y)
        )
        return cur.fetchone()[0]

def create_research_project(title, description, lead_scientist_id, priority=1):
    """Create a new research project."""
    with get_db() as db:
        cur = db.execute(
            """INSERT INTO research_projects 
            (title, description, lead_scientist_id, priority, start_date) 
            VALUES (?, ?, ?, ?, datetime('now'))
            RETURNING id""",
            (title, description, lead_scientist_id, priority)
        )
        return cur.fetchone()[0]

def add_project_finding(project_id, finding_type, description, code_change=None):
    """Add a new finding to a research project."""
    with get_db() as db:
        db.execute(
            """INSERT INTO project_findings 
            (project_id, finding_type, description, code_change) 
            VALUES (?, ?, ?, ?)""",
            (project_id, finding_type, description, code_change)
        )

def publish_news_article(title, content, access_level=0, source="Meta University Press"):
    """Publish a news article in the simulation."""
    with get_db() as db:
        db.execute(
            """INSERT INTO news_articles 
            (title, content, access_level, source) 
            VALUES (?, ?, ?, ?)""",
            (title, content, access_level, source)
        )

def get_news_feed(access_level=0):
    """Get news articles accessible at given access level."""
    with get_db() as db:
        return db.execute(
            """SELECT id, title, content, source, publication_date 
            FROM news_articles 
            WHERE access_level <= ? 
            ORDER BY publication_date DESC""",
            (access_level,)
        ).fetchall()

def get_events(limit=100):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT timestamp, description FROM events ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall(); conn.close(); return rows

def push_metric(pop, avg_energy):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO metrics (timestamp, population, avg_energy) VALUES (?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pop, avg_energy))
    conn.commit(); conn.close()

def get_metrics(limit=100):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT timestamp, population, avg_energy FROM metrics ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall(); conn.close(); return rows

def init_tech_tree():
    """Initialize the technology tree with prerequisites and requirements."""
    techs = [
        ("foraging", 50, "", {
            "food_gather_rate": 1.2,
            "food_discover_chance": 1.3
        }),
        ("farming", 100, "foraging", {
            "food_production": 1.5,
            "settlement_bonus": 1.2
        }),
        ("stone_tools", 75, "foraging", {
            "work_efficiency": 1.3,
            "defense": 1.2
        }),
        ("storage", 150, "farming", {
            "food_spoilage_rate": 0.7,
            "max_food_stored": 1.5
        }),
        ("trade", 200, "storage", {
            "trade_success_rate": 1.3,
            "wealth_gain_rate": 1.2
        }),
        ("science", 300, "stone_tools,trade", {
            "research_rate": 1.5,
            "tech_spread_rate": 1.3
        })
    ]
    
    conn = connect(); c = conn.cursor()
    for name, points, prereqs, effects in techs:
        c.execute("""INSERT OR REPLACE INTO tech 
                     (name, unlocked, research_points, points_required, prerequisites, effects)
                     VALUES (?, 0, 0, ?, ?, ?)""",
                  (name, points, prereqs, json.dumps(effects)))
    conn.commit(); conn.close()

def get_tech():
    """Get full tech tree status."""
    conn = connect(); c = conn.cursor()
    c.execute("""SELECT name, unlocked, research_points, points_required,
                         prerequisites, effects, discovered_by, discovered_time 
                 FROM tech""")
    rows = c.fetchall()
    conn.close()
    
    return {r['name']: {
        'unlocked': r['unlocked'],
        'progress': r['research_points'] / r['points_required'],
        'prerequisites': r['prerequisites'].split(',') if r['prerequisites'] else [],
        'effects': json.loads(r['effects']) if r['effects'] else {},
        'discoverer': r['discovered_by'],
        'discovery_time': r['discovered_time']
    } for r in rows}

def can_research_tech(name: str) -> bool:
    """Check if a technology can be researched (prerequisites met)."""
    tech = get_tech()
    if name not in tech:
        return False
    
    # Check prerequisites
    for prereq in tech[name]['prerequisites']:
        if not tech.get(prereq, {}).get('unlocked', False):
            return False
    return True

def add_research_points(agent_id: int, tech_name: str, points: int):
    """Add research points to a technology."""
    conn = connect(); c = conn.cursor()
    
    # Record research progress
    c.execute("INSERT INTO research_progress (agent_id, tech_name, points, timestamp) VALUES (?, ?, ?, ?)",
              (agent_id, tech_name, points, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # Update tech points
    c.execute("UPDATE tech SET research_points = research_points + ? WHERE name = ?",
              (points, tech_name))
    
    # Check if tech is now complete
    c.execute("SELECT research_points, points_required FROM tech WHERE name = ?", (tech_name,))
    tech = c.fetchone()
    
    if tech and tech['research_points'] >= tech['points_required']:
        # Technology discovered!
        c.execute("""UPDATE tech 
                     SET unlocked = 1, 
                         discovered_by = ?,
                         discovered_time = ? 
                     WHERE name = ?""",
                  (agent_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tech_name))
        
        # Log the discovery
    # agent = get_agent_name(agent_id)  # TODO: Implement or import get_agent_name if needed
    # log_event(f"Technology discovered: {tech_name} by {agent}")  # TODO: Define 'agent' if needed
        
    conn.commit(); conn.close()

def get_tech_effects(tech_name: str) -> dict:
    """Get the active effects of a technology."""
    conn = connect(); c = conn.cursor()
    c.execute("SELECT effects FROM tech WHERE name = ? AND unlocked = 1", (tech_name,))
    row = c.fetchone()
    conn.close()
    
    return json.loads(row['effects']) if row and row['effects'] else {}

def get_research_progress(agent_id: int) -> list:
    """Get research contributions by an agent."""
    conn = connect(); c = conn.cursor()
    c.execute("""SELECT tech_name, SUM(points) as total_points 
                 FROM research_progress 
                 WHERE agent_id = ? 
                 GROUP BY tech_name""", (agent_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# --- Group Functions ---
def create_group(name: str, group_type: str, leader_id: int, x: int, y: int) -> int:
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO groups (name, group_type, leader_id, location_x, location_y, founded_time) VALUES (?, ?, ?, ?, ?, ?)",
              (name, group_type, leader_id, x, y, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    group_id = c.lastrowid
    # Add leader as first member
    c.execute("INSERT INTO group_members (group_id, agent_id, join_time, role) VALUES (?, ?, ?, ?)",
              (group_id, leader_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "leader"))
    conn.commit(); conn.close()
    return group_id

def add_group_member(group_id: int, agent_id: int, role: str = "member"):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO group_members (group_id, agent_id, join_time, role) VALUES (?, ?, ?, ?)",
              (group_id, agent_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role))
    conn.commit(); conn.close()

def get_agent_groups(agent_id: int):
    conn = connect(); c = conn.cursor()
    c.execute("""SELECT g.*, gm.role 
                 FROM groups g 
                 JOIN group_members gm ON g.id = gm.group_id 
                 WHERE gm.agent_id = ?""", (agent_id,))
    rows = c.fetchall(); conn.close(); return rows

def get_group_members(group_id: int):
    conn = connect(); c = conn.cursor()
    c.execute("""SELECT a.*, gm.role, gm.join_time 
                 FROM agents a 
                 JOIN group_members gm ON a.id = gm.agent_id 
                 WHERE gm.group_id = ?""", (group_id,))
    rows = c.fetchall(); conn.close(); return rows

# --- Trade Functions ---
def record_trade(from_id: int, to_id: int, trade_type: str, amount: int, success: bool = True):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO trades (timestamp, from_agent_id, to_agent_id, trade_type, amount, success) VALUES (?, ?, ?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), from_id, to_id, trade_type, amount, 1 if success else 0))
    conn.commit(); conn.close()

def get_agent_trades(agent_id: int, limit: int = 50):
    conn = connect(); c = conn.cursor()
    c.execute("""SELECT * FROM trades 
                 WHERE from_agent_id = ? OR to_agent_id = ? 
                 ORDER BY timestamp DESC LIMIT ?""", (agent_id, agent_id, limit))
    rows = c.fetchall(); conn.close(); return rows

# --- Social Status Functions ---
def update_agent_status(agent_id: int, social_class: str = None, prestige_delta: int = 0, wealth_delta: int = 0):
    conn = connect(); c = conn.cursor()
    if social_class:
        c.execute("UPDATE agents SET social_class = ? WHERE id = ?", (social_class, agent_id))
    if prestige_delta:
        c.execute("UPDATE agents SET prestige = prestige + ? WHERE id = ?", (prestige_delta, agent_id))
    if wealth_delta:
        c.execute("UPDATE agents SET wealth = wealth + ? WHERE id = ?", (wealth_delta, agent_id))
    conn.commit(); conn.close()

def get_agent_status(agent_id: int):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT social_class, prestige, wealth FROM agents WHERE id = ?", (agent_id,))
    row = c.fetchone(); conn.close(); return row

# --- Agent Memory Functions ---
def add_memory(agent_id: int, memory_type: str, memory_data: dict):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO agent_memories (agent_id, memory_type, memory_data, timestamp) VALUES (?, ?, ?, ?)",
              (agent_id, memory_type, json.dumps(memory_data), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()

def get_agent_memories(agent_id: int, memory_type: str = None, limit: int = 50):
    conn = connect(); c = conn.cursor()
    if memory_type:
        c.execute("SELECT * FROM agent_memories WHERE agent_id=? AND memory_type=? ORDER BY id DESC LIMIT ?",
                  (agent_id, memory_type, limit))
    else:
        c.execute("SELECT * FROM agent_memories WHERE agent_id=? ORDER BY id DESC LIMIT ?",
                  (agent_id, limit))
    rows = c.fetchall(); conn.close(); return rows

# --- Agent Goal Functions ---
def set_agent_goal(agent_id: int, goal_type: str, target_data: dict, priority: int):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO agent_goals (agent_id, goal_type, target_data, priority, progress) VALUES (?, ?, ?, ?, 0)",
              (agent_id, goal_type, json.dumps(target_data), priority))
    conn.commit(); conn.close()

def update_goal_progress(goal_id: int, progress: float):
    conn = connect(); c = conn.cursor()
    c.execute("UPDATE agent_goals SET progress=? WHERE id=?", (progress, goal_id))
    conn.commit(); conn.close()

def get_agent_goals(agent_id: int):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM agent_goals WHERE agent_id=? ORDER BY priority DESC", (agent_id,))
    rows = c.fetchall(); conn.close(); return rows

# --- Relationship Functions ---
def set_relationship(agent_id: int, target_id: int, rel_type: str, strength: float):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO agent_relationships (agent_id, target_id, relationship_type, strength) VALUES (?, ?, ?, ?)",
              (agent_id, target_id, rel_type, max(-1, min(1, strength))))
    conn.commit(); conn.close()

def get_relationships(agent_id: int):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM agent_relationships WHERE agent_id=?", (agent_id,))
    rows = c.fetchall(); conn.close(); return rows

# --- Resource Functions ---
def add_resource(x: int, y: int, resource_type: str, amount: int):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO resources (x, y, resource_type, amount) VALUES (?, ?, ?, ?)",
              (x, y, resource_type, amount))
    conn.commit(); conn.close()

def update_resource(x: int, y: int, amount_delta: int):
    conn = connect(); c = conn.cursor()
    c.execute("UPDATE resources SET amount = amount + ? WHERE x=? AND y=?",
              (amount_delta, x, y))
    conn.commit(); conn.close()

def get_resources_in_range(x: int, y: int, radius: int):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM resources WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ?",
              (x - radius, x + radius, y - radius, y + radius))
    rows = c.fetchall(); conn.close(); return rows

# --- Environment Functions ---
def set_environment(weather: str, season: str, day_phase: str, effects: dict):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO environment (timestamp, weather, season, day_phase, effects) VALUES (?, ?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), weather, season, day_phase, json.dumps(effects)))
    conn.commit(); conn.close()

def get_current_environment():
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM environment ORDER BY id DESC LIMIT 1")
    row = c.fetchone(); conn.close(); return row
