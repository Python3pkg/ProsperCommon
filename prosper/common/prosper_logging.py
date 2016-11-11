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
    '''a handy enum of reporting formats for every occasion'''
    DEFAULT = '[%(asctime)s;%(levelname)s;%(filename)s;%(funcName)s;%(lineno)s] %(message)s'
    PRETTY_PRINT = '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s]\n%(message).1400s'
    STDOUT = '[%(levelname)s:%(filename)s--%(funcName)s:%(lineno)s] %(message)s'

class ProsperLogger(object):
    '''container for building a logger for prosper tools'''
    _debug_mode = False
    def __init__(
            self,
            log_name,
            log_path,
            config_obj=COMMON_CONFIG,
            debug_mode=_debug_mode
    ):
        self.logger = logging.getLogger(log_name)
        self.log_options = p_utils.parse_options(config_obj, 'LOGGING')
        self._debug_mode = debug_mode
        self.log_name = log_name
        self.log_path = test_logpath(log_path, debug_mode)

        self.log_info = []
        self.log_handlers = []
        self.configure_default_logger(debug_mode=debug_mode)

    def get_logger(self):
        '''yield logging object for script to work with'''
        return self.logger

    def __str__(self):
        '''for debug purposes, list attached log handlers'''
        return ','.join(self.log_info)

    def configure_default_logger(
            self,
            log_freq=None,
            log_total=None,
            log_level=None,
            log_format=ReportingFormats().DEFAULT,
            debug_mode=_debug_mode
    ):
        '''build default logger object and handlers'''
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
            backupCount=log_total #FIXME: defaults
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
        '''attach debug logging info for debug'''
        formatter = logging.Formatter(log_format)
        debug_handler = logging.StreamHandler()
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(log_level)

        self.logger.addHandler(debug_handler)
        self.logger.setLevel(log_level)     #override log_level minimum

        self.log_info.append('debug @ ' + str(log_level))
        self.log_handlers.append(debug_handler)

    def configure_discord_logger(
            self,
            log_level='ERROR',
            log_format=ReportingFormats().PRETTY_PRINT,
            discord_webhook=None,
            discord_recipient=None,
            debug_mode=_debug_mode
    ):
        '''attach discord options'''

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
                #raise KeyError('Lacking discord_webhook definition')
            finally:
                if not discord_webhook:
                    #raise KeyError('Lacking discord_webhook definition')
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

def test_logpath(log_path, debug_mode=False):
    '''test if logger has access to given path, and set up directories
    RETURNS: valid log_path, after setting up pathing
        '.' or log_path
    '''
    if debug_mode:
        return '.' #if debug, do not deploy to production paths

    ## Try to create path to log ##
    if not path.exists(log_path):
        try:
            makedirs(log_path, exist_ok=True)
        except PermissionError as err_permission:
            #UNABLE TO CREATE LOG PATH
            warning_msg = \
                'Unable to create logging path.  Defaulting to \'.\'' + \
                'log_path={0}'.format(log_path) + \
                'exception={0}'.format(err_permission)
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
        warning_msg = \
            'Lacking write permissions to path.  Defaulting to \'.\'' + \
            'log_path={0}'.format(log_path) + \
            'exception={0}'.format(err_permission)
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
    '''creates logging handle for programs'''
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
        backupCount=log_total
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
    '''parser for webhooks for easier api calling'''
    __base_url = 'https://discordapp.com/api/webhooks/'
    def __init__(self):
        self.webhook_url = ''
        self.serverid = 0
        self.api_key = ''
        self.can_query = False
        self.webhook_response = None

    def webhook(self, webhook_url):
        '''parse pieces of webhook credentials from url'''
        if webhook_url:
            self.can_query = True
        self.webhook_url = webhook_url
        #FIXME vv this is hacky as fuck
        trunc_url = self.webhook_url.replace(self.__base_url, '')
        id_list = trunc_url.split('/')
        self.serverid = int(id_list[0])
        self.api_key = id_list[1]

    def api_keys(self, serverid, api_key):
        '''with a id/api pair, assemble the webhook_url'''
        if serverid and api_key:
            self.can_query = True
        self.serverid = serverid
        self.api_key = api_key
        self.webhook_url = self.__base_url + self.serverid + '/' + self.api_key


    def get_webhook_info(self):
        '''fetch api profile from discord servers'''
        if not self.can_query:
            raise RuntimeError('webhook information not loaded, cannot query')

        raise NotImplementedError('requests call to discord server for API info: TODO')

    def __bool__(self):
        return self.can_query

    def __str__(self):
        return self.webhook_url

class HackyDiscordHandler(logging.Handler):
    '''hacky in-house discord/REST handler'''
    def __init__(self, webhook_obj, alert_recipient=None):
        logging.Handler.__init__(self)
        self.webhook_obj = webhook_obj
        self.api_url = self.webhook_obj.webhook_url
        self.alert_recipient = alert_recipient
        self.alert_length = 0
        if self.alert_recipient:
            self.alert_length = len(self.alert_recipient)

    def emit(self, record):
        '''logging logic goes here'''
        log_msg = self.format(record)
        if len(log_msg) + self.alert_length > DISCORD_MESSAGE_LIMIT:
            log_msg = log_msg[:(DISCORD_MESSAGE_LIMIT - DISCORD_PAD_SIZE)]

        if self.alert_recipient and record.levelno == logging.CRITICAL:
            log_msg = log_msg + '\n' + str(self.alert_recipient)

        self.send_msg_to_webhook(log_msg)

    def send_msg_to_webhook(self, message):
        '''requests framework for sending log message to webhook'''
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
                'EXCEPTION: UNABLE TO COMMIT LOG MESSAGE' + \
                '\r\texception={0}'.format(error_msg) + \
                '\r\tmessage={0}'.format(message)
            )
    def test(self, message):
        '''hook for testing webhook logic'''
        try:
            self.send_msg_to_webhook(message)
        except Exception as error_msg:
            raise error_msg
class LoggerLevels:
    '''enums for logger'''
    #FIXME vvv import actual logger enum?
    #https://docs.python.org/3/library/logging.html#logging-levels
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    def str_to_level(self, log_level):
        '''converts str to int enum'''
        log_level = log_level.upper()
        if  log_level == 'CRITICAL':
            return self.CRITICAL
        elif log_level == 'ERROR':
            return self.ERROR
        elif log_level == 'WARNING':
            return self.WARNING
        elif log_level == 'INFO':
            return self.INFO
        elif log_level == 'DEBUG':
            return self.DEBUG
        else:
            return self.NOTSET

if __name__ == '__main__':
    TEST_LOGGER = create_logger(
        'common_logger_debug',
        '.',
        COMMON_CONFIG,
        'DEBUG'
    )

    TEST_LOGGER.debug('prosper.common.prosper_logging TEST --DEBUG--')
    TEST_LOGGER.info('prosper.common.prosper_logging TEST --INFO--')
    TEST_LOGGER.warning('prosper.common.prosper_logging TEST --WARNING--')
    TEST_LOGGER.error('prosper.common.prosper_logging TEST --ERROR--')
    TEST_LOGGER.critical('prosper.common.prosper_logging TEST --CRITICAL--')
