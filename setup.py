#!/usr/bin/env python
###############################################################################

from setuptools import setup

###############################################################################
###############################################################################

setup(
    author='Hasan Karahan',
    author_email='hasan.karahan@blackhan.com',
    description='OAuth2 gateway',
    install_requires=[
        'falcon>=1.1.0',
        'gunicorn>=19.6.0',
        'pytest>=3.0.5',
        'requests>=2.12.4',
    ],
    name='oauth2-gateway',
    url='https://github.org/hsk81/oauth2-gateway',
    version='1.0.0',
)

###############################################################################
###############################################################################
