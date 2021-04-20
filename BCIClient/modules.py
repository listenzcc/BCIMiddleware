import os
import time
import threading
import traceback

from . import logger
from .dataCollector import DataStack
from .BCIDecoder import BCIDecoder


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
        decoder = BCIDecoder()
        decoderpath = self.decoderpath

        # Train decoder
        decoder.fit(data)

        # Save decoder
        decoder.save_model(decoderpath)
        logger.info(f'Saved the decoder to {decoderpath}')

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
            self.ds.save()
            self.ds.close()
            self.generate_decoder()

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
        self.interval = interval

        # Start collecting data
        self.ds = DataStack(filepath)
        self.ds.start()

        # Load the decoder
        self.load_decoder(decoderpath)

        self.timely_job(send)

        self.stopped = False

        logger.debug(
            f'Active module starts as {filepath}, {decoderpath}, {interval}')

    def load_decoder(self, decoderpath):
        # Load decoder
        self.decoder = BCIDecoder()
        self.decoder.load_model(decoderpath)
        logger.debug(f'Loaded decoder of "{decoderpath}"')

    def _keep_active(self, send):
        logger.debug(f'Active module timely job starts.')
        while self.state == 'alive':
            time.sleep(self.interval)
            # Get data
            d = self.ds.latest()
            logger.debug(
                f'Got the latest data from device, shape is {d.shape}')

            if d.shape[1] < 4000:
                logger.warning(
                    f'Not enough data for compute label, doing nothing')
                continue

            # Compute label
            d[-1] = 0
            d[-1, -1] = 33
            d[-1, 0] = 22
            label = self.decoder.predict(d)
            logger.debug(f'Computed label of {label}')
            out = dict(
                method='labelComputed',
                label=f'{label}'
            )
            send(out)

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
        self.updatedecoderpath = updatedecoderpath

        # Start collecting data
        self.ds = DataStack(filepath,
                            autoDetectLabelFlag=True,
                            predict=self.predict)
        self.ds.start()

        # Load the decoder
        self.load_decoder(decoderpath, update_count)

        self.send = send

        self.results = []

        self.stopped = False
        logger.debug(
            f'Passive module starts as {filepath}, {decoderpath}, {update_count}')

    def load_decoder(self, decoderpath, update_count):
        # Load decoder
        self.decoder = BCIDecoder(update_count)
        self.decoder.load_model(decoderpath)
        logger.debug(f'Loaded decoder of "{decoderpath}"')

    def save_updatedecoder(self):
        # Save the updated decoder
        path = self.updatedecoderpath
        self.decoder.save_model(path)
        logger.info(f'Saved the updated decoder to {path}')

    def predict(self):
        try:
            d = self.ds.latest()
            label = self.decoder.predict(d)

            if 11 in d[-1, :]:
                true_label = 0
                logger.debug(f'True label: {true_label}')

            if 22 in d[-1, :]:
                true_label = 1
                logger.debug(f'True label: {true_label}')

            logger.debug(f'Predicted label: {label}')
            self.send(dict(
                method='labelComputed',
                label=f'{label}'
            ))
            self.results.append([true_label, label])
        except:
            err = traceback.format_exc()
            logger.warning(f'Failed on predict: {err}')

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

            c = 0
            n = 0
            for t, p in self.results:
                n += 1
                if t == 1 and p == 1:
                    c += 1
                if t == 0 and p == 0:
                    c += 1

            accuracy = c / n

            return 0, dict(
                method='sessionStopped',
                sessionName='youbiaoqian',
                accuracy=f'{accuracy}'
            )

        return 1, dict(
            method='error',
            reason='invalidMessage',
            raw='',
            comment=f'Passive module failed to parse {dct}'
        )
