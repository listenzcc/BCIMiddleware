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

# Imports
import os
import time
import logging
import configparser
from EasyLogging.logger import new_logger

# Tools


def timestr():
    return time.strftime('%Y-%m-%d-%H-%M-%S')


# Read cfg
cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__),
                      '..',
                      'settings',
                      'default.cfg'))

level = eval(cfg['Runtime']['logLevel'])

# Setup logger
default_kwargs = dict(name='BCIMC',
                      filepath=os.path.join(os.path.dirname(__file__),
                                            '..',
                                            'logs',
                                            'log-{}.log'.format(timestr())),
                      level=level,
                      test=False)

logger = new_logger(**default_kwargs)

logger.debug('Logger inits at {}'.format(time.ctime()))
