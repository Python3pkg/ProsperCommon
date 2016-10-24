'''wheel setup for Prosper common utilities'''

from os import path, listdir
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

def include_all_subfiles(path_included):
    '''for data_files {path_included}/*'''
    local_path = path.join(HERE, path_included)
    file_list = []

    for file in listdir(local_path):
        file_list.append(path_included + '/' + file)

    return file_list

def hack_find_packages(include_str):
    '''setuptools.find_packages({include_str}) does not work.  Adjust pathing'''
    new_list = [include_str]
    for element in find_packages(include_str):
        new_list.append(include_str + '.' + element)

    return new_list

setup(
    name='ProsperCommon',
    author='John Purcell',
    author_email='prospermarketshow@gmail.com',
    url='https://github.com/EVEprosper/ProsperCommon',
    download_url='https://github.com/EVEprosper/ProsperCommon/tarball/v0.2.1',
    version='0.2.1',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5'
    ],
    keywords='prosper eveonline api CREST',
    packages=hack_find_packages('prosper'),
    data_files=[
        #TODO: license + README
        #TODO
    ],
    package_data={
        'prosper':[
            'common/common_config.cfg'
        ]
    },
    install_requires=[
        'requests==2.11.1'
    ]
)
