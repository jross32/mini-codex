"""Test web application routes."""
import pytest
from flask import url_for
import database

def test_home_redirect(app_client):
    """Test home page redirects to core AI."""
    rv = app_client.get('/')
    assert rv.status_code == 302
    assert '/core' in rv.headers['Location']

def test_core_ai_chat(app_client, temp_db):
    """Test core AI chat interface."""
    database.init_db()
    
    # Get chat page
    rv = app_client.get('/core')
    assert rv.status_code == 200
    assert b'Cognitia Core' in rv.data
    
    # Submit message (mock core_ai response)
    rv = app_client.post('/core', data={'prompt': 'test message'})
    assert rv.status_code == 302
    
    # Check message was saved
    msgs = database.get_chat(limit=1)
    assert len(msgs) == 1
    assert msgs[0]['role'] == 'user'
    assert msgs[0]['content'] == 'test message'

def test_simulation_views(app_client, temp_db):
    """Test simulation related views."""
    database.init_db()
    database.seed_agents(n=5, grid=6)
    
    # Overview page
    rv = app_client.get('/sim/overview')
    assert rv.status_code == 200
    assert b'World Overview' in rv.data
    
    # Population page
    rv = app_client.get('/sim/population')
    assert rv.status_code == 200
    assert b'Population' in rv.data
    
    # Society page
    rv = app_client.get('/sim/society')
    assert rv.status_code == 200
    assert b'Society' in rv.data
    
def test_simdata_api(app_client, temp_db):
    """Test simulation data API."""
    database.init_db()
    database.seed_agents(n=5, grid=6)
    
    rv = app_client.get('/simdata')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'grid' in data
    assert 'agents' in data
    assert len(data['agents']) == 5

def test_agent_at_api(app_client, temp_db):
    """Test agent-at-position API."""
    database.init_db()
    database.add_agent("TEST", 1, 1)
    
    # Check existing agent
    rv = app_client.get('/agent_at?x=1&y=1')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == "TEST"
    
    # Check empty position
    rv = app_client.get('/agent_at?x=0&y=0')
    assert rv.status_code == 200
    assert rv.get_json() == {}