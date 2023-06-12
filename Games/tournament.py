from abc import ABC, abstractstaticmethod
from Games.game import game
from Games.nim_game import nim_game
from Games.player import player

class tournament(ABC):
    def __init__(self, players : list[player], initial_state : int, game : game) -> None:
        self.players = players
        self.initial_state = initial_state
        self.game = game
    
    @abstractstaticmethod
    def create_matching():
        pass

class elimination(tournament):
    def __init__(self, players: list[player], initial_state: int, game: game) -> None:
        super().__init__(players, initial_state, game)
    
    def create_matching(self): #ver la paridad de la cantidad de jugadores
        game_list = []
        for k in range(0, len(self.players) - 1, 2):
            game_instace = self.game.copy()
            game_instace._players = [self.players[k], self.players[k + 1]]
            game_instace.config = self.initial_state
            game_list.append([game_instace, k])
        return [game_list, False] if len(game_list) > 1 else [game_list, True]
    
