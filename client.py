from protocol import *
from Nim.nim_game import nim_game
from Nim.tic_tac_toe import tic_tac_toe
from Nim.random_player import random_player
from Nim.optimal_player import optimal_player
from Nim.tournament import *
import logging
import struct
import pickle
import socket
import sys
import time
import threading
from protocol import sg

PORT = 1112

def main():
    
    logging.basicConfig(filename='client.log', filemode='w', format='%(asctime)s - %(message)s')
    
    tournaments = create_games()
    
    # sock = -1
    # while sock == -1:
    sock = sendrecv_multicast()
    
    if sock!=-1:   
        print(f'Tengo el socket: {sock}')
        start_game = sg()        
        start_game.games = tournaments
        start_game.ip = socket.gethostbyname(socket.gethostname())
        data = pickle.dumps(start_game)
        #!TRYYYYYYYYYYYYYYYYYYYYY
        bytes=sock.send(data)
        #print(f'\nEnvie sg {bytes}')
        receiver(sock)
    else:
        print('Error al intentar conectarme')

def sendrecv_multicast():
        
        message = pickle.dumps(socket.gethostbyname(socket.gethostname()))
        multicast_group = ('224.3.29.72', 10000)

        # Create the datagram socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        sock.settimeout(0.9)

        # Set the time-to-live for messages to 1 so they do not
        # go past the local network segment.
        ttl = struct.pack('b', 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        
        while True:
            try:
                # Send data to the multicast group
                # print('sending {!r}'.format(message))

                sock.sendto(message, multicast_group)
                #print('en sender multic mensaje enviado a todos')

                while True:                        
                            try:
                                data, server = sock.recvfrom(1024)
                                print(f'recibi de ip {server[0]}')
                            except socket.timeout:
                                #pass
                                print('Server timed out, no responses')
                                sock.settimeout(1)
                                time.sleep(5)
                                #sock.close()
                                break
                            except socket.error as e:
                                print('Error en send multicast ' + str(e.errno))
                                time.sleep(5)
                                #sock.close()
                                break
                            except:
                                print('send multicast except')
                                #print(sys.exc_info)
                                time.sleep(5)
                                #sock.close()
                                break
                            else:
                                print('en send multicast received {!r} from {}'.format( data, server))

                                if(server != None): 
                                    data = pickle.loads(data)                                         
                                    ip = server[0]
                                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            
                                    #print(f'conectandome a ip: {ip}, result:ado: {res}')           
                                    res=s.connect((ip, PORT))
                                    if res==None:
                                        #thread = threading.Thread(target=receiver, args=(s,))
                                        #thread.start()
                                        print(f'Connected to server: {ip}, res = {res}')
                                        return s
                                    else:
                                        print(f'Error Connected to server: {ip}, res = {res}')
                                        sock.close()
                                        break
                #return -1
            except socket.error as e:
                logging.warning('Error al enviar multicast en send_multicast ' + str(e.errno))
            except:
                logging.warning('en send_multicast except')

def receiver(sock):
    playcount = 0
    #sock.settimeout(5)
    while True:
        try:
            #with threading.Lock():
                data = sock.recv(4096)
                #print(f'desp data sock {data}')

                if (data):
                    sms = pickle.loads(data)
                    for i in sms:
                        print(f'playcount={playcount} player1: {i[0][0].name} player2: {i[0][1].name}, {i[1:]}')
                        playcount+=1
                    #time.sleep(1)
                    
        #except socket.timeout:
        #    print('estoy esperando en el receiver')
        #    sock.settimeout(5)
        except socket.error as e:
            print('Waiting...')
            sock.close()
            #print('cierro socket')
            continue_game = sg()
            continue_game.continue_game = True
            #sock = -1
            #while sock == -1:
            #print('Trying to connect a new server')
            while True:
                sock = sendrecv_multicast()
                if(sock != -1):
                    sms = pickle.dumps(continue_game)
                    try:
                        sock.send(sms)
                        time.sleep(0.5)
                        break
                    except socket.error:
                        pass
                        print('socket error me conecte a otro servidor y le envie sms')

def create_games():

        game_list = []
    
        print('\nWelcome to the Nim game tournament simmulator!!!')
        #number_tournaments = read_integer('Type how many tournaments: ')
    
    #for i in range(number_tournaments): #number_tournaments+1
        
        tournament_type = None
        while True:
            tournament_type =  input('Type the type of the tournament ( elimination (e) dos_a_dos (d) ): ')
            if tournament_type in ['e', 'd']:
                break
            
        game_type = None
        while True:
            game_type =  input('Type the type of the game ( nim (n) tictactoe (t) ): ')
            if game_type in ['n', 't']:
                break
        
        player_list = []
        while True:
            number_players =  read_integer('Type how many players for tournament: ')
            if number_players % 2 == 0:
                break

        while(True):  
            player_names = input('Type names of each player: ').split(' ')
            if(len(player_names) == number_players):
                break

        while(True):
            player_types = input('Type the type of each player ( optimal (o) random (r) ): ').split(' ')
            if(len(player_types) == number_players):
                #verificar o y r
                break
        
        initial_state = 0
        
        if(game_type == 'n'):
            sticks = read_integer('Type how many sticks for each game: ')
            initial_state = sticks
        
        if game_type == 'n':
            game_instance = nim_game()
        else:
            game_instance = tic_tac_toe()
        
        for j in range(number_players):
            if(player_types[j] == 'o'):
                player_list.append(optimal_player(player_names[j], game_type))
            else:
                player_list.append(random_player(player_names[j], game_type))
        
        if tournament_type == 'e':
            tournament_instance = elimination(player_list, initial_state,  game_instance)
        else:
            pass #! implementar otro tipo de torneo
        
        # for k in range(0, number_players - 1, 2):
        #     game_list.append([nim_game([player_list[k], player_list[k + 1]], sticks), k])
    
        return tournament_instance

def read_integer(etiqueta):
    data = None
    while True:
        data =  input(etiqueta)
        if data != None and data.isdigit:
            break;
    return int(data);

main()