import socket
import random
import hashlib
import struct
import threading
import pickle
import time
from socket_thread import socket_thread
from Nim.nim_game import nim_game
from Nim.random_player import random_player
from Nim.optimal_player import optimal_player
from protocol import *
import sys
import logging

PORT = 1111

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
        
        self.sd = sd()
        self.sd_rlock = threading.RLock()
        
        self.sg = sg()
        self.sg_rlock = threading.RLock()

        self.dg = dg()
        self.dg_rlock = threading.RLock()
        
        self.gr = gr()
        self.gr_rlock = threading.RLock()

        self.finger_table = {((self.id+(2**i))%2**bits) : 0 for i in range(bits)} #node : start
        self.finger_table_rlock = threading.RLock()
        
        self.succesor_table = {self.id : self.ip}
        self.succesor_table_rlock = threading.RLock()
        
        self.connection_threads = []
        
        self.connections_out = {}
        self.connections_out_rlock = threading.RLock()
        
        self.connections_in = {}
        self.connections_in_rlock = threading.RLock()
        
        self.game_threads = []
        self.game_pause = False
                
        #self.close_send = False
        #self.close_receive = False
        
        self.multicast_closed = False
        self.multicast_closed_rlock = threading.RLock()

        self.lock = threading.Lock()
        self.is_threading_client = False
        
    def receive_multicast(self):
        multicast_group = '224.3.29.70'
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
        print(f'SERVER READY!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! {self.multicast_closed}')
        
        while True:
            self.multicast_closed = False
            sock.settimeout(10)
            while not self.multicast_closed:
                try:
                    data, address = sock.recvfrom(4096)
                    print(f'@@@ en recv multicast desp del recvfrom {address}')
                    sock.settimeout(10)
                except socket.timeout:  
                    logging.warning(f'en receive_multicast   timeout')
                    logging.warning('en receive_multicast cierro el hilo de multicast por timeout')
                    self.multicast_closed_rlock.acquire()
                    self.multicast_closed = True 
                    self.multicast_closed_rlock.release()
                    self.update_finger_table()
                    
                    if len(self.succesor_table)==1: #arregle 
                        self.leader = self.ip
                        self.predecesor = []
                        self.succesor = []
                        logging.warning('en receive_multicast. solo quedo en succesor_table 1 servidor que debe ser este')
                    else:
                        a = list(self.succesor_table.keys())[-1]
                        logging.warning(f'en recv multicast timout self.id = {self.id}, id mas alto = {a} succ_table={self.succesor_table}')
                        if len(self.succesor_table)==1:
                            self.succesor = None
                            self.predecesor = None
                        elif(self.id == a):
                            next_id = next(iter(self.succesor_table.keys()))
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

                    self.leader_rlock.acquire()    
                    self.leader = list(self.succesor_table.values())[-1]
                    self.leader_rlock.release()
                    
                    k = list(self.succesor_table.keys())
                    logging.warning(f'k = {k}')
                    my_id_pos = k.index(self.id)
                    logging.warning(f'my_id_pos = {my_id_pos}')
                    
                    if(len(self.succesor) and len(self.predecesor) and self.succesor[0] == k[(my_id_pos + 1)%len(k)] and self.predecesor[0] == k[my_id_pos - 1]):
                        logging.warning('Tengo sucesor y predecesor ok')
                        
                    self.finger_connections()
                    
                    logging.warning(f'sucesor: {self.succesor}') 
                    logging.warning(f'predecesor: {self.predecesor}')    
                    logging.warning(f'succesor table: {self.succesor_table}')
                    logging.warning(f'finger table: {self.finger_table}')
                    logging.warning(f'Lider: {self.leader}')

                except  :
                    logging.warning(sys.exc_info)
                    logging.warning('en rev multicas except')
                else:
                        logging.warning('received {} bytes POR MULTICAST from {}'.format(len(data), address))             
                        if (data):
                            data = pickle.loads(data)
                            if(type(data) == int): #servidor solicitando entrar
                                data = self.receiverm(data, address, sock)
                            else: #cliente solicitando entrar
                                logging.warning('en recv mult cliente solic entrar')
                                print(f'@@@@@@@@@@@@@@@@ en recv mult cliente solic entrar {address}')
                                if (self.ip == self.leader):
                                    self.sg.ip = data
                                    sms = pickle.dumps('Hola')
                                    sock.sendto(sms, address)
                                    print('le envie mi ip al cliente')
                                
                logging.warning(f'en conect_to connect_out es {self.connections_out}')
                                

        logging.warning('en receive_multicast. sali del procedure receive_multicast')
        
    def receiverm(self,data, address, sock):
                    logging.warning(f'entre en receive   m con data ={data} y adress[0]= {address[0]}') 
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
                        #self.succesor_rlock.acquire()
                        self.succesor = [data, address[0]]
                        #self.succesor_rlock.release()
                        logging.warning(f'-------------------Me conecte a {address[0]} : {data} retorne {res}')
                        
                    elif(len(self.predecesor) == 0 and data < self.id):
                        logging.warning(f'en receive_multicast. No tengo predecesor y self.id = {self.id} > {data} = data')
                        
                        my_id = pickle.dumps([self.id, self.succesor_table, True, None])
                        sock.sendto(my_id, address)
                        #self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        #self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                    
                    elif(len(self.succesor) and data > self.id and self.id > self.succesor[0]):
                        logging.warning(f'en receive_multicast. Mi sucesor es menor que yo self.id = {self.id} < {self.succesor[0]} = sucesor y data mayor que yo')
                        #my_id = pickle.dumps([self.id, self.succesor_table, False])
                        #sock.sendto(my_id, address)
                        res=self.connect_to(address[0])
                        #self.succesor_rlock.acquire()
                        self.succesor = [data, address[0]]
                        #self.succesor_rlock.release()
                        logging.warning(f'-------------------Me conecte a {address[0]} : {data} retorne {res}')
                        
                    elif(len(self.predecesor) and data > self.predecesor[0] and self.id < self.predecesor[0]):
                        logging.warning(f'en receive_multicast. Mi predecesor es mayor que yo self.id = {self.id} < {self.predecesor[0]} = predecesor y data mayor que yo')
                        my_id = pickle.dumps([self.id, self.succesor_table, True, self.predecesor])
                        sock.sendto(my_id, address)
                        #self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        #self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                        
                    elif(data < self.id and data > self.predecesor[0]):
                        logging.warning(f'en receive_multicast. {data} es menor ( < ) que mi id : {self.id} y mayor que e de mi predecesor : {self.predecesor[0]}')
                        my_id = pickle.dumps([self.id, self.succesor_table, True, self.predecesor])
                        #self.connections_in_rlock.acquire()
                        self.connections_in[self.predecesor[1]].active = False
                        #self.connections_in_rlock.release()
                        sock.sendto(my_id, address) #connect_to_me
                        #self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        #self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                        
                    elif(data > self.id and data < self.succesor[0]):
                        logging.warning(f'en receive_multicast. {data} es mayor que mi id : {self.id} y menor que e de mi sucesor : {self.succesor[0]}')
                        self.connections_out[self.succesor[1]].active = False
                        res=self.connect_to(address[0])
                        #self.succesor_rlock.acquire()
                        self.succesor = [data, address[0]]
                        #self.succesor_rlock.release()
                        logging.warning(f'------------------Me conecte a : {address[0]} : {data} retorne {res}')
                        
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
                except:
                    logging.warning('send multicast except')
                    logging.warning(sys.exc_info)
                else:
                    logging.warning('en send multicast received {!r} from {}'.format( data, server))
                    logging.warning(server)
                    
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
        except:
            logging.warning('en send_multicast. Error pde ser de connect_to')
            logging.warning(sys.exc_info)
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

    def send_server(self, ip):
        playcount=0
        sock = self.connections_out[ip].sock        
        try:
            while self.connections_out[ip].active:
                with self.lock:
                    sms = None
                    #este if es cuando se estan conectando los server
                    if(len(self.succesor) > 0 and ip == self.succesor[1] and not self.sd.already_sent and (self.sd.active or len(self.sd.server_down) > 0)):
                        sms = pickle.dumps(self.sd)
                        self.sd_rlock.acquire()
                        self.sd.already_sent = True
                        self.sd_rlock.release()
                        logging.warning(f'estoy enviando sms xq alguien se cayo: {self.sd}')
                    elif(len(self.succesor) and ip == self.succesor[1] and not self.dg.already_sent and self.dg.active):
                        sms = pickle.dumps(self.dg)
                        self.dg.already_sent = True
                        logging.warning('Estoy enviando mensaje DG')
                    elif len(self.gr.update)<playcount and not self.game_pause: #hay jugadas para reclicar y enviar al cliente
                        sms = pickle.dumps(self.gr.update[playcount]) #prepare jugada a replicar
                        print('en send_server estoy env message a replica ' + ip)
                    else:
                        sms = pickle.dumps('Estoy vivo')
                        print('en send_server estoy env message estoy vivo a ' + ip)
                        time.sleep(1)
                    try:
                        if(sms != None):
                            sock.send(sms)  #msg.encode('UTF-8')
                            
                            if(type(sms) == sd and self.ip != self.sd.sender):
                                self.sd_rlock.acquire()
                                self.sd.default()
                                self.sd_rlock.release()
                            #time.sleep(0.5)

                    except: # socket.error:  
                        logging.warning('lock en send_server error {} de {}  '.format(socket.error, ip))
                        #!OJOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO

                        #if(ip in self.connections_out):
                        print(f' en send server antes que quitar connections_out {self.connections_out}')
                        print(f'y quitar self.succesor[0] = {self.succesor[0]}')
                        print(f'y quitar self.succesor_table= {self.succesor_table}')
                        #if ip in self.connections_out: #pq pde haber habido una cola esperando para enviar mensaje ya dentro del while
                            #print('entre en el connect out')
                        self.connections_out_rlock.acquire()
                        self.connections_out[ip].active=False
                        self.connections_out_rlock.release()
                        self.succesor_table_rlock.acquire()
                        self.succesor_table.pop(self.succesor[0])
                        self.succesor_table_rlock.release()
                        self.sd_rlock.acquire()
                        self.sd.server_down.append(self.succesor)
                        self.sd_rlock.release()
                        
                        succ_keys = list(self.succesor_table.keys())
                        pos = succ_keys.index(self.id)
                        
                        logging.warning(f'en sender server succ_keys={succ_keys} y el subindice de mi server es {pos}')
                        for i in range((pos + 1)%len(succ_keys), len(succ_keys) + pos, 1):
                                idd = succ_keys[i%len(succ_keys)]
                                if self.id==idd: #arregle, a lo mejor hay que actualizar algunos self.
                                    logging.warning('quedo solo mi servidor y me pongo como lider')
                                    self.leader_rlock.acquire()
                                    self.leader = list(self.succesor_table.values())[-1]
                                    self.leader_rlock.release()
                                    self.sd_rlock.acquire()
                                    self.sd.default()
                                    self.sd_rlock.release()
                                    logging.warning(self.succesor_table)
                                    # self.sd_rlock.release()
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
                                        break
                                    else:                        
                                        logging.warning(f'en send_server. No pude conectarme a : {ipp}, error {res}, voy pal sgte idd es {idd}  ')
                                        self.succesor_rlock.acquire()
                                        self.succesor_table.pop(idd)
                                        self.succesor_rlock.release()
                                        logging.warning(self.succesor_table)
                                        self.sd_rlock.acquire()
                                        self.sd.server_down.append([idd, ipp])
                                        self.sd_rlock.release()
                        break #ultimo anadido
                        logging.warning(f'succesor_table = {self.succesor_table} al final del except send server')
        #except:
        #    logging.warning(f'en send server entre en except al enviar a {ip}')    
        
        except KeyError:
            print(f'al salir de send server except keyerror , no pasa nada es un while que ya estaba en camino')                        
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
                    data = sock.recv(1024)
                    if(data):
                        logging.warning(f'en receiver recibiendo de ip {ip}')
                        sms = pickle.loads(data)

                        if(type(sms) == sd):
                            logging.warning(f'========= Me llego {sms}')
                            #self.sd_rlock.acquire()
                            if(sms.sender == self.ip):
                                self.sd_rlock.acquire()
                                self.sd.default()
                                self.sd_rlock.release()
                                logging.warning(f'en recv SD sender {sms.sender}  !!!!!!!!!YA TODOS ACTUALIZARON!!!! ')
                            else:
                                self.sd_rlock.acquire()
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
                                logging.warning(' !!!!!DESPUES DE ACTUALIZAR')

                                logging.warning(f'self.predecesor: {self.predecesor}')
                                logging.warning(f'self.finger_table: {self.finger_table}')
                                logging.warning(f'self.succesor_table: {self.succesor_table}')
                                logging.warning('ACTUALICE TODAS LAS COSAS!!!!!!!!!!!!!!!!!!!!!!!!!!')
                            self.sd.already_sent = False

                        elif type(sms) == sg:
                            logging.info(f'reciendo info del cliente {sms.games} ')
                            #el lider envia los juegos a los servidores
                            if not self.is_threading_client or sms.continue_game:
                                logging.warning('voy a crear hilo send_client')
                                self.connection_threads.append(threading.Thread(target=self.send_client, args=(ip,)))
                                self.connection_threads[-1].start()
                                self.is_threading_client = True
                            self.distribute_games(sms.games)
                                
                            #self.sg.game = None
                            
                        elif(type(sms) == dg):
                            self.distribute_games(sms.games)
                            logging.warning('Recibi mensaje DG')
                        else:
                            print(sms)                        
                        #self.sd_rlock.release()
            except socket.timeout: 
                logging.warning('en receiver timeout, espero 0.2 seg y sigo')          
                time.sleep(0.2)
                continue
            except: #socket.error:
                logging.warning(f'en receiver. Se cayo {ip}'  )
                #time.sleep(1)
                logging.warning('en recv error connection_in = {self.connections_in}')
                print(f'en recv en el except connec_in {self.connections_in}')
                if ip in self.connections_in:
                    self.connections_in_rlock.acquire()
                    self.connections_in[ip].active = False    
                    self.connections_in_rlock.release()
                break
        print(f'en recv sali de while connec_in {self.connections_in}')
        if ip in self.connections_in: #se pregunta pq puede que haya entrado un mensaje antes de active false y el pop se hizo alante
            self.connections_in_rlock.acquire()
            self.connections_in.pop(ip)
            self.connections_in_rlock.release()
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
        logging.warning(f'en server Estoy vivo en send client {self.connections_in} ip={ip}')
        sock = self.connections_in[ip].sock    
        sms = pickle.dumps('en server Estoy vivo en send client') 
        print('en send client del server estoy  enviando a ' + ip)
        time.sleep(1)
        playcount = 0
        while True:
            # if  len(self.gr)<playcount and not self.game_pause: #hay jugadas para reclicar y enviar al cliente
            #     sms = pickle.dumps(self.gr.update[playcount]) #prepare jugada a replicar
            #     print('en send_server estoy env message de jugada ' + ip)
            try:
                if(sms != None):
                    sock.send(sms)  #msg.encode('UTF-8')
                    print('\n /\/\/\/\/\/\/\/\/\/\ en serverg en send_client envie sms al client')
                    # if  len(self.gr.update)<playcount and not self.game_pause:
                    #     playcount = playcount + 1
                    time.sleep(1)                    
            except socket.error:  
                logging.warning('lock en send client error {} de {} '.format(socket.error,ip))
                break
            except:
                logging.warning(f'en send client entre en except al enviar a {ip}')    
                break
    
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
            if (self.finger_table[i] not in self.connections_out and self.finger_table[i] != self.ip):
                self.connect_to(self.finger_table[i])
                logging.warning(f'--------------me conecte a {self.finger_table[i]} por finger table')
    
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
    
    def get_id(self, key_length):
        key = str(socket.gethostbyname(socket.gethostname())) + str(random.randint(0, 10000000))
        hash_func = hashlib.sha1
        hash_value = int(hash_func(key.encode()).hexdigest(), 16)
        return hash_value % (2 ** key_length)

    def distribute_games(self, game_list):
        if(len(game_list)):
            logging.warning('Estoy eligiendo el juego que voy a simular')
            game = game_list[0].pop(0) #!CAMBIAR
            logging.warning(f'game = {game}')
            self.dg.games = game_list
            self.dg.active = True
            
            logging.warning('Estoy creando hilo para ejecutar mi juego')
            self.game_threads.append(threading.Thread(target=self.start_game, args=(game, )))
            self.game_threads[-1].start()

        else:
            print('Ya se acabo de repartir juegos')
            
    def start_game(self, game):
        
        logging.warning('Voy a empezar a ejecutar el juego')
        game.initialize()
        while not game._end and not self.game_pause:
            game._excecute_turn()
            if(len(game._current_play)):
                print(game._current_play[-1]) #tiene la ultima jugada
                self.gr_rlock.acquire()
                self.gr.update.append(game._current_play[-1]) #protocolo para la replica
                self.gr_rlock.release()
            time.sleep(2)

def main():
    logging.basicConfig(filename='server_g.log', filemode='w', format='%(asctime)s - %(message)s')

    s = server(6)
    logging.warning(f'Mi id es: {s.id}')

    thread = threading.Thread(target=s.create_server)
    thread.start()
    
    s.send_multicast()
    
    thread2 = threading.Thread(target=s.receive_multicast)
    thread2.start()

main()