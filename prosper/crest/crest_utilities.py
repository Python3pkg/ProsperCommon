from datetime import datetime
from os import path

import requests
from tinyDB import TinyDB, Query

from prosper.common.prosper_logging import create_logger
from prosper.common.prosper_config import get_config

HERE = path.abspath(path.dirname(__file__))
CONFIG_ABSPATH = path.join(HERE, 'crest_config.cfg')

if __name__ == '__main__':
    pass
