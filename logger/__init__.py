'''
Generate logger by one sentence:

>> from logger import logger

**Notions**:
1. My EasyLogging package is used to generate the 'logger',
be sure it is in your python environment.

2. The logging file will be in the 'logs' folder beside the package,
make sure the folder exists.

3. The logger will be automatically named as the created time.
To prevent the logging being recorded into separate files,
I suggest the users to generate the 'logger' and use it across the whole connected functions or packages.
'''

import os
import time
import logging
from EasyLogging.logger import new_logger


def timestr():
    return time.strftime('%Y-%m-%d-%H-%M-%S')


default_kwargs = dict(name='BCIMC',
                      filepath=os.path.join(os.path.dirname(__file__),
                                            '..',
                                            'logs',
                                            'log-{}.txt'.format(timestr())),
                      level=logging.DEBUG,
                      test=True)

logger = new_logger(**default_kwargs)

logger.info('Logger inits at {}'.format(time.ctime()))
