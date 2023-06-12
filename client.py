from protocol import *
from Nim.nim_game import nim_game
from Nim.random_player import random_player
from Nim.optimal_player import optimal_player
import logging
import struct
import pickle
import socket
import sys
import time
import threading
from protocol import sg

PORT = 1111

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
        data = pickle.dumps(start_game)
        bytes=sock.send(data)
        print(f'\nEnvie sg {bytes}')
        receiver(sock)
    else:
        print('Error al intentar conectarme')

def sendrecv_multicast():
        
        message = pickle.dumps(socket.gethostbyname(socket.gethostname()))
        multicast_group = ('224.3.29.70', 10000)

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
                logging.warning('sending {!r}'.format(message))

                sock.sendto(message, multicast_group)
                print('en sender multic mensaje enviado')

                print('$$$$$$$$$$$$$$$voy a recibir del servidor')
                while True:                        
                            try:
                                data, server = sock.recvfrom(1024)
                                print(f'recibi de ip {server[0]}')
                            except socket.timeout:
                                #pass
                                # print('Server timed out, no responses')
                                # sock.settimeout(0.9)
                                #time.sleep(1)
                                #sock.close()
                                break
                            except socket.error as e:
                                print('Error en send multicast ' + str(e.errno))
                                sock.close()
                                break
                            except:
                                print('send multicast except')
                                print(sys.exc_info)
                                sock.close()
                                break
                            else:
                                print('en send multicast received {!r} from {}'.format( data, server))
                                print(server)

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
    while True:
        try:
            print('estoy en el receiver')
            data = sock.recv(1024)
            print(f'desp data sock {data}')

            if (data):
                sms = pickle.loads(data)
                print(f'en el cliente recv del server sms= {sms}')
                time.sleep(1)
        except socket.error as e:
            print('socket error Un servidor dejo de responder, voy a intentar conectarme a otro')
            sock.close()
            print('cierro socket')
            continue_game = sg()
            continue_game.continue_game = True
            #sock = -1
            #while sock == -1:
            print('Trying to connect a new server')
            sock = sendrecv_multicast()
            if(sock != -1):
                sms = pickle.dumps(continue_game)
                sock.send(sms)
                time.sleep(0.5)
                print('socket error me conecte a otro servidor y le envie sms')
            else:
                print('error al conectar al servidor')
            #print(f'error en recver {e}')
            #break
        # except:
        #     print('except Un servidor dejo de responder, voy a intentar conectarme a otro')
        #     sock.close()
        #     print('cierro socket')
        #     continue_game = sg()
        #     continue_game.continue_game = True
        #     #sock = -1
        #     #while sock == -1:
        #     print('Trying to connect a new server')
        #     sock = sendrecv_multicast()
        #     if(sock != -1):
        #         sms = pickle.dumps(continue_game)
        #         sock.send(sms)
        #         time.sleep(0.5)
        #         print('socket error me conecte a otro servidor y le envie sms')
        #     else:
        #         print('error al conectar al servidor')
            #break

def create_games():
    tournament_list = []
    game_list = []
    
    print('\nWelcome to the Nim game tournament simmulator!!!')
    number_tournaments = read_integer('Type how many tournaments: ')
    
    for i in range(number_tournaments): #number_tournaments+1
        
        player_list = []
        number_players =  read_integer('Type how many players for tournament: ')

        while(True):  
            player_names = input('Type names of each player: ').split(' ')
            if(len(player_names) == number_players):
                break

        while(True):
            player_types = input('Type the type of each player ( optimal (o) random (r) ): ').split(' ')
            if(len(player_types) == number_players):
                #verificar o y r
                break
        
        sticks = int(input('Type how many sticks for each game: '))
        
        for i in range(number_players):
            if(player_types[i] == 'optimal'):
                player_list.append(optimal_player(player_names[i]))
            else:
                player_list.append(random_player(player_names[i]))
        
        for i in range(number_players - 1):
            game_list.append(nim_game([player_list[i], player_list[i + 1]], sticks))
        
        tournament_list.append(game_list)
    
    return tournament_list

def read_integer(etiqueta):
    data = None
    while True:
        data =  input(etiqueta)
        if data.isdigit:
            break;
    return int(data);

main()