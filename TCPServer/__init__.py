import os
import sys
import time
import configparser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # noqa
from Logger import default_kwargs, new_logger

cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__),
                      '..',
                      'settings',
                      'default.cfg'))

default_kwargs['name'] = 'TCPServer'
logger = new_logger(**default_kwargs)
logger.info('TCPServer inits at {}'.format(time.ctime()))
