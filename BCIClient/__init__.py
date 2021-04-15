'''Initialize the BCI Client Package

The setup will be settled;
The local tools will be generated.
'''

# Default Imports
import os
import time
import json
import logging
import configparser

# Custom Imports
from .Logger import logger_kwargs, generate_logger

# ------------------------------------------------------------------------
# Setup
# PWD
pwd = os.path.join(os.path.dirname(__file__))

# Load Configures
cfg = configparser.ConfigParser()
cfg.read(os.path.join(pwd,
                      'settings',
                      'setting.ini'))

# TCP Parameters
tcp_params = dict(
    IP=cfg['TCP']['serverIP'],
    port=int(cfg['TCP']['serverPort']),
    buffer_size=int(cfg['TCP']['bufferSize']),
    coding=cfg['TCP']['coding']
)

active_interval = int(cfg['Online']['wubiaoqianInterval'])

# Logging
logger_kwargs['name'] = 'BCIClient'
logger_kwargs['level_console'] = eval(
    'logging.{}'.format(cfg['Log']['consoleLogLevel']))


def timestr():
    ''' Generate time string currently '''
    return time.strftime('%Y-%m-%d-%H-%M-%S')


logger_kwargs['filepath'] = os.path.join(pwd,
                                         '..',
                                         'logs',
                                         'log-{}.log'.format(timestr()))

logger = generate_logger(**logger_kwargs)

logger.info('Package initialized')


# ------------------------------------------------------------------------
# Tools
# Binary Tools
# The TCP message is binary, so decoding and encoding is necessary.

coding = cfg['TCP']['coding']


def decode(content, coding=coding):
    ''' Decode [content] if necessary '''
    t = type(content)
    logger.debug(f'Decoding "{content}", {t}')
    if isinstance(content, type(b'')):
        return content.decode(coding)
    else:
        return content


def encode(content, coding=coding):
    ''' Encode [content] if necessary '''
    t = type(content)
    logger.debug(f'Encoding "{content}", {t}')
    if isinstance(content, type('')):
        return content.encode(coding)
    else:
        return content

# Dict Tools
# Deal with dict in TCP message.


def unpack(pack):
    ''' Unpack [pack] into dict using json.loads '''
    try:
        out = json.loads(pack)
        logger.debug(f'Unpack "{pack}"')
        return out
    except:
        logger.error(f'Failed to unpack "{pack}"')
        return None


def pack(dct):
    ''' Pack [dct] into bytes using json.dumps '''
    try:
        for key in dct:
            dct[key] = decode(dct[key])
        out = json.dumps(dct)
        logger.debug(f'Pack "{dct}"')
        return out
    except:
        logger.error(f'Failed to pack "{dct}"')
        return None
