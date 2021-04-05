import time
import threading
import numpy as np


default_kwargs = dict(
    n_channels=64,  # Number of channels
    interval=1,  # Seconds
    freq=100,  # Hz
    latest_length=2,  # Seconds
)


def get_latest_device(simulation=True):
    ''' Get the latest data from the device,
    it may change over time.
    '''
    # Simulation
    if simulation:
        d = np.zeros((100, 64))
        return d

    # Real application
    # todo: Read the latest data from the device
    print(f'Getting latest data by amazing code.')
    return None


class DataStack(object):
    ''' The data stack.

    Useful methods:
    - @start: Start the data collecting;
    - @stop: Stop the data collecting;
    - @save: Save the data to the disk;
    - @latest: Get the latest data from the stack;
    - @report: Get the current state of the report.
    '''

    def __init__(self, filepath, n_channels, interval, freq, latest_length):
        ''' Initialize the data stack

        Args:
        - @filepath: Where the data will be stored in;
        - @n_channels: Number of channels, has default value;
        - @interval: The interval of collecting data from the device, has default value;
        - @freq: The sampling frequency, has default value;
        - @latest_length: The length of data at fetching the latest data.
        '''
        self.filepath = filepath

        self.n_channels = n_channels
        self.interval = interval
        self.freq = freq
        self.latest_length = latest_length

        self._reset()

        print(
            f'Initialized with filepath: {filepath}, n_channels: {n_channels}, interval: {interval}')

    def _reset(self):
        # Built-in method of reseting the state
        self.state = 'free'
        self.data = np.zeros((0, self.n_channels))

    def _add(self, data):
        ''' Built-in method of add the data into the stack

        Args:
        - @data: The data to be added
        '''
        self.data = np.concatenate([self.data, data], axis=0)
        print(f'Data stack is changed to the shape of {self.data.shape}')

    def _keep_collecting(self):
        # Keep collecting the data
        print(f'Collecting starts at {time.ctime()}')
        while self.state == 'collecting':
            d = get_latest_device()
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

    def save(self):
        # Save the data to the disk
        d = self.data
        print(f'Saving the data ({d.shape}) to {self.filepath}')

    def report(self):
        # Report the current state of the stack,
        # it may change on developping.
        print(f'Current data shape is: {self.data.shape}')

    def latest(self, length=None):
        ''' Get the latest data by the [length]

        Args:
        - @length: The length of the fetched data, the unit is 'second', the default value is None,
                   the None value means the self.latest_length will be used.
        '''
        if length is None:
            length = self.latest_length

        n = length * self.freq
        if self.data.shape[0] < n:
            print(
                f'Warning: There is not enough data for your request of length={length}')
        return self.data[-n:]


if __name__ == '__main__':
    ds = DataStack('default_name', **default_kwargs)

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

        if inp == 't':
            ds.start()
            continue

        if inp == 'k':
            ds.stop()
            continue

        if inp == 's':
            ds.save()
            continue

    print('Done')
