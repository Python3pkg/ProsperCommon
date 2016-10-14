'''prosper_logging.py: extension/standadized logging utilities for prosper'''

from os import path
import logging
from logging.handlers import TimedRotatingFileHandler

import requests

from prosper_config import get_config

HERE = path.abspath(path.dirname(__file__))
ME = __file__.replace('.py', '')
CONFIG_ABSPATH = path.join(HERE, 'common_config.cfg')

COMMON_CONFIG = get_config(CONFIG_ABSPATH)

def create_logger(
        log_name,
        log_path,
        config_obj = None,
        log_level_override = ''
):
    '''creates logging handle for programs'''
    if not config_obj:
        #build up mini-config off in-script defaults
        tmpconfig = configparser.ConfigParser()
        tmpconfig['LOGGING'] = LOGGER_DEFAULTS
        config_obj = tmpconfig

    if not os.path.exists(log_path):
        os.makedirs(log_path)
    #logFolder = os.path.join('../', tmpConfig.get('LOGGING', 'logFolder'))
    #if not os.path.exists(logFolder):
    #    os.makedirs(logFolder)

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
        self.webhook_url = webhook_url
        #FIXME vv this is hacky as fuck
        trunc_url = self.webhook_url.replace(self.__base_url, '')
        id_list = trunc_url.split('/')
        self.serverid = int(id_list[0])
        self.api_key = id_list[1]

    def api_keys(self, serverid, api_key):
        '''with a id/api pair, assemble the webhook_url'''
        self.serverid = serverid
        self.api_key = api_key
        self.webhook_url = self.__base_url + self.serverid + '/' + self.api_key

    def get_webhook_info(self):
        '''fetch api profile from discord servers'''
        if not self.can_query:
            raise RuntimeError('webhook information not loaded, cannot query')

        raise NotImplementedError('requests call to discord server for API info: TODO')

class HackyDiscordHandler(logging.Handler):
    '''hacky in-house discord/REST handler'''
    def __init__(self, webhook_obj):
        pass
