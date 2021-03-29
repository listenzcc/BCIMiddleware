'''
File: TCP_client_interface.py
Aim: Start new TCP client and make interface for it in the console.

- @interface: The function for starting client and user interface.
'''

from TCPClient import TCPClient

if __name__ == '__main__':
    client = TCPClient()
    client.connect()

    help_msg = dict(
        h="Show help message",
        q="Quit",
        terminate="Terminate the client",
        send="Send message through all alive sessions, send [message]"
    )

    while True:
        inp = input('>> ')

        if inp == 'h':
            for key, value in help_msg.items():
                print(f'{key}: {value}')
            continue

        if inp == 'q':
            client.send('Terminate')
            break

        if inp == 'terminate':
            client.send('Terminate')
            break

        if inp.startswith('send '):
            message = inp.split(' ', 1)[1]
            client.send(message)
            continue

    input('ByeBye, press enter to escape.')
