'''wheel setup for Prosper common utilities'''

from os import path
from setuptools import setup, find_packages


HERE = path.abspath(path.dirname(__file__))

setup(
    name='ProsperCommon',
    version='0.0.4',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5'
    ],
    keywords='prosper eveonline api CREST',
    packages=find_packages(),
    package_data={
        #TODO
    },
    install_requires=[
        #TODO
    ]
)
