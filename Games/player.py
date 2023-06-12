from abc import ABC, abstractstaticmethod
from Games.play import *

class player(ABC):
    
    def __init__(self, name, game) -> None:
        self.name = name
        self.game = game
        self.points = 0
        self.hand = None
        
    @abstractstaticmethod
    def _select_move():
        pass