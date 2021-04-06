import os
import time
import threading
from .dataCollector import DataStack, default_kwargs

kwargs = default_kwargs


def isfile(path):
    return os.path.isfile(path)


def isdir(path):
    return os.path.isdir(path)


def load_decoder(path):
    # todo: Read the decoder on [path]
    return path


class TrainModule(object):
    ''' The train module
    1. Automatically collecting data;
    2. Stop to training the decoder;
    3. Stop to save the data.
    '''

    def __init__(self, filepath, decoderpath):
        ''' Initialize the train module,

        Args:
        - @filepath: The path of the file to be stored;
        - @decoderpath: The path of the decoder to be stored.
        '''
        # Assert safe values
        assert(isdir(os.path.dirname(filepath)))
        assert(not isfile(filepath))

        assert(isdir(decoderpath))
        assert(not isfile(decoderpath))

        # Necessary parameters
        self.filepath = filepath
        self.decoderpath = decoderpath

        # Start collecting data
        self.ds = DataStack(filepath, **kwargs)
        self.ds.start()

    def generate_decoder(self):
        # Generate and save decoder
        data = self.ds.data
        decoder = self.decoderpath

        # todo: Train decoder
        print(
            f'Trained {decoder} with {data.shape}, save the decoder to {self.decoderpath}')

        # todo: Save decoder
        print(f'Saved the decoder to {self.decoderpath}')

    def receive(self, dct):
        method = dct.get('method', None)

        if method == 'stop':
            # Stop training session,
            # 1. Stop collecting data;
            # 2. Generate decoder and save it to the disk;
            # 3. Save the data to the disk
            self.ds.stop()
            self.generate_decoder()
            self.ds.save()
            return 0, f'The save has been saved to {self.filepath}'

        return 1, f'Failed to parse {dct}'


class ActiveModule(object):
    ''' The active module
    1. Automatically collecting data;
    2. Compute event timely;
    3. Stop to save the data.
    '''

    def __init__(self, filepath, decoderpath, interval):
        ''' Initialize the active module,

        Args:
        - @filepath: The path of the file to be stored;
        - @decoderpath: The path of the decoder exists;
        - @interval: The path of the timely job.
        '''
        # Assert safe values
        assert(isdir(os.path.dirname(filepath)))
        assert(not isfile(filepath))

        assert(isfile(decoderpath))

        # Necessary parameters
        self.filepath = filepath
        self.decoderpath = decoderpath
        self.interval = interval

        # Start collecting data
        self.ds = DataStack(filepath, **kwargs)
        self.ds.start()

        # Load the decoder
        self.load_decoder()

    def load_decoder(self):
        # todo: Load decoder
        self.decoder = self.decoderpath

    def _keep_active(self, handler):
        while self.state == 'alive':
            # Get data
            d = self.ds.latest()

            # todo: Compute event
            out = (self.decoder, d.shape)
            handler(out)

            time.sleep(self.interval)

    def timely_job(self, handler):
        ''' The timely job method

        Args:
        - @handler: The handler on time.
        '''
        thread = threading.Thread(target=self._keep_active, args=(handler,))
        thread.setDaemon(True)
        thread.start()

    def receive(self, dct):
        method = dct.get('method', None)

        if method == 'stop':
            # Stop active session,
            # 1. Stop collecting data;
            # 2. Save the data to the disk
            self.state = 'alive'
            self.ds.stop()
            self.ds.save()
            return 0, f'The save has been saved to {self.filepath}'

        return 1, f'Failed to parse {dct}'


class PassiveModule(object):
    ''' The passive module
    1. Automatically collecting data;
    2. Compute event on request;
    3. Stop to save the data.
    '''

    def __init__(self, filepath, decoderpath):
        ''' Initialize the passive module,

        Args:
        - @filepath: The path of the file to be stored;
        - @decoderpath: The path of the decoder exists.
        '''
        # Assert safe values
        assert(isdir(os.path.dirname(filepath)))
        assert(not isfile(filepath))

        assert(isfile(decoderpath))

        # Necessary parameters
        self.filepath = filepath
        self.decoderpath = decoderpath

        # Start collecting data
        self.ds = DataStack(filepath, **kwargs)
        self.ds.start()

        # Load the decoder
        self.load_decoder()

    def load_decoder(self):
        # todo: Load decoder
        self.decoder = self.decoderpath

    def receive(self, dct):
        method = dct.get('method', None)

        if method == 'query':
            # Compute event on query,
            # 1. Get the latest data;
            # 2. Compute the event using decoder and data.

            # Get data
            d = self.ds.latest()

            # todo: Compute event
            out = (self.decoder, d.shape)
            return 0, out

        if method == 'stop':
            # Stop passive session,
            # 1. Stop collecting data;
            # 2. Save the data to the disk
            self.ds.stop()
            self.ds.save()
            return 0, f'The save has been saved to {self.filepath}'

        return 1, f'Failed to parse {dct}'
