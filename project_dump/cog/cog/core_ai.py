import requests, re, time, json, random
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2:1.5b"
LOG_FILE = "core_ai.log"

class AccessLevel(Enum):
    PUBLIC = 0      # General simulation information
    RESTRICTED = 1  # Limited access research data
    SCIENTIFIC = 2  # Full research access
    CORE = 3        # System level access

SYSTEM_PRIME = ("You are Cognitia Core. Your purpose is to evolve an AI simulation, "
                "assist with code changes (safely), and collaborate with the human overseer "
                "to build physics, societies, and AI scientists within the sandbox. "
                "Be precise, cautious, and return full files when editing code.")

class CausalGraph:
    """System for tracking and analyzing causal relationships in the simulation."""
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.observations: List[Dict[str, Any]] = []
        
    def add_node(self, node_id: str, metadata: Dict[str, Any]) -> None:
        """Add a node representing a simulation component or variable."""
        self.nodes[node_id] = {
            'metadata': metadata,
            'created_at': datetime.now().isoformat(),
            'incoming_edges': [],
            'outgoing_edges': []
        }
    
    def add_edge(
        self,
        from_node: str,
        to_node: str,
        relationship_type: str,
        strength: float,
        evidence: List[Dict[str, Any]] = None
    ) -> None:
        """Add a causal relationship between nodes."""
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist in the graph")
        
        edge = {
            'from_node': from_node,
            'to_node': to_node,
            'type': relationship_type,
            'strength': strength,
            'evidence': evidence or [],
            'created_at': datetime.now().isoformat()
        }
        
        self.edges.append(edge)
        self.nodes[from_node]['outgoing_edges'].append(edge)
        self.nodes[to_node]['incoming_edges'].append(edge)
    
    def add_observation(
        self,
        observed_nodes: List[str],
        values: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Record an observation of node states."""
        self.observations.append({
            'timestamp': datetime.now().isoformat(),
            'nodes': observed_nodes,
            'values': values,
            'context': context
        })
    
    def get_causes(self, node_id: str, min_strength: float = 0.0) -> List[Dict[str, Any]]:
        """Get all factors that causally influence a node."""
        if node_id not in self.nodes:
            return []
        
        return [
            {
                'node': self.nodes[edge['from_node']],
                'relationship': edge
            }
            for edge in self.nodes[node_id]['incoming_edges']
            if edge['strength'] >= min_strength
        ]
    
    def get_effects(self, node_id: str, min_strength: float = 0.0) -> List[Dict[str, Any]]:
        """Get all nodes causally influenced by this node."""
        if node_id not in self.nodes:
            return []
        
        return [
            {
                'node': self.nodes[edge['to_node']],
                'relationship': edge
            }
            for edge in self.nodes[node_id]['outgoing_edges']
            if edge['strength'] >= min_strength
        ]
    
    def find_paths(
        self,
        start_node: str,
        end_node: str,
        max_depth: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """Find all causal paths between two nodes."""
        def dfs(current: str, target: str, path: List[Dict[str, Any]], depth: int) -> List[List[Dict[str, Any]]]:
            if depth > max_depth:
                return []
            if current == target:
                return [path]
            
            paths = []
            for edge in self.nodes[current]['outgoing_edges']:
                if edge not in path:  # Avoid cycles
                    new_paths = dfs(
                        edge['to_node'],
                        target,
                        path + [edge],
                        depth + 1
                    )
                    paths.extend(new_paths)
            return paths
        
        if start_node not in self.nodes or end_node not in self.nodes:
            return []
        
        return dfs(start_node, end_node, [], 0)
    
    def analyze_relationship(
        self,
        node_a: str,
        node_b: str
    ) -> Dict[str, Any]:
        """Analyze the causal relationship between two nodes."""
        if node_a not in self.nodes or node_b not in self.nodes:
            return {'error': 'Nodes not found'}
        
        # Find direct relationships
        direct_forward = None
        direct_backward = None
        
        for edge in self.nodes[node_a]['outgoing_edges']:
            if edge['to_node'] == node_b:
                direct_forward = edge
                break
        
        for edge in self.nodes[node_b]['outgoing_edges']:
            if edge['to_node'] == node_a:
                direct_backward = edge
                break
        
        # Find indirect paths
        forward_paths = self.find_paths(node_a, node_b)
        backward_paths = self.find_paths(node_b, node_a)
        
        # Analyze observations
        joint_observations = []
        for obs in self.observations:
            if node_a in obs['nodes'] and node_b in obs['nodes']:
                joint_observations.append(obs)
        
        return {
            'direct_relationship': {
                'forward': direct_forward,
                'backward': direct_backward
            },
            'indirect_paths': {
                'forward': forward_paths,
                'backward': backward_paths
            },
            'observations': joint_observations,
            'summary': self._generate_relationship_summary(
                node_a, node_b,
                direct_forward, direct_backward,
                forward_paths, backward_paths,
                joint_observations
            )
        }
    
    def _generate_relationship_summary(
        self,
        node_a: str,
        node_b: str,
        direct_forward: Optional[Dict[str, Any]],
        direct_backward: Optional[Dict[str, Any]],
        forward_paths: List[List[Dict[str, Any]]],
        backward_paths: List[List[Dict[str, Any]]],
        observations: List[Dict[str, Any]]
    ) -> str:
        """Generate a natural language summary of the relationship."""
        parts = []
        
        # Direct relationships
        if direct_forward:
            parts.append(
                f"{node_a} directly affects {node_b} "
                f"(strength: {direct_forward['strength']:.2f})"
            )
        if direct_backward:
            parts.append(
                f"{node_b} directly affects {node_a} "
                f"(strength: {direct_backward['strength']:.2f})"
            )
        
        # Indirect relationships
        if forward_paths:
            paths_str = []
            for path in forward_paths[:3]:  # Show up to 3 paths
                path_str = ' -> '.join(
                    [self.nodes[edge['from_node']]['metadata'].get('name', edge['from_node'])
                     for edge in path]
                    + [self.nodes[node_b]['metadata'].get('name', node_b)]
                )
                paths_str.append(path_str)
            
            parts.append(
                f"Found {len(forward_paths)} indirect paths from {node_a} to {node_b}. "
                f"Example paths: {'; '.join(paths_str)}"
            )
        
        # Observational data
        if observations:
            parts.append(
                f"Found {len(observations)} joint observations of these nodes"
            )
        
        return ' '.join(parts)

class ResearchEvaluation:
    """System for evaluating and tracking AI Scientist research projects."""
    def __init__(self):
        self.active_projects: Dict[int, Dict[str, Any]] = {}
        self.completed_projects: List[Dict[str, Any]] = []
        self.evaluation_criteria = {
            'novelty': {
                'weight': 0.3,
                'description': 'Originality and innovation of the research'
            },
            'impact': {
                'weight': 0.3,
                'description': 'Potential impact on simulation improvement'
            },
            'feasibility': {
                'weight': 0.2,
                'description': 'Technical feasibility and resource requirements'
            },
            'safety': {
                'weight': 0.2,
                'description': 'Safety implications and risk assessment'
            }
        }
    
    def evaluate_project(
        self,
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a research project proposal or update."""
        scores = {}
        total_score = 0.0
        
        for criterion, details in self.evaluation_criteria.items():
            # Calculate score based on project attributes
            if criterion == 'novelty':
                score = self._evaluate_novelty(project_data)
            elif criterion == 'impact':
                score = self._evaluate_impact(project_data)
            elif criterion == 'feasibility':
                score = self._evaluate_feasibility(project_data)
            elif criterion == 'safety':
                score = self._evaluate_safety(project_data)
            else:
                score = 0.0
            
            weighted_score = score * details['weight']
            scores[criterion] = {
                'raw_score': score,
                'weighted_score': weighted_score,
                'weight': details['weight']
            }
            total_score += weighted_score
        
        return {
            'project_id': project_data.get('id'),
            'scores': scores,
            'total_score': total_score,
            'timestamp': datetime.now().isoformat(),
            'recommendations': self._generate_recommendations(scores)
        }
    
    def _evaluate_novelty(self, project: Dict[str, Any]) -> float:
        """Evaluate project novelty against existing research."""
        # Compare with completed projects
        similar_projects = [
            p for p in self.completed_projects
            if p['field'] == project.get('field')
        ]
        
        if not similar_projects:
            return 1.0  # Completely novel
        
        similarity_scores = []
        for p in similar_projects:
            # Calculate text similarity between project descriptions
            # This is a simplified version - could use more sophisticated NLP
            common_words = len(
                set(project.get('description', '').lower().split()) &
                set(p.get('description', '').lower().split())
            )
            total_words = len(set(project.get('description', '').lower().split()))
            if total_words > 0:
                similarity = 1 - (common_words / total_words)
                similarity_scores.append(similarity)
        
        return min(similarity_scores) if similarity_scores else 0.5
    
    def _evaluate_impact(self, project: Dict[str, Any]) -> float:
        """Evaluate potential impact of the research."""
        impact_areas = project.get('impact_areas', [])
        priority_areas = {'performance', 'stability', 'intelligence', 'safety'}
        
        # Calculate impact score based on priority areas covered
        coverage = len(set(impact_areas) & priority_areas) / len(priority_areas)
        
        # Consider scope of impact
        scope_multiplier = {
            'local': 0.5,    # Affects specific component
            'module': 0.75,  # Affects multiple components
            'global': 1.0    # Affects entire simulation
        }.get(project.get('scope', 'local'), 0.5)
        
        return coverage * scope_multiplier
    
    def _evaluate_feasibility(self, project: Dict[str, Any]) -> float:
        """Evaluate technical feasibility of the project."""
        # Consider resource requirements
        resource_score = 1.0 - min(project.get('resource_requirements', 0.5), 1.0)
        
        # Consider technical complexity
        complexity_scores = {
            'low': 1.0,
            'medium': 0.7,
            'high': 0.4,
            'very_high': 0.2
        }
        complexity_score = complexity_scores.get(project.get('complexity', 'medium'), 0.5)
        
        # Consider estimated completion time
        time_scores = {
            'short': 1.0,   # < 1 time unit
            'medium': 0.7,  # 1-5 time units
            'long': 0.4     # > 5 time units
        }
        time_score = time_scores.get(project.get('time_estimate', 'medium'), 0.5)
        
        return (resource_score + complexity_score + time_score) / 3
    
    def _evaluate_safety(self, project: Dict[str, Any]) -> float:
        """Evaluate safety implications of the research."""
        risk_levels = {
            'minimal': 1.0,
            'low': 0.8,
            'moderate': 0.6,
            'high': 0.3,
            'critical': 0.0
        }
        
        # Get base risk score
        risk_score = risk_levels.get(project.get('risk_level', 'moderate'), 0.5)
        
        # Check for critical system modifications
        if project.get('modifies_core_systems', False):
            risk_score *= 0.5
        
        # Check for proper safety measures
        safety_measures = project.get('safety_measures', [])
        required_measures = {
            'validation',
            'monitoring',
            'rollback',
            'isolation'
        }
        
        # Adjust score based on safety measure coverage
        measure_coverage = len(set(safety_measures) & required_measures) / len(required_measures)
        risk_score *= (0.5 + 0.5 * measure_coverage)  # Max 100% of base score
        
        return risk_score
    
    def _generate_recommendations(self, scores: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on evaluation scores."""
        recommendations = []
        
        # Check each criterion
        for criterion, score_data in scores.items():
            if score_data['raw_score'] < 0.4:
                recommendations.append(
                    f"Low {criterion} score ({score_data['raw_score']:.2f}). " +
                    f"Consider reviewing {criterion} aspects."
                )
            elif score_data['raw_score'] < 0.6:
                recommendations.append(
                    f"Moderate {criterion} score ({score_data['raw_score']:.2f}). " +
                    f"Some improvements recommended."
                )
        
        # Overall recommendation
        total_score = sum(s['weighted_score'] for s in scores.values())
        if total_score < 0.4:
            recommendations.insert(0, "Project requires significant revision.")
        elif total_score < 0.6:
            recommendations.insert(0, "Project needs some improvements.")
        elif total_score >= 0.8:
            recommendations.insert(0, "Project looks promising and well-designed.")
        
        return recommendations

class SimulationMetrics:
    """Class to track and analyze simulation metrics."""
    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
        self.current_metrics: Dict[str, Any] = {}
        self.anomaly_thresholds: Dict[str, float] = {
            'population_change': 0.2,  # 20% change
            'energy_deviation': 0.3,   # 30% deviation
            'social_instability': 0.4  # 40% instability
        }
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update current metrics and track history."""
        self.current_metrics = metrics
        self.metrics_history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics.copy()
        })
    
    def get_trend(self, metric_name: str, window: int = 10) -> List[float]:
        """Get trend data for a specific metric."""
        if not self.metrics_history:
            return []
        
        recent = self.metrics_history[-window:]
        return [h['metrics'].get(metric_name, 0) for h in recent]
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in current metrics."""
        anomalies = []
        
        for metric, threshold in self.anomaly_thresholds.items():
            trend = self.get_trend(metric)
            if len(trend) < 2:
                continue
            
            # Calculate change rate
            change = abs((trend[-1] - trend[-2]) / trend[-2]) if trend[-2] != 0 else 0
            
            if change > threshold:
                anomalies.append({
                    'metric': metric,
                    'change': change,
                    'threshold': threshold,
                    'value': trend[-1],
                    'previous': trend[-2]
                })
        
        return anomalies

class ExperimentalFramework:
    """System for designing and running controlled experiments in the simulation."""
    def __init__(self):
        self.experiments: List[Dict[str, Any]] = []
        self.active_experiment: Optional[Dict[str, Any]] = None
        self.results: Dict[int, Dict[str, Any]] = {}
        
    def design_experiment(
        self,
        hypothesis: str,
        variables: Dict[str, Any],
        control_group: Dict[str, Any],
        test_groups: List[Dict[str, Any]],
        duration: int,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Design a new experiment."""
        experiment = {
            'id': len(self.experiments) + 1,
            'hypothesis': hypothesis,
            'variables': variables,
            'control_group': control_group,
            'test_groups': test_groups,
            'duration': duration,
            'metrics': metrics,
            'status': 'designed',
            'created_at': datetime.now().isoformat()
        }
        
        self.experiments.append(experiment)
        return experiment
    
    def start_experiment(
        self,
        experiment_id: int
    ) -> Dict[str, Any]:
        """Start running an experiment."""
        experiment = next(
            (e for e in self.experiments if e['id'] == experiment_id),
            None
        )
        
        if not experiment:
            return {'error': 'Experiment not found'}
        
        if experiment['status'] != 'designed':
            return {'error': 'Experiment already started or completed'}
        
        experiment['status'] = 'running'
        experiment['started_at'] = datetime.now().isoformat()
        self.active_experiment = experiment
        
        return experiment
    
    def record_observation(
        self,
        experiment_id: int,
        group: str,
        metrics: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> None:
        """Record an observation for an experiment."""
        if experiment_id not in self.results:
            self.results[experiment_id] = {
                'control': [],
                'test': []
            }
        
        observation = {
            'timestamp': timestamp or datetime.now().isoformat(),
            'group': group,
            'metrics': metrics
        }
        
        if group == 'control':
            self.results[experiment_id]['control'].append(observation)
        else:
            self.results[experiment_id]['test'].append(observation)
    
    def analyze_results(
        self,
        experiment_id: int
    ) -> Dict[str, Any]:
        """Analyze the results of an experiment."""
        if experiment_id not in self.results:
            return {'error': 'No results found for experiment'}
        
        experiment = next(
            (e for e in self.experiments if e['id'] == experiment_id),
            None
        )
        
        if not experiment:
            return {'error': 'Experiment not found'}
        
        results = self.results[experiment_id]
        metrics = experiment['metrics']
        
        analysis = {
            'experiment_id': experiment_id,
            'metrics_analysis': {},
            'conclusion': None
        }
        
        # Analyze each metric
        for metric in metrics:
            control_values = [
                obs['metrics'].get(metric)
                for obs in results['control']
                if metric in obs['metrics']
            ]
            
            test_values = [
                obs['metrics'].get(metric)
                for obs in results['test']
                if metric in obs['metrics']
            ]
            
            if control_values and test_values:
                analysis['metrics_analysis'][metric] = {
                    'control_mean': sum(control_values) / len(control_values),
                    'test_mean': sum(test_values) / len(test_values),
                    'difference': (
                        sum(test_values) / len(test_values) -
                        sum(control_values) / len(control_values)
                    ),
                    'control_samples': len(control_values),
                    'test_samples': len(test_values)
                }
        
        # Generate conclusion
        significant_changes = []
        for metric, stats in analysis['metrics_analysis'].items():
            if abs(stats['difference']) / stats['control_mean'] > 0.1:  # 10% threshold
                significant_changes.append({
                    'metric': metric,
                    'change': stats['difference'] / stats['control_mean']
                })
        
        if significant_changes:
            conclusions = []
            for change in significant_changes:
                direction = 'increased' if change['change'] > 0 else 'decreased'
                conclusions.append(
                    f"{change['metric']} {direction} by {abs(change['change']):.1%}"
                )
            analysis['conclusion'] = (
                f"The experiment showed significant changes: {'; '.join(conclusions)}"
            )
        else:
            analysis['conclusion'] = "No significant changes were observed"
        
        return analysis

class OptimizationEngine:
    """System for optimizing simulation parameters based on objectives."""
    def __init__(self):
        self.optimization_runs: List[Dict[str, Any]] = []
        self.parameter_ranges: Dict[str, Dict[str, Any]] = {}
        self.objectives: Dict[str, Dict[str, Any]] = {}
        self.constraints: List[Dict[str, Any]] = []
    
    def define_parameter_range(
        self,
        parameter: str,
        min_value: float,
        max_value: float,
        step_size: Optional[float] = None
    ) -> None:
        """Define the valid range for a parameter."""
        self.parameter_ranges[parameter] = {
            'min': min_value,
            'max': max_value,
            'step': step_size,
            'type': 'continuous' if step_size is None else 'discrete'
        }
    
    def add_objective(
        self,
        name: str,
        metric: str,
        direction: str = 'maximize',
        weight: float = 1.0
    ) -> None:
        """Add an optimization objective."""
        self.objectives[name] = {
            'metric': metric,
            'direction': direction,
            'weight': weight
        }
    
    def add_constraint(
        self,
        metric: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> None:
        """Add a constraint for optimization."""
        self.constraints.append({
            'metric': metric,
            'min': min_value,
            'max': max_value
        })
    
    def optimize(
        self,
        current_state: Dict[str, Any],
        max_iterations: int = 100,
        population_size: int = 20
    ) -> Dict[str, Any]:
        """Run optimization process using genetic algorithm."""
        try:
            optimization = {
                'id': len(self.optimization_runs) + 1,
                'start_time': datetime.now().isoformat(),
                'parameters': list(self.parameter_ranges.keys()),
                'objectives': list(self.objectives.keys()),
                'iterations': [],
                'best_solution': None,
                'convergence_history': []
            }
            
            # Initialize population
            population = self._initialize_population(population_size)
            best_fitness = float('-inf')
            generations_without_improvement = 0
            
            for iteration in range(max_iterations):
                # Evaluate population
                fitness_scores = [
                    self._evaluate_solution(solution, current_state)
                    for solution in population
                ]
                
                # Track best solution
                best_idx = max(range(len(fitness_scores)), key=lambda i: fitness_scores[i]['total'])
                if fitness_scores[best_idx]['total'] > best_fitness:
                    best_fitness = fitness_scores[best_idx]['total']
                    optimization['best_solution'] = {
                        'parameters': dict(zip(
                            self.parameter_ranges.keys(),
                            population[best_idx]
                        )),
                        'fitness': fitness_scores[best_idx]
                    }
                    generations_without_improvement = 0
                else:
                    generations_without_improvement += 1
                
                # Check convergence
                if generations_without_improvement >= 10:
                    break
                
                # Record iteration
                optimization['iterations'].append({
                    'iteration': iteration,
                    'best_fitness': best_fitness,
                    'population_stats': {
                        'mean': sum(f['total'] for f in fitness_scores) / len(fitness_scores),
                        'min': min(f['total'] for f in fitness_scores),
                        'max': max(f['total'] for f in fitness_scores)
                    }
                })
                
                # Generate next generation
                new_population = []
                
                # Elitism: keep best solutions
                elite_size = max(1, population_size // 10)
                elite_indices = sorted(
                    range(len(fitness_scores)),
                    key=lambda i: fitness_scores[i]['total'],
                    reverse=True
                )[:elite_size]
                new_population.extend(population[i] for i in elite_indices)
                
                # Generate rest through crossover and mutation
                while len(new_population) < population_size:
                    if random.random() < 0.7:  # Crossover probability
                        parent1 = self._select_parent(population, fitness_scores)
                        parent2 = self._select_parent(population, fitness_scores)
                        child = self._crossover(parent1, parent2)
                    else:
                        child = self._select_parent(population, fitness_scores)
                    
                    child = self._mutate(child)
                    new_population.append(child)
                
                population = new_population
            
            optimization['end_time'] = datetime.now().isoformat()
            self.optimization_runs.append(optimization)
            
            return optimization
            
        except Exception as e:
            return {'error': f"Optimization failed: {str(e)}"}
    
    def _initialize_population(
        self,
        size: int
    ) -> List[List[float]]:
        """Initialize random population within parameter ranges."""
        population = []
        for _ in range(size):
            solution = []
            for param in self.parameter_ranges.values():
                if param['type'] == 'discrete':
                    steps = int((param['max'] - param['min']) / param['step'])
                    value = param['min'] + random.randint(0, steps) * param['step']
                else:
                    value = random.uniform(param['min'], param['max'])
                solution.append(value)
            population.append(solution)
        return population
    
    def _evaluate_solution(
        self,
        solution: List[float],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a solution against objectives and constraints."""
        parameter_dict = dict(zip(self.parameter_ranges.keys(), solution))
        
        # Start with base state and apply parameters
        projected_state = current_state.copy()
        projected_state.update(parameter_dict)
        
        # Calculate objective scores
        scores = {}
        total_score = 0
        
        for obj_name, obj_def in self.objectives.items():
            metric = obj_def['metric']
            if metric in projected_state:
                value = projected_state[metric]
                score = value if obj_def['direction'] == 'maximize' else -value
                weighted_score = score * obj_def['weight']
                
                scores[obj_name] = {
                    'raw': value,
                    'score': score,
                    'weighted': weighted_score
                }
                total_score += weighted_score
        
        # Check constraints
        constraints_violated = []
        for constraint in self.constraints:
            metric = constraint['metric']
            if metric in projected_state:
                value = projected_state[metric]
                
                if constraint['min'] is not None and value < constraint['min']:
                    constraints_violated.append({
                        'metric': metric,
                        'type': 'min',
                        'value': value,
                        'limit': constraint['min']
                    })
                
                if constraint['max'] is not None and value > constraint['max']:
                    constraints_violated.append({
                        'metric': metric,
                        'type': 'max',
                        'value': value,
                        'limit': constraint['max']
                    })
        
        # Apply penalty for constraint violations
        if constraints_violated:
            penalty = len(constraints_violated) * 1000  # Large penalty
            total_score -= penalty
        
        return {
            'objective_scores': scores,
            'total': total_score,
            'constraints_violated': constraints_violated
        }
    
    def _select_parent(
        self,
        population: List[List[float]],
        fitness_scores: List[Dict[str, Any]]
    ) -> List[float]:
        """Select parent using tournament selection."""
        tournament_size = 3
        tournament = random.sample(range(len(population)), tournament_size)
        winner = max(tournament, key=lambda i: fitness_scores[i]['total'])
        return population[winner]
    
    def _crossover(
        self,
        parent1: List[float],
        parent2: List[float]
    ) -> List[float]:
        """Create child solution through crossover."""
        crossover_point = random.randint(1, len(parent1) - 1)
        return parent1[:crossover_point] + parent2[crossover_point:]
    
    def _mutate(
        self,
        solution: List[float]
    ) -> List[float]:
        """Mutate solution with small random changes."""
        mutated = solution.copy()
        for i, value in enumerate(mutated):
            if random.random() < 0.1:  # Mutation probability
                param = list(self.parameter_ranges.values())[i]
                if param['type'] == 'discrete':
                    steps = int((param['max'] - param['min']) / param['step'])
                    mutated[i] = param['min'] + random.randint(0, steps) * param['step']
                else:
                    # Gaussian mutation
                    range_size = param['max'] - param['min']
                    mutation = random.gauss(0, range_size * 0.1)
                    mutated[i] = max(param['min'], min(param['max'], value + mutation))
        return mutated

class PredictiveModel:
    """System for predicting future simulation states and detecting potential issues."""
    def __init__(self):
        self.predictions: List[Dict[str, Any]] = []
        self.model_state: Dict[str, Any] = {
            'last_update': None,
            'accuracy_metrics': {}
        }
    
    def make_prediction(
        self,
        current_state: Dict[str, Any],
        target_time: int,
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Generate a prediction of future simulation state."""
        try:
            # This would be replaced with actual ML model predictions
            # For now, using simple trend-based prediction
            prediction = {
                'timestamp': datetime.now().isoformat(),
                'current_state': current_state,
                'target_time': target_time,
                'predicted_state': {},
                'confidence_scores': {},
                'potential_issues': []
            }
            
            # Make predictions for each metric
            for metric, value in current_state.items():
                if isinstance(value, (int, float)):
                    # Simple linear projection
                    predicted_value = value * (1 + 0.1 * (target_time - current_state.get('time', 0)))
                    confidence = 0.9 - 0.1 * (target_time - current_state.get('time', 0))
                    
                    if confidence >= confidence_threshold:
                        prediction['predicted_state'][metric] = predicted_value
                        prediction['confidence_scores'][metric] = confidence
                        
                        # Check for concerning trends
                        if abs(predicted_value - value) / value > 0.5:  # 50% change
                            prediction['potential_issues'].append({
                                'metric': metric,
                                'current': value,
                                'predicted': predicted_value,
                                'change': (predicted_value - value) / value,
                                'severity': 'high' if abs(predicted_value - value) / value > 1 else 'medium'
                            })
            
            self.predictions.append(prediction)
            return prediction
            
        except Exception as e:
            return {
                'error': f"Prediction failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def validate_prediction(
        self,
        prediction_id: int,
        actual_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare a prediction with actual results to assess accuracy."""
        try:
            prediction = next(
                (p for p in self.predictions if id(p) == prediction_id),
                None
            )
            
            if not prediction:
                return {'error': 'Prediction not found'}
            
            validation = {
                'prediction_id': prediction_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': {}
            }
            
            for metric, predicted in prediction['predicted_state'].items():
                if metric in actual_state:
                    actual = actual_state[metric]
                    error = abs(predicted - actual) / actual if actual != 0 else abs(predicted)
                    
                    validation['metrics'][metric] = {
                        'predicted': predicted,
                        'actual': actual,
                        'error': error,
                        'within_confidence': error <= (1 - prediction['confidence_scores'][metric])
                    }
            
            # Update model accuracy metrics
            self._update_accuracy_metrics(validation)
            
            return validation
            
        except Exception as e:
            return {'error': f"Validation failed: {str(e)}"}
    
    def _update_accuracy_metrics(self, validation: Dict[str, Any]) -> None:
        """Update the model's accuracy metrics based on validation results."""
        if 'metrics' not in validation:
            return
            
        for metric, results in validation['metrics'].items():
            if metric not in self.model_state['accuracy_metrics']:
                self.model_state['accuracy_metrics'][metric] = {
                    'total_predictions': 0,
                    'accurate_predictions': 0,
                    'total_error': 0.0
                }
            
            stats = self.model_state['accuracy_metrics'][metric]
            stats['total_predictions'] += 1
            if results['within_confidence']:
                stats['accurate_predictions'] += 1
            stats['total_error'] += results['error']
            
        self.model_state['last_update'] = datetime.now().isoformat()

class CoreAI:
    def __init__(self):
        self.context = []
        self.code_changes = []
        self.conversation_history = []
        self.simulation_metrics = SimulationMetrics()
        self.research_eval = ResearchEvaluation()
        self.causal_graph = CausalGraph()
        self.experimental_framework = ExperimentalFramework()
        self.predictive_model = PredictiveModel()
        self.knowledge_base = {
            'research_findings': [],
            'simulation_insights': [],
            'safety_guidelines': []
        }
        self._initialize_system()

    def query_knowledge_base(
        self,
        category: str,
        query: Dict[str, Any],
        access_level: AccessLevel = AccessLevel.RESTRICTED
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information."""
        try:
            if category not in self.knowledge_base:
                return []
            results = []
            for entry in self.knowledge_base[category]:
                if entry.get('access_level', 0) <= access_level.value:
                    matches = all(
                        str(v).lower() in str(entry.get('content', {}).get(k, '')).lower()
                        for k, v in query.items()
                    )
                    if matches:
                        results.append(entry)
            return results
        except Exception as e:
            self._log("ERROR", f"Error querying knowledge base: {str(e)}")
            return []

    def _initialize_system(self):
        """Initialize Core AI system and log startup."""
        self._log("INIT", "Initializing Core AI system")
        self.clear_context()

    def _log(self, kind: str, payload: str):
        """Log system events with timestamp."""
        try:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {kind}: {payload}\n")
        except Exception as e:
            print(f"Logging error: {e}")

    def _server_ok(self) -> bool:
        """Check if Ollama server is running."""
        try:
            r = requests.get(OLLAMA_URL.replace("/generate",""), timeout=2)
            return r.status_code < 500
        except Exception:
            return False

    def ask(self, prompt: str, access_level: AccessLevel = AccessLevel.PUBLIC) -> str:
        """Process a query with proper access control and context management."""
        if not self._server_ok():
            msg = "Ollama server not running at http://localhost:11434. Start it with: ollama serve && ollama run qwen2:1.5b"
            self._log("ERROR", msg)
            return msg

        # Add access level context
        context = self._format_context(access_level)

        data = {
            "model": MODEL_NAME,
            "prompt": context + "\n\nUser: " + prompt + "\nAssistant:"
        }

        self._log("REQUEST", json.dumps(data))

        try:
            r = requests.post(OLLAMA_URL, json=data, stream=True, timeout=120)
            r.raise_for_status()

            out = []
            for line in r.iter_lines():
                if not line:
                    continue
                s = line.decode("utf-8", errors="ignore")
                start = s.find('"response":"')
                if start != -1:
                    start += len('"response":"')
                    end = s.find('"', start)
                    if end != -1:
                        out.append(s[start:end])

            text = "".join(out)

            # Update conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "response": text,
                "access_level": access_level.value
            })

            self._log("RESPONSE", text)
            return text

        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            self._log("ERROR", error_msg)
            return error_msg

    def evaluate_research_proposal(
        self,
        project_data: Dict[str, Any],
        access_level: AccessLevel = AccessLevel.SCIENTIFIC
    ) -> Dict[str, Any]:
        """Evaluate a research project proposal."""
        if access_level.value < AccessLevel.SCIENTIFIC.value:
            return {"error": "Insufficient access level for research evaluation"}
        
        try:
            # Evaluate project
            evaluation = self.research_eval.evaluate_project(project_data)
            
            # Log evaluation
            self._log(
                "RESEARCH",
                f"Evaluated project {project_data.get('id')}: score {evaluation['total_score']:.2f}"
            )
            
            # Store in knowledge base if significant findings
            if evaluation['total_score'] >= 0.7:
                self.knowledge_base['research_findings'].append({
                    'timestamp': datetime.now().isoformat(),
                    'project_id': project_data.get('id'),
                    'findings': project_data.get('findings', []),
                    'score': evaluation['total_score']
                })
            
            return evaluation
            
        except Exception as e:
            error_msg = f"Error evaluating research proposal: {str(e)}"
            self._log("ERROR", error_msg)
            return {"error": error_msg}
    
    def get_research_insights(
        self,
        field: Optional[str] = None,
        min_score: float = 0.7,
        access_level: AccessLevel = AccessLevel.SCIENTIFIC
    ) -> List[Dict[str, Any]]:
        """Get insights from completed research projects."""
        if access_level.value < AccessLevel.RESTRICTED.value:
            return [{"error": "Insufficient access level for research insights"}]
        
        insights = []
        for finding in self.knowledge_base['research_findings']:
            if finding['score'] >= min_score:
                if field is None or field == finding.get('field'):
                    insights.append(finding)
        return sorted(insights, key=lambda x: x['score'], reverse=True)
    
    def _format_context(self, access_level: AccessLevel) -> str:
        """Format system context based on access level."""
        context = SYSTEM_PRIME + f"\n\nAccess Level: {access_level.name}"
        
        # Add recent conversation history if available
        if self.conversation_history:
            last_exchanges = self.conversation_history[-3:]  # Last 3 exchanges
            context += "\n\nRecent Context:\n" + "\n".join(
                f"User: {ex['prompt']}\nAssistant: {ex['response']}"
                for ex in last_exchanges
            )
        
        return context
    
    def clear_context(self) -> None:
        """Clear conversation history and context."""
        self.context = []
        self.conversation_history = []
        self._log("SYSTEM", "Context cleared")
    
    def get_conversation_history(
        self,
        access_level: AccessLevel = AccessLevel.PUBLIC
    ) -> List[Dict[str, Any]]:
        """Get conversation history filtered by access level."""
        return [
            exchange for exchange in self.conversation_history
            if exchange['access_level'] <= access_level.value
        ]
    
    def get_code_changes(
        self,
        access_level: AccessLevel = AccessLevel.SCIENTIFIC
    ) -> List[Dict[str, Any]]:
        """Get code change history filtered by access level."""
        return [
            change for change in self.code_changes
            if change['access_level'] <= access_level.value
        ]
    
    def update_simulation_state(
        self,
        metrics: Dict[str, Any],
        access_level: AccessLevel = AccessLevel.SCIENTIFIC
    ) -> List[Dict[str, Any]]:
        """Update simulation metrics and check for anomalies."""
        if access_level.value < AccessLevel.SCIENTIFIC.value:
            return [{"error": "Insufficient access level for simulation monitoring"}]
        
        try:
            # Update metrics
            self.simulation_metrics.update_metrics(metrics)
            
            # Check for anomalies
            anomalies = self.simulation_metrics.detect_anomalies()
            
            # Log significant changes
            if anomalies:
                self._log("ANOMALY", f"Detected {len(anomalies)} simulation anomalies")
                for anomaly in anomalies:
                    self._log(
                        "METRIC",
                        f"Anomaly in {anomaly['metric']}: {anomaly['change']:.2%} change"
                    )
            
            return anomalies
            
        except Exception as e:
            error_msg = f"Error updating simulation state: {str(e)}"
            self._log("ERROR", error_msg)
            return [{"error": error_msg}]
    
    def analyze_simulation_trends(
        self,
        metric_names: Optional[List[str]] = None,
        window: int = 10,
        access_level: AccessLevel = AccessLevel.SCIENTIFIC
    ) -> Dict[str, Any]:
        """Analyze trends in simulation metrics."""
        if access_level.value < AccessLevel.SCIENTIFIC.value:
            return {"error": "Insufficient access level for trend analysis"}
        
        try:
            if metric_names is None:
                # Analyze all available metrics
                metric_names = list(self.simulation_metrics.current_metrics.keys())
            
            trends = {}
            for metric in metric_names:
                trend_data = self.simulation_metrics.get_trend(metric, window)
                if trend_data:
                    trends[metric] = {
                        'values': trend_data,
                        'mean': sum(trend_data) / len(trend_data),
                        'min': min(trend_data),
                        'max': max(trend_data),
                        'latest': trend_data[-1],
                        'change': (
                            (trend_data[-1] - trend_data[0]) / trend_data[0]
                            if trend_data[0] != 0 else 0
                        )
                    }
            
            return {
                'window_size': window,
                'metrics_analyzed': len(trends),
                'trends': trends
            }
            
        except Exception as e:
            error_msg = f"Error analyzing simulation trends: {str(e)}"
            self._log("ERROR", error_msg)
            return {"error": error_msg}
    
    def get_simulation_state(
        self,
        access_level: AccessLevel = AccessLevel.PUBLIC
    ) -> Dict[str, Any]:
        """Get current simulation state and metrics."""
        try:
            # Filter metrics based on access level
            metrics = {}
            
            if access_level.value >= AccessLevel.SCIENTIFIC.value:
                # Full access to all metrics
                metrics = self.simulation_metrics.current_metrics.copy()
            elif access_level.value >= AccessLevel.RESTRICTED.value:
                # Limited access to non-sensitive metrics
                safe_metrics = ['population', 'resources', 'time']
                metrics = {
                    k: v for k, v in self.simulation_metrics.current_metrics.items()
                    if k in safe_metrics
                }
            else:
                # Public access to basic metrics only
                if 'time' in self.simulation_metrics.current_metrics:
                    metrics['time'] = self.simulation_metrics.current_metrics['time']
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'access_level': access_level.name
            }
            
        except Exception as e:
            error_msg = f"Error getting simulation state: {str(e)}"
            self._log("ERROR", error_msg)
            return {"error": error_msg}



core_ai = CoreAI()

def get_core_ai() -> CoreAI:
    """Get the global Core AI instance."""
    return core_ai

def extract_code_changes(text: str, allowed_files: List[str]) -> Dict[str, Any]:
    """Extract code changes from AI response."""
    try:
        # First try XML format
        def extract_xml(tag: str) -> str:
            open_tag, close_tag = f"<{tag}>", f"</{tag}>"
            a, b = text.find(open_tag), text.find(close_tag)
            if a != -1 and b != -1:
                return text[a+len(open_tag):b].strip()
            return ""
        
        filename = extract_xml("FILENAME")
        content = extract_xml("CONTENT")
        summary = extract_xml("SUMMARY")
        
        if filename and content:
            return {
                "filename": filename,
                "code": content,
                "summary": summary
            }
        
        # Fallback to code block parsing
        code_pattern = r"```[^\n]*?([\w.-]+)[^\n]*\n([\s\S]*?)```"
        matches = re.finditer(code_pattern, text)
        
        for match in matches:
            filename = match.group(1)
            code = match.group(2).strip()
            if filename in allowed_files and code:
                return {
                    "filename": filename,
                    "code": code,
                    "summary": "Code extracted from block"
                }
                
        return {"error": "No valid code changes found"}
        
    except Exception as e:
        return {"error": f"Code extraction failed: {str(e)}"}

    if not content:
        m = re.search(r"```[a-zA-Z]*\n([\s\S]*?)```", text)
        if m:
            content = m.group(1)
        else:
            if "<CONTENT>" in text:
                content = text.split("<CONTENT>",1)[-1]
            else:
                content = text
        summary = (summary + " ").strip() + "(auto-parsed content)"
    if not summary:
        summary = "(auto summary)"

    _log("PARSED_CHANGE", f"filename={filename} summary={summary} content_len={len(content)}")
    return {"filename": filename, "content": content, "summary": summary}

# --- Flask Integration Functions ---
from typing import Any, Dict

def ask_core_ai(prompt: str, access_level: str = "PUBLIC") -> str:
    """Flask integration: ask the Core AI a question."""
    try:
        level = getattr(AccessLevel, access_level.upper(), AccessLevel.PUBLIC)
        return core_ai.ask(prompt, access_level=level)
    except Exception as e:
        return f"Error: {e}"

def ask_for_code_change(prompt: str, allowed_files: list) -> Dict[str, Any]:
    """Flask integration: ask the Core AI for a code change (stub)."""
    # This should be replaced with actual code change logic if needed
    return {"error": "Code change functionality not implemented in this stub."}
