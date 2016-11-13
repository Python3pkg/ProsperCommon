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

TEST_GLOBAL_CONFIG_PATH = path.join(HERE, 'test_config_global.cfg')
TEST_LOCAL_CONFIG_PATH = path.join(HERE, 'test_config_local.cfg')
def test_priority_order():
    """Makes sure desired priority order is followed

        1. override_value
        2. local_config option
        3. global_config option
        4. default_value

    """
    TestConfigObj = prosper_config.ProsperConfig(
        TEST_GLOBAL_CONFIG_PATH,
        local_filepath_override=TEST_LOCAL_CONFIG_PATH
    )

    ## Test #1 priority:
    assert TestConfigObj.get_option('TEST', 'key2', 999, None) == 999

    ## Test #2 priority
    assert TestConfigObj.get_option('TEST', 'key2', None, None) == str(100)

    ## Test #3 priority
    assert TestConfigObj.get_option('TEST', 'key3', None, None) == 'stuff'

    ## Test #4 priority
    assert TestConfigObj.get_option('TEST', 'nokey', 111, 111) == 111

def test_local_filepath_helper():
    """test helper function for fetching local configs"""
    expected_local_filepath = TEST_LOCAL_CONFIG_PATH.replace('.cfg', '_local.cfg')

    assert prosper_config.get_local_config_filepath(TEST_LOCAL_CONFIG_PATH) == TEST_LOCAL_CONFIG_PATH

    assert prosper_config.get_local_config_filepath(TEST_LOCAL_CONFIG_PATH, True) == expected_local_filepath
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
