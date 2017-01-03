#!/usr/bin/env python
###############################################################################

import falcon
import json as JSON
import os
import requests

from datetime import datetime as dt
from requests.utils import urlparse

###############################################################################
###############################################################################

DEBUG = os.environ.get('DEBUG', 'false').lower().capitalize()
assert DEBUG in ['False', '0', 'True', '1']
DEBUG = bool(eval(DEBUG))
assert DEBUG in [False, True]

##############################################################################
##############################################################################

class DateTime:

    def on_get(self, req, res):

        res.body = JSON.dumps({'now': str(dt.now())})
        res.content_type = 'application/json'
        res.status = falcon.HTTP_200

##############################################################################

DATETIME_PATH = os.environ.get('DATETIME_PATH', '/now')
assert DATETIME_PATH

###############################################################################
###############################################################################

class Gateway:

    def __init__(self):

        self.req_template = 'POST {ACCESS_TOKEN_URI} ' \
           'client_id="{CLIENT_ID}" client_secret="{CLIENT_SECRET}" ' \
           'code="{CODE}" grant_type="{GRANT_TYPE}" ' \
           'redirect_uri="{REDIRECT_URI}"'

        self.req_template = self.req_template.format(
            ACCESS_TOKEN_URI=ACCESS_TOKEN_URI,
            CLIENT_ID=CLIENT_ID,
            CLIENT_SECRET=CLIENT_SECRET,
            CODE='{CODE}',
            GRANT_TYPE=GRANT_TYPE,
            REDIRECT_URI=REDIRECT_URI
        )

        ##
        ## TODO: replace with external service like memcached or redis!
        ##

        self.CACHE = {}

    def on_get(self, req, res):

        state = req.get_param('state')
        if state is None:
            raise falcon.HTTPInvalidParam(
                param_name='state', msg='Should be a random string.')

        res_cached = self.CACHE.get(state)
        if res_cached is not None:
            res.body = res_cached['body']
            res.content_type = res_cached['content_type']
            res.status = res_cached['status']
            res.set_header('X-Code', res_cached['X-Code'])
            res.set_header('X-State', res_cached['X-State'])
            return

        code = req.get_param('code')
        if code is None:
            raise falcon.HTTPInvalidParam(
                param_name='code', msg='Should be a string.')

        if DEBUG:
            print(self.req_template.format(CODE=code))

        result = requests.post(ACCESS_TOKEN_URI, {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'grant_type': GRANT_TYPE,
            'redirect_uri': REDIRECT_URI
        })

        res.body = result.text
        res.content_type = result.headers['content-type']
        res.status = '{0} {1}'.format(result.status_code, result.reason)
        res.set_header('X-Code', code)
        res.set_header('X-State', state)

        if result.status_code == requests.codes.ok:

            self.CACHE[state] = {
                'body': res.body,
                'content_type': res.content_type,
                'status': res.status,
                'X-Code': code,
                'X-State': state
            }

###############################################################################

CLIENT_ID = os.environ.get('CLIENT_ID')
assert CLIENT_ID
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
assert CLIENT_SECRET
ACCESS_TOKEN_URI = os.environ.get('ACCESS_TOKEN_URI')
assert ACCESS_TOKEN_URI
GRANT_TYPE = os.environ.get('GRANT_TYPE', 'authorization_code')
assert GRANT_TYPE
REDIRECT_URI = os.environ.get('REDIRECT_URI')
assert REDIRECT_URI
REDIRECT_PATH = urlparse(REDIRECT_URI).path
assert REDIRECT_PATH

###############################################################################
###############################################################################

app = application = falcon.API()
app.add_route(DATETIME_PATH, DateTime())
app.add_route(REDIRECT_PATH, Gateway())

###############################################################################
###############################################################################
