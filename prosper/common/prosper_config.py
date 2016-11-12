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
        global_cache (:obj:`dict`) volatile stash of read configs
        local_cache (:obj:`dict`) volatile stash of read configs

    """
    _debug_mode = False
    def __init__(
            self,
            config_filename,
            logger=DEFAULT_LOGGER,
            debug_mode=_debug_mode
    ):
        """get the config filename for initializing data structures

        Args:
            config_filename (str): path to config
            logger (:obj:`logging.Logger`, optional): capture messages to logger
            debug_mode (bool, optional): enable debug modes for config helper

        """
        pass

def get_configs(
        config_filepath,
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
    pass

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
