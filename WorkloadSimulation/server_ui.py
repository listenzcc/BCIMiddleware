'''
TCP server interface for console.
The TCP server will be automatically built.

- @interface: The function for user interface, and keep the server running.
'''

import time
import json
from TCPServerSimulation import TCPServer


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


server = TCPServer()
server.start()


def training(send):
    send(pack(dict(
        method='startSession',
        sessionName='training',
        subjectID="subject-1"
    )))

    time.sleep(100)

    send(pack(dict(
        method='stopSession',
        sessionName='training'
    )))


def youbiaoqian(send):
    send(pack(dict(
        method='startSession',
        sessionName='youbiaoqian',
        subjectID="subject-1",
        sessionCount="1",
        updateCount="4"
    )))

    time.sleep(10)

    send(pack(dict(
        method='stopSession',
        sessionName='youbiaoqian'
    )))
    pass


def wubiaoqian(send):
    send(pack(dict(
        method='startSession',
        sessionName='wubiaoqian',
        subjectID="subject-1",
        sessionCount="1"
    )))

    time.sleep(10)

    send(pack(dict(
        method='stopSession',
        sessionName='wubiaoqian'
    )))
    pass


def interface():
    print(f'Interface starts')

    help_msg = dict(
        h="Show help message",
        q="Quit",
        list="List the alive sessions",
        send="Send message through all alive sessions, send [message]",
        training="Start training simulation",
        youbiaoqian="Start youbiaoqian simulation",
        wubiaoqian="Start wubiaoqian simulation"
    )

    while True:
        inp = input('>> ')

        if inp == 'q':
            break

        if inp == 'h' or inp == '':
            for key, value in help_msg.items():
                print(f'{key}: {value}')
            continue

        if inp == 'list':
            for i, session in enumerate(server.alive_sessions()):
                print(f'[{i}]', session.address)
            continue

        if inp.startswith('send '):
            message = inp.split(' ', 1)[1]
            for session in server.alive_sessions():
                session.send(message)
            continue

        if inp in ['training', 'youbiaoqian', 'wubiaoqian']:
            session = None

            for session in server.alive_sessions():
                break

            if session is None:
                print(f'No client connected')
                continue

            if inp == 'training':
                training(session.send)

            if inp == 'youbiaoqian':
                youbiaoqian(session.send)

            if inp == 'wubiaoqian':
                wubiaoqian(session.send)

    print('ByeBye')
    print(f'Interface stops')
    return 0


if __name__ == '__main__':
    interface()
