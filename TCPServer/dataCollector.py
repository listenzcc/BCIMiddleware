import time
import threading
import numpy as np

n_channels = 64


class StackedData(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = np.zeros((n_channels, 0))
        print(f'Initialized with {filepath}')

    def concat(self, data):
        self.data = np.concatenate([self.data, data], axis=1)

    def report(self):
        print(f'Current data shape is: {self.data.shape}')


def add_data_timely(sd, interval=1):
    d = np.zeros((n_channels, 10))

    def add(sd, d):
        while True:
            sd.concat(d)
            time.sleep(interval)

    thread = threading.Thread(target=add, args=(sd, d))
    thread.setDaemon(True)
    thread.start()


if __name__ == '__main__':
    sd = StackedData('default_name')

    add_data_timely(sd)

    while True:
        inp = input('>> ')
        if inp == 'q':
            break

        if inp == 'r':
            sd.report()

    print('Done')
