'''prosper_logging.py: extension/standadized logging utilities for prosper'''

from os import path, makedirs, access, W_OK#, R_OK
import logging
from logging.handlers import TimedRotatingFileHandler
import warnings

import requests

from prosper.common.prosper_config import get_config
import prosper.common.prosper_utilities as p_utils

HERE = path.abspath(path.dirname(__file__))
ME = __file__.replace('.py', '')
CONFIG_ABSPATH = path.join(HERE, 'common_config.cfg')

COMMON_CONFIG = get_config(CONFIG_ABSPATH)
DISCORD_MESSAGE_LIMIT = 2000
DISCORD_PAD_SIZE = 100

#DEFAULT_LOGGER = logging.getLogger('NULL')
#DEFAULT_LOGGER.addHandler(logging.NullHandler())

class ReportingFormats:
    """Enum for storing handy log formats"""
    DEFAULT = '[%(asctime)s;%(levelname)s;%(filename)s;%(funcName)s;%(lineno)s] %(message)s'
    PRETTY_PRINT = '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s]\n%(message).1400s'
    STDOUT = '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s] %(message)s'

    def str_to_format(self, format_name):
        """parse a string to enum.  For loading from config

        Args:
            format_name (str): name of an enum format

        Returns:
            str: ReportingFormats enum for requested level

        """
        format_name = format_name.upper()
        if   format_name == 'DEFAULT':
            return self.DEFAULT
        elif format_name == 'PRETTY_PRINT':
            return self.PRETTY_PRINT
        elif format_name == 'STDOUT':
            return self.STDOUT
        else:
            return self.DEFAULT

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
        self.log_options = p_utils.parse_options(config_obj, 'LOGGING')
        self._debug_mode = debug_mode
        self.log_name = log_name
        self.log_path = test_logpath(log_path, debug_mode)

        self.log_info = []
        self.log_handlers = []

        self.configure_default_logger(debug_mode=debug_mode)

    def get_logger(self):
        """return the logger for the user"""
        return self.logger

    def __str__(self):
        """return list of 'handler_name @ log_level' for debug"""
        return ','.join(self.log_info)

    def configure_default_logger(
            self,
            log_freq=None,
            log_total=None,
            log_level=None,
            log_format=ReportingFormats().DEFAULT,
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
        try:
            if not log_freq:
                log_freq = self.log_options['log_freq']
            if not log_total:
                log_total = self.log_options['log_total']
            if not log_level:
                log_level = self.log_options['log_level']
        except KeyError as error_msg:
            raise error_msg

        log_filename = self.log_name + '.log'
        log_abspath = path.join(self.log_path, log_filename)
        general_handler = TimedRotatingFileHandler(
            log_abspath,
            when=log_freq,
            interval=1,
            backupCount=int(log_total) #FIXME: defaults
        )

        formatter = logging.Formatter(log_format)
        general_handler.setFormatter(formatter)

        self.logger.setLevel(log_level)
        self.logger.addHandler(general_handler)

        self.log_info.append('default @ ' + str(log_level))
        self.log_handlers.append(general_handler)

    def configure_debug_logger(
            self,
            log_level='DEBUG',
            log_format=ReportingFormats().STDOUT,
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
        formatter = logging.Formatter(log_format)
        debug_handler = logging.StreamHandler()
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(log_level)

        self.logger.addHandler(debug_handler)
        if not self.logger.isEnabledFor(log_level):
            self.logger.setLevel(log_level) #override log_level min if less than current min

        self.log_info.append('debug @ ' + str(log_level))
        self.log_handlers.append(debug_handler)

    def configure_discord_logger(
            self,
            discord_webhook=None,
            discord_recipient=None,
            log_level='ERROR',
            log_format=ReportingFormats().PRETTY_PRINT,
            debug_mode=_debug_mode
    ):
        """logger for sending messages to Discord.  Easy way to alert humans of issues

        Note:
            Will try to overwrite minimum log level to enable requested log_level
            Will warn and not attach hipchat logger if missing webhook key
            Learn more about webhooks: https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks
        Args:
            discord_webhook (str): hipchat room webhook (full URL)
            discord_recipient (`str`:<@int>, optional): user/group to notify
            log_level (str): desired log level for handle https://docs.python.org/3/library/logging.html#logging-levels
            log_format (str): format for logging messages https://docs.python.org/3/library/logging.html#logrecord-attributes
            debug_mode (bool): a way to trigger debug/verbose modes inside object (UNIMPLEMENTED)

        """
        ## Make sure we can set discord handlers ##
        if not discord_webhook:
            try:
                discord_webhook = self.log_options['discord_webhook']
            except KeyError:
                warnings.warn(
                    'Lacking discord_webhook defintion, unable to attach webhook',
                    ResourceWarning
                )
                return None
            finally:
                if not discord_webhook:
                    warnings.warn(
                        'Lacking discord_webhook defintion, unable to attach webhook',
                        ResourceWarning
                    )
                    return None

        ## Actually build discord logging handler ##
        discord_obj = DiscordWebhook()
        discord_obj.webhook(discord_webhook)
        if discord_obj.can_query:
            try:
                discord_handler = HackyDiscordHandler(
                    discord_obj,
                    discord_recipient
                )
                discord_format = logging.Formatter(log_format)
                discord_handler.setFormatter(discord_format)
                discord_handler.setLevel(log_level)
                self.logger.addHandler(discord_handler)
            except Exception as error_msg:
                raise error_msg

            self.log_info.append('discord @ ' + str(log_level))
            self.log_handlers.append(discord_handler)
        else:
            warnings.warn('Unable to execute webhook', ResourceWarning)

def test_logpath(log_path, debug_mode=False):
    """Tests if logger has access to given path and sets up directories

    Note:
        Should always yield a valid path.  May default to script directory
        Will throw warnings.ResourceWarning if permissions do not allow file write at path

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
                ResourceWarning
            )
            return '.'
        except Exception as err_msg:
            raise err_msg

    ## Make sure logger can write to path ##
    if not access(log_path, W_OK):
        #UNABLE TO WRITE TO LOG PATH
        warning_msg = (
            'Lacking write permissions to path.  Defaulting to \'.\'' +
            'log_path={0}'.format(log_path) +
            'exception={0}'.format(err_permission)
        )
        warnings.warn(
            warning_msg,
            ResourceWarning
        )
        return '.'
        #TODO: windows behavior requires abspath to existing file

    return log_path

def create_logger(
        log_name,
        log_path,
        config_obj = None,
        log_level_override = ''
):
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
    #print(logName + ':' + logLevel)
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
        #print('LOGGER: adding stdout handler')
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
        #print('LOGGER: adding discord handler')
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
                print('UNABLE TO ATTATCH DISCORD HANDLER - ' + str(error_msg))

    return Logger

class DiscordWebhook(object):
    """Helper object for parsing info and testing discord webhook credentials

    Attributes:
        webhook_url (str): address of webhook endpoint
        serverid (int): Discord 'guild' webhook is attached to
        api_key (`str`:uuid): unique ID for webhook

    """
    __base_url = 'https://discordapp.com/api/webhooks/'
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
        if webhook_url:
            self.can_query = True
        self.webhook_url = webhook_url
        #FIXME vv this is hacky as fuck
        trunc_url = self.webhook_url.replace(self.__base_url, '')
        id_list = trunc_url.split('/')
        self.serverid = int(id_list[0])
        self.api_key = id_list[1]

    def api_keys(self, serverid, api_key):
        """Load object with id/API pair

        Args:
            serverid (int): Discord 'guild' webhook is attached to
            api_key (`str`:uuid): unique ID for webhook

        """
        if serverid and api_key:
            self.can_query = True
        self.serverid = serverid
        self.api_key = api_key
        self.webhook_url = self.__base_url + self.serverid + '/' + self.api_key


    def get_webhook_info(self):
        """Ping Discord endpoint to make sure webhook is valid and working"""
        if not self.can_query:
            raise RuntimeError('webhook information not loaded, cannot query')

        raise NotImplementedError('requests call to discord server for API info: TODO')

    def __bool__(self):
        return self.can_query

    def __str__(self):
        return self.webhook_url

class HackyDiscordHandler(logging.Handler):
    """Custom logging.Hnalder for pushing messages to Discord

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
        self.api_url = self.webhook_obj.webhook_url
        self.alert_recipient = alert_recipient
        self.alert_length = 0
        if self.alert_recipient:
            self.alert_length = len(self.alert_recipient)

    def emit(self, record):
        """required classmethod for logging to execute logging message"""
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
            print(
                'EXCEPTION: UNABLE TO COMMIT LOG MESSAGE' +
                '\r\texception={0}'.format(error_msg) +
                '\r\tmessage={0}'.format(message)
            )
    def test(self, message):
        """testing hook for exercising webhook directly"""
        try:
            self.send_msg_to_webhook(message)
        except Exception as error_msg:
            raise error_msg
