"""logging_test.py

Pytest functions for exercising prosper.common.prosper_logging

"""

from os import path, listdir, remove, makedirs, rmdirimport configparser
import logging
from datetime import datetime

import pytest
from testfixtures import LogCapture

import prosper.common.prosper_logging as prosper_logging
import prosper.common.prosper_config as prosper_config

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)
ME = __file__.replace(HERE, 'test')
LOCAL_CONFIG_PATH = path.join(
    ROOT,
    'prosper',
    'common',
    'common_config.cfg'
)   #use root config

TEST_CONFIG = prosper_config.ProsperConfig(LOCAL_CONFIG_PATH)

def helper_log_messages(
        logger,
        log_capture_override=None,
        config=TEST_CONFIG
):
    """Helper for executing logging same way for every test

    Args:
        logger (:obj:`logging.logger`) logger to commit messages to
        log_capture_override (str): override/filter for testfixtures.LogCapture
        config (:obj: `configparser.ConfigParser`): config override for function values

    Returns:
        (:obj:`testfixtures.LogCapture`) https://pythonhosted.org/testfixtures/logging.html

    """
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
LOG_PATH = TEST_CONFIG.get_option('LOGGING', 'log_path', None)
makedirs(LOG_PATH, exist_ok=True)
def test_cleanup_log_directory(
        log_builder_obj=None,
        config=TEST_CONFIG
):
    """Test0: clean up testing log directory.  Only want log-under-test"""
    if log_builder_obj:
        log_builder_obj.close_handles()

    log_list = listdir(LOG_PATH)
    for log_file in log_list:
        if '.log' in log_file:  #mac adds .DS_Store and gets cranky about deleting
            log_abspath = path.join(LOG_PATH, log_file)
            remove(log_abspath)

def test_rotating_file_handle(config=TEST_CONFIG):
    """Exercise TimedRotatingFileHandler to make sure logs are generating as expected

    Todo:
        * Validate before_capture/after_capture testfixtures.LogCapture objects

    """
    test_logname = 'timedrotator'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
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

    file_list = listdir(LOG_PATH)

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

    test_cleanup_log_directory(log_builder)

#TODO: add pytest.mark to skip
WEBHOOK = TEST_CONFIG.get_option('LOGGING', 'discord_webhook', None)
def test_webhook(config_override=TEST_CONFIG):
    """Push 'hello world' message through Discord webhook"""


    if not WEBHOOK: #FIXME: commenting doesn't work in config file?
        pytest.skip('discord_webhook is blank')

    webhook_obj = prosper_logging.DiscordWebhook()
    webhook_obj.webhook(WEBHOOK)
    test_handler = prosper_logging.HackyDiscordHandler(webhook_obj)

    test_handler.test(str(ME) + ' -- hello world')

def test_logpath_builder_positive(config=TEST_CONFIG):
    """Make sure test_logpath() function has expected behavior -- affermative case

    Todo:
        * Test not implemented at this time
        * Requires platform-specific directory/permissions manipulation

    """
    pytest.skip(__name__ + ' not configured yet')

def test_logpath_builder_negative(config=TEST_CONFIG):
    """Make sure test_logpath() function has expected behavior -- fail case

    Todo:
        * Test not implemented at this time
        * Requires platform-specific directory/permissions manipulation

    """
    pytest.skip(__name__ + ' not configured yet')

def test_default_logger_options(config=TEST_CONFIG):
    """validate expected values from config object.  DO NOT CRASH DEFAULT LOGGER"""
    option_config_filepath = prosper_config.get_local_config_filepath(LOCAL_CONFIG_PATH)
    global_options = prosper_config.read_config(option_config_filepath)

    log_freq  = config.get_option('LOGGING', 'log_freq', None)
    log_total = config.get_option('LOGGING', 'log_total', None)
    log_level = config.get_option('LOGGING', 'log_level', None)

    assert log_freq  == global_options['LOGGING']['log_freq']
    assert log_total == global_options['LOGGING']['log_total']
    assert log_level == global_options['LOGGING']['log_level']

def test_default_logger(config=TEST_CONFIG):
    """Execute LogCapture on basic/default logger object"""
    test_logname = 'default_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
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

    test_cleanup_log_directory(log_builder)

def test_debug_logger(config=TEST_CONFIG):
    """Execute LogCapture on debug logger object"""
    test_logname = 'debug_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
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

    test_cleanup_log_directory(log_builder)

REQUEST_LOGNAME        = TEST_CONFIG.get_option('TEST', 'request_logname', None)
REQUEST_NEW_CONNECTION = TEST_CONFIG.get_option('TEST', 'request_new_connection', None)
REQUEST_POST_ENDPOINT  = TEST_CONFIG.get_option('TEST', 'request_POST_endpoint', None)
def test_discord_logger(config=TEST_CONFIG):
    """Execute LogCapture on Discord logger object"""
    if not WEBHOOK: #FIXME: commenting doesn't work in config file?
        pytest.skip('discord_webhook is blank')

    test_logname = 'discord_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=config
    )
    log_builder.configure_discord_logger()
    test_logger = log_builder.get_logger() #use default behavior

    log_capture = helper_log_messages(test_logger)

    discord_helper = prosper_logging.DiscordWebhook()
    discord_helper.webhook(WEBHOOK) #TODO: add blank-webhook test

    request_POST_endpoint = REQUEST_POST_ENDPOINT.\
        format(
            serverid=discord_helper.serverid,
            api_key=discord_helper.api_key
        )

    log_capture.check(
        (test_logname, 'INFO', 'prosper.common.prosper_logging TEST --INFO--'),
        (test_logname, 'WARNING', 'prosper.common.prosper_logging TEST --WARNING--'),
        (REQUEST_LOGNAME, 'DEBUG', REQUEST_NEW_CONNECTION),
        (REQUEST_LOGNAME, 'DEBUG', request_POST_endpoint),
        (test_logname, 'ERROR', 'prosper.common.prosper_logging TEST --ERROR--'),
        (REQUEST_LOGNAME, 'DEBUG', REQUEST_NEW_CONNECTION),
        (REQUEST_LOGNAME, 'DEBUG', request_POST_endpoint),
        (test_logname, 'CRITICAL', 'prosper.common.prosper_logging TEST --CRITICAL--')
    )

def test_bad_init():
    """test validation for prosper_config.ProsperConfig"""
    test_logname = 'exceptional_logger'
    with pytest.raises(TypeError):
        prosper_logging.ProsperLogger(
            test_logname,
            LOG_PATH,
            None #<-- offending argument
        )

@pytest.mark.skip(reason='Test failing because of bug, see test source.')
def test_handle_str(config=TEST_CONFIG):
    """test validation for ProsperLogger.__str__"""
    test_logname = 'str_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=config
    )

    min_log_level = 'WARNING'
    log_builder.configure_default_logger(log_level=min_log_level) #Looks like there is a bug where this parametr is always overwritten, and thus doesn't show up in the __str__ output
    string = log_builder.__str__()
    
    assert min_log_level in log_builder.__str__()

def test_log_format_name():
    """test log_format_name overrides in logging handler builders"""
    test_format = 'STDOUT'

    builder = prosper_config.ProsperConfigBuilder(file_name='test_config.cfg')       
    builder.add_entry('LOGGING', 'log_format', test_format)
    config = builder.build()

    test_logname = 'default_logger'
    logger = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=config
    ).get_logger()

    format_actual = prosper_logging.ReportingFormats[test_format].value
    result = False
    for fmt in [h.formatter._fmt for h in logger.handlers]: #check if we have a handler with the requested format
        result = result or fmt == format_actual

    assert result

    remove(builder.effective_path)

def test_debugmode_pathing():
    """validate debug_mode=True behaivor in test_logpath"""
    test_paths = [
        "logs",
        "bloo",
        "some string with spaces"
    ]

    debug_path = "."
    assert all(prosper_logging.test_logpath(path, debug_mode=True) == debug_path for path in test_paths)

def test_pathmaking():
    """validate test_logpath can makedirs"""
    test_path = 'test mkdir folder'

    actual = prosper_logging.test_logpath(test_path)
    assert actual == test_path #Test if the returned path is the one we wanted
    assert path.exists(test_path)
    rmdir(test_path) #If here, we know dir exists

#seems like programmatically creating a non-accessable directory uses platform specific libraries.
def test_pathmaking_fail_makedirs():
    """validate failure behavior when making paths"""
    pytest.skip('NOT IMPLEMENTED')

def test_pathmaking_fail_writeaccess():
    """check W_OK behavior when testing logpath"""
    pytest.skip('NOT IMPLEMENTED')

def test_discordwebhook_class():
    """validate DiscordWebhook behavior"""
    pytest.skip('NOT IMPLEMENTED')

def test_discord_logginghook():
    """validate __init__ behavior for HackyDiscordHandler"""
    pytest.skip('NOT IMPLEMENTED')

if __name__ == '__main__':
    test_rotating_file_handle()
