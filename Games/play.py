from abc import ABC, abstractstaticmethod
from Games.tic_tac_toe_utils import minimax
import random as rd

class play(ABC):
    
    def __init__(self, state, game, hand) -> None:
        self.state = state
        self.game = game
        self.hand = hand
    
    @abstractstaticmethod
    def create_play():
        pass

class optimal(play):
    
    def __init__(self, state, game, hand) -> None:
        super().__init__(state, game, hand)
        
    def create_play(self):
        if(self.game=='n'):
            mod_4 = self.state.count(1) % 4
            return mod_4 if mod_4 % 4 != 0 else rd.randint(1, 3)
        
        elif(self.game=='t'):
            pos=-1;
            value=-2;
            for i in range(0,9):
                if(self.state[i]==0):
                    self.state[i]=1;
                    score =- minimax(self.state, self.hand);
                    self.state[i]=0;
                    if(score>value):
                        value=score;
                        pos=i;
            return pos

class random(play):
    
    def __init__(self, state, game, hand) -> None:
        super().__init__(state, game, hand)
        
    def create_play(self):
        if(self.game=='n'):
            return rd.randint(1, 3)
        
        elif(self.game=='t'):
            empty_cells = []
            for i in range(len(self.state)):
                if(self.state[i] == 0):
                    empty_cells.append(i)
            x = rd.sample(empty_cells, k=1)
            return x[0]