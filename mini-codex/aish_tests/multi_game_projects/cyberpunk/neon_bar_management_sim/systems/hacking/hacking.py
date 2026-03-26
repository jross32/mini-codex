"""Cyberpunk hacking subsystem"""
class HackingSystem:
    def __init__(self, risk):
        self.risk = risk

    def attempt(self):
        return {'success': True, 'risk': self.risk}

