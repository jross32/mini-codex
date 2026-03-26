ROLES = {'zookeeper': 2400, 'vet': 4200, 'janitor': 1800, 'guide': 2200}

def morale_tick(morale, workload='normal'):
    decay = {'light': 1, 'normal': 2, 'heavy': 5, 'extreme': 10}.get(workload, 2)
    return max(0, morale - decay)

def get_salary(role):
    return ROLES.get(role, 2000)