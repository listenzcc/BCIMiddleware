'''
File: TCPClient.py
Aim: Define TCP client object for BCI application.
'''

# Imports
import socket
import threading
import traceback

# Local Imports
from . import logger, tcp_params, decode, encode, pack, unpack


# TCPClient


class TCPClient(object):
    ''' TCP client object,
    it connects to the TCP server, sends and receives messages.
    '''

    def __init__(self, IP=tcp_params['IP'], port=tcp_params['port'], buffer_size=tcp_params['buffer_size']):
        ''' Initialize and setup client '''
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Connet to IP:port
        client.connect((IP, port))
        name = client.getsockname()

        # Setup client and name
        self.buffer_size = buffer_size
        self.serverIP = IP
        self.client = client
        self.name = name
        logger.info(f'TCP Client is initialized as {name} to {IP}')

        # Keep listening
        client.listen()

    def _listen(self):
        ''' Listen to the server.
        - Received the message;
        - Send reply;
        - It will be closed if it receives empty message or error occurs.
        '''
        logger.info(f'Start listening to {self.serverIP}')

        while True:
            try:
                # ----------------------------------------------------------------
                # Wait until new message is received
                income = self.client.recv(self.buffer_size)

                if income == b'':
                    logger.debug('Received empty message')
                    self.client.close()
                    logger.debug('Connection is closed to {self.serverIP}')
                    break

                logger.debug(f'Received message: {income}')

            except ConnectionResetError as err:
                logger.warning(f'Connection reset occurs. It can be normal.')
                break

            except Exception as err:
                logger.error(f'Unexpected error: {err}')
                traceback.print_exc()
                break

        logger.info(f'Stopped listening to {self.serverIP}')

    def listen(self):
        ''' Keep listening to the server '''
        thread = threading.Thread(target=self._listen,
                                  name='TCPClient Listening')
        thread.setDaemon(True)
        thread.start()
        logger.debug(f'Keep Listening to the {self.serverIP}')

        # Say hello to server
        self.send(f'Hello from client: {self.name}')

    def send(self, message):
        ''' Send [message] to server
        Args:
        - @message: The message to be sent
        '''
        message = encode(message)
        self.client.sendall(message)
        self.debug(f'Sent "{message}" to {self.serverIP}')
