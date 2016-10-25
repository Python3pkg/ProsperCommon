'''utilities.py: worker functions for CREST calls'''

import os
import logging
from configparser import ExtendedInterpolation
from socket import gethostname, gethostbyname
import smtplib
from datetime import datetime

DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())

def send_email(
        mail_subject,
        error_msg,
        config_object,
        logger=DEFAULT_LOGGER
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
            logger.info(
                'Sent Email from {source} to {recipients} about {mail_subject}'.\
                format(
                    source=email_source,
                    recipients=email_recipients,
                    mail_subject=mail_subject
                ))
        except Exception as exe_msg:
            logger.critical(
                'EXCEPTION unable to send email ' + \
                '\r\texception={0} '.format(exe_msg) + \
                '\r\temail_source={0} '.format(email_source) + \
                '\r\temail_recipients={0} '.format(email_recipients) + \
                '\r\temail_username={0} '.format(email_username) + \
                '\r\temail_secret=SECRET ' + \
                '\r\temail_server={0} '.format(email_server) + \
                '\r\temail_port={0} '.format(email_port)
            )
    else:
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
