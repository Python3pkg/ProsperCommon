'''utilities.py: worker functions for CREST calls'''

import os
import logging
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
import configparser
from configparser import ExtendedInterpolation

#CONFIG_FILES = ['prosperAPI_local.cfg','prosperAPI.cfg'] #TODO: change to .cfg?

LOGGER_DEFAULTS = {
    'log_level': 'DEBUG',
    'log_freq': 'd',
    'log_total': '60',
    'log_email_level': 'CRITICAL'
}

def get_config(
        config_filepath
):
    '''returns config object for parsing global values'''
    config = configparser.ConfigParser(
        interpolation=ExtendedInterpolation(),
        allow_no_value=True,
        delimiters=('=')
    )

    local_config_filepath = config_filepath.replace('.cfg', '_local.cfg')

    real_config_filepath = ''
    if os.path.isfile(local_config_filepath):
        #if _local.cfg version exists, use it instead
        real_config_filepath = local_config_filepath
    else:
        #else use tracked default
        real_config_filepath = config_filepath

    with open(real_config_filepath, 'r') as filehandle:
        config.read_file(filehandle)
    return config
    #TODO: add cfg error handling just in case

def create_logger(
        logName,
        logPath,
        configObject = None,
        logLevel_override = ''
):
    '''creates logging handle for programs'''
    if not configObject:
        #build up mini-config off in-script defaults
        tmpconfig = configparser.ConfigParser()
        tmpconfig['LOGGING'] = LOGGER_DEFAULTS
        configObject = tmpconfig

    if not os.path.exists(logPath):
        os.makedirs(logPath)
    #logFolder = os.path.join('../', tmpConfig.get('LOGGING', 'logFolder'))
    #if not os.path.exists(logFolder):
    #    os.makedirs(logFolder)

    Logger = logging.getLogger(logName)

    logLevel  = configObject.get('LOGGING', 'log_level')
    logFreq   = configObject.get('LOGGING', 'log_freq')
    logTotal  = configObject.get('LOGGING', 'log_total')

    logName   = logName + '.log'
    logFormat = '[%(asctime)s;%(levelname)s;%(filename)s;%(lineno)s] %(message)s'
    #print(logName + ':' + logLevel)
    if logLevel_override:
        logLevel = logLevel_override

    logFullpath = os.path.join(logPath, logName)

    Logger.setLevel(logLevel)
    generalHandler = TimedRotatingFileHandler(
        logFullpath,
        when        = logFreq,
        interval    = 1,
        backupCount = logTotal
    )
    formatter = logging.Formatter(logFormat)
    generalHandler.setFormatter(formatter)
    Logger.addHandler(generalHandler)

#    bool_doEmail = False
#    try:
#        emailSource     = configObject.get('LOGGING', 'emailSource')
#        emailRecipients = configObject.get('LOGGING', 'emailRecipients')
#        emailUsername   = configObject.get('LOGGING', 'emailUsername')
#        emailFromaddr   = configObject.get('LOGGING', 'emailFromaddr')
#        emailSecret     = configObject.get('LOGGING', 'emailSecret')
#        emailServer     = configObject.get('LOGGING', 'emailServer')
#        emailPort       = configObject.get('LOGGING', 'emailPort')
#        emailTitle      = logName + ' CRITICAL ERROR'
#
#        bool_doEmail = (
#            emailSource     and
#            emailRecipients and
#            emailUsername   and
#            emailFromaddr   and
#            emailSecret     and
#            emailServer     and
#            emailPort
#        )
#    except (KeyError, configparser.NoOptionError) as error:
#        #email keys not included, don't set up SMTPHandler
#        bool_doEmail = False
#
#    if bool_doEmail:
#        emailHandler = SMTPHandler(
#            mailhost    = emailServer + ':' + emailPort,
#            fromaddr    = emailFromaddr,
#            toaddrs     = str(emailRecipients).split(','),
#            subject     = emailTitle,
#            credentials = (emailUsername, emailSecret)
#        )
#        emailHandler.setFormatter(formatter)
#        Logger.addHandler(emailHandler)

    return Logger

def email_body_builder(errorMsg, helpMsg):
    '''Builds email message for easier reading with SMTPHandler'''
    #todo: format emails better
    return errorMsg + '\n' + helpMsg

def quandlfy_json(jsonObj):
    '''turn object from JSON into QUANDL-style JSON'''
    pass

def quandlfy_xml(xmlObj):
    '''turn object from XML into QUANDL-style XML'''
    pass

def log_and_debug(debug_str, debug=False, logger=None, log_level="DEBUG"):
    '''handles debug logger/print statements'''
    if debug:
        print(debug_str)
    if logger:
        logger.log(log_level.upper(), debug_str)

class LoggerDebugger(object):
    '''container for executing print/debug/log calls'''
    def __init__(self, debug, logger):
        self.debug=debug,
        self.logger=logger
        self.do_debug=bool(debug)
        self.do_logger=bool(logger)

    def message(self, message_str, log_level):
        '''actually do the thing'''
        if self.do_debug:
            print(message_str)
        if self.do_logger:
            self.logger.log(message_str, log_level)
