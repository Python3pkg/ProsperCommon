"""logging_test.py

Pytest functions for exercising prosper.common.prosper_logging

"""

from os import path, listdir, remove, makedirs, rmdir
import configparser
import logging
from datetime import datetime
from warnings import warn

import pytest
from mock import patch, Mock
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
DISCORD_WEBHOOK = TEST_CONFIG.get_option('LOGGING', 'discord_webhook', None)
def test_discord_webhook(config_override=TEST_CONFIG):
    """Push 'hello world' message through Discord webhook"""


    if not DISCORD_WEBHOOK: #FIXME: commenting doesn't work in config file?
        pytest.skip('discord_webhook is blank')

    webhook_obj = prosper_logging.DiscordWebhook()
    webhook_obj.webhook(DISCORD_WEBHOOK)
    test_handler = prosper_logging.HackyDiscordHandler(webhook_obj)

    test_handler.test(str(ME) + ' -- hello world')

SLACK_WEBHOOK = TEST_CONFIG.get_option('LOGGING', 'slack_webhook', None)
def test_slack_webhook(config_override=TEST_CONFIG):
    """push 'hello world' message through Slack webhook"""
    if not SLACK_WEBHOOK:
        pytest.skip('slack_webhoo is blank')

    test_payload = {
        'fallback': 'hello world',
        'text': 'hello world',
        'color': 'good'
    }
    test_handler = prosper_logging.HackySlackHandler(SLACK_WEBHOOK)

    test_handler.send_msg_to_webhook(test_payload)

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

def test_iter_util(config=TEST_CONFIG):
    """validate __iter__ works as expected"""
    test_logname = 'debug_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=config
    )
    log_builder.configure_debug_logger()
    test_logger = log_builder.get_logger() #use default behavior

    expected_handlers = [
        logging.handlers.TimedRotatingFileHandler,  #default handler
        logging.StreamHandler                       #debug handler
    ]
    for indx, handler in enumerate(log_builder):
        print(type(handler))
        assert isinstance(handler, expected_handlers[indx])

REQUEST_LOGNAME        = TEST_CONFIG.get_option('TEST', 'request_logname', None)
REQUEST_NEW_CONNECTION = TEST_CONFIG.get_option('TEST', 'request_new_connection', None)
REQUEST_POST_ENDPOINT  = TEST_CONFIG.get_option('TEST', 'request_POST_endpoint', None)
def test_discord_logger(config=TEST_CONFIG):
    """Execute LogCapture on Discord logger object"""
    if not DISCORD_WEBHOOK: #FIXME: commenting doesn't work in config file?
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
    discord_helper.webhook(DISCORD_WEBHOOK) #TODO: add blank-webhook test

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

SLACK_NEW_CONNECTION = TEST_CONFIG.get_option('TEST', 'slack_new_connection', None)
SLACK_POST_ENDPOINT = TEST_CONFIG.get_option('TEST', 'slack_POST_endpoint', None)
def test_slack_logger(config=TEST_CONFIG):
    """Execute LogCapture on Slack logger object"""
    if not SLACK_WEBHOOK:
        pytest.skip('slack_webhook is blank')

    test_logname = 'slack_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=config
    )
    log_builder.configure_slack_logger(SLACK_WEBHOOK)
    test_logger = log_builder.get_logger()

    log_capture = helper_log_messages(test_logger)

    request_POST_endpoint = SLACK_POST_ENDPOINT.\
        format(webhook_info=SLACK_WEBHOOK.replace('https://hooks.slack.com', ''))

    log_capture.check(
        (test_logname, 'INFO',     'prosper.common.prosper_logging TEST --INFO--'),
        (test_logname, 'WARNING',  'prosper.common.prosper_logging TEST --WARNING--'),
        (REQUEST_LOGNAME, 'DEBUG', SLACK_NEW_CONNECTION),
        (REQUEST_LOGNAME, 'DEBUG', request_POST_endpoint),
        (test_logname, 'ERROR',    'prosper.common.prosper_logging TEST --ERROR--'),
        (REQUEST_LOGNAME, 'DEBUG', SLACK_NEW_CONNECTION),
        (REQUEST_LOGNAME, 'DEBUG', request_POST_endpoint),
        (test_logname, 'CRITICAL', 'prosper.common.prosper_logging TEST --CRITICAL--'),
    )

def test_configure_common(config=TEST_CONFIG):
    """test if minimal log level is used"""
    test_logname = 'test_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=config
    )

    min_log_level = 'WARNING'
    log_builder.configure_default_logger(log_level=min_log_level)
    logger = log_builder.get_logger()

    assert logger.isEnabledFor(logging.getLevelName(min_log_level))

def test_bad_init():
    """test validation for prosper_config.ProsperConfig"""
    test_logname = 'exceptional_logger'
    with pytest.raises(TypeError):
        prosper_logging.ProsperLogger(
            test_logname,
            LOG_PATH,
            None #<-- offending argument
        )

def test_handle_str(config=TEST_CONFIG):
    """test validation for ProsperLogger.__str__"""
    test_logname = 'str_logger'
    log_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=config
    )
    log_builder.configure_default_logger()

    # test that there is _some_ implementation
    assert object.__str__(log_builder) != log_builder.__str__()

def test_log_format_name():
    """test log_format_name overrides in logging handler builders"""
    test_format = 'STDOUT'
    format_actual = prosper_logging.ReportingFormats[test_format].value
    test_file = 'test/test_alt_format.cfg'

    test_logname = 'test_logger'
    logger_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=prosper_config.ProsperConfig(test_file)
    )

    logger_builder.configure_default_logger()
    logger = logger_builder.get_logger()

    result = False
    for fmt in [h.formatter._fmt for h in logger.handlers]: #check if we have a handler with the requested format
        result = result or fmt == format_actual

    assert result

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

def test_discordwebhook_api_keys():
    """validate that we can query after setting serverid and api key"""
    test_serverid = 1234
    test_apikey = 'some_key'

    webhook = prosper_logging.DiscordWebhook()
    webhook.api_keys(test_serverid, test_apikey)

    assert webhook #using __bool__

def test_discordwebhook_webhook_url():
    """validate that we can query after setting serverid and api key"""
    base_url = 'https://discordapp.com/api/webhooks/'
    test_serverid = 1234
    test_apikey = 'some-key'
    test_url_faulty = 'some string'
    test_url_correct = base_url + str(test_serverid) + '/' + test_apikey

    discord_webhook = prosper_logging.DiscordWebhook()

    with pytest.raises(Exception):
        discord_webhook.webhook(None)

    with pytest.raises(Exception):
        discord_webhook.webhook(test_url_faulty)

    discord_webhook.webhook(test_url_correct)
    assert discord_webhook

def test_discordwebhook_str():
    """test that there is some str implementation"""

    webhook = prosper_logging.DiscordWebhook()

    assert object.__str__(webhook) != webhook.__str__()

def test_discordwebhook_get_webhook_info():
    """test get_webhook_method"""

    webhook = prosper_logging.DiscordWebhook()

    with pytest.raises(RuntimeError): #Because we have not set serverid and apikey yet
        webhook.get_webhook_info()

def test_discord_logginghook():
    """validate __init__ behavior for HackyDiscordHandler"""
    test_serverid = 1234
    test_apikey = 'some_key'
    test_alert_recipient = 'some_user'

    webhook = prosper_logging.DiscordWebhook()
    webhook.api_keys(test_serverid, test_apikey)
    handler = prosper_logging.HackyDiscordHandler(webhook, test_alert_recipient)

    # validate that parameters are actually used
    assert handler.webhook_obj == webhook
    assert handler.alert_recipient == test_alert_recipient

def test_discord_logginghook_unconfigured():
    """verify exception when webhook is unconfigured"""

    webhook = prosper_logging.DiscordWebhook()

    with pytest.raises(Exception):
        prosper_logging.HackyDiscordHandler(webhook)

@patch('prosper.common.prosper_logging.makedirs', side_effect=PermissionError)
@patch('prosper.common.prosper_logging.warnings.warn')
def test_pathmaking_fail_makedirs(warn, makedirs):
    """validate failure behavior when making paths"""
    test_log_path = 'test_folder delete this'

    ret = prosper_logging.test_logpath(test_log_path)

    assert warn.called

@patch('prosper.common.prosper_logging.access', return_value=False)
@patch('prosper.common.prosper_logging.warnings.warn')
def test_pathmaking_fail_writeaccess(warn, access):
    """check W_OK behavior when testing logpath"""
    test_log_path = 'logs'

    ret = prosper_logging.test_logpath(test_log_path)

    assert warn.called

@patch('requests.post')
def test_send_msg_to_webhook_success(post):
    """verify that the handler is sending messages"""
    test_serverid = 1234
    test_apikey = 'some_key'

    webhook = prosper_logging.DiscordWebhook()
    webhook.api_keys(test_serverid, test_apikey)
    handler = prosper_logging.HackyDiscordHandler(webhook)

    handler.send_msg_to_webhook('dummy')

    assert post.called

@patch('requests.post', side_effect=Exception)
@patch('prosper.common.prosper_logging.warnings.warn')
def test_send_msg_to_webhook_faulty(warn, post):
    """verify that the handler gives a warning on exception"""
    test_serverid = 1234
    test_apikey = 'some_key'

    webhook = prosper_logging.DiscordWebhook()
    webhook.api_keys(test_serverid, test_apikey)
    handler = prosper_logging.HackyDiscordHandler(webhook)

    handler.send_msg_to_webhook('dummy')

    assert warn.called

@patch('prosper.common.prosper_logging.warnings.warn')
def test_prosper_logger_close_handles(warn, config=TEST_CONFIG):
    "test if warning is given when closing a handler exceptionlally"

    fake_handler = logging.StreamHandler()
    fake_handler.close = Mock(side_effect=Exception)

    test_logname = 'test_logger'
    logger_builder = prosper_logging.ProsperLogger(
        test_logname,
        LOG_PATH,
        config_obj=config
    )

    logger_builder.log_handlers.append(fake_handler)
    logger_builder.close_handles()

    assert warn.called

if __name__ == '__main__':
    test_rotating_file_handle()
