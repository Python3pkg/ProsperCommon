from os import path, makedirs

import prosper.common.prosper_logging as prosper_logging
from prosper.common.prosper_config import get_config
HERE = path.abspath(path.dirname(__file__))
LOCAL_CONFIG = path.join(HERE, 'common_config.cfg') #use /test config
if not path.isfile(LOCAL_CONFIG):   #else use /prosper/common config
    DEFAULT_PATH = path.join(path.dirname(HERE), 'prosper/common')
    LOCAL_CONFIG = path.join(DEFAULT_PATH, 'common_config.cfg')

def test_logger(config_override=None):
    '''excercise logger utility'''

    logger = prosper_logging.create_logger(
        'test_logging',
        '.',
        config_override,
        'DEBUG'
    )

    logger.debug('prosper.common.prosper_logging TEST --DEBUG--')
    logger.info('prosper.common.prosper_logging TEST --INFO--')
    logger.warning('prosper.common.prosper_logging TEST --WARNING--')
    logger.error('prosper.common.prosper_logging TEST --ERROR--')
    logger.critical('prosper.common.prosper_logging TEST --CRITICAL--')


if __name__ == '__main__':
    TEST_CONFIG = get_config(LOCAL_CONFIG)
    test_logger(TEST_CONFIG)
