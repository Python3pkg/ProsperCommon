'''config_test.py: test prosper_config functionality'''
from os import path
import json
import pytest

import prosper.common.prosper_config as prosper_config
import prosper.common.prosper_utilities as prosper_utilities

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)
LOCAL_CONFIG_PATH = path.join(
    ROOT,
    'prosper',
    'common',
    'common_config.cfg'
)


TEST_LOCAL_CONFIG_PATH = path.join(HERE, 'test_config_local.cfg')
TEST_LOCAL_CONFIG = prosper_config.read_config(TEST_LOCAL_CONFIG_PATH)

TEST_GLOBAL_CONFIG_PATH = path.join(HERE, 'test_config_global.cfg')
TEST_GLOBAL_CONFIG = prosper_config.read_config(TEST_GLOBAL_CONFIG_PATH)

TEST_BAD_CONFIG_PATH = path.join(HERE, 'bad_config.cfg')
TEST_BAD_PATH = path.join(HERE, 'no_file_here.cfg')
def test_bad_config():
    """failing test: bad parsing"""
    test_config = prosper_config.read_config(TEST_BAD_CONFIG_PATH)

    ## Test keys with bad delimters
    with pytest.raises(KeyError):
        test_config['TEST']['key3']
        test_config['FAILS']['shared_key']

    ## Assert good keys are working as expected
    good_val = test_config['TEST']['key1']
    assert good_val == 'vals'

    ## Test behavior with bad filepath
    with pytest.raises(FileNotFoundError):
        bad_config = prosper_config.read_config(TEST_BAD_PATH)

def test_config_file():
    """Test makes sure tracked/local configs have all matching keys"""
    unique_values = prosper_utilities.compare_config_files(LOCAL_CONFIG_PATH)

    message = ''
    if unique_values:
        message = json.dumps(
            unique_values,
            sort_keys=True,
            indent=4
        )

    if message:
        assert False, message #FIXME: this seems wrong

if __name__ == '__main__':
    print(test_config_file())
