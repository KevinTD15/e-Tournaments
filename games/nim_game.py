from games.game import game
from games.player import player

class nim_game(game):
    
    def __init__(self, _players: list[player] = [], config: object = 0, current_player_init: int = 0, winner: str = ''):
        super().__init__(_players, config, current_player_init, winner)
    
    def excecute_game(self):
        self.initialize()
        while(not self._end and self.winner == ''):
            self._excecute_turn()
    
    def _excecute_turn(self):
        if(self._start):
            self._start = False
            self._sticks_list = [1 for i in range(self.config)]
        else:
            if(self._current_player_index >= len(self._players)):
                self._current_player_index= 0
            current_player = self._players[self._current_player_index]
            
            move = current_player._select_move(self._sticks_list)
            
            self._update_sitcks_list(move)
            
            self._verify_sticks()
            
            if(self._end):
                self.winner = self._players[self._current_player_index].name
                self._current_play.append([self._players, self._current_player_index, move, self._sticks_list.count(1), self.winner])
                return
            else:
                self._current_play.append([self._players, self._current_player_index, move, self._sticks_list.count(1), ''])
                self._current_player_index += 1
                
    def _update_sitcks_list(self, move : int):        
        index = self._sticks_list.index(1)
        for i in range(index, index + move, 1):
            if(i == len(self._sticks_list)):
                return
            self._sticks_list[i] = 0
    
    def _verify_sticks(self):
        self._end = True if self._sticks_list.count(0) == self.config else False
        
    def initialize(self):
        self._sticks_list = [1 for i in range(self.config)]
        self._start = True
        
    def copy(self):
        return nim_game()
    
    def show_board(self):
        self._sticks_list = [1 for i in range(self.config)]
        x = self._current_player_index % 2
        print (f'Player 1: {self._players[0].name}, Player 2: {self._players[1].name} Current: {self._players[x].name} Play: {self._sticks_list}')