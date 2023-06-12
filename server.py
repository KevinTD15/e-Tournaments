import socket
import random
import hashlib
import struct
import threading
import pickle
import time
from socket_thread import socket_thread
from Games.nim_game import nim_game
from Games.random_player import random_player
from Games.optimal_player import optimal_player
from protocol import *
import sys
import logging

PORT = 1111
PORTCLIENT = 1112

class server:
    
    def __init__(self, bits) -> None:
        
        self.ip = socket.gethostbyname(socket.gethostname())
        self.id = self.get_id(bits)
        self.bits = bits
        
        self.succesor = [] #id, ip
        self.succesor_rlock = threading.RLock()
        
        self.predecesor = [] #id, ip
        self.predecesor_rlock = threading.RLock()
        
        self.leader = None
        self.leader_rlock = threading.RLock()
        
        self.leader_id = None
        
        self.sd = sd()
        self.sd_rlock = threading.RLock()
        
        self.sg = sg()
        self.sg_rlock = threading.RLock()

        self.dg = dg()
        self.dg_rlock = threading.RLock()
        
        self.gr = gr()
        self.gr_rlock = threading.RLock()
        
        self.rep = rep()
        self.rep_rlock = threading.RLock()
        
        self.stl = stl()
        
        #self.frep = frep()

        self.finger_table = {((self.id+(2**i))%2**bits) : 0 for i in range(bits)} #node : start
        self.finger_table_rlock = threading.RLock()
        
        self.succesor_table = {self.id : self.ip}
        self.succesor_table_rlock = threading.RLock()
        
        self.connection_threads = []
        
        self.connections_out = {}
        self.connections_out_rlock = threading.RLock()
        
        self.connections_in = {}
        self.connections_in_rlock = threading.RLock()

        self.multicast_closed = False
        self.multicast_closed_rlock = threading.RLock()

        self.lock = threading.Lock()            
        
        self.game_threads = []
        self.game_pause = False
        self.game_list = []
        
        self.game_replicas = {}
        self.game_replicas_rlock = threading.RLock()
        
        self.send_leader_replica = []
        
        self.winners = {}
        self.winners_replica = {}
        
        self.players_per_client = {}
        self.players_per_client_replica = {}
        
        self.tournament_per_client = {}
        self.tournament_per_client_replica = {}
        self.tournament_per_client_rlock = threading.RLock()
        
        self.send_leader = []
        self.send_leader_rlock = threading.RLock()
        self.server_client=False
        
        self.sender_leader_count = 0
        #self.sender_leader_count_rlock = threading.RLock()
        
        self.play_clients = {}
        self.play_clients_rlock = threading.RLock()
        
        self.lock_client = threading.Lock()    
        
        self.flag = False
    
    def receive_multicast(self):
        multicast_group = '224.3.29.72'
        server_address = ('', 10000)
        # Create the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to the server address
        sock.bind(server_address)
        # Tell the operating system to add the socket to
        # the multicast group on all interfaces.
        group = socket.inet_aton(multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP,  socket.IP_ADD_MEMBERSHIP, mreq)
        
        logging.warning('waiting to receive message de multicast en receive_multicast')
        print(f'server ready para la entrada de servidores a  la red!!!!!!!!!!!!!!')
        
        show=False
        while True:
            self.multicast_closed = False
            sock.settimeout(10)
            while not self.multicast_closed:
                try:
                    data, address = sock.recvfrom(4096)
                    #logging.warning(f'@@@ en recv multicast hice recvfrom {address}')
                    sock.settimeout(2)
                except socket.timeout:  
                    logging.warning('en receive_multicast cierro el hilo de multicast por timeout')
                    # while self.game_pause==True:
                    #     pass
                    self.multicast_closed_rlock.acquire() #ojoooo me parece que no es necesario
                    self.multicast_closed = True 
                    self.multicast_closed_rlock.release()
                    
                    
                    if len(self.succesor_table)==1: #arregle 
                        self.leader = self.ip
                        self.leader_id = self.leader_id
                        self.predecesor = []
                        self.succesor = []
                        logging.warning('en receive_multicast. solo quedo en succesor_table 1 servidor que debe ser este')
                    else:
                        a = list(self.succesor_table.keys())[-1]
                        if(self.id == a):
                            next_id = next(iter(self.succesor_table.keys()))
                            if(self.succesor_table[next_id] not in self.connections_out):
                                res=self.connect_to(self.succesor_table[next_id])
                                self.succesor_rlock.acquire()
                                self.succesor = [next_id, self.succesor_table[next_id]]
                                self.succesor_rlock.release()
                                logging.warning(f'---------------en receive_multicast me conecte (retorne del conect_to {res}) al nodo de id mas bajo para cerrar anillo: {next_id}')
                            
                        elif(self.id == next(iter(self.succesor_table.keys()))):
                            prev_id = list(self.succesor_table.keys())[-1]
                            self.predecesor_rlock.acquire()
                            self.predecesor = [prev_id, self.succesor_table[prev_id]]
                            self.predecesor_rlock.release()
                            logging.warning(f'---------------en receive_multicast soy el id mas pequeno y se me conecta el mayor, su id es: {prev_id}')

                    self.update_finger_table()
                    self.leader_rlock.acquire()    
                    self.leader = list(self.succesor_table.values())[-1]
                    self.leader_id = list(self.succesor_table.keys())[-1]
                    self.leader_rlock.release()
                    #print(f'en multicast leader={self.leader} flag={self.flag}')
                    #if(self.flag and self.ip == self.leader):
                    if (self.ip == self.leader):
                        if show==False:
                            show=True
                            show_thread = threading.Thread(target=self.update_play_clients)
                            show_thread.start()
                        if self.flag:
                            self.flag = False
                            print(f'l*l*l*l*l*l*l*l*l*l**l*l*l*l* players_per_client={self.players_per_client}')
                            print(f'l*l*l*l*l*l*l*l*l*l**l*l*l*l* players_per_client_replica={self.players_per_client_replica}')
                            self.players_per_client = self.players_per_client_replica
                            self.winners = self.winners_replica
                            self.tournament_per_client = self.tournament_per_client_replica
                            logging.warning(f'len send leader = {self.send_leader}, len replica = {self.send_leader_replica}')
                            print(f'len send leader = {self.send_leader}, len replica = {self.send_leader_replica}')
                            #self.send_leader.extend(self.send_leader_replica)
                            for i in self.send_leader_replica:
                                if i not in self.send_leader:
                                    self.send_leader.append(i)
                            
                    
                    if(self.ip != self.leader and self.leader not in self.connections_in):
                        self.players_per_client_replica = {}
                        self.winners_replica = {}
                        self.tournament_per_client_replica = {}
                        self.send_leader_replica = []
                    
                    k = list(self.succesor_table.keys())
                    my_id_pos = k.index(self.id)
                    #logging.warning(f'my_id_pos = {my_id_pos} k = {k}')
                    
                    if(len(self.succesor) and len(self.predecesor) and self.succesor[0] == k[(my_id_pos + 1)%len(k)] and self.predecesor[0] == k[my_id_pos - 1]):
                        logging.warning('Tengo sucesor y predecesor ok')
                        
                    self.finger_connections()  #ojoooooo chequear retorno si no se pudo conectar
                    
                    
                    
                    #print(f'sucesor: {self.succesor}') 
                    #print(f'predecesor: {self.predecesor}')    
                    logging.warning(f'succesor table: {self.succesor_table}')
                    logging.warning(f'finger table: {self.finger_table}')
                    #print(f'Lider: {self.leader}')
                    
                    if self.ip==self.leader:
                        if self.server_client==False:
                            thread_rec = threading.Thread(target=self.create_server_client)
                            thread_rec.start()
                            self.server_client=True
                            print('(((((ya pueden entrar los clientes)))))')

                except  :
                    logging.warning(sys.exc_info)
                    logging.warning('en rev multicas except')
                else:
                        #logging.warning('@@@ en recv multicast else: recibi {} bytes from {}'.format(len(data), address))             
                        if (data):
                            data = pickle.loads(data)
                            if(type(data) == int): #servidor solicitando entrar
                                data = self.receiverm(data, address, sock)
                            else: #cliente solicitando entrar
                                logging.warning('en recv mult cliente solic entrar ip {ip}')

                                if (self.ip == self.leader):
                                    logging.warning('en recv mult voy a enviar mi ip al cliente {ip}')
                                    self.sg.ip = data
                                    sms = pickle.dumps('Hola')
                                    sock.sendto(sms, address)
                                    logging.warning('en recv mult le envie mi ip al cliente {ip}')
                                
        logging.warning('en receive_multicast. sali del procedure receive_multicast')
        
    def receiverm(self,data, address, sock):
                    #logging.warning(f'entre en receive   m con data ={data} y adress[0]= {address[0]}') 
        #with self.lock:    
                    self.succesor_rlock.acquire()
                    self.predecesor_rlock.acquire()
                    if self.ip==address[0] or address[0] == '127.0.0.1':
                        pass                
                    elif(len(self.succesor) == 0 and data > self.id):
                        logging.warning(f'en receive_multicast. No tengo sucesor y self.id = {self.id} < {data} = data')
                        my_id = pickle.dumps([self.id, self.succesor_table, False])
                        sock.sendto(my_id, address)
                        time.sleep(0.5) #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        logging.warning(f'en receive multicast estoy enviando a {address[0]} succesor_table {self.succesor_table}')
                        res=self.connect_to(address[0])
                        if res==None:
                            self.succesor_rlock.acquire()
                            self.succesor = [data, address[0]]
                            self.succesor_rlock.release()
                            logging.warning(f'-------------------Me conecte a {address[0]} : {data}')
                        else:
                            logging.warning(f'-------------------NOOO Me conecte a {address[0]} : {data} retorne {res}')
                            #ojoooooooo no se hace nada  y lo mismo abajo                      

                    elif(len(self.predecesor) == 0 and data < self.id):
                        logging.warning(f'en receive_multicast. No tengo predecesor y self.id = {self.id} > {data} = data')
                        
                        my_id = pickle.dumps([self.id, self.succesor_table, True, None])
                        sock.sendto(my_id, address)
                        self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                    
                    elif(len(self.succesor) and data > self.id and self.id > self.succesor[0]):
                        logging.warning(f'en receive_multicast. Mi sucesor es menor que yo self.id = {self.id} < {self.succesor[0]} = sucesor y data mayor que yo')
                        #my_id = pickle.dumps([self.id, self.succesor_table, False])
                        #sock.sendto(my_id, address)
                        res=self.connect_to(address[0])
                        if res==None:
                            self.succesor_rlock.acquire()
                            self.succesor = [data, address[0]]
                            self.succesor_rlock.release()
                            logging.warning(f'-------------------Me conecte a {address[0]} : {data}')
                        else:
                            logging.warning(f'-------------------NOOOOO Me conecte a {address[0]} : {data} retorne {res}')
                        
                    elif(len(self.predecesor) and data > self.predecesor[0] and self.id < self.predecesor[0]):
                        logging.warning(f'en receive_multicast. Mi predecesor es mayor que yo self.id = {self.id} < {self.predecesor[0]} = predecesor y data mayor que yo')
                        my_id = pickle.dumps([self.id, self.succesor_table, True, self.predecesor])
                        sock.sendto(my_id, address)
                        self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                        
                    elif(data < self.id and data > self.predecesor[0]):
                        logging.warning(f'en receive_multicast. {data} es menor ( < ) que mi id : {self.id} y mayor que e de mi predecesor : {self.predecesor[0]}')
                        my_id = pickle.dumps([self.id, self.succesor_table, True, self.predecesor])
                        self.connections_in_rlock.acquire()
                        if self.predecesor[1] in self.connections_in:
                            self.connections_in[self.predecesor[1]].active = False #ojooo anadido 4/6
                        self.connections_in_rlock.release()
                        sock.sendto(my_id, address) #connect_to_me
                        self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                        
                    elif(data > self.id and data < self.succesor[0]):
                        logging.warning(f'en receive_multicast. {data} es mayor que mi id : {self.id} y menor que e de mi sucesor : {self.succesor[0]}')
                        self.connections_out_rlock.acquire()
                        if self.succesor[1] in self.connections_out:
                            self.connections_out[self.succesor[1]].active = False
                        self.connections_out_rlock.acquire()
                        res=self.connect_to(address[0])
                        if res==None:
                            self.succesor_rlock.acquire()
                            self.succesor = [data, address[0]]
                            self.succesor_rlock.release()
                            logging.warning(f'------------------Me conecte a : {address[0]} : {data}  ')
                        else:
                            logging.warning(f'------------------NOOOOOO Me conecte a {address[0]} : {data} retorne {res}')
                        
                    else:
                        logging.warning('en receive_multicast. El que entro no tiene nada que ver conmigo')

                    self.succesor_rlock.release()
                    self.predecesor_rlock.release()
                    
                    self.succesor_table_rlock.acquire()   
                    self.succesor_table[data] = address[0]
                    self.succesor_table = dict(sorted(self.succesor_table.items(), key=lambda item:item[0]))
                    self.succesor_table_rlock.release()   
                    logging.warning(f'termine de ejecutar el receive-m y succeso_table es {self.succesor_table}')
                    
                    logging.warning(self.succesor_table)
                    return None

    def send_multicast(self):
        
        message = pickle.dumps(self.id)
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
        
        try:
            # Send data to the multicast group
            logging.warning('sending {!r}'.format(message))
            sock.sendto(message, multicast_group)
            print('en sender multic mensaje enviado')
            # Look for responses from all recipients
            while True:
                logging.warning('send multicast waiting to receive de un recv multicast')
                try:
                    data, server = sock.recvfrom(1024)
                except socket.timeout:
                    logging.warning('NADIE MAS RESPONDE al send multicast--timed out, no more responses')
                    sock.close()
                    break
                except socket.error as e:
                    logging.warning('Error en send multicast ' + str(e.errno))
                    sock.close()
                    break
                except:
                    logging.warning('send multicast except')
                    break
                else:
                    logging.warning('en send multicast received {!r} from {}'.format( data, server))
                    
                    if(server != None): 
                        data = pickle.loads(data)                                         
                        ip = server[0]
                        if(data[2]):
                            #logging.warning(f'me voy a conectar a: {ip}')
                            res=self.connect_to(ip)
                            logging.warning(f'en send_multicast. -------------------Me conecte a {ip} : {data} retorne {res}')
                            self.succesor_rlock.acquire()
                            self.succesor = [data[0], ip]
                            self.succesor_rlock.release()
                            sock.close()  
                            
                            if(data[3] != None):
                                self.predecesor_rlock.acquire()
                                self.predecesor = data[3]
                                self.predecesor_rlock.release() 
                        else:
                            logging.warning(f'Se me conecto {ip} con id = {data[0]} que es menor que el mio')
                            self.predecesor_rlock.acquire()
                            self.predecesor = [data[0], ip]
                            self.predecesor_rlock.release() 

                        self.succesor_rlock.acquire()
                        self.succesor_table = self.succesor_table | data[1]
                        self.succesor_table = dict(sorted(self.succesor_table.items(), key=lambda item:item[0]))
                        self.succesor_rlock.release()
                        
                        logging.warning(f'en send multicas self.succesor_table quedo con con {self.succesor_table}')

                        #self.update_finger_table()
                        break
        except socket.error as e:
            logging.warning('Error al enviar multicast en send_multicast ' + str(e.errno))
            sock.close()
        except:
            logging.warning('en send_multicast. Error pde ser de connect_to')
            sock.close()
        finally:
            logging.warning('closing socket send multicast')
            #sock.close()
    
    def create_server(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sock==-1:
                logging.warning('Error al crear el socket ')
                exit()
            if sock.bind((socket.gethostbyname(socket.gethostname()), PORT))==-1:
                logging.warning('Error en el bind')
                exit()
            logging.warning('creando server ip: ' + socket.gethostbyname(socket.gethostname()))
            if sock.listen(5)==-1:
                logging.warning('Error al activar el listen')
                exit()
            while True:
                client_socket, client_address = sock.accept()
                
                ip=client_address[0]
                self.connections_in_rlock.acquire()
                self.connections_in[ip]= socket_thread(client_socket, True)
                self.connections_in_rlock.release()
                
                logging.warning(f"******************Acepte conexion de: {ip}!")               
                thread_rec = threading.Thread(target=self.receiver, args=(ip, ))
                thread_rec.start()
        except:
            logging.warning('Error al crear server en except')
            
    def create_server_client(self):
        #try:
            #print('entre a crear server client')
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sock==-1:
                logging.warning('Error al crear el socket client')
                exit()
            if sock.bind((socket.gethostbyname(socket.gethostname()), PORTCLIENT))==-1:
                logging.warning('Error en el bind client')
                exit()
            logging.warning('creando server client ip: ' + socket.gethostbyname(socket.gethostname()))
            if sock.listen(5)==-1:
                logging.warning('Error al activar el listen client')
                exit()
            #print('listen client')
            while True:
                client_socket, client_address = sock.accept()
                
                ip=client_address[0]
                self.connections_in_rlock.acquire()
                self.connections_in[ip]= socket_thread(client_socket, True)
                self.connections_in_rlock.release()
                
                print(f"******************Acepte conexion del cliente: {ip}!")               
                thread_rec = threading.Thread(target=self.receiver, args=(ip, ))
                thread_rec.start()
        #except:
        #    logging.warning('Error al crear server en except')

    def send_server(self, ip):
        play_count=0
        send_count = 0
        send_replica  = False 
        ke=1
        sock = self.connections_out[ip].sock        
        try:
            while self.connections_out[ip].active:
                with self.lock:
                    sms = None
                    sm = None

                    #este if es cuando se estan conectando los server
                    if(len(self.succesor) > 0 and ip == self.succesor[1] and not self.sd.already_sent and (self.sd.active or len(self.sd.server_down) > 0)):
                        sms = self.sd
                        #self.sd_rlock.acquire()
                        self.sd.already_sent = True
                        #self.sd_rlock.release()
                        logging.warning(f'estoy enviando sms xq alguien se cayo: {self.sd}')
                    elif(self.dg.active and len(self.succesor) and ip == self.succesor[1] and not self.dg.already_sent ):
                        sms = self.dg
                        self.dg.already_sent = True
                        a = len(self.dg.games)
                        logging.warning(f'/////--------Estoy enviando mensaje DG len(self.dg.games)={a} a ip {ip}')
                        for index, i in enumerate(self.dg.games):
                            logging.warning(f'en {self.dg.client_ip} game_list[{index}] es: player1={i[0]._players[0].name}, player2={i[0]._players[1].name}')
                    elif play_count<len(self.gr.update) and not self.game_pause: #  and not self.game_pause #hay jugadas para reclicar y enviar al cliente
                        lon =  len(self.gr.update)
                        self.rep.play = self.gr.update[play_count:lon] 
                        e=len(self.send_leader)
                        logging.warning(f'en sender rep antes de rep self.sender_leader_count={self.sender_leader_count} len send leader={e}')
                        if self.ip==self.leader:
                            self.rep.winner = self.winners
                            self.rep.tournamens = self.tournament_per_client
                            self.rep.play_count = self.players_per_client
                            len_send_leader=len(self.send_leader)
                            send_leader_count=self.sender_leader_count
                            if send_leader_count<len_send_leader:
                                self.rep.send_leader_rep = self.send_leader[send_leader_count:len_send_leader]
                                h=len(self.rep.send_leader_rep)
                                logging.warning(f'send server rep ip=leader replique {h} jugadas')
                            else:
                                self.rep.send_leader_rep=[]
                        
                            print(f'eeeeeeeeen send server en self.rep puse tournament_per_client= {self.tournament_per_client} winners={self.winners} play_count={self.players_per_client}')
                            print(f'play_count:{play_count} lon grpda:{lon}  send_leader_count:{send_leader_count} len_send_leader:{len_send_leader}')
                        sms = self.rep #prepare jugada a replicar
                        logging.warning(f'Estoy replicando en: {ip} con playcont={play_count} lon= {lon} ' )
                    
                    # elif self.ip==self.leader:
                    #     lon = 0
                    #     e=len(self.send_leader)
                    #     logging.warning(f'en sender rep antes de rep ip=leader self.sender_leader_count={self.sender_leader_count} len send leader={e}')
                    #     self.rep.winner = self.winners
                    #     self.rep.tournamens = self.tournament_per_client
                    #     self.rep.play_count = self.players_per_client                        
                    #     len_send_leader=len(self.send_leader)
                    #     send_leader_count=self.sender_leader_count
                    #     self.rep.play=None
                    #     if send_leader_count<len_send_leader:
                    #         self.rep.send_leader_rep = self.send_leader[send_leader_count:len_send_leader]
                    #         h=len(self.rep.send_leader_rep)
                    #         logging.warning(f'send server ip=leader replique {h}')
                    #     #print(f'eeeeeeeeen send server en self.rep puse tournament_per_client= {self.tournament_per_client} winners={self.winners} play_count={self.players_per_client}')
                    #     sms = self.rep #prepare jugada a replicar
                    #     pass

                    try:
                        if(sms != None):
                            if type(sms)  == rep: 
                                a=self.find_node(self.leader_id)
                                #print(f'leader={self.leader} != self.ip={self.ip} and ip={ip} == {a} and stlpause={ self.stl.pause}')
                                if(self.leader != self.ip and self.leader_id != None  and ip == self.find_node(self.leader_id) and not self.stl.pause): #and not self.stl.already_sent 
                                    lon_send_leader = len(self.send_leader)
                                    #print(f'send server send_count={send_count} lon_send_leader={lon_send_leader}')
                                    if send_count < lon_send_leader:
                                        self.stl.play = self.send_leader[send_count:lon_send_leader]
                                        logging.warning(f'^^^^^^^^^^^^send server enviando send leader a {ip} {self.stl.play}')
                                    else:
                                        self.stl.play = []
                                    self.stl.repl=self.rep.play
                                    logging.warning(f'^^^^^^^^^^send server enviando replica a {ip} {self.stl.play}')
                                    sms = self.stl
                            sm = pickle.dumps(sms)
                            sock.send(sm)  #msg.encode('UTF-8')
                            
                            if(type(sms) == sd and self.ip != self.sd.sender):
                                #self.sd_rlock.acquire()
                                self.sd.default()
                                #self.sd_rlock.release()
                            elif type(sms)  == rep: 
                                play_count = lon
                                if(self.rep.play != None):
                                    for i in self.rep.play:
                                        logging.warning(f'&.&.& sender rep de ip={ip}  j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                
                                if(self.ip == self.leader):
                                    for i in self.rep.send_leader_rep:
                                        logging.warning(f'&.&.& sender leader rep de ip={ip}  j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                
                            elif type(sms) == dg:
                                #self.dg_rlock.acquire() ojooo quite esto p tengo lock 
                                self.dg.active = False
                                self.dg.already_sent = False
                                #self.dg_rlock.release()
                            elif type(sms) == stl:
                                play_count = lon
                                #send_count =lon_send_leader
                                logging.warning(f'Replique  stl.rep={self.stl.repl}')   
                                for i in self.stl.repl:
                                        logging.warning(f'&.&.& sender stl.rep de ip={ip}  j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
 
                                print(f'Replique  stl. send_leader={self.stl.play}')  
                                logging.warning(f'Replique de send leader {self.send_leader[send_count:lon_send_leader] }')    
                                if len(self.send_leader[send_count:lon_send_leader])>0:                          
                                    for i in self.send_leader[send_count:lon_send_leader] :
                                        self.send_leader.remove(i)
                                    print(f'desssspues del remove en stl quedo count={send_count} lon_send_leader={lon_send_leader} send leader={self.send_leader}')
                                    

                        # a=len(self.send_leader)
                        # b=-1
                        # if self.leader_id!=None:
                        #     b=self.find_node(self.leader_id)
                        # c=type(sms)
                        #print(f'en send server type(sms)={c} {self.leader} != {self.ip} send_count={send_count} < len(self.send_leader) ={a} and ip={ip} == {b}  {self.stl.pause}')
                        send_count = self.sender_leader_count
                        if(type(sms) != stl and self.leader != self.ip and self.leader_id != None and send_count < len(self.send_leader) and ip == self.find_node(self.leader_id) and not self.stl.pause): #and not self.stl.already_sent 
                            lon_send_leader = len(self.send_leader)
                            logging.warning(f'^^^send server enviar al leader  send_count={send_count} len (send_leader)= {lon_send_leader}')
                            self.stl.play = self.send_leader[send_count:lon_send_leader] 
                            print(f'send server enviando abajo stl a {ip} {self.stl.play}')
                            self.stl.repl=None
                            smsl = pickle.dumps(self.stl) #prepare jugada a enviar al proximo nodo hasta llegar al lider
                            
                            try:
                                sock.send(smsl)
                                print(f'Envie jugada al lider a traves de: {ip} en type(sms) != stl')
                                print(f'send count={send_count} lon_send_leader={lon_send_leader} send leader={self.send_leader}')
                                for i in  self.send_leader[send_count:lon_send_leader] :
                                    self.send_leader.remove(i)
                                print(f'desssspues del remove quedo count={send_count} lon_send_leader={lon_send_leader} send leader={self.send_leader}')
                                
                            except socket.error as e:  #ojooo aqui tenias puesto 'except:'
                                logging.warning(f'El ip = {ip} se cayo asi que la jugada al lider se pone en pausa err {e.errno}')                                    
                                self.stl.pause = True 
                        #elif self.ip==self.leader and self.sender_leader_count<len(self.send_leader): #distribuyo las jugadas al arreglo que le corresponda al cliente
                            # print(f'$$$$ poblando play client self.sender_leader_count {self.sender_leader_count} len {len(self.send_leader)}')
                            # lon = len(self.send_leader)
                            # print(f'send server ip==leader len (send_leader)= {lon}')
                        #    self.set_play_clients(self.send_leader[self.sender_leader_count])
                        #    self.sender_leader_count+=1
                        if sms==None:
                            sms = pickle.dumps('nada que enviar')
                            logging.warning('nadaaaaaaaaaaa que enviar')
                            sock.send(sms)
                        time.sleep(0.5)
                    except socket.error as e: 
                        self.game_pause = True 
                        # while self.multicast_closed==True:
                        #     pass
                        logging.warning('lock en send_server error {} de {}  '.format(e.errno, ip))
                        #!OJOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
                        #if(ip in self.connections_out):
                        print(f' en send server antes que quitar connections_out {self.connections_out}')
                        print(f'y quitar self.succesor[0] = {self.succesor[0]}')
                        print(f'y quitar self.succesor_table= {self.succesor_table}')
                        #if ip in self.connections_out: #pq pde haber habido una cola esperando para enviar mensaje ya dentro del while
                            #print('entre en el connect out')
                        
                        ke=2
                        self.connections_out_rlock.acquire() #ojooo estoy bajo with lock, esto pdo quitarlo
                        self.connections_out[ip].active=False
                        self.connections_out_rlock.release()
                        self.succesor_table_rlock.acquire()
                        self.succesor_table.pop(self.succesor[0]) #ojon el que se cayo no tiene pq se el sucesor
                        self.succesor_table_rlock.release()
                        self.sd_rlock.acquire()
                        self.sd.server_down.append(self.succesor)
                        self.sd.resumed_games.append(self.succesor[1])
                        ke=3
                        print(f'antest server_down={self.sd.server_down}')
                        self.sd_rlock.release()
                        
                        succ_keys = list(self.succesor_table.keys())
                        pos = succ_keys.index(self.id)
                        logging.warning(f'en sender server succ_keys={succ_keys} y el subindice de mi server es {pos}')
                        for i in range((pos + 1)%len(succ_keys), len(succ_keys) + pos, 1):
                                idd = succ_keys[i%len(succ_keys)]
                                if self.id==idd: #arregle, a lo mejor hay que actualizar algunos self.
                                    print('KKKKKEEEEE quedo solo mi servidor y me pongo como lider self.leader ={self.leader} connec in={self.connections_in}')
                                    #if self.leader != None and self.ip != self.leader and self.leader not in self.connections_in:
                                    if  len(self.tournament_per_client)==0:
                                        print(f'ennnnnnnn linea 619 self.players_per_client={self.players_per_client} y players_per_client_replica={self.players_per_client_replica}')                    
                                        self.players_per_client = self.players_per_client_replica
                                        print(f'ennnnn winners={self.winners} winners_replica={self.winners_replica}')
                                        self.winners = self.winners_replica
                                        print(f'ennnnn tournament_per_client={self.tournament_per_client} tournament_per_client_replica={self.tournament_per_client_replica}')
                                        self.tournament_per_client = self.tournament_per_client_replica
                                        for i in self.send_leader_replica:
                                            if i not in self.send_leader:
                                                self.send_leader.append(i)
                                        #self.send_leader.extend(self.send_leader_replica)
                                    l =  len(self.gr.update)
                                    self.send_leader.extend(self.gr.update[play_count:l] )
                                    self.predecesor = []
                                    self.succesor = []
                                    self.leader_rlock.acquire()
                                    self.leader = list(self.succesor_table.values())[-1]
                                    self.leader_id = list(self.succesor_table.keys())[-1]
                                    self.predecesor = []
                                    self.succesor = []
                                    self.leader_rlock.release()
                                    self.sd_rlock.acquire()
                                    self.sd_rlock.release()
                                    self.stl.pause = False
                                    self.game_pause = False
                                    print(f'ffffffffff tournament_per_client={self.tournament_per_client} tournament_per_client_replica={self.tournament_per_client_replica}')
                                    logging.warning(self.succesor_table)
                                    print('antes de entrar al for para reanudar juegos')
                                    print(f'server_down={self.sd.server_down}')
                                    print(f'connections_in={self.connections_in}')
                                    print(f'resumed_games={self.sd.resumed_games}')
                                    for i in self.sd.server_down:
                                        print(f'i[1]={i[1]}, resumed_games={self.sd.resumed_games}, server_down={self.sd.server_down}')
                                        if(i[1] in self.connections_in and i[1] in self.sd.resumed_games):
                                            print(f'Voy a empezar a reanudar juegos connc_out={self.connections_out}')
                                            self.start_replicas(i[1])
                                            self.connections_in.pop(i[1])
                                            self.sd.resumed_games.remove(i[1]) 

                                    self.sd.default()

                                    #print(f'qqqqqqqqq connc_out={self.connections_out}')
                                    #show_thread = threading.Thread(target=self.show_rest)
                                    #show_thread.start()
                                    #self.show_rest()
                                    # self.sd_rlock.release()
                                    ke=12
                                    if ip in self.connections_out:
                                        k=13
                                        self.connections_out[ip].active=False
                                        k=14
                                    print('****abajo de donde pregunto if ip in self.connections_out k')
                                else:
                                    logging.warning(f'idd= {idd} ')
                                    ipp = self.succesor_table[idd]
                                    logging.warning(f'en send_server. Me voy a conectar a {ipp}----------------------')
                                    res = self.connect_to(ipp)
                                    
                                    if (res==None):
                                        logging.warning(f'en send_server -------Me conecte a {ipp}')
                                        self.succesor_rlock.acquire()
                                        self.succesor = [idd, ipp]
                                        self.succesor_rlock.release()
                                        self.update_finger_table() 
                                        self.finger_connections()
                                        self.sd_rlock.acquire()                           
                                        self.sd.sender = self.ip
                                        self.sd.sender_id = self.id
                                        self.sd.active = True
                                        self.sd_rlock.release()
                                        self.game_pause = False
                                        self.stl.pause = False
                                        break
                                    else:                        
                                        logging.warning(f'en send_server. No pude conectarme a : {ipp}, error {res}, voy pal sgte idd es {idd}  ')
                                        self.succesor_rlock.acquire()
                                        self.succesor_table.pop(idd)
                                        self.succesor_rlock.release()
                                        logging.warning(self.succesor_table)
                                        self.sd_rlock.acquire()
                                        self.sd.server_down.append([idd, ipp])
                                        self.sd.resumed_games.append(ipp)
                                        self.sd_rlock.release()
                        break #ultimo anadido
                        logging.warning(f'succesor_table = {self.succesor_table} al final del except send server')
        #except:
        #    logging.warning(f'en send server entre en except al enviar a {ip}')    
        
        except KeyError as e:
            print(f'send server except keyerror {KeyError} , estaba en camino ip {ip}  connec ot {self.connections_out} connec in ={self.connections_in}')                        
        logging.warning(f'sali del procedimiento send_server del ip {ip}')        
        print(f' en send server fuera del while connections_out {self.connections_out}')
        if ip in self.connections_out:
            self.connections_out_rlock.acquire()
            self.connections_out.pop(ip)
            self.connections_out_rlock.release()
            sock.close()
        logging.warning(f'en send_server.Deje de enviar a {ip}')
    
    def receiver(self, ip):
        sock = self.connections_in[ip].sock
        while self.connections_in[ip].active:
            try:
                #with self.lock:
                    data = sock.recv(40960)
                    if(data):
                        sms = pickle.loads(data)
                        logging.warning(f'en receiver recibi de ip {ip} data {sms}')
                        if(type(sms) == sd):
                            logging.warning(f'========= Me llego {sms}')
                            #self.sd_rlock.acquire()
                            if(sms.sender == self.ip):
                                self.sd_rlock.acquire()
                                self.sd.default()
                                self.sd_rlock.release()
                                if(len(self.players_per_client_replica) == 0):
                                    print(f'Ya todos actualizaron y yo actualizo las cosas del lider')
                                    self.tournament_per_client_replica = sms.rep_leader[0]
                                    self.winners_replica = sms.rep_leader[1]
                                    self.players_per_client_replica = sms.rep_leader[2]
                                    self.send_leader_replica = sms.rep_leader[3]
                                    self.flag = True
                                logging.warning(f'en recv SD sender {sms.sender}  !!!!!!!!!YA TODOS ACTUALIZARON!!!! ')
                            else:
                                for i in sms.server_down:
                                    if(i[1]==self.leader):
                                        if(i[1] in self.connections_in):
                                            self.sd.rep_leader = [self.tournament_per_client_replica, self.winners_replica, self.players_per_client_replica, self.send_leader_replica]
                                        else:
                                            self.tournament_per_client_replica = sms.rep_leader[0]
                                            self.winners_replica = sms.rep_leader[1]
                                            self.players_per_client_replica = sms.rep_leader[2]
                                            self.send_leader_replica = sms.rep_leader[3]
                                        self.flag = True
                                        
                                    if(i[1] in self.connections_in and i[1] in sms.resumed_games):
                                        logging.warning(f'Voy a empezar a reanudar juegos')
                                        self.start_replicas(i[1]) 
                                        #for j in self.send_leader_replica[i[1]]:
                                        #    if j not in self.send_leader:
                                        #        self.send_leader.append(j) #.extend(self.send_leader_replica[i[1]])
                                        logging.warning(f'antes del pop de connec in {i[1]} ={self.connections_in} y sms.resumed_games={sms.resumed_games}')
                                        self.connections_in.pop(i[1])                                  
                                        sms.resumed_games.remove(i[1])
                                    elif(i[1] in self.connections_in):
                                        self.connections_in.pop(i[1])
                                self.sd_rlock.acquire()
                                self.sd.resumed_games = sms.resumed_games
                                self.sd.sender = sms.sender
                                self.sd.sender_id = sms.sender_id
                                self.sd.server_down.extend(sms.server_down)
                                self.sd_rlock.release()
                                logging.warning(f'server_down = {sms.server_down}')
                                logging.warning(f'self.predecesor = {self.predecesor}')
                                self.predecesor_rlock.acquire()
                                if(self.predecesor in sms.server_down):
                                    self.predecesor = [sms.sender_id, sms.sender]
                                self.predecesor_rlock.release()
                                logging.warning(f'en recv SD sender de {sms.sender} !!!!!!!!!¨ANTES DE ACTUALIZAR')
                                self.update_succesor_table(sms.server_down) #arreglo. no arregle nada, lo que solo veo ese update esa vez
                                self.update_finger_table()
                                self.finger_connections()
                                self.stl.pause = False 
                                logging.warning(' !!!!!DESPUES DE ACTUALIZAR')

                                logging.warning(f'self.predecesor: {self.predecesor}')
                                logging.warning(f'self.finger_table: {self.finger_table}')
                                logging.warning(f'self.succesor_table: {self.succesor_table}')
                                logging.warning('ACTUALICE TODAS LAS COSAS!!!!!!!!!!!!!!!!!!!!!!!!!!')
                            self.sd.already_sent = False

                        elif type(sms) == sg:
                            print(f'ojooooooooooooooooooo recibiendo info de cliente={ip}')
                            #el lider envia los juegos a los servidores
                            if not sms.continue_game:
                                logging.warning(f'voy a crear hilo send_client {ip} y llama a distribute')
                                print(f'sms.games={sms.games}')
                                self.connection_threads.append(threading.Thread(target=self.send_client, args=(ip,)))
                                self.connection_threads[-1].start()
                                self.tournament_per_client[ip] = sms.games
                                games =  self.tournament_per_client[ip].create_matching()
                                self.players_per_client[ip] = len(games[0])
                                print(f'ip={ip} games={games} self.players_per_client[ip]={self.players_per_client[ip]}')
                                self.distribute_games(games[0], sms.ip)
                            else:
                                print('voy a continuar el juego que se quedo a mitad')
                                
                                self.connection_threads.append(threading.Thread(target=self.send_client, args=(ip,)))
                                self.connection_threads[-1].start()
                                pass
                                
                            #self.sg.game = None
                            
                        elif(type(sms) == dg):
                            a = len(sms.games)
                            logging.warning(f'ssssssssRecibi mensaje DG de {sms.client_ip} en ip {ip} y sms.active ={sms.active } len sms.games={a}')
                            for index, i in enumerate(sms.games):
                                print(f'en {sms.client_ip} game_list[{index}] es: player1={i[0]._players[0].name}, player2={i[0]._players[1].name}')
                            print('ahora llamo a distribute game')
                            self.distribute_games(sms.games, sms.client_ip)
                        
                        elif(type(sms) == rep):
                            if(sms.play != None):
                                for i in sms.play:
                                    logging.warning(f'&.&.& recv de ip={ip} rep sms.repl j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')

                            if sms.tournamens!=None:
                                self.winners_replica = sms.winner
                                self.tournament_per_client_replica = sms.tournamens
                                self.players_per_client_replica = sms.play_count
                                print(f'tttttttttttttttttt recibi tournament_per_client_replica={sms.tournamens}')
                            
                            if(sms.play != None):
                                self.game_replicas_rlock.acquire()
                                if(ip not in self.game_replicas):
                                    self.game_replicas[ip] = []
                                    #self.send_leader_replica[ip] = []
                                for i in sms.play:
                                    logging.warning(f'&**.&.& antes de extend de ip={ip} rep sms.repl j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                self.game_replicas[ip].extend(sms.play)
                                for i in self.game_replicas[ip]:
                                    logging.warning(f'&**.&.& desp de extend de ip={ip} rep sms.repl j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                self.game_replicas_rlock.release()
                                x = self.game_replicas[ip][-1]
                                logging.warning(f'Replico en mi {ip}: {x}')

                        elif(type(sms) == stl):
                            #print (f'en recv stl send_leader={self.send_leader}')
                            logging.warning (f'&&&&&& recv de ip={ip} stl sms.play={sms.play}')
                            logging.warning (f'&&&&&& recv de ip={ip} stl sms.repl={sms.repl}')

                            a=len(self.send_leader)
                            print(f'??????????en recv antes del stl start game len send leader ={a} count={self.sender_leader_count} leader={self.leader}')
                            if sms.play!=None:
                                self.send_leader_rlock.acquire()
                                for i in sms.play:
                                    if i not in self.send_leader:
                                        self.send_leader.append(i)
                                #self.send_leader.extend(sms.play)
                                self.send_leader_rlock.release()
                                for i in sms.play:
                                    logging.warning(f'&&& &&& recv de ip={ip} stl sms.play j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                    print(f'&&& &&& recv de ip={ip} stl sms.play j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')

                            
                            if sms.repl!=None:
                                self.game_replicas_rlock.acquire()
                                if(ip not in self.game_replicas):
                                    self.game_replicas[ip] = []
                                self.game_replicas[ip].extend(sms.repl)
                                self.game_replicas_rlock.release()
                                
                                for i in sms.repl:
                                    if i not in self.send_leader:
                                        self.send_leader.append(i)
                                #self.send_leader.extend(sms.repl)
                                for i in sms.repl:
                                    logging.warning(f'&& & &&& recv de ip={ip} stl sms.repl j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                    print(f'&& & &&& recv de ip={ip} stl sms.repl j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
 
                            a = len(self.send_leader)
                            print (f'______________en recv stl len= {a} de send_leader')
                            #else:
                            #    logging.warning('Soy lider y me llego jugada de otra gente')
                            
                        else:
                            pass                        
                        #self.sd_rlock.release()
            except socket.timeout: 
                logging.warning('en receiver timeout, espero 0.2 seg y sigo')          
                time.sleep(0.2)
                continue
            except socket.error as e: 
                logging.warning(f'en receiver. Se cayo {ip} socket,error={e.errno}'  )
                logging.warning(f'en recv error connection_in = {self.connections_in}')
                print(f'en recv en el except connec_in {self.connections_in}')
                #if time.sleep(1)
                # socket.clsose()
                if ip in self.connections_in:
                    self.connections_in_rlock.acquire()
                    self.connections_in[ip].active = False    
                    self.connections_in_rlock.release()
                break
                
        print(f'en recv sali de while connec_in {self.connections_in}')
        if ip in self.connections_in: #se pregunta pq puede que haya entrado un mensaje antes de active false y el pop se hizo alante
            #self.connections_in_rlock.acquire()
            #self.connections_in.pop(ip)
            #self.connections_in_rlock.release()
                    #self.predecesor = []
            sock.close()


        logging.warning(f'en receiver. Deje de recibir de {ip}')
    
    def connect_to(self, ip):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            

            #logging.warning(f'conectandome a ip: {ip}, result:ado: {res}')           
            res=s.connect((ip, PORT))
            logging.warning(f'resultado de la connect: {res} ip {ip}')
            if res == None:
                self.connections_out_rlock.acquire()
                self.connections_out[ip]= socket_thread(s, True)
                self.connections_out_rlock.release()
                self.connection_threads.append(threading.Thread(target=self.send_server, args=(ip,)))
                self.connection_threads[-1].start()
                logging.warning(f'en conect_to connect_out es {self.connections_out}')
            return res
        except socket.error as e:
            print (f'en connect_to error: {e.errno}')
            return e.errno

    def send_client(self, ip):
        logging.warning(f'vvvvvvvvvvvvvvvvvvvvvventre en send client,  ip={ip} connec_in= {self.connections_in} play_clients={self.play_clients}')
        sock = self.connections_in[ip].sock
        #time.sleep(1)
        play_count = 0
        while True:
            #with self.lock_client:
                sms = None       
                #print(f'en send client self.connections_in={self.connections_in}')
                if(ip in self.play_clients):
                    lon=len(self.play_clients[ip])
                    if play_count < lon:
                        sms = pickle.dumps(self.play_clients[ip][play_count:lon])
                        try:
                            if(sms != None):
                                sock.send(sms)  #msg.encode('UTF-8')
                                for i in self.play_clients[ip][play_count:lon]:
                                    logging.warning(f'/\/\/\/\/\/ enviado en send client ip= {ip} playcount={play_count}  J1: {i[0][0].name} J2: {i[0][1].name} se le anadio {i[1:]} sender_leader_count={self.sender_leader_count}')
                                # if  len(self.gr.update)<play_count and not self.game_pause:
                                play_count =lon
                                time.sleep(1)                   
                        except socket.error as e:  
                            print(f'lock en send client error {e.errno}')
                            #break
                        #except:
                            #logging.warning(f'en send client entre en except al enviar a {ip}') 
                            #socket.error   
                            #break
    
    def update_succesor_table(self, server_down):
        self.succesor_table_rlock.acquire()
        logging.warning(f'sever_down antes de update: {server_down}')
        logging.warning(f'succesor_table antes de update: {self.succesor_table}')
        for i in server_down:
            logging.warning(f'i = {i}')
            logging.warning(f'i[0] = {i[0]}')
            if(i[0] in self.succesor_table):
                self.succesor_table.pop(i[0])
                logging.warning(f'succesor table = {self.succesor_table} despues de eliminar i[0] = {i[0]}')
        self.succesor_table_rlock.release()
        logging.warning('ejecuto el update_succesor_table')
    
    def finger_connections(self):
        for i in self.finger_table:
            # logging.warning(f'self.finger_table[i] = {self.finger_table[i]}')
            # logging.warning(f'self.connections_out = {self.connections_out}')
            # logging.warning(f'self.ip = {self.ip}')
            res=None
            if (self.finger_table[i] not in self.connections_out and self.finger_table[i] != self.ip):
                res=self.connect_to(self.finger_table[i])
                logging.warning(f'--------------me conecte a {self.finger_table[i]} por finger table res={res}')
            return res
    
    def update_finger_table(self):
        self.finger_table_rlock.acquire()
        for i in self.finger_table:
            for index, j in enumerate(self.succesor_table):
                if index == 0:
                    pos = j
                if(i <= j):
                    self.finger_table[i] = self.succesor_table[j]
                    break
            else:
                self.finger_table[i] = self.succesor_table[pos]
        self.finger_table_rlock.release()
        logging.warning('ejecuto update_finger_table')
    
    def find_node(self, node):
        #logging.warning(f'entre a fin_node')
        for i in self.finger_table:
            if node >= i:
                #logging.warning(f'El nodo mas cercano a {node} es i = {i}, ip = {self.finger_table[i]}')
                return self.finger_table[i]
        id = list(self.finger_table.keys())[-1]
        ip = self.finger_table[id]
        #logging.warning(f'El nodo mas cercano a {node} es i = {id}, ip = {ip}')
        return ip
    
    def get_id(self, key_length):
        key = str(socket.gethostbyname(socket.gethostname())) + str(random.randint(0, 10000000))
        hash_func = hashlib.sha1
        hash_value = int(hash_func(key.encode()).hexdigest(), 16)
        return hash_value % (2 ** key_length)
    
    def set_play_clients(self, send_play):
        ip = send_play[1]   #la jugada corresponde a esta ip
        #print(f'lllll entre en set play conn in={self.connections_in}')
        if ip in self.connections_in and ip in self.players_per_client:
            if ip not in self.play_clients:
                self.play_clients[ip] = []
            self.play_clients_rlock.acquire()
            self.play_clients[ip].append(send_play[0])
            self.play_clients_rlock.release()
            
            logging.warning(f'++++++ set_play_clients anadido al cliente {ip}, J1: {send_play[0][0][0].name} J2: {send_play[0][0][1].name} jugada={send_play[0][1:]}')
            if(send_play[0][4] != ''):
                #with threading.Lock():
                    #print(f'..... set_play_clients ya esta guardado que gano {send_play[0][4]}')
                    if(ip not in self.winners):
                        self.winners[ip] = []
                    #print(f'instancia del jugador={send_play[0][0][send_play[0][1]]}')
                    self.winners[ip].append(send_play[0][0][send_play[0][1]])
                    #print(f'self.winners[ip]={self.winners[ip]}')
                    #print(f'self.players_per_client={self.players_per_client}')
                    if(len(self.winners[ip]) == self.players_per_client[ip]):
                        print(f'++++++++++++self.winner, termino una vuelta  ganadores = {self.winners[ip]}')
                        #print(f'self.tournament_per_client[ip].players={self.tournament_per_client[ip].players}')
                        self.tournament_per_client[ip].players = self.winners[ip]
                        new_round = self.tournament_per_client[ip].create_matching()
                        #print(f'self.players_per_client={self.players_per_client}')
                        self.players_per_client[ip] = len(new_round[0])
                        if len(new_round[0])==0:
                            print(f'SE TERMINO EL TORNEO Y EL winners[ip]={self.winners[ip]}')
                        self.winners[ip] = []
                        print(f'lllllllllllllllll new_round[0]={new_round[0]}')
                        self.distribute_games(new_round[0], ip)
                    else:
                        print('Annadi ganador a self.winner')
            return 1
        return 0

    def distribute_games(self, game_list, client_ip):
        with threading.Lock():
            if(len(game_list)):
                for index, i in enumerate(game_list):
                    print(f'en {client_ip} game_list[{index}] es: player1={i[0]._players[0].name}, player2={i[0]._players[1].name}')
                    logging.warning(f'en {client_ip} game_list[{index}] es: player1={i[0]._players[0].name}, player2={i[0]._players[1].name}')

                # while self.multicast_closed==True:
                #     pass
                q=len(self.succesor)
                r=len(self.predecesor)
                print(f'**** entre a distrib games {self.ip}=={self.leader} multicast={self.multicast_closed} and sucesor={self.succesor} predecesor={self.predecesor}')

                if self.ip==self.leader and len(self.succesor)==0 and len(self.predecesor)==0:
                    print('wwwwwwwww soy l lider y estoy solo, abro todos los juegos que reciba')
                    for i in game_list:
                        self.game_threads.append(threading.Thread(target=self.start_game, args=(i[0], client_ip, i[1], )))
                        self.game_threads[-1].start()
                else:
                    self.game_list.append(game_list[0][0])
                    game_id = game_list[0][1]
                    game_list.pop(0)
                    self.dg_rlock.acquire()
                    if len(game_list)==0:
                        self.dg.active = False
                        self.dg.games = []
                    else:
                        self.dg.games = game_list
                        self.dg.client_ip = client_ip
                        self.dg.active = True             
                        self.dg.already_sent=False   
                    self.dg_rlock.release()
                    
                    b = len(self.dg.games)
                    print(f'  ===== en distrib game dejo en self.dg.games {b} juegos a distribuir game_id={game_id}')
                    #print(f'active={self.dg.active} already={self.dg.already_sent}')    
                    print(f'----------cliente={client_ip} en el distribute_game jugador1={self.game_list[0]._players[0].name}, jugador2={self.game_list[0]._players[1].name}')

                    self.game_threads.append(threading.Thread(target=self.start_game, args=(self.game_list[0], client_ip, game_id, )))
                    self.game_threads[-1].start()
                    self.game_list.pop(0)

            else:
                #self.dg.active = False
                logging.warning('Ya se acabo de repartir juegos')
    
    def start_game(self, game, client_ip, game_id):
        
        print(f'*****Voy a empezar a jugar cliente {client_ip} game {game} jugador1={game._players[0].name}, jugador2={game._players[1].name}')
        logging.warning(f'*****Voy a empezar a jugar cliente {client_ip} game {game} jugador1={game._players[0].name}, jugador2={game._players[1].name}')

        game.initialize()
        print(f'game.winner={game.winner} end={game._end}')
        logging.warning(f'game.winner={game.winner} end={game._end}')

        while not game._end and game.winner == '': # and not self.game_pause
            logging.warning(f'ejecutando turno en game_id={game_id}')
            game._excecute_turn()
            if(len(game._current_play)):
                x = game._current_play[-1]
                logging.warning(f'j1: {x[0][0].name} j2: {x[0][1].name} Jugada: {x[1:]}') #tiene la ultima jugada
                self.gr_rlock.acquire()
                cpy = game.copy()
                self.gr.update.append([game._current_play[-1], client_ip, game_id, cpy]) #protocolo para la replica
                self.gr_rlock.release()
                if self.ip==self.leader:
                    q =game._current_play[-1]
                    print(f'sssstart game client_ip {client_ip} guarde en send leader ip=leader jugada {q}')
                    self.send_leader_rlock.acquire()
                    self.send_leader.append([game._current_play[-1], client_ip, game_id]) #protocolo para la replica
                    self.send_leader_rlock.release()
                    a=len(self.send_leader)
                    logging.warning(f'??????????start game len send leader ={a} count={self.sender_leader_count}')

            time.sleep(2)
        if(game._end or game.winner != ''):
            print(f'Juego terminado gano: {game.winner}')
            logging.warning(f'Juego terminado gano: {game.winner}')

    def start_replicas(self, ip):
        print(f'estoy en start replicas {ip}')
        mark_ids = []
        reps = list(self.game_replicas[ip])
        #print(f'replicas={reps}')
        for i in range(len(reps)-1, -1, -1):
            logging.warning(f'start replicas antes del if id: {reps[i][2]}   J1:{reps[i][0][0][0].name}  J2: {reps[i][0][0][1].name} jugada: {reps[i][0][1:]}')
            logging.warning(f'mark_ids={mark_ids}')
            if([reps[i][2], reps[i][1]] not in mark_ids):
                mark_ids.append([reps[i][2],reps[i][1]])
                self.resume_game(reps[i])
                logging.warning(f'start replicas   J1:{reps[i][0][0][0].name}  J2: {reps[i][0][0][1].name} jugada: {reps[i][0][1:]}')
                print(f'reps[i][0][0][0].name={reps[i][0][0][0].name}')
                print(f'reps[i][0][0][1].name={reps[i][0][0][1].name}')
                print(f'reps[i][1]={reps[i][1]}')
                print(f'reps[i][2]={reps[i][2]}')
    
    def resume_game(self, game):
        
        game[0][0] #players
        game[0][1] #current_player index
        game[0][2] #move
        game[0][3] #stick count
        game[0][4] #winner
        game[1] #client_ip
        game[2] #game_id
        game[3] #game copy

        print('Estoy reanudando un juego')
        print(f'self.tournament_per_client[{game[1]}] self.tournament_per_client={self.tournament_per_client}')
        print(f'self.tournament_per_client[{game[1]}] self.tournament_per_client_replica={self.tournament_per_client_replica}')
        # if len(self.tournament_per_client)==0:
        #     self.tournament_per_client_rlock.acquire()
        #     self.tournament_per_client=self.tournament_per_client_replica
        #     self.tournament_per_client_rlock.release()        
        #     self.players_per_client = self.players_per_client_replica
        #     self.winners = self.winners_replica

        # print(f'self.tournament_per_client[{game[1]}] self.tournament_per_client={self.tournament_per_client_replica}')
        if(game[0][4] == ''):
            x_game = game[3].copy()            
    
            x_game._players = game[0][0]
            x_game._current_player_index = game[0][1]
    
            x_game.config = game[0][3]
            x_game.winner = game[0][4]
    
            self.game_list.append(x_game)
            print(f'>>>>>>>> estoy funcionando J1: {x_game._players[0].name} J2: {x_game._players[1].name} x_game={x_game}')
            print(f'game[1]={game[1]} game[2]={game[2]}')
            logging.warning(f'>>>>>>>> voy a llamar a start_game J1: {x_game._players[0].name} J2: {x_game._players[1].name} x_game={x_game}')
            self.game_threads.append(threading.Thread(target=self.start_game, args=(x_game, game[1], game[2], )))
            self.game_threads[-1].start()
            
        # else:
        #     self.gr.update.append(game)
        #     if self.ip==self.leader:
        #         print(f'vino con ganador game client_ip {game[1]} guarde en send leader ip=leader jugada {game}')
        #         self.send_leader_rlock.acquire()
        #         self.send_leader.append(game) #protocolo para la replica
        #         self.send_leader_rlock.release()
            

    def update_play_clients(self):
        while True:
            #print(f'entre en show self.sender_leader_count={self.sender_leader_count}')
            while self.sender_leader_count<len(self.send_leader):
                #a=len(self.send_leader)
                #logging.warning(f'ssshow self.send_leader[{self.sender_leader_count}]={self.send_leader[self.sender_leader_count]}  len={a} conn in={self.connections_in}')
                self.sender_leader_count += self.set_play_clients(self.send_leader[self.sender_leader_count])
                    
                    

def main():
    logging.basicConfig(filename='server_g.log', filemode='w', format='%(message)s')

    s = server(160)
    logging.warning(f'Mi id es: {s.id}')

    thread = threading.Thread(target=s.create_server)
    thread.start()
    
    s.send_multicast()
    
    thread2 = threading.Thread(target=s.receive_multicast)
    thread2.start()

main()