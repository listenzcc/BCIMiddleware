import json
import time
from TCPClient import TCPClient


def unpack(pack):
    try:
        return json.loads(pack)
    except:
        return None


def pack(dct):
    return json.dumps(dct)


if __name__ == '__main__':
    client = TCPClient()
    client.connect()

    client.send(pack(dict(
        method='startSession',
        sessionName='asynchronous',
        dataPath='D:\\BCIMiddlewareFolder\\data-2.npy',
        modelPath='D:\\BCIMiddlewareFolder\\model.txt'
    )))

    for _ in range(3):
        time.sleep(3)
        client.send(pack(dict(
            method='computeLabel'
        )))

    client.send(pack(dict(
        method='stopSession',
        sessionName='synchronous'
    )))

input('Press Enter to Escape')

print('ByeBye')
