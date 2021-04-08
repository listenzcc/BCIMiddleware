'''
File: TCPServer/defines.py
Describe:
Defines TCPServer and ClientConnection objects.
TCPServer will serve forever and it handles several TCP sessions.
- @TCPServer: The TCP socket server;
- @TCPSession: The Client connection handler used by the TCPServer;
'''

# Imports
import json
import socket
import threading
import traceback

from .modules import TrainModule, ActiveModule, PassiveModule
from . import logger, cfg

# Read configures
IP = cfg['Server']['localIP']
port = int(cfg['Server']['localPort'])
buffer_size = int(cfg['Server']['bufferSize'])
coding = cfg['Server']['coding']
interval = 2

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


def unpack(pack):
    try:
        return json.loads(pack)
    except:
        return None


def pack(dct):
    return json.dumps(dct)


# Error Messages
def invalidMessageError(raw, comment=''):
    logger.error(f'InvalidMessageError: {raw}, {comment}')
    return pack(dict(method='error',
                     reason='invalidMessage',
                     raw=decode(raw),
                     comment=decode(comment)))


def operationFailedError(raw, detail='', comment=''):
    logger.error(f'OperationFailedError: {raw}, {comment}')
    return pack(dict(method='error',
                     reason='operationFailed',
                     detail=detail,
                     raw=raw,
                     comment=comment))

# TCPServer


class TCPServer(object):
    ''' TCP server serves forever,
    it handles several sessions.
    '''

    def __init__(self):
        ''' Init by empty sessions pool '''
        self.server = None
        self.sessions = []

    def alive_sessions(self):
        ''' Remove disconnected sessions and return the remains '''
        n = len(self.sessions)
        self.sessions = [e for e in self.sessions if e.is_connected]
        logger.debug('There are {} alive sessions, squeezed from {}'.format(
            len(self.sessions), n))
        return self.sessions

    def start(self):
        ''' Run the pipeline to start serving '''
        self.bind()
        self.serve()

    def bind(self, IP=IP, port=port):
        ''' Bind the server to IP and port.
        Args:
        - @IP: The host IP;
        - @port: The port number, make sure it is large.
        '''
        assert(self.server is None)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((IP, port))
        self.server = server
        logger.info(f'TCP server binds on {IP}:{port}')

    def serve(self):
        ''' Start serving.
        - Listen forever;
        - Generate separated thread to serve incoming sessions;
        - self.new_session function is used for handling.
        '''
        # Listen
        self.server.listen(1)
        logger.info(f'TCP server is listening')

        # Generate thread
        thread = threading.Thread(target=self.new_session,
                                  name='TCP session interface')
        thread.setDaemon(True)
        thread.start()
        logger.info(f'TCP server is ready for new session')

    def new_session(self):
        ''' The function to handle new session.
        - Get client and address;
        - Generate TCP session with them;
        - Append into the sessions pool.
        '''
        while True:
            client, address = self.server.accept()
            session = TCPSession(client=client, address=address)
            session.send('Hello from server')
            logger.info(f'New session established: {client} at {address}')
            self.sessions.append(session)
            self.alive_sessions()


# TCPSession
class TCPSession(object):
    ''' Session object used by TCP server '''

    def __init__(self, client, address):
        ''' Init the session
        - Setup the session;
        - Mark it with is_connected = True.
        Args:
        - @client: The client object;
        - @address: The address of the client.
        '''
        self.client = client
        self.address = address
        self.start()
        self.is_connected = True
        self.module = None
        logger.info(f'Client connected: {self.address}')

    def start(self):
        ''' Take new thread to handle the client's message.
        - self.handle is used to handle messages.
        '''
        thread = threading.Thread(
            target=self.handle, name='TCP session handler')
        thread.setDaemon(True)
        thread.start()

    def close(self):
        ''' Close the session '''
        self.client.close()
        self.is_connected = False
        logger.info(f'Client closed: {self.address}')

    def handle(self):
        ''' It will serve the client's messaging until being forcedly closed.
        - Received the message;
        - Send reply;
        - It will be closed if it receives empty message or error occurs.
        '''
        while True:
            try:
                # ----------------------------------------------------------------
                # Receive new incoming message
                income = self.client.recv(buffer_size)
                logger.debug(f'Received {income} from {self.address}')
                self.send(f'Message is received: {income}')

                # ----------------------------------------------------------------
                # Terminating commands
                if income == b'':
                    self.close()
                    break

                if income == b'Terminate':
                    self.close()
                    break

                # ----------------------------------------------------------------
                # Unpack incoming message.
                # It should be parseable json object.
                dct = unpack(income)
                # If unpack fails,
                # send invalid message error.
                if dct is None:
                    self.send(invalidMessageError(income,
                                                  comment=f'Illegal JSON from {self.address}'))
                    continue
                logger.debug(f'Parsed message {dct} from {self.address}')

                # ----------------------------------------------------------------
                # Start training module
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'training'],
                        self.module == None):
                    logger.info(f'Training module is starting')
                    try:
                        self.module = TrainModule(filepath=dct['filepath'],
                                                  decoderpath=dct['decoderpath'])
                    except:
                        self.send(operationFailedError(income,
                                                       detail=f'folderInvalid, fileExists',
                                                       comment=f'Can not start training module for {self.address}'))
                    logger.info(f'Training module started')

                # ----------------------------------------------------------------
                # Start active module
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'synchronous'],
                        self.module == None):
                    logger.info(f'Active module is starting')
                    try:
                        self.module = ActiveModule(filepath=dct['filepath'],
                                                   decoderpath=dct['decoderpath'],
                                                   interval=interval)
                    except:
                        self.send(operationFailedError(income,
                                                       detail=f'folderInvalid, fileExists',
                                                       comment=f'Can not start active module for {self.address}'))
                    logger.info(
                        f'Active module started, the labels will be sent every {interval} seconds.')

                # ----------------------------------------------------------------
                # Start passive module
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'asynchronous'],
                        self.module == None):
                    logger.info(f'Passive module is starting')
                    try:
                        self.module = PassiveModule(filepath=dct['filepath'],
                                                    decoderpath=dct['decoderpath'])
                    except:
                        self.send(operationFailedError(income,
                                                       detail=f'folderInvalid, fileExists',
                                                       comment=f'Can not start active module for {self.address}'))
                    logger.info(
                        f'Passive module started, the labels will be sent at every requests.')

                # ----------------------------------------------------------------
                # Feed
                if self.module is not None:
                    success, rdct = self.module.receive(dct)

                    logger.debug(
                        f'Module receives {dct}, operation returns {success}:{rdct}')

                    if success == 0:
                        self.send(pack(rdct))
                    else:
                        self.send(invalidMessageError(income,
                                                      comment=rdct['comment']))

                    # Remove existing module if it has stopped
                    if self.module.stopped:
                        self.module = None

                # ----------------------------------------------------------------
                # Un dealed operation
                self.send(invalidMessageError(income,
                                              comment=f'Invalid operation from {self.address}'))

            except Exception as err:
                logger.error(f'Unexpected error: {err}')
                traceback.print_exc()
                self.close()
                break

    def send(self, message):
        ''' Send message to the client.
        Args:
        - @message: The message to be sent.
        '''
        msg = encode(message)
        self.client.sendall(msg)
        logger.debug(f'Sent {message} to {self.address}')
