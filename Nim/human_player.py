from player import player

class human_player(player):
    def __init__(self, name) -> None:
        super().__init__(name)
        
    def _select_move(self, sticks_list : list) -> int:
        print(sticks_list)
        move = 0
        while(move < 1 or move > 3):
            move = int(input('Cuantos palillos desea escoger (1..3): '))
        return move