from os import path, makedirs, listdir, remove
from testfixtures import LogCapture
import configparser
import pytest

import prosper.common.prosper_logging as prosper_logging
from prosper.common.prosper_config import get_config

HERE = path.abspath(path.dirname(__file__))
ME = __file__.replace(HERE, 'test')
LOCAL_CONFIG = path.join(HERE, 'test_config.cfg') #use /test config

TEST_CONFIG = get_config(LOCAL_CONFIG)

def helper_log_messages(
        logger,
        log_capture_override=None,
        config=TEST_CONFIG
):
    '''messages each logger tester should execute with their log handler'''
    with LogCapture(log_capture_override) as log_tracker:
        logger.debug('prosper.common.prosper_logging TEST -- DEBUG --')
        logger.info('prosper.common.prosper_logging TEST -- INFO --')
        logger.warning('prosper.common.prosper_logging -- WARNING --')
        logger.error('prosper.common.prosper_logging TEST -- ERROR --')
        logger.critical('prosper.common.prosper_logging TEST -- CRITICAL --')
        #logger.notify('prosper.common.prosper_logging TEST -- NOTIFY --')
        #logger.alert('prosper.common.prosper_logging TEST -- ALERT --')

    return log_tracker

def test_cleanup_log_directory(config=TEST_CONFIG):
    '''step0: make sure directory is set up and ready to accept logs'''
    log_path = path.abspath(config['Logging']['log_path'])

    log_list = listdir(log_path)
    for log_file in log_list:
        if '.log' in log_file:  #mac adds .DS_Store and gets cranky about deleting
            log_abspath = path.join(log_path, log_file)
            remove(log_abspath)

def test_default_logger(config=TEST_CONFIG):
    '''validate default logger'''
    test_logname = 'default_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        TEST_CONFIG['LOGGING']['log_path'],
        config
    )
    logger = log_builder.get_logger()
    log_capture = helper_log_messages(logger)
    log_capture.check(
        ('test_logging', 'DEBUG',    'prosper.common.prosper_logging TEST --DEBUG--'),
        ('test_logging', 'INFO',     'prosper.common.prosper_logging TEST --INFO--'),
        ('test_logging', 'WARNING',  'prosper.common.prosper_logging TEST --WARNING--'),
        ('test_logging', 'ERROR',    'prosper.common.prosper_logging TEST --ERROR--'),
        ('test_logging', 'CRITICAL', 'prosper.common.prosper_logging TEST --CRITICAL--'),
    )

    test_cleanup_log_directory()

#TODO: add pytest.mark to skip
def test_webhook(config_override=TEST_CONFIG):
    '''push hello world message to discord for testing'''
    try:
        webhook = config_override.get('LOGGING', 'discord_webhook')
    except configparser.NoOptionError as error_msg:
        pytest.skip('discord_webhook key not found in config')
    except Exception as error_msg:
        raise error_msg

    if not webhook: #FIXME: commenting doesn't work in config file?
        pytest.skip('discord_webhook is blank')

    webhook_obj = prosper_logging.DiscordWebhook()
    webhook_obj.webhook(webhook)
    test_handler = prosper_logging.HackyDiscordHandler(webhook_obj)

    test_handler.test(str(ME) + ' -- hello world')

if __name__ == '__main__':
    pass
