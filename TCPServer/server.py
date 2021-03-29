'''
TCP server interface for console.
The TCP server will be automatically built.

- @interface: The function for user interface, and keep the server running.
'''

from . import logger
from .defines import TCPServer

server = TCPServer()
server.start()


def interface():
    logger.info(f'Interface starts')

    help_msg = dict(
        h="Show help message",
        q="Quit",
        list="List the alive sessions",
        send="Send message through all alive sessions, send [message]"
    )

    while True:
        inp = input('>> ')

        if inp == 'q':
            break

        if inp == 'h':
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

    print('ByeBye')
    logger.info(f'Interface stops')
    return 0
