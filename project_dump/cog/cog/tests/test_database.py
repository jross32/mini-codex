"""Test database operations."""
import pytest
from datetime import datetime
import database

def test_init_db(temp_db):
    """Test database initialization creates tables."""
    database.init_db()
    with database.connect() as conn:
        c = conn.cursor()
        # Check all tables exist
        tables = ['logs', 'chat_messages', 'code_changes', 'agents',
                 'events', 'metrics', 'tech']
        for table in tables:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                     (table,))
            assert c.fetchone() is not None

def test_seed_agents(temp_db):
    """Test agent seeding."""
    database.init_db()
    database.seed_agents(n=5, grid=6)
    with database.connect() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM agents")
        assert c.fetchone()[0] == 5

def test_agent_crud(temp_db):
    """Test agent creation, reading, updating."""
    database.init_db()
    
    # Create
    database.add_agent("TEST", 1, 2, age=25, energy=70, role="farmer")
    
    # Read
    agent = database.get_agent_at(1, 2)
    assert agent['name'] == "TEST"
    assert agent['age'] == 25
    assert agent['energy'] == 70
    assert agent['role'] == "farmer"
    
    # Update energy
    database.update_energy_all(10)
    agent = database.get_agent_at(1, 2)
    assert agent['energy'] == 80  # 70 + 10
    
    # Update energy with clamping
    database.update_energy_all(30)
    agent = database.get_agent_at(1, 2)
    assert agent['energy'] == 100  # clamped at max

def test_chat_messages(temp_db):
    """Test chat message storage and retrieval."""
    database.init_db()
    
    database.save_chat("user", "Hello")
    database.save_chat("assistant", "Hi there")
    
    msgs = database.get_chat(limit=10)
    assert len(msgs) == 2
    assert msgs[0]['role'] == "user"
    assert msgs[0]['content'] == "Hello"
    assert msgs[1]['role'] == "assistant"
    assert msgs[1]['content'] == "Hi there"

def test_events(temp_db):
    """Test event logging and retrieval."""
    database.init_db()
    
    database.log_event("Test event 1")
    database.log_event("Test event 2")
    
    events = database.get_events(limit=10)
    assert len(events) == 2
    assert events[0]['description'] == "Test event 2"  # most recent first
    assert events[1]['description'] == "Test event 1"

def test_metrics(temp_db):
    """Test metrics storage and retrieval."""
    database.init_db()
    
    database.push_metric(10, 75.5)
    database.push_metric(11, 80.0)
    
    metrics = database.get_metrics(limit=10)
    assert len(metrics) == 2
    assert metrics[0]['population'] == 11
    assert metrics[0]['avg_energy'] == 80.0

def test_tech_tree(temp_db):
    """Test tech tree operations."""
    database.init_db()
    
    # Initially empty
    tech = database.get_tech()
    assert len(tech) == 0
    
    # Set tech states
    database.set_tech("farming", True)
    database.set_tech("science", False)
    
    tech = database.get_tech()
    assert tech['farming'] == 1
    assert tech['science'] == 0

def test_code_changes(temp_db):
    """Test code change logging."""
    database.init_db()
    
    database.save_code_change("test.py", "Added feature", "diff content")
    changes = database.get_code_changes(limit=10)
    assert len(changes) == 1
    assert changes[0]['filename'] == "test.py"
    assert changes[0]['summary'] == "Added feature"
    assert changes[0]['diff'] == "diff content"