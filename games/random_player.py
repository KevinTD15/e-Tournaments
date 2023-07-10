from games.player import player
from games.play import random

class random_player(player):
    def __init__(self, name, game) -> None:
        super().__init__(name, game)
        
    def _select_move(self, state : list) -> int:
        random_play = random(state, self.game, self.hand)
        return random_play.create_play()
    
    