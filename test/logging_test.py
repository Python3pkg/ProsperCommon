from os import path, makedirs, listdir, remove
import configparser
import logging
from datetime import datetime

import pytest
from testfixtures import LogCapture

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
        logger.debug(   'prosper.common.prosper_logging TEST --DEBUG--')
        logger.info(    'prosper.common.prosper_logging TEST --INFO--')
        logger.warning( 'prosper.common.prosper_logging TEST --WARNING--')
        logger.error(   'prosper.common.prosper_logging TEST --ERROR--')
        logger.critical('prosper.common.prosper_logging TEST --CRITICAL--')
        #logger.notify('prosper.common.prosper_logging TEST --NOTIFY --')
        #logger.alert('prosper.common.prosper_logging TEST --ALERT --')

    return log_tracker

## TEST0: must clean up log directory for tests to be best ##
def test_cleanup_log_directory(config=TEST_CONFIG):
    '''step0: make sure directory is set up and ready to accept logs'''
    log_path = path.abspath(config['LOGGING']['log_path'])

    log_list = listdir(log_path)
    for log_file in log_list:
        if '.log' in log_file:  #mac adds .DS_Store and gets cranky about deleting
            log_abspath = path.join(log_path, log_file)
            remove(log_abspath)

def test_rotating_file_handle(config=TEST_CONFIG):
    '''validate that rotating filehandle object executes correctly'''
    test_logname = 'timedrotator'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        config['LOGGING']['log_path'],
        config_obj=config
    )
    test_logger = log_builder.get_logger() #use default behavior
    test_handles = log_builder.log_handlers
    timed_handle = None
    for handle in test_handles:
        if isinstance(handle, logging.handlers.TimedRotatingFileHandler):
            timed_handle = handle
            break
    assert \
        (not timed_handle is None), \
        'No TimedRotatingFileHandler found in logging object'

    before_capture = helper_log_messages(test_logger) #run logging
    timed_handle.doRollover() #force rollover
    after_capture = helper_log_messages(test_logger) #run logging

    logging_abspath = config['Logging']['log_path']
    file_list = listdir(logging_abspath)

    simple_file_list = []
    for logfile in file_list:
        if test_logname in logfile:
            simple_file_list.append(logfile)

    today = datetime.today().strftime('%Y-%m-%d')

    find_count = 0
    expected_vanilla_logname = str(test_logname + '.log')
    assert \
        expected_vanilla_logname in simple_file_list, \
        'Unable to find basic logname: {0} in list {1}'.\
            format(
                expected_vanilla_logname,
                ','.join(simple_file_list)
            )
    find_count += 1

    expected_rotator_logname = str(test_logname + '.log.' + today)
    assert \
        expected_rotator_logname in simple_file_list, \
        'Unable to find rotated logname: {0} in list {1}'.\
            format(
                expected_rotator_logname,
                ','.join(simple_file_list)
            )
    find_count += 1

    assert find_count == len(simple_file_list)

    #TODO: validate before_capture/after_capture

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

def test_logpath_builder_positive(config=TEST_CONFIG):
    '''make sure `test_logpath` has expected behavior -- affirmative case'''
    pytest.skip(__name__ + ' not configured yet')

def test_logpath_builder_negative(config=TEST_CONFIG):
    '''make sure `test_logpath` has expected behavior -- fail case'''
    pytest.skip(__name__ + ' not configured yet')

def test_default_logger(config=TEST_CONFIG):
    '''validate default logger'''
    test_logname = 'default_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        TEST_CONFIG['LOGGING']['log_path'],
        config_obj=config
    )
    logger = log_builder.get_logger()
    log_capture = helper_log_messages(logger)
    log_capture.check(
        (test_logname, 'INFO',     'prosper.common.prosper_logging TEST --INFO--'),
        (test_logname, 'WARNING',  'prosper.common.prosper_logging TEST --WARNING--'),
        (test_logname, 'ERROR',    'prosper.common.prosper_logging TEST --ERROR--'),
        (test_logname, 'CRITICAL', 'prosper.common.prosper_logging TEST --CRITICAL--'),
    )

    test_cleanup_log_directory()

def test_debug_logger(config=TEST_CONFIG):
    '''validate debug logger'''
    test_logname = 'debug_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        config['LOGGING']['log_path'],
        config_obj=config
    )
    log_builder.configure_debug_logger()
    test_logger = log_builder.get_logger() #use default behavior

    log_capture = helper_log_messages(test_logger)
    log_capture.check(
        (test_logname, 'DEBUG',    'prosper.common.prosper_logging TEST --DEBUG--'),
        (test_logname, 'INFO',     'prosper.common.prosper_logging TEST --INFO--'),
        (test_logname, 'WARNING',  'prosper.common.prosper_logging TEST --WARNING--'),
        (test_logname, 'ERROR',    'prosper.common.prosper_logging TEST --ERROR--'),
        (test_logname, 'CRITICAL', 'prosper.common.prosper_logging TEST --CRITICAL--'),
    )

    test_cleanup_log_directory()

def test_discord_logger(config=TEST_CONFIG):
    '''validate discord/webhook logger'''
    test_logname = 'discord_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        config['LOGGING']['log_path'],
        config_obj=config
    )
    log_builder.configure_discord_logger()
    test_logger = log_builder.get_logger() #use default behavior

    log_capture = helper_log_messages(test_logger)

    discord_helper = prosper_logging.DiscordWebhook()
    discord_helper.webhook(config['LOGGING']['discord_webhook'])

    request_logname = config['TEST']['request_logname']
    request_new_connection = config['TEST']['request_new_connection']
    request_POST_endpoint = config['TEST']['request_POST_endpoint'].\
        format(
            serverid=discord_helper.serverid,
            api_key=discord_helper.api_key
        )

    log_capture.check(
        (test_logname, 'INFO', 'prosper.common.prosper_logging TEST --INFO--'),
        (test_logname, 'WARNING', 'prosper.common.prosper_logging TEST --WARNING--'),
        (request_logname, 'INFO', request_new_connection),
        (request_logname, 'DEBUG', request_POST_endpoint),
        (test_logname, 'ERROR', 'prosper.common.prosper_logging TEST --ERROR--'),
        (request_logname, 'INFO', request_new_connection),
        (request_logname, 'DEBUG', request_POST_endpoint),
        (test_logname, 'CRITICAL', 'prosper.common.prosper_logging TEST --CRITICAL--')
    )

if __name__ == '__main__':
    test_debug_logger()
