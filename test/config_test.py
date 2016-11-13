'''config_test.py: test prosper_config functionality'''
from os import path
import json
import pytest

import prosper.common.prosper_config as prosper_config
import prosper.common.prosper_utilities as prosper_utilities

HERE = path.abspath(path.dirname(__file__))
LOCAL_CONFIG = path.join(HERE, 'common_config.cfg') #use /test config
if not path.isfile(LOCAL_CONFIG):   #else use /prosper/common config
    DEFAULT_PATH = path.join(path.dirname(HERE), 'prosper', 'common')
    LOCAL_CONFIG = path.join(DEFAULT_PATH, 'common_config.cfg')

TEST_LOCAL_CONFIG_PATH = path.join(HERE, 'test_config_local.cfg')
TEST_LOCAL_CONFIG = prosper_utilities.read_config(TEST_LOCAL_CONFIG_PATH)

TEST_GLOBAL_CONFIG_PATH = path.join(HERE, 'test_config_global.cfg')
TEST_GLOBAL_CONFIG = prosper_utilities.read_config(TEST_GLOBAL_CONFIG_PATH)

def test_config_file():
    '''make sure local/tracked config files mesh'''
    unique_values = prosper_utilities.compare_config_files(LOCAL_CONFIG)

    #if local_debug:
    #    return unique_values
    message = ''
    if unique_values:
        message = json.dumps(
            unique_values,
            sort_keys=True,
            indent=4
        )

    if message:
        assert False, message

if __name__ == '__main__':
    print(test_config_file())
