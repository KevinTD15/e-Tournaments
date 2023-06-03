from Nim.player import player

class nim_game:

    def __init__(self, players : list[player], sticks_number : int, current_player : player = None) -> None:
        self._players = players
        self._sticks_number = sticks_number
        self._current_player = current_player
        self._current_play = []
    
    def excecute_game(self):
        self.initialize()
        while(not self._end):
            self._excecute_turn()
    
    def _excecute_turn(self):
        if(self._start):
            self._start = False
            self._put_sticks()
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
            
    def _put_sticks(self):        
        self._sticks_list = [1 for i in range(self._sticks_number)]
    
    def _update_sitcks_list(self, move : int):        
        index = self._sticks_list.index(1)
        for i in range(index, index + move, 1):
            if(i == len(self._sticks_list)):
                return
            self._sticks_list[i] = 0
    
    def _verify_sticks(self):
        self._end = True if self._sticks_list.count(0) == self._sticks_number else False
        
    def initialize(self):
        self.winner = ''
    
        self._current_player_index = self._players.index(self._current_player) if self._current_player != None else 0
        self._sticks_list = []
        self._start = True
        self._end = False    