"""RPG combat subsystem"""
class CombatSystem:
    def __init__(self, turn):
        self.turn = turn

    def next_turn(self):
        self.turn += 1
        return self.turn

