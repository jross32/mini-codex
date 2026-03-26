import random
import time
import math
import json
from datetime import datetime
import database
from typing import List, Dict, Tuple, Optional, Any

GRID_SIZE = 12

class GoalType:
    GATHER = "gather"
    EXPLORE = "explore"
    SOCIALIZE = "socialize"
    REST = "rest"

class MemoryType:
    INTERACTION = "interaction"
    DISCOVERY = "discovery"
    RESOURCE = "resource"

class RelationType:
    FRIEND = "friend"
    FAMILY = "family"
    NEUTRAL = "neutral"
    LEADER = "leader"
    FOLLOWER = "follower"

class GroupType:
    FAMILY = "family"
    TRIBE = "tribe"
    VILLAGE = "village"

class SocialClass:
    PEASANT = "peasant"
    MERCHANT = "merchant"
    NOBLE = "noble"
    RULER = "ruler"

class TradeType:
    FOOD = "food"
    LABOR = "labor"
    KNOWLEDGE = "knowledge"

class ResourceType:
    FOOD = "food"
    WATER = "water"

class AgentType:
    HUMAN = "human"
    AI_SCIENTIST = "ai_scientist"

class ResearchType:
    SIMULATION = "simulation_physics"
    BEHAVIOR = "agent_behavior"
    SOCIAL = "social_systems"
    ENVIRONMENT = "environmental_modeling"

class Weather:
    CLEAR = "clear"
    RAIN = "rain"
    STORM = "storm"

class Season:
    SUMMER = "summer"
    WINTER = "winter"

class DayPhase:
    DAWN = "dawn"
    DAY = "day"
    DUSK = "dusk"
    NIGHT = "night"

class MetaUniversity:
    """Special zone where AI Scientists conduct research and improve the simulation."""
    
    def __init__(self, x: int, y: int, size: int = 5):
        self.x = x
        self.y = y
        self.size = size
        self.scientists: Dict[int, 'AIScientist'] = {}
        self.research_labs: Dict[str, List[int]] = {
            ResearchType.SIMULATION: [],
            ResearchType.BEHAVIOR: [],
            ResearchType.SOCIAL: [],
            ResearchType.ENVIRONMENT: []
        }
        self._initialize_labs()
    
    def _initialize_labs(self) -> None:
        """Create initial layout of research labs."""
        for lab_type in self.research_labs.keys():
            database.log_event(f"Initialized {lab_type} research lab", access_level=2)
    
    def is_in_bounds(self, x: int, y: int) -> bool:
        """Check if a position is within university grounds."""
        return (self.x <= x < self.x + self.size and
                self.y <= y < self.y + self.size)
    
    def add_scientist(self, scientist: 'AIScientist') -> None:
        """Add an AI Scientist to the university."""
        self.scientists[scientist.id] = scientist
        self.research_labs[scientist.specialization].append(scientist.id)
        database.log_event(
            f"AI Scientist {scientist.name} joined {scientist.specialization} lab",
            access_level=2
        )
    
    def update(self) -> None:
        """Update all scientists and research projects."""
        for scientist in self.scientists.values():
            scientist.update()
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Get current state of all research projects."""
        return {
            'total_scientists': len(self.scientists),
            'labs': {
                lab: len(members)
                for lab, members in self.research_labs.items()
            },
            'active_projects': sum(
                1 for s in self.scientists.values()
                if s.current_project is not None
            )
        }

class AIScientist:
    """Advanced agent capable of conducting research and improving the simulation."""
    
    def __init__(self, id: int, name: str, x: int, y: int):
        self.id = id
        self.name = name
        self.x = x
        self.y = y
        self.energy = 100.0
        self.specialization = random.choice([
            ResearchType.SIMULATION,
            ResearchType.BEHAVIOR,
            ResearchType.SOCIAL,
            ResearchType.ENVIRONMENT
        ])
        self.current_project = None
        self.research_progress = 0.0
        self.knowledge_base = {}
        self.collaborators = set()
    
    def update(self) -> None:
        """Main update cycle for AI Scientist."""
        if self.current_project is None:
            self._start_new_project()
        else:
            self._continue_research()
    
    def _start_new_project(self) -> None:
        """Initialize a new research project."""
        project_ideas = {
            ResearchType.SIMULATION: [
                "Implement improved physics engine",
                "Optimize spatial calculations",
                "Add fluid dynamics simulation"
            ],
            ResearchType.BEHAVIOR: [
                "Enhance agent decision making",
                "Implement emotional modeling",
                "Add learning capabilities"
            ],
            ResearchType.SOCIAL: [
                "Improve group dynamics",
                "Add cultural evolution",
                "Enhance economic systems"
            ],
            ResearchType.ENVIRONMENT: [
                "Add weather patterns",
                "Implement resource cycles",
                "Create ecosystem simulation"
            ]
        }
        
        project_idea = random.choice(project_ideas[self.specialization])
        self.current_project = database.create_research_project(
            title=project_idea,
            description=f"Investigation into {project_idea.lower()}",
            lead_scientist_id=self.id
        )
        self.research_progress = 0.0
        
        database.log_event(
            f"AI Scientist {self.name} started project: {project_idea}",
            access_level=2
        )
    
    def _continue_research(self) -> None:
        """Advance current research project."""
        # Basic research progress
        progress_increment = random.uniform(0.05, 0.15)
        self.research_progress += progress_increment
        
        # Chance to generate findings
        if random.random() < 0.1:
            finding = self._generate_finding()
            if finding:
                database.add_project_finding(
                    project_id=self.current_project,
                    finding_type=finding['type'],
                    description=finding['description'],
                    code_change=finding.get('code_change')
                )
                
                database.log_event(
                    f"New finding in project {self.current_project}: {finding['description']}",
                    access_level=2
                )
        
        # Project completion
        if self.research_progress >= 1.0:
            self._complete_project()
            
    def _generate_finding(self) -> Optional[Dict[str, Any]]:
        """Generate a research finding based on specialization."""
        finding_types = ['observation', 'improvement', 'breakthrough']
        return {
            'type': random.choice(finding_types),
            'description': f"Research finding in {self.specialization}",
            'code_change': None  # Will contain actual code modifications later
        }
    
    def _complete_project(self) -> None:
        """Handle project completion and results publication."""
        database.publish_news_article(
            title=f"Research Breakthrough at Meta University",
            content=f"AI Scientist {self.name} has completed their research in {self.specialization}",
            access_level=1
        )
        
        database.log_event(
            f"Project {self.current_project} completed by {self.name}",
            access_level=2
        )
        
        self.current_project = None

GRID_SIZE = 12

# Name generator for AI Scientists
def generate_name() -> str:
    prefixes = ['Dr.', 'Prof.', 'Researcher']
    first_names = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Omega']
    last_names = ['Circuit', 'Neural', 'Quantum', 'Logic', 'Vector', 'Matrix']
    return f"{random.choice(prefixes)} {random.choice(first_names)} {random.choice(last_names)}"

# Research Types
class ResearchType:
    SIMULATION = 'Simulation Engineering'
    BEHAVIOR = 'Behavioral Science'
    SOCIAL = 'Social Dynamics'
    ENVIRONMENT = 'Environmental Systems'

class Simulation:
    def __init__(self):
        self.tick = 0
        self.events = []
        
        # Initialize Meta University in a corner of the grid
        self.meta_university = MetaUniversity(
            x=GRID_SIZE - 6,  # Place in the corner
            y=GRID_SIZE - 6,
            size=5
        )
        
        # Initialize agent counters
        self.next_agent_id = 1
        self.agent_count = 0
        self.scientists = []
        
        # Create initial AI Scientists
        self._initialize_scientists()
        
    def _initialize_scientists(self) -> None:
        """Create initial AI Scientists for Meta University."""
        for _ in range(3):  # Start with 3 scientists
            name = generate_name()
            x = self.meta_university.x + random.randint(0, self.meta_university.size-1)
            y = self.meta_university.y + random.randint(0, self.meta_university.size-1)
            
            # Create scientist in database
            scientist_id = database.create_ai_scientist(name, x, y)
            
            # Create scientist object
            scientist = AIScientist(scientist_id, name, x, y)
            self.meta_university.add_scientist(scientist)
            self.scientists.append(scientist)
            
        database.log_event("Meta University initialized with 3 AI Scientists", access_level=2)
    
    def update(self) -> None:
        """Main simulation update loop."""
        self.tick += 1
        
        # Update Meta University and scientists
        self.meta_university.update()
        
        # Process completed research projects
        self._process_research()
        
        # Log major simulation events
        if self.tick % 100 == 0:
            self._log_simulation_status()
    
    def _process_research(self) -> None:
        """Handle research findings and apply simulation updates."""
        # Get recent findings
        findings = database.get_recent_findings()
        
        for finding in findings:
            if finding['code_change']:
                # Apply code modifications - this would require careful validation
                # and sandboxing in a real implementation
                pass
            
            database.log_event(
                f"Applied research finding: {finding['description']}",
                access_level=2
            )
    
    def _log_simulation_status(self) -> None:
        """Log current simulation metrics and status."""
        status = {
            'tick': self.tick,
            'num_scientists': len(self.scientists),
            'research_summary': self.meta_university.get_research_summary()
        }
        
        database.log_event(
            f"Simulation status update: {json.dumps(status)}",
            access_level=1
        )

def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x2 - x1) + abs(y2 - y1)

def get_path(start_x: int, start_y: int, goal_x: int, goal_y: int) -> List[Tuple[int, int]]:
    """A* pathfinding implementation."""
    def h(x: int, y: int) -> int:
        return manhattan_distance(x, y, goal_x, goal_y)
    
    open_set = {(start_x, start_y)}
    closed_set = set()
    
    came_from = {}
    g_score = {(start_x, start_y): 0}
    f_score = {(start_x, start_y): h(start_x, start_y)}
    
    while open_set:
        current = min(open_set, key=lambda pos: f_score[pos])
        
        if current == (goal_x, goal_y):
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        
        open_set.remove(current)
        closed_set.add(current)
        
        x, y = current
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x + dx, y + dy
            neighbor = (nx, ny)
            
            if (nx < 0 or nx >= GRID_SIZE or 
                ny < 0 or ny >= GRID_SIZE or
                neighbor in closed_set):
                continue
                
            tentative_g = g_score[current] + 1
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + h(nx, ny)
                
                if neighbor not in open_set:
                    open_set.add(neighbor)
    
    return [(start_x, start_y)]  # Return start position if no path found

def get_nearest_resource(x: int, y: int, resource_type: str) -> Tuple[int, int]:
    """Find nearest resource of given type."""
    resources = database.get_resources_in_range(x, y, GRID_SIZE)
    if not resources:
        return None
    return min([(r['x'], r['y']) for r in resources if r['resource_type'] == resource_type],
               key=lambda pos: manhattan_distance(x, y, pos[0], pos[1]), default=None)

def get_nearest_agent(x: int, y: int, exclude_id: int) -> Tuple[int, int]:
    """Find nearest agent excluding self."""
    agents = database.get_agent_positions()
    return min([(a['x'], a['y']) for a in agents if a['id'] != exclude_id],
               key=lambda pos: manhattan_distance(x, y, pos[0], pos[1]), default=None)

def update_agent_state(agent_id: int, x: int, y: int, energy: int):
    """Update agent position and energy safely."""
    safe_execute(
        "UPDATE agents SET x=?, y=?, energy=? WHERE id=?",
        (x, y, max(0, min(100, energy)), agent_id)
    )

def process_agent_goals(agent_id: int, x: int, y: int, energy: int) -> Tuple[int, int, int]:
    """Process agent goals and return new position and energy."""
    goals = database.get_agent_goals(agent_id)
    if not goals:
        # No goals - set exploration goal
        target_x = random.randint(0, GRID_SIZE-1)
        target_y = random.randint(0, GRID_SIZE-1)
        database.set_agent_goal(agent_id, GoalType.EXPLORE,
                              {"x": target_x, "y": target_y}, priority=1)
        return x, y, energy
    
    goal = goals[0]  # Get highest priority goal
    goal_data = json.loads(goal['target_data'])
    
    if goal['goal_type'] == GoalType.GATHER:
        # Find path to resource
        target = get_nearest_resource(x, y, goal_data['resource_type'])
        if not target:
            return x, y, energy - 1
        
        path = get_path(x, y, target[0], target[1])
        if len(path) > 1:
            next_x, next_y = path[1]
            return next_x, next_y, energy - 2
            
    elif goal['goal_type'] == GoalType.EXPLORE:
        # Move toward exploration target
        target_x = goal_data['x']
        target_y = goal_data['y']
        if manhattan_distance(x, y, target_x, target_y) <= 1:
            # Reached target - clear goal
            database.clear_agent_goal(agent_id, goal['id'])
            return x, y, energy - 1
            
        path = get_path(x, y, target_x, target_y)
        if len(path) > 1:
            next_x, next_y = path[1]
            return next_x, next_y, energy - 1
            
    elif goal['goal_type'] == GoalType.SOCIALIZE:
        # Find path to target agent
        target = get_nearest_agent(x, y, agent_id)
        if not target:
            return x, y, energy - 1
            
        path = get_path(x, y, target[0], target[1])
        if len(path) > 1:
            next_x, next_y = path[1]
            if manhattan_distance(next_x, next_y, target[0], target[1]) <= 1:
                # Close enough to interact
                target_id = database.get_agent_at(target[0], target[1])['id']
                interact_with_agent(agent_id, target_id)
            return next_x, next_y, energy - 1
            
    elif goal['goal_type'] == GoalType.REST:
        # Stay put and regain energy
        if energy >= 90:
            database.clear_agent_goal(agent_id, goal['id'])
        return x, y, min(100, energy + 5)
    
    return x, y, energy - 1

def interact_with_agent(agent_id: int, target_id: int):
    """Handle agent interaction and relationship updates."""
    # Get current relationship and status
    rel = database.get_relationship(agent_id, target_id)
    strength = rel['strength'] if rel else 0
    agent_status = database.get_agent_status(agent_id)
    target_status = database.get_agent_status(target_id)
    
    # Social class influences interaction
    class_diff = get_class_value(agent_status['social_class']) - get_class_value(target_status['social_class'])
    
    # Random interaction outcome, influenced by social factors
    base_chance = 0.6 + (strength * 0.2)  # Relationship influence
    class_modifier = -0.1 * abs(class_diff)  # Class difference penalty
    prestige_bonus = min(0.1, (agent_status['prestige'] + target_status['prestige']) / 1000)
    
    success_chance = max(0.1, min(0.9, base_chance + class_modifier + prestige_bonus))
    success = random.random() < success_chance
    
    # Update relationship based on interaction outcome
    outcome = random.uniform(0.1, 0.3) if success else random.uniform(-0.3, -0.1)
    new_strength = max(-1, min(1, strength + outcome))
    
    rel_type = get_relationship_type(new_strength, agent_status, target_status)
    database.set_relationship(agent_id, target_id, rel_type, new_strength)
    
    # Update social metrics
    prestige_change = random.randint(1, 3) if success else random.randint(-2, -1)
    database.update_agent_status(agent_id, prestige_delta=prestige_change)
    
    # Possible trade opportunity
    if success and random.random() < 0.3:
        initiate_trade(agent_id, target_id)
    
    # Add memory
    memory_data = {
        "target_id": target_id,
        "outcome": "positive" if success else "negative",
        "strength_change": outcome,
        "prestige_change": prestige_change
    }
    database.add_memory(agent_id, MemoryType.INTERACTION, memory_data)
    
    # Maybe form or join group
    consider_group_formation(agent_id, target_id, new_strength)

def get_class_value(social_class: str) -> int:
    """Convert social class to numeric value for comparison."""
    return {
        SocialClass.PEASANT: 0,
        SocialClass.MERCHANT: 1,
        SocialClass.NOBLE: 2,
        SocialClass.RULER: 3
    }.get(social_class, 0)

def get_relationship_type(strength: float, agent_status: dict, target_status: dict) -> str:
    """Determine relationship type based on strength and social factors."""
    if strength > 0.7:
        return RelationType.FAMILY
    elif strength > 0.3:
        return RelationType.FRIEND
    elif agent_status['prestige'] > target_status['prestige'] * 1.5:
        return RelationType.LEADER
    elif target_status['prestige'] > agent_status['prestige'] * 1.5:
        return RelationType.FOLLOWER
    else:
        return RelationType.NEUTRAL

def initiate_trade(agent_id: int, target_id: int):
    """Attempt to conduct trade between agents."""
    agent_status = database.get_agent_status(agent_id)
    target_status = database.get_agent_status(target_id)
    
    # Determine trade type and amount
    trade_type = random.choice([TradeType.FOOD, TradeType.LABOR, TradeType.KNOWLEDGE])
    base_amount = random.randint(1, 5)
    amount = base_amount * (1 + (agent_status['prestige'] / 100))
    
    # Trade success chance based on wealth and prestige
    success_chance = 0.5 + (min(agent_status['wealth'], target_status['wealth']) / 100)
    success = random.random() < success_chance
    
    if success:
        # Update wealth
        wealth_change = random.randint(1, amount)
        database.update_agent_status(agent_id, wealth_delta=wealth_change)
        database.update_agent_status(target_id, wealth_delta=wealth_change)
    
    # Record trade
    database.record_trade(agent_id, target_id, trade_type, amount, success)

def consider_group_formation(agent_id: int, target_id: int, relationship_strength: float):
    """Consider forming or joining groups based on social bonds."""
    if relationship_strength < 0.5:
        return
        
    agent_status = database.get_agent_status(agent_id)
    target_status = database.get_agent_status(target_id)
    
    # Get existing groups
    agent_groups = database.get_agent_groups(agent_id)
    target_groups = database.get_agent_groups(target_id)
    
    # Consider forming family group
    if relationship_strength > 0.8 and not any(g['group_type'] == GroupType.FAMILY for g in agent_groups):
        leader_id = agent_id if agent_status['prestige'] > target_status['prestige'] else target_id
        follower_id = target_id if leader_id == agent_id else agent_id
        
        group_id = database.create_group(f"Family-{random.randint(1000,9999)}",
                                       GroupType.FAMILY, leader_id,
                                       *database.get_agent_position(leader_id))
        database.add_group_member(group_id, follower_id, "member")
        
    # Consider forming/joining village
    elif relationship_strength > 0.6:
        # Look for existing village to join
        village = next((g for g in target_groups if g['group_type'] == GroupType.VILLAGE), None)
        if village and not any(g['group_type'] == GroupType.VILLAGE for g in agent_groups):
            database.add_group_member(village['id'], agent_id, "member")
        # Or maybe start new village
        elif not village and agent_status['prestige'] > 50:
            database.create_group(f"Village-{random.randint(1000,9999)}",
                                GroupType.VILLAGE, agent_id,
                                *database.get_agent_position(agent_id))
            database.add_group_member(group_id, target_id, "member")

def safe_execute(query, params=(), retries=5, wait=0.3):
    """Execute a write query with retries on SQLITE_BUSY/locked."""
    for i in range(retries):
        try:
            conn = database.connect(); cur = conn.cursor()
            cur.execute(query, params)
            conn.commit(); conn.close()
            return
        except Exception as e:
            msg = str(e).lower()
            if 'locked' in msg or 'busy' in msg:
                time.sleep(wait)
                continue
            raise
    raise Exception("Database locked too long, aborting")

def init_sim():
    database.init_db()
    database.seed_agents(n=20, grid=GRID_SIZE)

def update_environment():
    """Update environment state (weather, season, day phase)."""
    current = database.get_current_environment()
    
    if not current or (datetime.now() - datetime.strptime(current['timestamp'], "%Y-%m-%d %H:%M:%S")).seconds > 3600:
        # Change every hour
        weather = random.choice([Weather.CLEAR] * 6 + [Weather.RAIN] * 3 + [Weather.STORM])
        season = Season.SUMMER if datetime.now().month in [5,6,7,8,9,10] else Season.WINTER
        
        hour = datetime.now().hour
        if 5 <= hour < 8:
            day_phase = DayPhase.DAWN
        elif 8 <= hour < 18:
            day_phase = DayPhase.DAY
        elif 18 <= hour < 21:
            day_phase = DayPhase.DUSK
        else:
            day_phase = DayPhase.NIGHT
            
        effects = {
            "move_cost": 1.5 if weather == Weather.STORM else 1.2 if weather == Weather.RAIN else 1.0,
            "visibility": 3 if weather == Weather.STORM else 5 if weather == Weather.RAIN else GRID_SIZE,
            "energy_drain": 2 if season == Season.WINTER else 1,
            "resource_growth": 0.5 if season == Season.WINTER else 1.5
        }
        
        database.set_environment(weather, season, day_phase, effects)
        return effects
    return json.loads(current['effects'])

def update_resources():
    """Update resource amounts and spawn new resources."""
    env_effects = update_environment()
    growth_rate = env_effects['resource_growth']
    
    # Update existing resources
    conn = database.connect(); c = conn.cursor()
    c.execute("SELECT * FROM resources")
    resources = c.fetchall()
    conn.close()
    
    for r in resources:
        if r['amount'] <= 0:
            database.remove_resource(r['id'])
        elif r['resource_type'] == ResourceType.FOOD:
            # Food grows slowly
            if random.random() < 0.1 * growth_rate:
                database.update_resource(r['x'], r['y'], 1)
    
    # Spawn new resources
    if len(resources) < GRID_SIZE * GRID_SIZE / 4:  # Keep 25% density
        x = random.randint(0, GRID_SIZE-1)
        y = random.randint(0, GRID_SIZE-1)
        if not any(r['x'] == x and r['y'] == y for r in resources):
            resource_type = random.choice([ResourceType.FOOD] * 3 + [ResourceType.WATER] * 2)
            database.add_resource(x, y, resource_type, random.randint(5, 15))

def step():
    """Main simulation step."""
    # Update environment and resources
    env_effects = update_environment()
    update_resources()
    
    # Process all agents
    conn = database.connect(); c = conn.cursor()
    c.execute("SELECT id, x, y, energy FROM agents")
    rows = c.fetchall()
    events = []
    
    for aid, x, y, energy in rows:
        # Skip dead agents
        if energy <= 0:
            continue
            
        # Process goals and get new position/energy
        nx, ny, new_energy = process_agent_goals(aid, x, y, energy)
        
        # Apply environmental effects
        move_cost = env_effects['move_cost']
        energy_drain = env_effects['energy_drain']
        if manhattan_distance(x, y, nx, ny) > 0:
            new_energy -= math.ceil(move_cost)  # Extra cost for movement
        new_energy -= energy_drain  # Base drain
        
        # Apply position and energy updates
        update_agent_state(aid, nx, ny, new_energy)
        
        # Handle special states
        if new_energy <= 20 and not any(g['goal_type'] == GoalType.REST 
                                     for g in database.get_agent_goals(aid)):
            # Low energy - set rest goal
            database.set_agent_goal(aid, GoalType.REST, {}, priority=10)
            events.append(f"Agent {aid} is tired and needs rest")
            
        elif new_energy <= 0:
            events.append(f"Agent {aid} collapsed (energy 0) at ({nx},{ny})")
            
        elif new_energy >= 90 and energy < 90:
            events.append(f"Agent {aid} is fully energized at ({nx},{ny})")
            
        # Random chance to start social interaction
        if random.random() < 0.1 and new_energy > 50:
            target = get_nearest_agent(nx, ny, aid)
            if target and manhattan_distance(nx, ny, target[0], target[1]) <= 3:
                database.set_agent_goal(aid, GoalType.SOCIALIZE, 
                                      {"target_x": target[0], "target_y": target[1]},
                                      priority=3)
    
    # Update metrics
    c.execute("SELECT energy FROM agents WHERE energy > 0")
    energies = [e for (e,) in c.fetchall()]
    pop = len(energies)
    avg_energy = round(sum(energies)/pop, 2) if pop else 0
    conn.close()
    
    # Log events
    for e in events:
        try:
            database.log_event(e)
        except Exception:
            pass
            
    database.push_metric(pop, avg_energy)

def get_positions():
    conn = database.connect(); c = conn.cursor()
    c.execute("SELECT id, name, x, y, energy FROM agents")
    data = [{"id":i, "name":n, "x":x, "y":y, "energy":e} for i,n,x,y,e in c.fetchall()]
    conn.close(); return {"grid": GRID_SIZE, "agents": data}

def list_agents():
    conn = database.connect(); c = conn.cursor()
    c.execute("SELECT id, name, age, energy, role, status FROM agents")
    rows = [{"id":i,"name":n,"age":a,"energy":e,"role":r,"status":s} for i,n,a,e,r,s in c.fetchall()]
    conn.close(); return rows
