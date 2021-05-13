'''
File: TCPClient.py
Aim: Define TCP client object for BCI application.
'''

# Imports
import time
import socket
import threading
import traceback

# Local Imports
from .sessions import TrainSession, BuildSession, ActiveSession, PassiveSession
from . import logger, tcp_params, decode, encode, pack, unpack, active_interval

# ------------------------------------------------------
# Pack Useful Messages

# Keep Alive Message


def keepAliveMessage(count='0'):
    ''' Make keep alive message '''
    logger.debug(f'Make keepAliveMessage')
    return pack(dict(method='keepAlive', count=count))

# Error Messages of Invalid Message Received


def invalidMessageError(raw, comment=''):
    ''' Make error message of invalid message received '''
    logger.error(f'InvalidMessageError: {raw}, {comment}')
    return pack(dict(method='error',
                     reason='invalidMessage',
                     raw=raw,
                     comment=comment))

# Error Message of Operation Failed


def operationFailedError(raw, detail='undefinedError', comment=''):
    ''' Make error message of operation failed '''
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

        self.session = None

        # Keep listening
        self.keep_listen()

    def close(self):
        ''' Close the session '''
        # Close the client
        self.client.close()
        self.is_connected = False

        # Stop the data stack
        if self.session is not None:
            self.session.ds.stop()

        logger.info(f'Client closed: {self.serverIP}')

    def keep_listen(self):
        ''' Keep listening to the server.
        - Received the message;
        - Send reply;
        - It will be closed if it receives empty message or error occurs.
        '''
        logger.info(f'Start listening to {self.serverIP}')

        thread = threading.Thread(target=self._keep_send_keepAliveMessages)
        thread.setDaemon(True)
        thread.start()

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
                    self.send(keepAliveMessage('1'))
                    continue

                if all([dct.get('method', None) == 'keepAlive',
                        dct.get('count', None) == '1']):
                    logger.debug(
                        f'Received replied keepAlive message, doing nothing.')
                    continue

                # ----------------------------------------------------------------
                # Start Training Session
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'training',
                        dct.get('dataPath', None) is not None,
                        self.session == None]):

                    logger.info(f'Training session is starting')

                    # Startup Training Session
                    try:
                        kwargs = dict(filepath=dct['dataPath'])

                        self.session = TrainSession(**kwargs)
                        logger.info(f'Training session started')
                    except:
                        self.session = None
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed start training session for "{kwargs}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    continue

                # ----------------------------------------------------------------
                # Start and Finish Build Session
                if all([dct.get('method', None) == 'startBuilding',
                        dct.get('sessionName') in [
                    'youbiaoqian', 'wubiaoqian'],
                        dct.get('dataPath', None) is not None,
                        dct.get('modelPath', None) is not None,
                        self.session == None]):

                    t_start = time.time()
                    logger.info(f'Building session is starting')

                    # Starting Building Session
                    try:
                        kwargs = dict(sessionname=dct['sessionName'],
                                      filepath=dct['dataPath'],
                                      decoderpath=dct['modelPath'])

                        self.session = BuildSession(**kwargs)
                        logger.info(f'Building session started')
                    except:
                        self.session = None
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed start building session for "{kwargs}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    # Compute Accuracy using Validation
                    try:
                        acc = self.session.decoder.k_fold_valid()
                        logger.info(
                            f'Validation Accuracy is Computed, Accuracy is {acc}')
                        self.send(dict(method='stopBuilding',
                                       sessionName=dct['sessionName'],
                                       validAccuracy=f'{acc}'))
                    except:
                        self.session = None
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed computing validation accuracy for "{kwargs}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    self.session = None
                    cost = time.time() - t_start
                    logger.info(
                        f'Building session finished, costing "{cost}" seconds')
                    continue

                # ----------------------------------------------------------------
                # Start Active Session
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'wubiaoqian',
                        dct.get('dataPath', None) is not None,
                        dct.get('modelPath', None) is not None,
                        self.session == None]):
                    logger.info(f'Active session is starting')

                    # Start Active Session
                    try:
                        kwargs = dict(
                            filepath=dct['dataPath'],
                            decoderpath=dct['modelPath'],
                            interval=active_interval,
                            send=self.send
                        )

                        self.session = ActiveSession(**kwargs)
                        logger.info(
                            f'Active session started, the labels will be sent every {active_interval} seconds.')
                    except:
                        self.session = None
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed start active session for "{kwargs}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    continue

                # ----------------------------------------------------------------
                # Start Passive Session
                if all([dct.get('method', None) == 'startSession',
                        dct.get('sessionName', None) == 'youbiaoqian',
                        dct.get('dataPath', None) is not None,
                        dct.get('modelPath', None) is not None,
                        dct.get('newModelPath', None) is not None,
                        dct.get('updateCount', None) is not None,
                        self.session == None]):
                    logger.info(f'Passive module is starting')

                    # Start Passive Module
                    try:
                        kwargs = dict(
                            filepath=dct['dataPath'],
                            decoderpath=dct['modelPath'],
                            updatedecoderpath=dct['newModelPath'],
                            update_count=int(dct['updateCount']),
                            send=self.send,
                        )
                        self.session = PassiveSession(**kwargs)
                        logger.info(
                            f'Passive session started, the labels will be sent at every requests.')
                    except:
                        self.session = None
                        error = traceback.format_exc()
                        logger.error(
                            f'Failed start passive session for "{kwargs}", error is "{error}"')
                        self.send(operationFailedError(income, comment=error))
                        continue

                    continue

                # ----------------------------------------------------------------
                # Feed
                if self.session is not None:
                    success, rdct = self.session.receive(dct)

                    logger.debug(
                        f'Module received {dct}, operation returned {success}:{rdct}')

                    if success == 0:
                        self.send(rdct)
                    else:
                        self.send(invalidMessageError(income,
                                                      comment=rdct['comment']))

                    # Remove existing module if it has stopped
                    if self.session.stopped:
                        self.session = None
                        logger.info(
                            f'Current session stopped for {self.serverIP}.')

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
                detail = traceback.format_exc()
                print(f'E: {detail}')
                logger.error(f'Unexpected error: {err}')
                logger.debug(f'Unexpected error detail: {detail}')
                self.send(operationFailedError(income,
                                               comment=f'Connection will be reset due to the undefined problems "{err}", detail is "{detail}"'))
                break

        self.close()
        logger.info(f'Stopped listening to {self.serverIP}')

    def _keep_send_keepAliveMessages(self):
        msg = keepAliveMessage('0')
        logger.debug(f'Start keep sending keepAliveMessage')
        while True:
            time.sleep(5)
            try:
                self.send(msg)
            except:
                err = traceback.format_exc()
                logger.debug(f'Failed on sending keepAliveMessage: {err}')
                break
        logger.debug(f'Stopped keep sending keepAliveMessage')

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
