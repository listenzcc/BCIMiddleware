''' TCP Server for BCI Simulation '''

import json
import socket
import threading
import traceback

IP = 'localhost'
port = 63365
buffer_size = 1024
coding = 'utf-8'


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
    for key in dct:
        dct[key] = decode(dct[key])
    return json.dumps(dct)


def keepAliveMessage():
    return pack(dict(method='keepAlive', count='1'))


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
        print('There are {} alive sessions, squeezed from {}'.format(
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
        print(f'TCP server binds on {IP}:{port}')

    def serve(self):
        ''' Start serving.
        - Listen forever;
        - Generate separated thread to serve incoming sessions;
        - self.new_session function is used for handling.
        '''
        # Listen
        self.server.listen(1)
        print(f'TCP server is listening')

        # Generate thread
        thread = threading.Thread(target=self.new_session,
                                  name='TCP session interface')
        thread.setDaemon(True)
        thread.start()
        print(f'TCP server is ready for new session')

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
            print(f'New session established: {client} at {address}')
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
        print(f'Client connected: {self.address}')

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

        print(f'Client closed: {self.address}')

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
                print(f'Received {income} from {self.address}')

                # ----------------------------------------------------------------
                # Terminating commands
                if income == b'':
                    self.close()
                    break

                # ----------------------------------------------------------------
                # Unpack incoming message.
                # It should be json object and parsed into a dict.
                try:
                    dct = unpack(income)
                except:
                    print(f'Failed to unpack message: "{income}"')
                    continue
                print(f'Parsed message {dct} from {self.address}')

                # ----------------------------------------------------------------
                # Keep alive message
                if all([dct.get('method', None) == 'keepAlive',
                        dct.get('count', None) == '0']):
                    print(f'Received keepAlive message')
                    self.send(keepAliveMessage())
                    continue

            except ConnectionResetError as err:
                print(f'Connection reset occurs. It can be normal.')
                break

            except Exception as err:
                print(f'Unexpected error: {err}')
                traceback.print_exc()
                break

        self.close()

    def send(self, message):
        ''' Send message to the client.

        Args:
        - @message: The message to be sent.
        '''
        if isinstance(message, dict):
            msg = encode(pack(message))
        else:
            msg = encode(message)

        self.client.sendall(msg)
        print(f'Sent "{message}" to {self.address}')
