import socket
import struct
import threading
import sys

PORT = 1111

connections_out = []
connections_in = []

connection_threads = []
#block = threading.RLock()

def receive_multicast():
    global connections_in
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
    sock.setsockopt(
        socket.IPPROTO_IP,
        socket.IP_ADD_MEMBERSHIP,
        mreq)
    
    # Receive/respond loop
    while True:
        print('\nwaiting to receive message')
        data, address = sock.recvfrom(1024)
        
        print('received {} bytes from {}'.format(
            len(data), address))
        print(data)
        if(len(connections_in) < 2):
            print('sending acknowledgement to', address)
            sock.sendto(b'ack', address)
        
def send_multicast():
    global connections_out
    global connection_threads
    message = b'very important data'
    multicast_group = ('224.3.29.71', 10000)

    # Create the datagram socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    sock.settimeout(0.2)

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
                if(server != None):
                    connections_out.append(server[0])
            except socket.timeout:
                print('timed out, no more responses')
                break
            else:
                print('received {!r} from {}'.format(
                    data, server))
                if(server != None):                    
                    # for i, val in enumerate(connections):
                    #     print(f'connections[{i}] = {val}')
                    connection_threads.append(threading.Thread(target=connect_server, args=(server[0],)))
                    connection_threads[-1].start()
                    # thread3 = threading.Thread(target=connect_server, args=(server[0],))
                    # thread3.start()

    finally:
        print('closing socket')
        sock.close()
        thread2 = threading.Thread(target=create_server)
        thread2.start()

def create_server():
    global connections_in
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((socket.gethostbyname(socket.gethostname()), PORT))
    print('creando server ip: ' + socket.gethostbyname(socket.gethostname()))
    sock.listen(5)
    while True:
        client_socket, client_address = sock.accept()
        connections_in.append(client_address)
        print(f"\nSe me conecto: {client_address}!")

def connect_server(ip):
    #global block
    #block.acquire()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f'me voy a conectar al ip: {ip}')
    s.connect((ip, PORT))
    print(f'Me conecte a: {ip}')
    #block.release()


send_multicast()

thread1 = threading.Thread(target=receive_multicast)
thread1.start()