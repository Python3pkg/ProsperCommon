'''utilities.py: worker functions for CREST calls'''

from os import path
import logging
from socket import gethostname, gethostbyname
import smtplib
from datetime import datetime
import time

from prosper.common.prosper_config import get_config, get_local_config_filepath

DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())

def compare_config_files(config_filepath):
    '''validate that keys in tracked .cfg match keys in _local.cfg'''
    tracked_config = get_config(config_filepath, True)
    local_config = get_config(config_filepath)

    unique_values = {}

    if not path.isfile(get_local_config_filepath(config_filepath)):
        #pytest.skip('no local .cfg found, skipping')
        return None

    local_unique_sections, local_unique_keys = find_unique_keys(
        local_config,
        tracked_config,
        'local'
    )
    tracked_unique_sections, tracked_unique_keys = find_unique_keys(
        tracked_config,
        local_config,
        'tracked'
    )

    if any([
            local_unique_keys,
            tracked_unique_keys
    ]):
        unique_values['unique_keys'] = {}
        unique_values['unique_keys']['local'] = local_unique_keys
        unique_values['unique_keys']['tracked'] = tracked_unique_keys
    if any([
            local_unique_sections,
            tracked_unique_sections
    ]):
        unique_values['unique_sections'] = [local_unique_sections, tracked_unique_sections]

    return unique_values

def find_unique_keys(base_config, comp_config, base_name):
    '''walks through BASE and looks for keys missing in COMP
        returns: unique_sections:list, unique_keys:list'''
    unique_keys = []
    unique_sections = []

    for section in base_config:
        if str(section) == 'DEFAULT':
            continue #.cfg has DEFAULT key, we do not use
        if not comp_config.has_section(section):
            unique_label = base_name + '.' + str(section)
            unique_sections.append(unique_label)
            continue

        for key in base_config[section]:
            if not comp_config.has_option(section, key):
                unique_label = str(section) + '.' + str(key)
                unique_keys.append(unique_label)
                continue
            #TODO: compare values?
    return unique_sections, unique_keys

def parse_options(config_obj, key):
    '''test/parse logging options from config
    RETURNS: dict() of everything at key
    '''
    if not config_obj.has_section(key):
        raise KeyError

    logging_options = {}
    for option in config_obj[key]:
        option_str = str(option)
        logging_options[option_str] = config_obj.get(key, option_str)

    return logging_options

class Timeit(object):
    '''decorator for timing funcs
    http://www.artima.com/weblogs/viewpost.jsp?thread=240845'''
    def __init__(self, logger=DEFAULT_LOGGER):
        self.logger=logger

    def __call__(self, func):
        def wrapped(*args, **kw):
            '''stolen from: http://www.samuelbosch.com/2012/02/timing-functions-in-python.html'''
            ts = time.time()
            result = func(*args, **kw)
            te = time.time()

            self.logger.debug('-- %r %2.2f sec' % (func.__name__, te-ts))
            return result
        return wrapped

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
