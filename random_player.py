from player import player
import random as rd

class random_player(player):
    def __init__(self, name) -> None:
        super().__init__(name)
        
    def _select_move(self, sticks_list : list) -> int:
        return rd.randint(1, 3)