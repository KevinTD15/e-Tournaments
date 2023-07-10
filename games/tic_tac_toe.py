from games.game import game
from games.player import player
from games.tic_tac_toe_utils import analyzeboard

class tic_tac_toe(game):
    
    def __init__(self, _players: list[player] = [], config: object = 0, current_player_init: int = 0, winner: str = ''):
        super().__init__(_players, config, current_player_init, winner)
    
    def excecute_game(self):
        self.initialize()
        while(not self._end and self.winner == ''):
            self._excecute_turn()
    
    def initialize(self):
        self.board = [0,0,0,0,0,0,0,0,0] if self.config == 0 else self.config
        self._start = True
        self._players[0].hand = 1
        self._players[1].hand = -1
        self._table = False
        self.turn_count = 0
    
    def _excecute_turn(self):
        if(self.turn_count == 9 and analyzeboard(self.board) == 0):
            print('Tabla')
            self.initialize()
            
        if(self._start):
            self._start = False
            self.board = [0,0,0,0,0,0,0,0,0] if self.config == 0 else self.config 
        else:
            if(self._current_player_index >= len(self._players)):
                self._current_player_index= 0
            current_player = self._players[self._current_player_index]
            
            move = current_player._select_move(self.board)
            
            self.board[move] = current_player.hand
            
            #self.board_state()
            
            result = analyzeboard(self.board)
            
            if(result == current_player.hand):
                self._end = True
            
            if(self._end):
                self.winner = self._players[self._current_player_index].name
                self._current_play.append([self._players, self._current_player_index, move, self.board, self.winner])
                return    
            else:
                self._current_play.append([self._players, self._current_player_index, move, self.board, ''])
                self._current_player_index += 1
                
            self.turn_count += 1
            
    def show_board(self):
        self.board = self.config
        x = self._current_player_index % 2
        print(f"Player 1: {self._players[0].name}, Player 2: {self._players[1].name}, Current: {self._players[x].name}, Play: \n\n");
        for i in range (0,9):
            if((i>0) and (i%3)==0):
                print("\n");
            if(self.board[i]==0):
                print("- ",end=" ");
            if (self.board[i]==1):
                print("O ",end=" ");
            if(self.board[i]==-1):    
                print("X ",end=" ");
        print("\n\n");
    
    def copy(self):
        return tic_tac_toe()