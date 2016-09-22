'''utilities.py: worker functions for CREST calls'''

import os
import logging
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
import configparser
from configparser import ExtendedInterpolation
from socket import gethostname, gethostbyname
import smtplib
from datetime import datetime

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
        delimiters=('='),
        inline_comment_prefixes=('#')
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
        log_name,
        log_path,
        configObject = None,
        log_level_override = ''
):
    '''creates logging handle for programs'''
    if not configObject:
        #build up mini-config off in-script defaults
        tmpconfig = configparser.ConfigParser()
        tmpconfig['LOGGING'] = LOGGER_DEFAULTS
        configObject = tmpconfig

    if not os.path.exists(log_path):
        os.makedirs(log_path)
    #logFolder = os.path.join('../', tmpConfig.get('LOGGING', 'logFolder'))
    #if not os.path.exists(logFolder):
    #    os.makedirs(logFolder)

    Logger = logging.getLogger(log_name)

    log_level = configObject.get('LOGGING', 'log_level')
    log_freq  = configObject.get('LOGGING', 'log_freq')
    log_total = configObject.get('LOGGING', 'log_total')

    log_name = log_name + '.log'
    log_format = '[%(asctime)s;%(levelname)s;%(filename)s;%(lineno)s] %(message)s'
    #print(logName + ':' + logLevel)
    if log_level_override:
        log_level = log_level_override

    log_full_path = os.path.join(log_path, log_name)

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

    return Logger

def send_email(
        mail_subject,
        error_msg,
        config_object,
        logger=None
):
    '''in case of catastrophic failure, raise the alarm'''
    email_source     = config_object.get('LOGGING', 'email_source')
    email_recipients = config_object.get('LOGGING', 'email_recipients')
    email_username   = config_object.get('LOGGING', 'email_username')
    #email_fromaddr   = config_object.get('LOGGING', 'email_fromaddr')
    email_secret     = config_object.get('LOGGING', 'email_secret')
    email_server     = config_object.get('LOGGING', 'email_server')
    email_port       = config_object.get('LOGGING', 'email_port')

    bool_do_email = all([   #only do mail if all values are set
        email_source.strip(),
        email_recipients.strip(),
        email_username.strip(),
        #email_fromaddr.strip(),
        email_secret.strip(),
        email_server.strip(),
        email_port.strip()
    ])

    if bool_do_email:
        subject = 'Prosper Error: ' + mail_subject
        body = '''{error_msg}

        alert time: {host_time}
        raised by: {host_name}
        location: {host_ip}'''.\
            format(
                error_msg=error_msg,
                host_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                host_name=str(gethostname()),
                host_ip=str(gethostbyname(gethostname()))
            )
        payload = '''From: {source}\nTo: {recipients}\nSubject: {subject}\n\n{body}'''.\
            format(
                source=email_source,
                recipients=email_recipients,
                subject=subject,
                body=body
            )
        try:
            mailserver = smtplib.SMTP(email_server, int(email_port))
            mailserver.ehlo()
            mailserver.starttls()
            mailserver.login(email_username, email_secret)
            mailserver.sendmail(
                email_source,
                email_recipients.split(','),
                payload
            )
            mailserver.close()
            if logger:
                logger.info(
                    'Sent Email from {source} to {recipients} about {mail_subject}'.\
                    format(
                        source=email_source,
                        recipients=email_recipients,
                        mail_subject=mail_subject
                    ))
        except Exception as error_msg:
            error_str = '''EXCEPTION unable to send email
        exception={exception}
        email_source={email_source}
        email_recipients={email_recipients}
        email_username={email_username}
        email_secret=SECRET
        email_server={email_server}
        email_port={email_port}'''.\
                format(
                    exception=str(error_msg),
                    email_source=email_source,
                    email_recipients=email_recipients,
                    email_username=email_username,
                    email_server=email_server,
                    email_port=email_port
                )
            if logger:
                logger.critical(error_str)
    else:
        if logger:
            logger.error('unable to send email - missing config information')

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


def email_body_builder(error_msg, help_msg):
    '''Builds email message for easier reading with SMTPHandler'''
    #todo: format emails better
    return error_msg + '\n' + help_msg

def quandlfy_json(jsonObj):
    '''turn object from JSON into QUANDL-style JSON'''
    pass

def quandlfy_xml(xmlObj):
    '''turn object from XML into QUANDL-style XML'''
    pass

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

class LoggerDebugger(object):
    '''container for executing print/debug/log calls'''
    def __init__(self, debug, logger):
        self.debug = debug,
        self.logger = logger
        self.do_debug = bool(debug)
        self.do_logger = bool(logger)

    def get_logger(self):
        return self.logger

    def message(self, message_str, log_level):
        '''actually do the thing'''
        log_level_enum = LoggerLevels().str_to_level(log_level)
        if self.do_debug:
            print(message_str)
        if self.do_logger:
            self.logger.log(log_level_enum, message_str)
