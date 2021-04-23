import time
import threading
import traceback
from BCIClient.TCPClient import TCPClient


def keep_try():
    while True:
        try:
            client = TCPClient()
        except:
            traceback.print_exc()
        time.sleep(5)


if __name__ == '__main__':
    thread = threading.Thread(target=keep_try)
    thread.setDaemon(True)
    thread.start()

    while 'q' == input('Press q to Escape'):
        break

    print('Done')
