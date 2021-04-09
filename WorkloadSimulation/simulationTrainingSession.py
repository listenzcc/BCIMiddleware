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
        sessionName='training',
        dataPath='H:\\BCIMiddlewareFolder\\data.npy',
        modelPath='H:\\BCIMiddlewareFolder\\model.txt'
    )))

    time.sleep(10)

    client.send(pack(dict(
        method='stopSession',
        sessionName='training'
    )))

input('Press Enter to Escape')

print('ByeBye')
