import socket
import struct
import threading
import pickle
import time
from protocol import *

PORT = 1111

class server(protocol):

    def __init__(self):
        self.connections_out = {}
        self.connections_out_Rlock = threading.RLock()
        
        self.connections_in = {}
        self.connections_in_Rlock = threading.RLock()

        self.connection_threads = []
        self.multicast_closed = False
        self.CR = CR()
        self.CR2 = CR2()

    def receive_multicast(self):

        multicast_group = '224.3.29.71'
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
        sock.settimeout(5)
        #print(sock.timeout)
        # Receive/respond loop
        print('\nwaiting to receive multicast message')
        while not self.multicast_closed: 
            try:
                data, address = sock.recvfrom(1024)
            except socket.timeout:
                # if len(connections_in)==0:
                #     #print('no cierro pq soy el server lider')
                #     pass
                # else:          
                print('cierro el hilo de multicast')
                self.multicast_closed = True
                #break
            else:
                print('received {} bytes POR MULTICAST from {}'.format(len(data), address))
                print(data)
                if(len(self.connections_in) < 2):
                    print('sending acknowledgement to', address)
                    sock.sendto(b'ack', address)
        
    def send_multicast(self):

        message = b'very important data'
        multicast_group = ('224.3.29.71', 10000)

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
            print('sending {!r}'.format(message))
            sent = sock.sendto(message, multicast_group)

            # Look for responses from all recipients
            while True:
                print('waiting to receive')
                try:
                    data, server = sock.recvfrom(16)
                except socket.timeout:
                    print('NADIE MAS RESPONDE --timed out, no more responses')
                    break
                else:
                    print('received {!r} from {}'.format( data, server))
                    if(server != None):                    
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        ip = server[0]
                        print(f'me voy a conectar al ip: {ip}')
                        s.connect((ip, PORT))
                        self.connections_out_Rlock.acquire()
                        self.connections_out[ip]=s
                        self.connections_out_Rlock.release()
                        print(f'Me conecte a: {ip}')
                        self.connection_threads.append(threading.Thread(target=self.send_server, args=(ip,)))
                        self.connection_threads[-1].start()
                    if len(self.connections_out)==2: #si estoy replicando para 2 server salgo
                        print('ya replico a 2 server\n')
                        break
        finally:
            print('closing socket')
            sock.close()
            thread2 = threading.Thread(target=self.create_server)
            thread2.start()

    def create_server(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((socket.gethostbyname(socket.gethostname()), PORT))
        print('creando server ip: ' + socket.gethostbyname(socket.gethostname()))
        sock.listen(5)
        while True:
            client_socket, client_address = sock.accept()
            ip=client_address[0]
            self.connections_in_Rlock.acquire()
            self.connections_in[ip]=client_socket
            self.connections_in_Rlock.release()
            print(f"\nAcepte conexion de: {ip}!")
            thread_rec = threading.Thread(target=self.receiver, args=(ip, ))
            thread_rec.start()
                
    def receiver(self, ip):
        self.connections_in_Rlock.acquire()
        sock = self.connections_in[ip]
        self.connections_in_Rlock.release()

        while True:
            try:
                bytes = sock.recv(1024)
                #print ('len(x)='+str(len(x)))
                if(len(bytes) != 0):
                    msg = pickle.loads(bytes)
                    print(msg)        #bytes.decode('UTF-8') o bytes.decode()
                    if(type(msg) == CR2 and len(self.connections_in) < 2):
                        print('recibi un cr2')
                        self.CR.active = True
                        self.CR.count = 0
                    elif(type(msg) == CR):
                        ips = msg.sms
                        if(ips == socket.gethostbyname(socket.gethostname())):
                            print('hello')
                            self.CR2.active = True
                        elif(len(self.connections_out) < 2 and ips not in self.connections_out and ips != socket.gethostbyname(socket.gethostname())):
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            print(f'me voy a conectar para cerrar anillo al ip: {ips}')
                            s.connect((ips, PORT))
                            self.connections_out_Rlock.acquire()
                            self.connections_out[ips]=s
                            self.connections_out_Rlock.release()
                            print(f'Me conecte para cerrar anillo a: {ips}')
                            self.connection_threads.append(threading.Thread(target=self.send_server, args=(ips,)))
                            self.connection_threads[-1].start()
                            
                            self.CR.sms = msg                      

                time.sleep(0.5)

            except socket.timeout:
                    time.sleep(1)
                    continue
            except socket.error as e:
                    print('Socket error al recv: {}'.format(e.errno))
                    break
        
    def send_server(self, ip):

        self.connections_out_Rlock.acquire()
        sock = self.connections_out[ip]
        self.connections_out_Rlock.release()
        
        while True:
            sms = None
            if(self.CR2.active and self.CR2.count < len(self.connections_out)):
                sms = pickle.dumps(self.CR2)
                self.CR2.count += 1
            elif self.CR.count < len(self.connections_out) or self.CR.active:
                if(self.multicast_closed and len(self.connections_in) < 2):
                    ips = socket.gethostbyname(socket.gethostname())
                    self.CR.sms = ips
                    sms = pickle.dumps(self.CR)
                    self.CR.count += 1
                elif(self.CR.sms != None):
                    sms = pickle.dumps(self.CR.sms)
                    self.CR.count += 1

            try:
                if(sms != None):
                    sock.send(sms)  #msg.encode('UTF-8')
            except socket.error as e:
                print ('socket erroe: {}'.format(e.errno))
                return
                
            time.sleep(3)

def main():
    s = server()
    s.send_multicast()

    thread1 = threading.Thread(target=s.receive_multicast)
    thread1.start()

main()

