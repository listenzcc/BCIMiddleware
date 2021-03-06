import time
import socket
import struct
import threading
import numpy as np

from . import logger, cfg
from .neuroScanToolbox import NeuroScanDeviceClient

n_channels = int(cfg['Device']['numChannels'])  # Number of channels
freq = int(cfg['Device']['sampleRate'])  # Hz

default_kwargs = dict(
    n_channels=n_channels,
    freq=freq,
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
    logger.debug(f'Getting latest data by amazing code.')
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

    def __init__(self, filepath, n_channels=n_channels, freq=freq):
        ''' Initialize the data stack

        Args:
        - @filepath: Where the data will be stored in;
        - @n_channels: Number of channels, has default value;
        - @freq: The sampling frequency, has default value;
        '''
        self.filepath = filepath

        self.n_channels = n_channels
        self.freq = freq

        self._reset()

        self.nsclient = NeuroScanDeviceClient(cfg['Device']['deviceIP'],
                                              int(cfg['Device']['devicePort']),
                                              freq,
                                              n_channels)

        logger.debug(
            f'Initialized with filepath: {filepath}, n_channels: {n_channels}')

    def _reset(self):
        # Built-in method of reseting the state
        self.state = 'free'

    def get_data(self):
        d = self.nsclient.get_all()
        logger.debug(f'Got all data from device, shape is {d.shape}')
        return d

    def _add(self, data):
        ''' Built-in method of add the data into the stack

        Args:
        - @data: The data to be added
        '''
        self.data = np.concatenate([self.data, data], axis=0)
        logger.debug(
            f'Data stack is changed to the shape of {self.data.shape}')

    def start(self):
        # Start the thread to keep collecting the data
        self._reset()
        self.state = 'collecting'
        self.nsclient.start_acq()

    def stop(self):
        # Stop the collecting thread
        self.nsclient.stop_acq()
        self.state = 'stopped'

    def close(self):
        self.nsclient.disconnect()

    def save(self):
        # Save the data to the disk
        d = self.get_data()
        print(f'Saving the data ({d.shape}) to {self.filepath}')
        np.save(self.filepath, d)

    def report(self):
        # Report the current state of the stack,
        # it may change on developping.
        d = self.get_data()
        logger.debug(f'Current data shape is: {d.shape}')

    def latest(self, length=4):
        ''' Get the latest data by the [length]

        Args:
        - @length: The length of the fetched data, the unit is 'second', the default value is 4 seconds,
        '''

        n = length * self.freq
        d = self.get_data()
        if d.shape[1] < n:
            logger.warning(
                f'There is not enough data for your request of length={length}')
        return d[-n:]
