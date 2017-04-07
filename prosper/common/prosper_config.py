"""prosper_config.py

Unified config parsing and option picking against config objects

"""

from os import path, getenv
import configparser
from configparser import ExtendedInterpolation
import warnings
import logging

DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())

HERE = path.abspath(path.dirname(__file__))

class ProsperConfig(object):
    """configuration handler for all prosper projects

    Helps maintain global, local, and args values to pick according to priority

    1. args given at runtile
    2. <config_file>_local.cfg -- untracked config with #SECRETS
    3. <config_file>.cfg -- tracked 'master' config without #SECRETS
    4. environment varabile
    5. args_default -- function default w/o global config

    Attributes:
        global_config (:obj:`configparser.ConfigParser`)
        local_config (:obj:`configparser.ConfigParser`)
        config_filename (str): filename of global/tracked/default .cfg file
        local_config_filename (str): filename for local/custom .cfg file
    """
    _debug_mode = False
    def __init__(
            self,
            config_filename,
            local_filepath_override=None,
            logger=DEFAULT_LOGGER,
            debug_mode=_debug_mode
    ):
        """get the config filename for initializing data structures

        Args:
            config_filename (str): path to config
            local_filepath_override (str, optional): path to alternate private config file
            logger (:obj:`logging.Logger`, optional): capture messages to logger
            debug_mode (bool, optional): enable debug modes for config helper

        """
        self.logger = logger
        self.config_filename = config_filename
        self.local_config_filename = get_local_config_filepath(config_filename)
        if local_filepath_override:
            self.local_config_filename = local_filepath_override
            #TODO: force filepaths to abspaths?
        self.global_config, self.local_config = get_configs(
            config_filename,
            self.local_config_filename
        )

    def get(
            self,
            section_name,
            key_name
    ):
        """Replicate configparser.get() functionality

        Args:
            section_name (str): section name in config
            key_name (str): key name in config.section_name

        Returns:
            (str): do not check defaults, only return local value

        """
        value = None
        try:
            value = self.local_config.get(section_name, key_name)
        except Exception as error_msg:
            self.logger.warning(
                '{0}.{1} not found in local config'.format(section_name, key_name)
            )
            try:
                value = self.global_config.get(section_name, key_name)
            except Exception as error_msg:
                self.logger.error(
                    '{0}.{1} not found in global config'.format(section_name, key_name)
                )
                raise KeyError('Could not find option in local/global config')

        return value

    def get_option(
            self,
            section_name,
            key_name,
            args_option=None,
            args_default=None
    ):
        """evaluates the requested option and returns the correct value

        Notes:
            Priority order
            1. args given at runtile
            2. <config_file>_local.cfg -- untracked config with #SECRETS
            3. <config_file>.cfg -- tracked 'master' config without #SECRETS
            4. environment varabile
            5. args_default -- function default w/o global config

        Args:
            section_name (str): section level name in config
            key_name (str): key name for option in config
            args_option (any): arg option given by a function
            args_default (any): arg default given by a function

        Returns:
            (str) appropriate response as per priority order

        """
        self.logger.debug('picking config')
        if args_option != args_default and\
           args_option is not None:
            self.logger.debug('-- using function args')
            return args_option

        section_info = section_name + '.' + key_name

        local_option = None
        try:
            local_option = self.local_config[section_name][key_name]
        except KeyError:
            self.logger.debug(section_info + 'not found in local config')
        if local_option:
            self.logger.debug('-- using local config')
            return local_option

        global_option = None
        try:
            global_option = self.global_config[section_name][key_name]
        except KeyError:# as error_msg:
            self.logger.warning(section_info + 'not found in global config')
        if global_option:
            self.logger.debug('-- using global config')
            return global_option

        env_option = get_value_from_environment(section_name, key_name, logger=self.logger)
        if env_option:
            self.logger.debug('-- using environment value')
            return env_option
        self.logger.debug('-- using default argument')
        return args_default #If all esle fails return the given default

    def attach_logger(self, logger):
        """because load orders might be weird, add logger later"""
        self.logger = logger

ENVNAME_PAD = 'PROSPER'
def get_value_from_environment(
        section_name,
        key_name,
        envname_pad=ENVNAME_PAD,
        logger=DEFAULT_LOGGER
):
    """check environment for key/value pair

    Args:
        section_name (str): section name
        key_name (str): key to look up
        envname_pad (str, optional): namespace padding
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (str) value in environment

    """
    var_name = '{pad}_{section}__{key}'.format(
        pad=envname_pad,
        section=section_name,
        key=key_name
    )

    logger.debug('var_name={0}'.format(var_name))
    value = getenv(var_name)
    logger.debug('env value={0}'.format(value))

    return value

def get_configs(
        config_filepath,
        local_filepath_override=None,
        debug_mode=False
):
    """go and fetch the global/local configs from file and load them with configparser

    Args:
        config_filename (str): path to config
        debug_mode (bool, optional): enable debug modes for config helper

    Returns:
        (:obj:`configparser.ConfigParser`) global_config
        (:obj:`configparser.ConfigParser`) local_config

    """
    global_config = read_config(config_filepath)

    local_filepath = get_local_config_filepath(config_filepath, True)
    if local_filepath_override:
        local_filepath = local_filepath_override
    local_config = read_config(local_filepath)

    return global_config, local_config

def read_config(
        config_filepath,
        logger=DEFAULT_LOGGER
):
    """fetch and parse config file

    Args:
        config_filepath (str): path to config file.  abspath > relpath
        logger (:obj:`logging.Logger`, optional): logger to catch error msgs

    """
    config_parser = configparser.ConfigParser(
        interpolation=ExtendedInterpolation(),
        allow_no_value=True,
        delimiters=('='),
        inline_comment_prefixes=('#')
    )
    logger.debug('config_filepath={0}'.format(config_filepath))
    try:
        with open(config_filepath, 'r') as filehandle:
            config_parser.read_file(filehandle)
    except Exception as error_msg:
        logger.error(
            'EXCEPTION - Unable to parse config file' +
            '\r\texception={0}'.format(error_msg) +
            '\r\tconfig_filepath{0}'.format(config_filepath)
        )
        raise error_msg

    return config_parser

def get_config(
        config_filepath,
        local_override=False
):
    """DEPRECATED: classic v1 config parser.  Obsolete by v0.3.0"""
    warnings.warn(
        __name__ + 'replaced with ProsperConfig',
        DeprecationWarning
    )
    config = configparser.ConfigParser(
        interpolation=ExtendedInterpolation(),
        allow_no_value=True,
        delimiters=('='),
        inline_comment_prefixes=('#')
    )

    real_config_filepath = get_local_config_filepath(config_filepath)

    if local_override:  #force lookup tracked config
        real_config_filepath = config_filepath

    with open(real_config_filepath, 'r') as filehandle:
        config.read_file(filehandle)
    return config

def get_local_config_filepath(
        config_filepath,
        force_local=False
):
    """helper for finding local filepath for config

    Args:
        config_filepath (str): path to local config abspath > relpath
        force_local (bool, optional): force return of _local.cfg version

    Returns:
        (str): Path to local config, or global if path DNE

    """
    local_config_filepath = config_filepath.replace('.cfg', '_local.cfg')

    real_config_filepath = ''
    if path.isfile(local_config_filepath) or force_local:
        #if _local.cfg version exists, use it instead
        real_config_filepath = local_config_filepath
    else:
        #else use tracked default
        real_config_filepath = config_filepath

    return real_config_filepath
