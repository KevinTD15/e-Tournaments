from player import player
import random as rd

class optimal_player(player):
    def __init__(self, name) -> None:
        super().__init__(name)
        
    def _select_move(self, sticks_list : list) -> int:
        mod_4 = sticks_list.count(1) % 4
        return mod_4 if mod_4 % 4 != 0 else rd.randint(1, 3)