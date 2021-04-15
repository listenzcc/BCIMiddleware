import os
import time
import threading

from . import logger
from .dataCollector import DataStack


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
        # Necessary parameters
        self.filepath = filepath
        self.decoderpath = decoderpath

        # Start collecting data
        self.ds = DataStack(filepath)
        self.ds.start()

        self.stopped = False

    def generate_decoder(self):
        # Generate and save decoder
        data = self.ds.get_data()
        decoder = self.decoderpath

        if os.path.isfile(decoder):
            logger.warning(
                f'File exists (decoder) "{decoder}", overriding it.')

        # todo: Train decoder
        logger.info(
            f'Trained {decoder} with {data.shape}, save the decoder to {self.decoderpath}')

        # todo: Save decoder
        logger.info(f'Saved the decoder to {self.decoderpath}')

        with open(decoder, 'w') as f:
            f.writelines([
                f'Trained {decoder} with {data.shape}, save the decoder to {self.decoderpath}',
                '\n',
                f'The data is stored in {self.filepath}'
                '\n',
            ])

    def receive(self, dct):
        logger.debug(f'Training module received {dct}')
        method = dct.get('method', None)

        if method == 'stopSession':
            # Stop training session,
            # 1. Stop collecting data;
            # 2. Generate decoder and save it to the disk;
            # 3. Save the data to the disk
            self.stopped = True
            self.ds.stop()
            self.generate_decoder()
            self.ds.save()
            self.ds.close()

            logger.debug(f'Training module stopped')
            return 0, dict(
                method='sessionStopped',
                sessionName='training',
                dataPath=self.filepath,
                modelPath=self.decoderpath
            )

        return 1, dict(
            method='error',
            reason='invalidMessage',
            raw='',
            comment=f'Training module failed to parse {dct}'
        )


class ActiveModule(object):
    ''' The active module
    1. Automatically collecting data;
    2. Compute event timely;
    3. Stop to save the data.
    '''

    def __init__(self, filepath, decoderpath, interval, send):
        ''' Initialize the active module,

        Args:
        - @filepath: The path of the file to be stored;
        - @decoderpath: The path of the decoder;
        - @interval: The path of the timely job;
        - @send: The sending method.
        '''

        # Necessary parameters
        self.filepath = filepath
        self.decoderpath = decoderpath
        self.interval = interval

        # Start collecting data
        self.ds = DataStack(filepath)
        self.ds.start()

        # Load the decoder
        self.load_decoder()

        self.timely_job(send)

        self.stopped = False

        logger.debug(
            f'Active module starts as {filepath}, {decoderpath}, {interval}')

    def load_decoder(self):
        # todo: Load decoder
        self.decoder = self.decoderpath

    def _keep_active(self, send):
        logger.debug(f'Active module timely job starts.')
        while self.state == 'alive':
            # Get data
            d = self.ds.latest()
            logger.debug(
                f'Got the latest data from device, shape is {d.shape}')

            # todo: Compute event
            label = (self.decoder, d.shape)
            label = '1'
            out = dict(
                method='labelComputed',
                label=label
            )
            send(out)

            time.sleep(self.interval)
        logger.debug(f'Active module timely job stops.')

    def timely_job(self, send):
        ''' The timely job method

        Args:
        - @handler: The handler on time.
        '''
        self.state = 'alive'
        thread = threading.Thread(target=self._keep_active, args=(send,))
        thread.setDaemon(True)
        thread.start()

    def receive(self, dct):
        logger.debug(f'Active module received {dct}')

        method = dct.get('method', None)
        name = dct.get('sessionName', None)

        if method == 'stopSession' and name == 'wubiaoqian':
            # Stop active session,
            # 1. Stop collecting data;
            # 2. Save the data to the disk
            self.state = 'stopped'
            self.stopped = True
            self.ds.stop()
            self.ds.save()
            self.ds.close()

            logger.debug(f'Active module stopped.')

            return 0, dict(
                method='sessionStopped',
                sessionName='wubiaoqian',
                dataPath=self.filepath
            )

        return 1, dict(
            method='error',
            reason='invalidMessage',
            raw='',
            comment=f'Active module failed to parse {dct}'
        )


class PassiveModule(object):
    ''' The passive module
    1. Automatically collecting data;
    2. Compute event on request;
    3. Stop to save the data.
    '''

    def __init__(self, filepath, decoderpath, updatedecoderpath, update_count, send):
        ''' Initialize the passive module,

        Args:
        - @filepath: The path of the file to be stored;
        - @decoderpath: The path of the decoder;
        - @updatedecoderpath: The path of the updated decoder;
        - @update_count: How many trials for update the module;
        - @send: The sending method.
        '''

        # Necessary parameters
        self.filepath = filepath
        self.decoderpath = decoderpath
        self.updatedecoderpath = updatedecoderpath

        # Start collecting data
        self.ds = DataStack(filepath)
        self.ds.start()

        # Load the decoder
        self.load_decoder()

        self.update_count = update_count
        self.send = send

        self.stopped = False
        logger.debug(
            f'Passive module starts as {filepath}, {decoderpath}, {update_count}')

    def load_decoder(self):
        # todo: Load decoder
        self.decoder = self.decoderpath

    def save_updatedecoder(self):
        # Save the updated decoder
        data = self.ds.get_data()
        decoder = self.updatedecoderpath

        if os.path.isfile(decoder):
            logger.warning(
                f'File exists (decoder) "{decoder}", overriding it.')

        # todo: Save decoder
        logger.info(f'Saved the decoder to {self.updatedecoderpath}')

        with open(decoder, 'w') as f:
            f.writelines([
                f'Trained {decoder} with {data.shape}, save the decoder to {self.updatedecoderpath}',
                '\n',
                f'The data is stored in {self.filepath}'
                '\n',
            ])

    def receive(self, dct):
        logger.debug(f'Passive module received {dct}')

        method = dct.get('method', None)
        name = dct.get('sessionName', None)

        if method == 'stopSession' and name == 'youbiaoqian':
            # Stop passive session,
            # 1. Stop collecting data;
            # 2. Save the data to the disk
            self.stopped = True
            self.ds.stop()
            self.ds.save()
            self.ds.close()
            self.save_updatedecoder()

            logger.debug(f'Passive module stopped.')
            return 0, dict(
                method='sessionStopped',
                sessionName='youbiaoqian',
                dataPath=self.filepath
            )

        return 1, dict(
            method='error',
            reason='invalidMessage',
            raw='',
            comment=f'Passive module failed to parse {dct}'
        )
