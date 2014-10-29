#!/usr/bin/env python

import httplib
try:
    import simplejson as json
except ImportError:
    import json
import requests
import sys
import urlparse

# ST2 configuration
ST2_HOST = ''
ST2_WEBHOOKS_PORT = '6000'
ST2_WEBHOOKS_PATH = '/webhooks/st2/'
ST2_API_PORT = '9101'
ST2_TRIGGERS_PATH = '/triggertypes/'
ST2_TRIGGER_TYPE = 'sensu.event_handler'

REGISTERED_WITH_ST2 = False

OK_CODES = [httplib.OK, httplib.CREATED, httplib.ACCEPTED, httplib.CONFLICT]


def _create_trigger_type():
    try:
        url = _get_st2_triggers_url()
        payload = {'name': ST2_TRIGGER_TYPE}
        # sys.stdout.write('POST: %s: Body: %s\n' % (url, payload))
        post_resp = requests.post(url, data=json.dumps(payload))
    except:
        sys.stderr.write('Unable to register trigger type with st2.')
        raise
    else:
        status = post_resp.status_code
        if status not in OK_CODES:
            sys.stderr.write('Failed to register trigger type with st2. HTTP_CODE: %d\n' %
                             status)
            raise
        else:
            sys.stdout.write('Registered trigger type with st2.\n')


def _register_with_st2():
    global REGISTERED_WITH_ST2
    try:
        url = _get_st2_triggers_url() + ST2_TRIGGER_TYPE + '/'
        # sys.stdout.write('GET: %s\n' % url)
        get_resp = requests.get(url)
        if get_resp.status_code == httplib.NOT_FOUND:
            _create_trigger_type()
        _create_trigger_type()
    except:
        raise
    else:
        REGISTERED_WITH_ST2 = True


def _get_st2_triggers_url():
    url = urlparse.urlunparse(('http', ST2_HOST + ':' + ST2_API_PORT, ST2_TRIGGERS_PATH,
                              None, None, None))
    return url


def _get_st2_webhooks_url():
    url = urlparse.urlunparse(('http',  ST2_HOST + ':' + ST2_WEBHOOKS_PORT, ST2_WEBHOOKS_PATH,
                               None, None, None))
    return url


def _post_event_to_st2(url, body):
    headers = {}
    headers['X-ST2-Integration'] = 'sensu.'
    headers['Content-Type'] = 'application/json; charset=utf-8'
    try:
        sys.stdout.write('POST: url: %s, body: %s\n' % (url, body))
        r = requests.post(url, data=json.dumps(body), headers=headers)
    except:
        sys.stderr.write('Cannot connect to st2 endpoint.')
    else:
        status = r.status_code
        if status not in OK_CODES:
            sys.stderr.write('Failed posting sensu event to st2. HTTP_CODE: %d\n' % status)
        else:
            sys.stdout.write('Sent sensu event to st2. HTTP_CODE: %d\n' % status)


def main(args):

    body = {}
    body['name'] = ST2_TRIGGER_TYPE
    body['payload'] = json.loads(sys.stdin.read().strip())
    _post_event_to_st2(_get_st2_webhooks_url(), body)


if __name__ == '__main__':
    try:
        if not REGISTERED_WITH_ST2:
            _register_with_st2()
    except:
        sys.stderr.write('Failed registering with st2. Won\'t post event.\n')
    else:
        main(sys.argv)