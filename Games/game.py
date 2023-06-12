from abc import ABC, abstractstaticmethod
from Games.player import player

class game(ABC):
    def __init__(self, _players : list[player] = [], config : object = 0, current_player_init : int= 0, winner : str = ''):
        self._players = _players
        self.config = config
        self._end = False
        self._current_play = []
        self.winner = winner
        self._current_player_index = (current_player_init + 1) % 2
    
    @abstractstaticmethod
    def initialize():
        pass
    
    @abstractstaticmethod
    def _excecute_turn():
        pass 
    
    @abstractstaticmethod
    def copy():
        pass