"""Test simulation operations."""
import pytest
import database
import simulation

def test_simulation_step(temp_db):
    """Test a single simulation step."""
    database.init_db()
    simulation.init_sim()
    
    # Get initial state
    agents_before = simulation.list_agents()
    assert len(agents_before) > 0
    
    # Run one step
    simulation.step()
    
    # Check agents still exist
    agents_after = simulation.list_agents()
    assert len(agents_after) == len(agents_before)
    
    # Check metrics were recorded
    metrics = database.get_metrics(limit=1)
    assert len(metrics) == 1
    assert metrics[0]['population'] == len(agents_after)
    assert 0 <= metrics[0]['avg_energy'] <= 100

def test_get_positions(temp_db):
    """Test getting agent positions."""
    database.init_db()
    simulation.init_sim()
    
    pos = simulation.get_positions()
    assert 'grid' in pos
    assert 'agents' in pos
    assert pos['grid'] == simulation.GRID_SIZE
    assert len(pos['agents']) > 0
    
    # Check agent data format
    agent = pos['agents'][0]
    assert all(k in agent for k in ('id', 'name', 'x', 'y', 'energy'))
    assert 0 <= agent['x'] < simulation.GRID_SIZE
    assert 0 <= agent['y'] < simulation.GRID_SIZE
    assert 0 <= agent['energy'] <= 100

def test_agent_movement(temp_db):
    """Test agent movement within grid bounds."""
    database.init_db()
    
    # Create test agent at edge
    database.add_agent("TEST", 0, 0, energy=50)
    
    # Run multiple steps
    for _ in range(10):
        simulation.step()
        pos = simulation.get_positions()
        agent = next(a for a in pos['agents'] if a['name'] == "TEST")
        # Check stays in bounds
        assert 0 <= agent['x'] < simulation.GRID_SIZE
        assert 0 <= agent['y'] < simulation.GRID_SIZE