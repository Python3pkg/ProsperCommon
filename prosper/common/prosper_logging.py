'''prosper_logging.py: extension/standadized logging utilities for prosper'''

from os import path, makedirs
import logging
from logging.handlers import TimedRotatingFileHandler

import requests

from prosper.common.prosper_config import get_config

HERE = path.abspath(path.dirname(__file__))
ME = __file__.replace('.py', '')
CONFIG_ABSPATH = path.join(HERE, 'common_config.cfg')

COMMON_CONFIG = get_config(CONFIG_ABSPATH)
DISCORD_MESSAGE_LIMIT = 2000
DISCORD_PAD_SIZE = 100

def create_logger(
        log_name,
        log_path,
        config_obj = None,
        log_level_override = ''
):
    '''creates logging handle for programs'''
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
