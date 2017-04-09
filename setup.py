"""wheel setup for Prosper common utilities"""

from os import path, listdir
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from codecs import open

HERE = path.abspath(path.dirname(__file__))
__version__ = '1.0.1'
__project_name__ = 'common'

def hack_find_packages(include_str):
    """patches setuptools.find_packages issue

    setuptools.find_packages(path='') doesn't work as intended

    Returns:
        (:obj:`list` :obj:`str`) append <include_str>. onto every element of setuptools.find_pacakges() call

    """
    new_list = [include_str]
    for element in find_packages(include_str):
        new_list.append(include_str + '.' + element)

    return new_list

def include_all_subfiles(*args):
    """Slurps up all files in a directory (non recursive) for data_files section

    Note:
        Not recursive, only includes flat files

    Returns:
        (:obj:`list` :obj:`str`) list of all non-directories in a file

    """
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
    """PyTest cmdclass hook for test-at-buildtime functionality

    http://doc.pytest.org/en/latest/goodpractices.html#manual-integration

    """
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = [
            'tests',
            '--cov=prosper/' + __project_name__,
            '--cov-report=term-missing'
        ]    #load defaults here

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

with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()

setup(
    name='ProsperCommon',
    description='Common Utilities for EVEProsper Projects',
    version=__version__,
    long_description=readme,
    author='John Purcell',
    author_email='prospermarketshow@gmail.com',
    url='https://github.com/EVEprosper/ProsperCommon',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5'
    ],
    keywords='prosper eve-online webhooks logging configuration-management',
    packages=hack_find_packages('prosper'),
    include_package_data=True,
    package_data={
        '': ['LICENSE', 'README.rst'],
        'prosper':[
            'common/common_config.cfg'
        ]
    },
    install_requires=[
        'requests>=2.12.0'
    ],
    tests_require=[
        'pytest>=3.0.0',
        'testfixtures>=4.12.0',
        'pytest_cov>=2.4.0',
        'mock>=2.0.0'
    ],
    cmdclass={
        'test':PyTest
    }
)
