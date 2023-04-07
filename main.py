from nim_game import nim_game
from random_player import random_player
from optimal_player import optimal_player
from human_player import human_player

def main():

    nim = nim_game([random_player('pepe'), human_player('kevin')], 8)
    for i in range(100):
        nim.excecute_game()
        print(nim.winner)

if __name__ == '__main__':
    main()