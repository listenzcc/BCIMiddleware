import time
import threading
import numpy as np

n_channels = 64  # Number of channels
interval = 1  # Seconds
freq = 1000  # Hz


def get_latest_data(simulation=True):
    ''' Get the latest data from the device
    '''
    # Simulation
    if simulation:
        d = np.zeros((n_channels, 10))
        return d

    # Real application
    print(f'Getting latest data by amazing code.')
    return None


class DataStack(object):
    ''' The data stack.
    Useful methods:
    - @start: Start the data collecting;
    '''

    def __init__(self, filepath, n_channels=n_channels, interval=interval, freq=freq):
        ''' Initialize the data stack

        Args:
        - @filepath: Where the data will be stored in;
        - @n_channels: Number of channels, has default value;
        - @interval: The interval of collecting data from the device, has default value;
        - @freq: The sampling frequency, has default value.
        '''
        self.filepath = filepath

        self.n_channels = n_channels
        self.interval = interval
        self.freq = freq

        self._reset()

        print(
            f'Initialized with filepath: {filepath}, n_channels: {n_channels}, interval: {interval}')

    def _reset(self):
        # Built-in method of reseting the state
        self.state = 'free'
        self.data = np.zeros((self.n_channels, 0))

    def _add(self, data):
        ''' Built-in method of add the data into the stack

        Args:
        - @data: The data to be added
        '''
        self.data = np.concatenate([self.data, data], axis=1)
        print(f'Data stack is changed to the shape of {self.data.shape}')

    def _keep_collecting(self):
        # Keep collecting the data
        print(f'Collecting starts at {time.ctime()}')
        while self.state == 'collecting':
            d = get_latest_data()
            self._add(d)
            time.sleep(self.interval)
        print(f'Collecting stopped at {time.ctime()}')

    def start(self):
        # Start the thread to keep collecting the data
        self._reset()
        self.state = 'collecting'
        thread = threading.Thread(target=self._keep_collecting)
        thread.setDaemon(True)
        thread.start()

    def stop(self):
        # Stop the collecting thread
        self.state = 'stopped'

    def report(self):
        # Report the current state of the stack,
        # it may change on developping.
        print(f'Current data shape is: {self.data.shape}')

    def latest(self, length=2):
        ''' Get the latest data by the [length]

        Args:
        - @length: The length of the fetched data, the unit is 'second', the default value is 2
        '''
        n = length * self.freq
        if self.data.shape[0] < n:
            print(
                f'Warning: There is not enough data for your request of length={length}')
        return self.data[-n:]


if __name__ == '__main__':
    ds = DataStack('default_name')

    ds.start()

    while True:
        inp = input('>> ')
        if inp == 'q':
            break

        if inp == 'r':
            ds.report()
            continue

        if inp == 'l':
            print(ds.latest().shape)
            continue

        if inp == 'start':
            ds.start()
            continue

        if inp == 's':
            ds.stop()
            continue

    print('Done')
