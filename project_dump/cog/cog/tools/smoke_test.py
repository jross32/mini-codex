import os, sys
sys.path.append(r"c:\Users\dmjr2\cog")
import database, simulation

print('DB file:', os.path.join(os.path.dirname(database.__file__), 'cognitia.db'))
database.init_db()
print('Initialized DB')
database.seed_agents(n=5, grid=6)
print('Seeded agents')
print('Agent list before step count:', len(simulation.list_agents()))
simulation.step()
print('Performed one simulation step')
print('Agent list after step count:', len(simulation.list_agents()))
print('Metrics (latest 3):', [dict(r) for r in database.get_metrics(3)])
