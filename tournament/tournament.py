from abc import ABC, abstractstaticmethod
from games.game import game
from games.player import player

class tournament(ABC):
    def __init__(self, players : list[player], initial_state : int, game : game) -> None:
        self.players = players
        self.initial_state = initial_state
        self.game = game
        self.round = None
    
    @abstractstaticmethod
    def create_matching():
        pass
    
    @abstractstaticmethod
    def get_winner():
        pass
    

class elimination(tournament):
    def __init__(self, players: list[player], initial_state: int, game: game) -> None:
        super().__init__(players, initial_state, game)
        self.round = True
        
    def create_matching(self): #ver la paridad de la cantidad de jugadores
        game_list = []
        for k in range(0, len(self.players) - 1, 2):
            game_instace = self.game.copy()
            game_instace._players = [self.players[k], self.players[k + 1]]
            game_instace.config = self.initial_state
            game_list.append([game_instace, k])
        return game_list 
    
    def get_winner(self):
        return self.players[0].name
    
class dosAdos(tournament):
    def __init__(self, players: list[player], initial_state: int, game: game) -> None:
        super().__init__(players, initial_state, game)
        self.round = False
        
    def create_matching(self): #ver la paridad de la cantidad de jugadores
        game_list = []
        for k in range(0, len(self.players) - 1):
            for l in range(k+1, len(self.players)):
                game_instace = self.game.copy()
                game_instace._players = [self.players[k], self.players[l]]
                game_instace.config = self.initial_state
                game_list.append([game_instace, k])
        return game_list #[game_list, False] if len(game_list) > 1 else [game_list, True]
    
    def get_winner(self):
        d = {}
        max = 0
        for i in self.players:
            if(i.name not in d):
                d[i.name] = 0
            d[i.name] += 1
        for i in d:
            if(d[i] > max):
                max = d[i]
                winner = i
        return winner
        