'''
File: TCPClient.py
Aim: Define TCP client object for BCI application.
'''

# Imports
import os
import socket
import threading
import traceback

# Local Imports
from .modules import TrainModule, ActiveModule, PassiveModule
from .subject import BCISubject
from . import logger, tcp_params, decode, encode, pack, unpack, active_interval

# Keep Alive Message


def keepAliveMessage():
    return pack(dict(method='keepAlive', count='1'))

# Error Messages


def invalidMessageError(raw, comment=''):
    logger.error(f'InvalidMessageError: {raw}, {comment}')
    return pack(dict(method='error',
                     reason='invalidMessage',
                     raw=raw,
                     comment=comment))


def operationFailedError(raw, detail='undefinedError', comment=''):
    logger.error(f'OperationFailedError: {raw}, {comment}')
    return pack(dict(method='error',
                     reason='operationFailed',
                     detail=detail,
                     raw=raw,
                     comment=comment))

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

        self.module = None

        # Keep listening
        self.keep_listen()

    def close(self):
        ''' Close the session '''
        self.client.close()
        self.is_connected = False

        if self.module is not None:
            self.module.ds.stop()

        logger.info(f'Client closed: {self.serverIP}')

    def keep_listen(self):
        ''' Keep listening to the server.
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
                    break
                logger.debug(f'Received message: {income}')

                # ----------------------------------------------------------------
                # Unpack incoming message.
                # It should be json object and parsed into a dict.
                dct = unpack(income)
                # If unpack fails,
                # send invalid message error.
                if dct is None:
                    self.send(invalidMessageError(income,
                                                  comment=f'Illegal JSON from {self.serverIP}'))
                    continue
                logger.debug(f'Parsed message "{dct}" from {self.serverIP}')

                # ----------------------------------------------------------------
                # Keep alive message
                if all([dct.get('method', None) == 'keepAlive',
                        dct.get('count', None) == '0']):
                    logger.debug(f'Received keepAlive message')
                    self.send(keepAliveMessage())
                    continue

                # ----------------------------------------------------------------
                # Start Training Module
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'training',
                        dct.get('subjectID', None) is not None,
                        self.module == None]):
                    logger.info(f'Training module is starting')

                    # Prepare Subject Folders
                    subjectID = dct['subjectID']
                    try:
                        subject = BCISubject(subjectID)
                        _path = subject.get_training_path()
                        kwargs = dict(
                            filepath=_path['data'],
                            decoderpath=_path['model'],
                        )
                    except:
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed to initialize subject for "{subjectID}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    # Startup Training Module
                    try:
                        self.module = TrainModule(**kwargs)
                        logger.info(f'Training module started')
                    except:
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed start training module for "{subjectID}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    continue

                # ----------------------------------------------------------------
                # Start Active Module
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'wubiaoqian',
                        dct.get('subjectID', None) is not None,
                        dct.get('sessionCount', None) is not None,
                        self.module == None]):
                    logger.info(f'Active module is starting')

                    subjectID = dct['subjectID']
                    sessionCount = dct['sessionCount']

                    # Prepare Subject Folders
                    # Setup Active Parameters
                    try:
                        subject = BCISubject(subjectID)
                        subject.set_wubiaoqian(sessionCount)
                        _path = subject.get_wubiaoqian_path(sessionCount)
                        kwargs = dict(
                            filepath=_path['data'],
                            decoderpath=_path['model'],
                            interval=active_interval,
                            send=self.send
                        )
                    except:
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed to initialize subject for "{subjectID}" - "{sessionCount}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    # Start Active Module
                    try:
                        self.module = ActiveModule(**kwargs)
                        logger.info(
                            f'Active module started, the labels will be sent every {active_interval} seconds.')
                    except:
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed start active module for "{subjectID}" - "{sessionCount}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    continue

                # ----------------------------------------------------------------
                # Start Passive Module
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'youbiaoqian',
                        dct.get('subjectID', None) is not None,
                        dct.get('sessionCount', None) is not None,
                        dct.get('updateCount', None) is not None,
                        self.module == None]):
                    logger.info(f'Passive module is starting')

                    subjectID = dct['subjectID']
                    sessionCount = dct['sessionCount']
                    updateCount = int(dct['updateCount'])

                    # Prepare Subject Folders
                    # Setup Passive Parameters
                    try:
                        subject = BCISubject(subjectID)
                        subject.set_youbiaoqian(sessionCount)
                        _path = subject.get_youbiaoqian_path(sessionCount)
                        kwargs = dict(
                            filepath=_path['data'],
                            decoderpath=_path['model'],
                            updatedecoderpath=_path['model_update'],
                            update_count=updateCount,
                            send=self.send,
                        )
                    except:
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed to initialize subject for "{subjectID}" - "{sessionCount}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    # Start Passive Module
                    try:
                        self.module = PassiveModule(**kwargs)
                        logger.info(
                            f'Passive module started, the labels will be sent at every requests.')
                    except:
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed start passive module for "{subjectID}" - "{sessionCount}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    continue

                # ----------------------------------------------------------------
                # Feed
                if self.module is not None:
                    success, rdct = self.module.receive(dct)

                    logger.debug(
                        f'Module received {dct}, operation returned {success}:{rdct}')

                    if success == 0:
                        self.send(rdct)
                    else:
                        self.send(invalidMessageError(income,
                                                      comment=rdct['comment']))

                    # Remove existing module if it has stopped
                    if self.module.stopped:
                        self.module = None
                        logger.info(
                            f'Current module stopped for {self.serverIP}.')

                    continue

                # ----------------------------------------------------------------
                # No operation is done
                self.send(invalidMessageError(income,
                                              comment=f'Invalid operation from {self.serverIP}'))

            except KeyboardInterrupt:
                logger.error(f'Keyboard Interruption is detected')
                break

            except ConnectionResetError as err:
                logger.warning(
                    f'Connection reset occurs. It can be normal when server closes the connection.')
                break

            except Exception as err:
                logger.error(f'Unexpected error: {err}')
                traceback.print_exc()
                break

        self.close()
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
        if isinstance(message, dict):
            msg = encode(pack(message))
            logger.debug(f'Pack dict message: "{message}"')
        else:
            msg = encode(message)
        self.client.sendall(msg)
        logger.debug(f'Sent "{msg}" to {self.serverIP}')
