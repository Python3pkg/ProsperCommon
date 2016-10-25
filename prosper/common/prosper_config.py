'''prosper_config.py standardized configparser for prosper'''

from os import path
import configparser
from configparser import ExtendedInterpolation

HERE = path.abspath(path.dirname(__file__))

def get_config(
        config_filepath,
        local_override=False
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
    if path.isfile(local_config_filepath):
        #if _local.cfg version exists, use it instead
        real_config_filepath = local_config_filepath
    else:
        #else use tracked default
        real_config_filepath = config_filepath

    if local_override:  #force lookup tracked config
        real_config_filepath = config_filepath

    with open(real_config_filepath, 'r') as filehandle:
        config.read_file(filehandle)
    return config
