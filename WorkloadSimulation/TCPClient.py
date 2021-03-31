'''
File: TCPClient.py
Aim:
Define the example TCP client object.
'''

# Imports
import os
import socket
import threading
import configparser

# Read configures
cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__),
                      '..',
                      'settings',
                      'default.cfg'))


IP = cfg['Server']['localIP']
port = int(cfg['Server']['localPort'])
buffer_size = int(cfg['Server']['bufferSize'])
coding = cfg['Server']['coding']

# Tools
# The TCP message is binary, so decoding and encoding is necessary.


def decode(content, coding=coding):
    ''' Decode [content] if necessary '''
    if isinstance(content, type(b'')):
        return content.decode(coding)
    else:
        return content


def encode(content, coding=coding):
    ''' Encode [content] if necessary '''
    if isinstance(content, type('')):
        return content.encode(coding)
    else:
        return content

# TCPClient


class TCPClient(object):
    ''' TCP client object,
    it connects to the TCP server, sends and receives messages.
    '''

    def __init__(self, IP=IP, port=port):
        ''' Initialize and setup client '''
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Connet to IP:port
        client.connect((IP, port))
        name = client.getsockname()

        # Setup client and name
        self.client = client
        self.name = name

    def listen(self):
        ''' Listen to the server.
        - Received the message;
        - Send reply;
        - It will be closed if it receives empty message or error occurs.
        '''
        while True:
            # Wait until new message is received
            income = self.client.recv(buffer_size)

            if income == b'':
                self.client.close()
                print('Client has been closed.')
                break

            print(f'Received message: {income}')
        print('ByeBye')

    def connect(self):
        ''' Require to establish a session to server '''
        thread = threading.Thread(target=self.listen,
                                  name='TCP client session')
        thread.setDaemon(True)
        thread.start()

        # Say hello to server
        self.send(f'Hello from client: {self.name}')

    def send(self, message):
        ''' Send [message] to server
        Args:
        - @message: The message to be sent
        '''
        message = encode(message)
        self.client.sendall(message)
