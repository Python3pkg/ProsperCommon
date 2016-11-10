'''wheel setup for Prosper common utilities'''

from os import path, listdir
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

HERE = path.abspath(path.dirname(__file__))

def hack_find_packages(include_str):
    '''append include_str into find_packages path'''
    # Some issue with find_packages() and directory design?
    new_list = [include_str]
    for element in find_packages(include_str):
        new_list.append(include_str + '.' + element)

    return new_list

def include_all_subfiles(*args):
    '''makes up for /* include'''
    file_list = []
    for path_included in args:
        local_path = path.join(HERE, path_included)

        for file in listdir(local_path):
            file_abspath = path.join(local_path, file)
            if path.isdir(file_abspath):    #do not include sub folders
                continue
            file_list.append(path_included + '/' + file)

    return file_list

class PyTest(TestCommand):
    '''PyTest cmdclass hook for test-at-buildtime functionality
    http://doc.pytest.org/en/latest/goodpractices.html#manual-integration'''
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ['test']    #load defaults here

    def run_tests(self):
        import shlex
        #import here, cause outside the eggs aren't loaded
        import pytest
        pytest_commands = []
        try:    #read commandline
            pytest_commands = shlex.split(self.pytest_args)
        except AttributeError:  #use defaults
            pytest_commands = self.pytest_args
        errno = pytest.main(pytest_commands)
        exit(errno)

setup(
    name='ProsperCommon',
    author='John Purcell',
    author_email='prospermarketshow@gmail.com',
    url='https://github.com/EVEprosper/ProsperCommon',
    download_url='https://github.com/EVEprosper/ProsperCommon/tarball/v0.2.1',
    version='0.3.0',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5'
    ],
    keywords='prosper eveonline api CREST',
    packages=hack_find_packages('prosper'),
    data_files=[
        #TODO: license + README
        ('test', include_all_subfiles('test'))
    ],
    package_data={
        'prosper':[
            'common/common_config.cfg',
            'crest/crest_config.cfg'
        ]
    },
    install_requires=[
        'requests==2.11.1',
        'pytest==3.0.3',
        'testfixtures==4.12.0',
        #TODO: pandas/numpy/matplotlib requirements
    ],
    cmdclass={
        'test':PyTest
    }
)
