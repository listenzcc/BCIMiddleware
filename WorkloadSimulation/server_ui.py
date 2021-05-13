# %%
'''
TCP server interface for console.
The TCP server will be automatically built.

- @interface: The function for user interface, and keep the server running.
'''

import os
import time
import json
from TCPServerSimulation import TCPServer

# %%
# Coding Tools
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


# %%
# Sessions
folder = r'D:\BCIMiddlewareFolder\DataFolder'


def path(name):
    return os.path.join(folder, name)


def training(send):
    send(pack(dict(
        method='startSession',
        sessionName='training',
        dataPath=path('d1.data')
    )))

    time.sleep(100)

    send(pack(dict(
        method='stopSession',
        sessionName='training'
    )))


def building(send):
    send(pack(dict(
        method='startBuilding',
        sessionName='youbiaoqian',
        dataPath=path('d1.data'),
        modelPath=path('m1.model')
    )))


def youbiaoqian(send):
    send(pack(dict(
        method='startSession',
        sessionName='youbiaoqian',
        dataPath=path('d2.data'),
        modelPath=path('m1.model'),
        newModelPath=path('m1-1.model'),
        updateCount="4"
    )))

    time.sleep(100)

    send(pack(dict(
        method='stopSession',
        sessionName='youbiaoqian'
    )))
    pass


def wubiaoqian(send):
    send(pack(dict(
        method='startSession',
        sessionName='wubiaoqian',
        dataPath=path('d3.data'),
        modelPath=path('m1.model')
    )))

    time.sleep(100)

    send(pack(dict(
        method='stopSession',
        sessionName='wubiaoqian'
    )))
    pass

# %%
# Interface


def interface():
    print(f'Interface starts')

    help_msg = dict(
        h="Show help message",
        q="Quit",
        list="List the alive sessions",
        send="Send message through all alive sessions, send [message]",
        training="Start training simulation",
        building="Start building simulation",
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

        if inp in ['training', 'building', 'youbiaoqian', 'wubiaoqian']:
            session = None

            for session in server.alive_sessions():
                break

            if session is None:
                print(f'No client connected')
                continue

            if inp == 'training':
                training(session.send)

            if inp == 'building':
                building(session.send)

            if inp == 'youbiaoqian':
                youbiaoqian(session.send)

            if inp == 'wubiaoqian':
                wubiaoqian(session.send)

    print('ByeBye')
    print(f'Interface stops')
    return 0


# %%
# Main Entrance
if __name__ == '__main__':
    server = TCPServer()
    server.start()
    interface()
