"""prosper_logging.py

A unified logger for all Prosper python scripts.  Easy extensions included to make life easy

Example:
    import prosper.common.prosper_logging as p_log

    LogBuilder = p_log.ProsperLogger(
        'log_name',
        'desired/log/path',
        configuration_object,
        bool:debug_mode [optional]
    )

    LogBuilder.configure_discord_logger() # log ERROR/CRITICAL to Discord

    if DEBUG:
        LogBuilder.configure_debug_logger()

    logger = LogBuilder.get_logger()

"""

from os import path, makedirs, access, W_OK#, R_OK
import logging
from logging.handlers import TimedRotatingFileHandler
import warnings
from enum import Enum
import re

import requests

#import prosper.common as common
import prosper.common.prosper_config as p_config
import prosper.common.prosper_utilities as p_utils

HERE = path.abspath(path.dirname(__file__))
ME = __file__.replace('.py', '')
CONFIG_ABSPATH = path.join(HERE, 'common_config.cfg')

#COMMON_CONFIG = get_config(CONFIG_ABSPATH)
COMMON_CONFIG = p_config.ProsperConfig(CONFIG_ABSPATH)

DISCORD_MESSAGE_LIMIT = 2000
DISCORD_PAD_SIZE = 100

DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())

SILENCE_OVERRIDE = False    #deactivate webhook loggers for testmode

class ReportingFormats(Enum):
    """Enum for storing handy log formats"""
    DEFAULT = '[%(asctime)s;%(levelname)s;%(filename)s;%(funcName)s;%(lineno)s] %(message)s'
    PRETTY_PRINT = '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s]\n%(message).1000s'
    STDOUT = '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s] %(message)s'
    SLACK_PRINT = '%(message).1000s'

class ProsperLogger(object):
    """One logger to rule them all.  Build the right logger for your script in a few easy steps

    Attributes:
        logger (logging.Logger): current built logger (use get_logger() to fetch)
        log_name (str): the name of the log/log_object
        log_path (str): path for logfile.  abspath > relpath
        log_info (:obj:`list` of :obj:`str`):  list of 'handler_name @ log_level' for debug
        log_handlers (:obj:`list` of :obj:`logging.handlers`): collection of all handlers attached (for testing)

    Todo:
        * add args/local/global config priority management

    """
    _debug_mode = False
    def __init__(
            self,
            log_name,
            log_path,
            config_obj=COMMON_CONFIG,
            debug_mode=_debug_mode
    ):
        """ProsperLogger initialization

        Attributes:
            log_name (str): the name of the log/log_object
            log_path (str): path for logfile.  abspath > relpath
            config_obj (:obj:`configparser.ConfigParser`, optional): config object for loading default behavior
            debug_mode (bool): debug/verbose modes inside object (UNIMPLEMENTED)

        """
        self.logger = logging.getLogger(log_name)
        if not isinstance(config_obj, p_config.ProsperConfig):
            raise TypeError
        self.config = config_obj

        #self.log_options = p_utils.parse_options(config_obj, 'LOGGING')
        self._debug_mode = debug_mode
        self.log_name = log_name
        self.log_path = test_logpath(log_path, debug_mode)

        self.log_info = []
        self.log_handlers = []

        self.configure_default_logger(
            log_freq='midnight',
            log_total=30,
            log_level='INFO',
            debug_mode=debug_mode
        )

    def get_logger(self):
        """return the logger for the user"""
        return self.logger

    def __str__(self):
        """return list of 'handler_name @ log_level' for debug"""
        return ','.join(self.log_info)

    def __iter__(self):
        """returns each handler in order"""
        for handler in self.log_handlers:
            yield handler

    def close_handles(self):
        """cannot delete logs unless handles are closed (windows)"""
        for handle in self.log_handlers:
            try:
                handle.close()
            except Exception:
                warnings.warn(
                    'WARNING: unable to close logging handle',
                    RuntimeWarning
                )
                pass #do not crash if can't close handle

    def _configure_common(
            self,
            prefix,
            fallback_level,
            fallback_format,
            handler_name,
            handler
    ):
        """commom configuration code

        Args:
            prefix (str): A prefix for the `log_level` and `log_format` keys to use with the config. #FIXME: Hacky, add separate sections for each logger config?
            fallback_level (str): Fallback/minimum log level, for if config does not have one.
            fallback_format (str): Fallback format for if it's not in the config.
            handler_name (str): Handler used in debug messages.
            handler (str): The handler to configure and use.

        """
        ## Retrieve settings from config ##
        log_level = self.config.get_option(
            'LOGGING', prefix + 'log_level',
            None, fallback_level
        )
        log_format_name = self.config.get_option(
            'LOGGING', prefix + 'log_format',
            None, None
        )
        log_format = ReportingFormats[log_format_name].value if log_format_name else fallback_format

        ## Attach handlers/formatter ##
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        self.logger.addHandler(handler)
        if not self.logger.isEnabledFor(logging.getLevelName(log_level)): # make sure logger level is not lower than handler level
            self.logger.setLevel(log_level)

        ## Save info about handler created ##
        self.log_info.append(handler_name + ' @ ' + str(log_level))
        self.log_handlers.append(handler)

    def configure_default_logger(
            self,
            log_freq='midnight',
            log_total=30,
            log_level='INFO',
            log_format=ReportingFormats.DEFAULT.value,
            debug_mode=_debug_mode
    ):
        """default logger that every Prosper script should use!!

        Args:
            log_freq (str): TimedRotatingFileHandle_str -- https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler
            log_total (int): how many log_freq periods between log rotations
            log_level (str): minimum desired log level https://docs.python.org/3/library/logging.html#logging-levels
            log_format (str): format for logging messages https://docs.python.org/3/library/logging.html#logrecord-attributes
            debug_mode (bool): a way to trigger debug/verbose modes inside object (UNIMPLEMENTED)

        """
        ## Override defaults if required ##
        log_freq  = self.config.get_option(
            'LOGGING', 'log_freq',
            None, log_freq
        )
        log_total = self.config.get_option(
            'LOGGING', 'log_total',
            None, log_total
        )

        ## Set up log file handles/name ##
        log_filename = self.log_name + '.log'
        log_abspath = path.join(self.log_path, log_filename)
        general_handler = TimedRotatingFileHandler(
            log_abspath,
            when=log_freq,
            interval=1,
            backupCount=int(log_total)
        )

        self._configure_common('', log_level, log_format, 'default', general_handler)

    def configure_debug_logger(
            self,
            log_level='DEBUG',
            log_format=ReportingFormats.STDOUT.value,
            debug_mode=_debug_mode
    ):
        """debug logger for stdout messages.  Replacement for print()

        Note:
            Will try to overwrite minimum log level to enable requested log_level

        Args:
            log_level (str): desired log level for handle https://docs.python.org/3/library/logging.html#logging-levels
            log_format (str): format for logging messages https://docs.python.org/3/library/logging.html#logrecord-attributes
            debug_mode (bool): a way to trigger debug/verbose modes inside object (UNIMPLEMENTED)

        """

        self._configure_common('debug_', log_level, log_format, 'Debug', logging.StreamHandler())

    def configure_discord_logger(
            self,
            discord_webhook=None,
            discord_recipient=None,
            log_level='ERROR',
            log_format=ReportingFormats.PRETTY_PRINT.value,
            debug_mode=_debug_mode
    ):
        """logger for sending messages to Discord.  Easy way to alert humans of issues

        Note:
            Will try to overwrite minimum log level to enable requested log_level
            Will warn and not attach hipchat logger if missing webhook key
            Learn more about webhooks: https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks
        Args:
            discord_webhook (str): discord room webhook (full URL)
            discord_recipient (`str`:<@int>, optional): user/group to notify
            log_level (str): desired log level for handle https://docs.python.org/3/library/logging.html#logging-levels
            log_format (str): format for logging messages https://docs.python.org/3/library/logging.html#logrecord-attributes
            debug_mode (bool): a way to trigger debug/verbose modes inside object (UNIMPLEMENTED)

        """
        ## Override defaults if required ##
        discord_webhook = self.config.get_option(
            'LOGGING', 'discord_webhook',
            None, discord_webhook
        )
        discord_recipient = self.config.get_option(
            'LOGGING', 'discord_recipient',
            None, discord_recipient
        )

        ## Make sure we CAN build a discord webhook ##
        if not discord_webhook:
            warnings.warn(
                'Lacking discord_webhook defintion, unable to attach webhook',
                RuntimeWarning
            )
            return

        ## Actually build discord logging handler ##
        discord_obj = DiscordWebhook()
        discord_obj.webhook(discord_webhook)
        if discord_obj.can_query:
            try:
                discord_handler = HackyDiscordHandler(
                    discord_obj,
                    discord_recipient
                )
                self._configure_common(
                    'discord_',
                    log_level,
                    log_format,
                    'Discord',
                    discord_handler
                )
            except Exception as error_msg: #FIXME: remove this, if we're just re-throwing?
                raise error_msg
        else:
            warnings.warn(
                'Unable to execute webhook',
                RuntimeWarning
            )

    def configure_slack_logger(
            self,
            slack_webhook=None,
            log_level='ERROR',
            log_format=ReportingFormats.SLACK_PRINT.value,
            debug_mode=_debug_mode
    ):
        """logger for sending messages to Discord.  Easy way to alert humans of issues

        Note:
            Will try to overwrite minimum log level to enable requested log_level
            Will warn and not attach hipchat logger if missing webhook key
            Learn more about webhooks: https://api.slack.com/docs/message-attachments
        Args:
            slack_webhook (str): slack bot webhook (full URL)
            log_level (str): desired log level for handle https://docs.python.org/3/library/logging.html#logging-levels
            log_format (str): format for logging messages https://docs.python.org/3/library/logging.html#logrecord-attributes
            debug_mode (bool): a way to trigger debug/verbose modes inside object (UNIMPLEMENTED)

        """
        ## Override defaults if required ##
        slack_webhook = self.config.get_option(
            'LOGGING', 'slack_webhook',
            None, slack_webhook
        )


        ## Make sure we CAN build a slack webhook ##
        if not slack_webhook:
            warnings.warn(
                'Lacking slack_webhook defintion, unable to attach webhook',
                RuntimeWarning
            )
            return

        ## Actually build slack logging handler ##
        try:
            slack_handler = HackySlackHandler(
                slack_webhook
            )
            self._configure_common(
                'slack_',
                log_level,
                log_format,
                'Slack',
                slack_handler
            )
        except Exception as error_msg:
            raise error_msg

def test_logpath(log_path, debug_mode=False):
    """Tests if logger has access to given path and sets up directories

    Note:
        Should always yield a valid path.  May default to script directory
        Will throw warnings.RuntimeWarning if permissions do not allow file write at path

    Args:
        log_path (str): path to desired logfile.  Abspath > relpath
        debug_mode (bool): way to make debug easier by forcing path to local

    Returns:
        str: path to log

        if path exists or can be created, will return log_path
        else returns '.' as "local path only" response

    """
    if debug_mode:
        return '.' #if debug, do not deploy to production paths

    ## Try to create path to log ##
    if not path.exists(log_path):
        try:
            makedirs(log_path, exist_ok=True)
        except PermissionError as err_permission:
            #UNABLE TO CREATE LOG PATH
            warning_msg = (
                'Unable to create logging path.  Defaulting to \'.\'' +
                'log_path={0}'.format(log_path) +
                'exception={0}'.format(err_permission)
            )
            warnings.warn(
                warning_msg,
                RuntimeWarning
            )
            return '.'

    ## Make sure logger can write to path ##
    if not access(log_path, W_OK):
        #UNABLE TO WRITE TO LOG PATH
        warning_msg = (
            'Lacking write permissions to path.  Defaulting to \'.\'' +
            'log_path={0}'.format(log_path)
        )
        warnings.warn(
            warning_msg,
            RuntimeWarning
        )
        return '.'
        #TODO: windows behavior requires abspath to existing file

    return log_path

def create_logger(
        log_name,
        log_path,
        config_obj = None,
        log_level_override = ''
):   #pragma: no cover
    """DEPRECATED: classic v1 logger.  Obsolete by v0.3.0"""
    warnings.warn(
        'create_logger replaced with ProsperLogger object',
        DeprecationWarning
    )
    if not config_obj:
        config_obj = COMMON_CONFIG

    if not path.exists(log_path):
        makedirs(log_path)

    Logger = logging.getLogger(log_name)

    log_level = config_obj.get('LOGGING', 'log_level')
    log_freq  = config_obj.get('LOGGING', 'log_freq')
    log_total = config_obj.get('LOGGING', 'log_total')

    log_name = log_name + '.log'
    log_format = '[%(asctime)s;%(levelname)s;%(filename)s;%(funcName)s;%(lineno)s] %(message)s'
    if log_level_override:
        log_level = log_level_override

    log_full_path = path.join(log_path, log_name)

    Logger.setLevel(log_level)
    generalHandler = TimedRotatingFileHandler(
        log_full_path,
        when=log_freq,
        interval=1,
        backupCount=int(log_total)
    )
    formatter = logging.Formatter(log_format)
    generalHandler.setFormatter(formatter)
    Logger.addHandler(generalHandler)

    if log_level_override == 'DEBUG':
        short_format = '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s] %(message)s'
        short_formatter = logging.Formatter(short_format)
        stdout = logging.StreamHandler()
        stdout.setFormatter(short_formatter)
        Logger.addHandler(stdout)

    if all([
            config_obj.has_option('LOGGING', 'discord_webhook'),
            config_obj.has_option('LOGGING', 'discord_level'),
            #config_obj.has_option('LOGGING', 'discord_alert_recipient')
    ]):
        #message_maxlength = DISCORD_MESSAGE_LIMIT - DISCORD_PAD_SIZE
        discord_format = '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s]\n%(message).1400s'
        alert_recipient = None
        if config_obj.has_option('LOGGING', 'discord_alert_recipient'):
            alert_recipient = config_obj.get('LOGGING', 'discord_alert_recipient')

        discord_obj = DiscordWebhook()
        discord_obj.webhook(config_obj.get('LOGGING', 'discord_webhook'))
        discord_level = config_obj.get('LOGGING', 'discord_level')
        do_discord = all([discord_obj.can_query, discord_level])
        if do_discord:
            try:
                dh = HackyDiscordHandler(
                    discord_obj,
                    alert_recipient
                )
                dh_format = logging.Formatter(discord_format)
                dh.setFormatter(dh_format)
                dh.setLevel(discord_level)
                Logger.addHandler(dh)
            except Exception as error_msg:
                raise error_msg

    return Logger

class DiscordWebhook(object):
    """Helper object for parsing info and testing discord webhook credentials

    Attributes:
        webhook_url (str): address of webhook endpoint
        serverid (int): Discord 'guild' webhook is attached to
        api_key (`str`:uuid): unique ID for webhook

    """
    __base_url = 'https://discordapp.com/api/webhooks/'
    __webhook_url_format = __base_url + r"(\d+)/([\w-]+)"
    def __init__(self):
        """DiscordWebhook initialization"""
        self.webhook_url = ''
        self.serverid = 0
        self.api_key = ''
        self.can_query = False
        self.webhook_response = None

    def webhook(self, webhook_url):
        """Load object with webhook_url

        Args:
            webhook_url (str): full webhook url given by Discord 'create webhook' func

        """
        if not webhook_url:
            raise Exception('Url can not be None')

        matcher = re.match(self.__webhook_url_format, webhook_url)
        if not matcher:
            raise Exception('Invalid url format, looking for: ' + self.__webhook_url_format)

        self.api_keys(int(matcher.group(1)), matcher.group(2))

    def api_keys(self, serverid, api_key):
        """Load object with id/API pair

        Args:
            serverid (int): Discord 'guild' webhook is attached to
            api_key (`str`:uuid): unique ID for webhook

        """
        if serverid and api_key:
            self.can_query = True # Yes, we _are_ (will be) configured
        self.serverid = int(serverid)
        self.api_key = api_key
        self.webhook_url = self.__base_url + str(self.serverid) + '/' + self.api_key


    def get_webhook_info(self):
        """Ping Discord endpoint to make sure webhook is valid and working"""
        if not self.can_query:
            raise RuntimeError('webhook information not loaded, cannot query')

        raise NotImplementedError('requests call to discord server for API info: TODO') # pragma: no cover

    def __bool__(self):
        return self.can_query

    def __str__(self):
        return self.webhook_url

class HackyDiscordHandler(logging.Handler):
    """Custom logging.Handler for pushing messages to Discord

    Should be able to push messages to any REST webhook with small adjustments

    Stolen from https://github.com/invernizzi/hiplogging/blob/master/hiplogging/__init__.py

    Discord webhook API docs: https://discordapp.com/developers/docs/resources/webhook

    """
    def __init__(self, webhook_obj, alert_recipient=None):
        """HackyDiscordHandler init

        Args:
            webhook_obj (:obj:`DiscordWebhook`): discord webhook has all the info for connection
            alert_recipients (`str`:<@int>, optional): user/group to notify

        """
        logging.Handler.__init__(self)
        self.webhook_obj = webhook_obj
        if not self.webhook_obj: # test if it's configured
            raise Exception('Webhook not configured.')

        self.api_url = webhook_obj.webhook_url
        self.alert_recipient = alert_recipient
        self.alert_length = 0
        if self.alert_recipient:
            self.alert_length = len(self.alert_recipient)

    def emit(self, record): # pragma: no cover
        """required classmethod for logging to execute logging message"""
        if record.exc_text:
            record.exc_text = '```python\n{0}\n```'.format(record.exc_text) # recast to code block
        log_msg = self.format(record)
        if len(log_msg) + self.alert_length > DISCORD_MESSAGE_LIMIT:
            log_msg = log_msg[:(DISCORD_MESSAGE_LIMIT - DISCORD_PAD_SIZE)]

        if self.alert_recipient and record.levelno == logging.CRITICAL:
            log_msg = log_msg + '\n' + str(self.alert_recipient)

        self.send_msg_to_webhook(log_msg)

    def send_msg_to_webhook(self, message):
        """separated Requests logic for easier testing

        Args:
            message (str): actual logging string to be passed to REST endpoint

        Todo:
            * Requests.text/json return for better testing options
        """
        payload = {
            'content':message
        }

        header = {
            'Content-Type':'application/json'
        }

        try:
            request = requests.post(
                self.api_url,
                headers=header,
                json=payload
            )
        except Exception as error_msg:
            warning_msg = (
                'EXCEPTION: UNABLE TO COMMIT LOG MESSAGE' +
                '\n\texception={0}'.format(error_msg) +
                '\n\tmessage={0}'.format(message)
            )
            warnings.warn(
                warning_msg,
                RuntimeWarning
            )
    def test(self, message):
        """testing hook for exercising webhook directly"""
        #TODO: remove and just use send_msg_to_webhook?
        try:
            self.send_msg_to_webhook(message)
        except Exception as error_msg:
            raise error_msg

class HackySlackHandler(logging.Handler):
    """Custom logging.Handler for pushing messages to Discord"""
    def __init__(self, webhook_url):
        logging.Handler.__init__(self)

        self.webhook_url = webhook_url

    def emit(self, record):
        #log_msg = self.format(record)
        log_payload = self.decorate(record)
        if record.exc_text:
            record.exc_text = '```\n{0}\n```'.format(record.exc_text) # recast to code block
        log_msg = self.format(record)
        self.send_msg_to_webhook(log_payload, log_msg)

    def decorate(self, record):
        """add slack-specific flourishes to responses

        https://api.slack.com/docs/message-attachments

        Args:
            record (:obj:`logging.record`): message to log

        Returns:
            (:obj:`dict`): attachments object for reporting

        """
        attachments = {}
        ## Set color
        if record.levelno >= logging.ERROR:
            attachments['color'] = 'warning' #builtin
        if record.levelno >= logging.CRITICAL:
            attachments['color'] = 'danger' #builtin

        ## Log text
        attach_text = '{levelname}: {name} {module}.{funcName}:{lineno}'.format(
            levelname=record.levelname,
            name=record.name,
            module=record.module,
            funcName=record.funcName,
            lineno=record.lineno
        )
        attachments['text'] = attach_text
        attachments['fallback'] = attach_text
        return attachments

    def send_msg_to_webhook(self, json_payload, log_msg):
        """push message out to webhook

        Args:
            json_payload(:obj:`dict`): preformatted payload a la https://api.slack.com/docs/message-attachments

        """
        if SILENCE_OVERRIDE:
            return

        payload = {
            'text': log_msg,
            'attachments':[json_payload]
        }
        header = {
            'Content-Type':'application/json'
        }

        try:
            request = requests.post(
                self.webhook_url,
                headers=header,
                json=payload
            )
        except Exception as error_msg:
            warning_msg = (
                'EXCEPTION: UNABLE TO COMMIT LOG MESSAGE' +
                '\n\texception={0}'.format(error_msg) +
                '\n\tmessage={0}'.format(message)
            )
            warnings.warn(
                warning_msg,
                RuntimeWarning
            )
