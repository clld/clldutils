# -*- coding: utf-8 -*-
import sys
from setuptools import setup, find_packages


requires = [
    'six',
    'python-dateutil',
    'configparser>=3.5.0b2',
    'tabulate>=0.7.7',
    'colorlog',
    'attrs>=17.1.0',
    'uritemplate>=3.0.0',
]

if sys.version_info.major == 2:
    requires.append('pathlib2')


def read(fname):
    with open(fname) as fp:
        return fp.read()


setup(
    name='clldutils',
    version="1.12.0",
    description='Utilities for clld apps',
    long_description=read("README.rst"),
    author='Robert Forkel',
    author_email='forkel@shh.mpg.de',
    url='https://github.com/clld/clldutils',
    install_requires=requires,
    license="Apache 2.0",
    zip_safe=False,
    keywords='',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    packages=find_packages(),
    tests_require=[
        'nose',
        'coverage',
        'mock>=2.0',
    ],
)
