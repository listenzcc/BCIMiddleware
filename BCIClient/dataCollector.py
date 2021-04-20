import os
import numpy as np

from . import logger, cfg
from .neuroScanToolbox import NeuroScanDeviceClient

n_channels = int(cfg['EEG']['numChannels'])  # Number of channels
freq = int(cfg['EEG']['sampleRate'])  # Hz
eeg_IP = cfg['EEG']['deviceIP']
eeg_port = int(cfg['EEG']['devicePort'])


class DataStack(object):
    ''' The data stack.

    Useful methods:
    - @start: Start the data collecting;
    - @stop: Stop the data collecting;
    - @save: Save the data to the disk;
    - @latest: Get the latest data from the stack;
    - @report: Get the current state of the report.
    '''

    def __init__(self, filepath, eeg_IP=eeg_IP, eeg_port=eeg_port, n_channels=n_channels, freq=freq, autoDetectLabelFlag=False, predict=None):
        ''' Initialize the data stack

        Args:
        - @filepath: Where the data will be stored in;
        - @eeg_IP: The IP address of the EEG device, has default value;
        - @eeg_port: The port number of the EEG device, has default value;
        - @n_channels: Number of channels, has default value;
        - @freq: The sampling frequency, has default value;
        '''
        self.filepath = filepath

        self.n_channels = n_channels
        self.freq = freq

        self._reset()

        self.nsclient = NeuroScanDeviceClient(eeg_IP,
                                              eeg_port,
                                              freq,
                                              n_channels,
                                              autoDetectLabelFlag=autoDetectLabelFlag,
                                              predict=predict)

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
        self.nsclient.start_send()

    def stop(self):
        # Stop the collecting thread
        self.nsclient.stop_send()
        self.state = 'stopped'

    def close(self):
        self.nsclient.disconnect()

    def save(self):
        # Save the data to the disk
        d = self.get_data()
        if os.path.isfile(self.filepath):
            logger.warning(
                f'File exists (data) "{self.filepath}", overriding it.')
        np.save(self.filepath, d)
        logger.debug(f'Saved the data ({d.shape}) to {self.filepath}')

    def report(self):
        # Report the current state of the stack,
        # it may change on developping.
        d = self.get_data()
        logger.debug(f'Current data shape is: {d.shape}')

    def latest(self, length=5):
        ''' Get the latest data by the [length]

        Args:
        - @length: The length of the fetched data, the unit is 'second', the default value is 4 seconds,
        '''

        n = length * self.freq
        d = self.get_data()
        if len(d.shape) == 1:
            logger.warning(
                f'There is not enough data for your request of length={length} seconds, current length is 1.')
            return d.reshape((len(d), 1))

        if d.shape[1] < n:
            logger.warning(
                f'There is not enough data for your request of length={length} seconds, current length is {d.shape[1]}.')

        return d[:, -n:]
