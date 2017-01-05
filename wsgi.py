#!/usr/bin/env python
###############################################################################

import falcon
import json as JSON
import os
import redis
import requests

from datetime import datetime as dt
from requests.utils import urlparse

###############################################################################
###############################################################################

HTML = """
<html>
    <head>
        <style>
            html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                width: 100%;
            }
            div.table {
                display: table;
                height: 100%;
                text-align: center;
                width: 100%;
            }
            div.table div.table-cell {
                display: table-cell;
                height: 100%;
                vertical-align: middle;
                width: 100%;
            }
            p {
                font-family: monospace;
                font-size: larger;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="table">
            <div class="table-cell">
                {content}
            </div>
        </div>
    </body>
</html>
"""

HTML_FAILURE = os.environ.get(
    'LOGIN_FAILURE', HTML.replace('{content}', '<p>login failure</p>'))
assert HTML_FAILURE

HTML_SUCCESS = os.environ.get(
    'LOGIN_SUCCESS', HTML.replace('{content}', '<p>login success</p>'))
assert HTML_SUCCESS

###############################################################################
###############################################################################

ACCESS_TOKEN_URI = os.environ.get('ACCESS_TOKEN_URI')
assert ACCESS_TOKEN_URI
CLIENT_ID = os.environ.get('CLIENT_ID')
assert CLIENT_ID
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
assert CLIENT_SECRET
DATETIME_PATH = os.environ.get('DATETIME_PATH', '/now')
assert DATETIME_PATH
DEBUG = os.environ.get('DEBUG', 'false').lower().capitalize()
assert DEBUG in ['False', '0', 'True', '1']
DEBUG = bool(eval(DEBUG))
assert DEBUG in [False, True]
GRANT_TYPE = os.environ.get('GRANT_TYPE', 'authorization_code')
assert GRANT_TYPE
REDIRECT_URI = os.environ.get('REDIRECT_URI')
assert REDIRECT_URI
REDIRECT_PATH = urlparse(REDIRECT_URI).path
assert REDIRECT_PATH
REDIS_EXPIRATION = int(os.environ.get('REDIS_EXPIRATION', '60'))
assert REDIS_EXPIRATION
REDIS_URL = os.environ.get('REDIS_URL')
assert REDIS_URL

##############################################################################
##############################################################################

class DateTime:

    def on_get(self, req, res):

        res.body = JSON.dumps({'now': str(dt.now())})
        res.content_type = 'application/json'
        res.status = falcon.HTTP_200

###############################################################################
###############################################################################

class Gateway:

    def __init__(self):

        self.req_template = 'POST {access_token_uri} ' \
           'client_id="{client_id}" client_secret="{client_secret}" ' \
           'code="{code}" grant_type="{grant_type}" ' \
           'redirect_uri="{redirect_uri}"'

        self.req_template = self.req_template.format(
            access_token_uri=ACCESS_TOKEN_URI,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            code='{code}',
            grant_type=GRANT_TYPE,
            redirect_uri=REDIRECT_URI
        )

        self.cache = redis.from_url(REDIS_URL)

    def on_get(self, req, res):

        state = req.get_param('state')
        if state is None:
            raise falcon.HTTPInvalidParam(
                param_name='state', msg='It should be a random challenge.')

        error = req.get_param('error')
        if error is not None:
            self.cache.set(state, JSON.dumps({
                'body': JSON.dumps({
                    'error-description': req.get_param('error_description'),
                    'error': req.get_param('error')
                }),
                'content-type': 'application/json; charset=utf-8',
                'status': falcon.HTTP_403
            }), ex=REDIS_EXPIRATION)

            return self.fromJson(res, JSON.dumps({
                'body': HTML_FAILURE,
                'content-type': 'text/html',
                'status': falcon.HTTP_403
            }), **{
                'x-code': None, 'x-state': state,
            })

        res_json = self.cache.get(state)
        if res_json is not None:
            return self.fromJson(res, res_json.decode('utf-8'), **{
                'x-code': True, 'x-state': True,
            })

        code = req.get_param('code')
        if code is None:
            raise falcon.HTTPInvalidParam(
                param_name='code', msg='It should be an authorization string.')

        if DEBUG:
            print(self.req_template.format(code=code))

        response = requests.post(ACCESS_TOKEN_URI, {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'grant_type': GRANT_TYPE,
            'redirect_uri': REDIRECT_URI
        })

        res = self.toFalcon(res, response, **{
            'x-code': code, 'x-state': state,
        })

        self.cache.set(state, self.toJson(res, **{
            'x-code': code, 'x-state': state,
        }), ex=REDIS_EXPIRATION)

        self.toFalconHtml(res, response, **{
            'x-code': code, 'x-state': state,
        })

    def toFalconHtml(self, res, response, **kwargs):

        res.status = '{0} {1}'.format(response.status_code, response.reason)
        res.content_type = 'text/html'

        try:
            response.raise_for_status()
        except requests.HTTPError:
            res.body = HTML_FAILURE
        else:
            res.body = HTML_SUCCESS

        for k, v in kwargs.items():
            if v is not None:
                res.set_header(k, v)

        return res

    def toFalcon(self, res, response, **kwargs):
        """
        Converts a Requests response to a Falcon response.
        """
        res.status = '{0} {1}'.format(response.status_code, response.reason)
        res.content_type = response.headers['content-type']
        res.body = response.text

        for k, v in kwargs.items():
            if v is not None:
                res.set_header(k, v)

        return res

    def toJson(self, res, **kwargs):
        """
        Converts a Falcon response to JSON.
        """
        data = {
            'body': res.body,
            'content-type': res.content_type,
            'status': res.status
        }

        for k, v in kwargs.items():
            data[k] = v

        return JSON.dumps(data)

    def fromJson(self, res, json, **kwargs):
        """
        Converts JSON to a Falcon response.
        """
        data = JSON.loads(json)

        res.body = data['body']
        res.content_type = data['content-type']
        res.status = data['status']

        for k, v in kwargs.items():
            if data.get(k) is not None:
                res.set_header(k, data.get(k))

        return res

###############################################################################
###############################################################################

app = application = falcon.API()
app.add_route(DATETIME_PATH, DateTime())
app.add_route(REDIRECT_PATH, Gateway())

###############################################################################
###############################################################################
