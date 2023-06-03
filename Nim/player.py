from abc import ABC, abstractstaticmethod

class player(ABC):
    
    def __init__(self, name) -> None:
        self.name = name
        
    @abstractstaticmethod
    def _select_move():
        pass