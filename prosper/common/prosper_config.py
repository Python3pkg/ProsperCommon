"""prosper_config.py

Unified config parsing and option picking against config objects

"""

from os import path
import configparser
from configparser import ExtendedInterpolation
import warnings
import logging

HERE = path.abspath(path.dirname(__file__))

DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())

class ProsperConfig(object):
    """configuration handler for all prosper projects

    Helps maintain global, local, and args values to pick according to priority

    1. args given at runtile
    2. <config_file>_local.cfg -- untracked config with #SECRETS
    3. <config_file>.cfg -- tracked 'master' config without #SECRETS

    Attributes:
        global_config (:obj:`configparser.ConfigParser`)
        local_config (:obj:`configparser.ConfigParser`)

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
        self.config_filename = config_filename
        self.global_config, self.local_config = get_configs(
            config_filename,
            local_filepath_override
        )

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

        Args:
            section_name (str): section level name in config
            key_name (str): key name for option in config
            args_option (any): arg option given by a function
            args_default (any): arg default given by a function

        Returns:
            (str) appropriate response as per priority order

        """
        pass

def get_configs(
        config_filepath,
        local_filepath_override=None,
        logger=DEFAULT_LOGGER,
        debug_mode=False
):
    """go and fetch the global/local configs from file and load them with configparser

    Args:
        config_filename (str): path to config
        logger (:obj:`logging.Logger`, optional): capture messages to logger
        debug_mode (bool, optional): enable debug modes for config helper

    Returns:
        (:obj:`configparser.ConfigParser`) global_config
        (:obj:`configparser.ConfigParser`) local_config

    """
    global_config = configparser.ConfigParser(
        interpolation=ExtendedInterpolation(),
        allow_no_value=True,
        delimiters=('='),
        inline_comment_prefixes=('#')
    )
    try:
        with open(config_filepath, 'r') as filehandle:
            global_config.read_file(filehandle)
    except Exception as error_msg:
        raise error_msg

    local_config = configparser.ConfigParser(
        interpolation=ExtendedInterpolation(),
        allow_no_value=True,
        delimiters=('='),
        inline_comment_prefixes=('#')
    )

    local_filepath = config_filepath.replace('.cfg', '_local.cfg')
    if local_filepath_override:
        local_filepath = local_filepath_override

    try:
        with open(local_filepath, 'r') as filehandle:
            local_config.read_file(filehandle)
    except IOError as error_msg:
        warnings.warn('No ' + local_filepath + ' found in path')
        local_config = None
    except Exception as error_msg:
        raise error_msg

    return global_config, local_config

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

def get_local_config_filepath(config_filepath, force_local=False):
    '''logic to find filepath of _local.cfg'''
    local_config_filepath = config_filepath.replace('.cfg', '_local.cfg')

    real_config_filepath = ''
    if path.isfile(local_config_filepath) or force_local:
        #if _local.cfg version exists, use it instead
        real_config_filepath = local_config_filepath
    else:
        #else use tracked default
        real_config_filepath = config_filepath

    return real_config_filepath
