# -*- coding: utf-8 -*-
import sys
from setuptools import setup, find_packages

py_version = sys.version_info[:2]

PY3 = py_version[0] == 3

if PY3:
    if py_version < (3, 4):
        raise RuntimeError('clldutils requires Python 3.4 or better')
else:
    if py_version < (2, 7):
        raise RuntimeError('clldutils requires Python 2.7 or better')


requires = [
    'six',
    'python-dateutil',
    'configparser>=3.5.0b2',
]

if not PY3:
    requires.append('pathlib2')

setup(
    name='clldutils',
    version="0.9.0",
    description='Utilities for clld apps',
    long_description="",
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
    tests_require=['nose', 'coverage', 'mock==1.0'],
)
