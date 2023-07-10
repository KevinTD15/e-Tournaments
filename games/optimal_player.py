from games.player import player
from games.play import optimal
import random as rd

class optimal_player(player):
    def __init__(self, name, game) -> None:
        super().__init__(name, game)
        
    def _select_move(self, state : list) -> int:
        optimal_play = optimal(state, self.game, self.hand)
        return optimal_play.create_play()
    
    