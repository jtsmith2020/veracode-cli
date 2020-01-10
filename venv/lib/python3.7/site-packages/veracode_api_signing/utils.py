# MIT License

# Copyright (c) 2019 Veracode, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import time
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


def get_current_timestamp():
    return int(round(time.time() * 1000))


def generate_nonce():
    if sys.version_info >= (3,):
        return os.urandom(16).hex()
    else:
        return os.urandom(16).encode('hex')


def get_host_from_url(url):
    """
    >>> get_host_from_url('https://api.veracode.com/apm/v1/assets')
    'api.veracode.com'
    >>> get_host_from_url('https://api.veracode.com:12345/apm/v1/assets')
    'api.veracode.com'
    >>> get_host_from_url('whackabacka')
    """
    return urlparse(url).hostname


def get_path_and_params_from_url(url):
    """
    >>> get_path_and_params_from_url('https://api.veracode.com/apm/v1/assets')
    '/apm/v1/assets'
    >>> get_path_and_params_from_url('https://api.veracode.com:12345/apm/v1/assets')
    '/apm/v1/assets'
    >>> get_path_and_params_from_url('https://api.veracode.com:12345/')
    '/'
    >>> get_path_and_params_from_url('https://api.veracode.com:12345')
    ''
    >>> get_path_and_params_from_url('https://api.veracode.com:12345/apm/v1/assets?page=2')
    '/apm/v1/assets?page=2'
    >>> get_path_and_params_from_url('https://api.veracode.com:123/foo?pagesize=2&page=90')
    '/foo?pagesize=2&page=90'
    """
    parsed = urlparse(url)
    path = parsed.path
    if path is None:
        path = ''

    query = parsed.query
    if query:
        return '{}?{}'.format(path, query)
    else:
        return path


def get_scheme_from_url(url):
    """
    >>> get_scheme_from_url('http://api.veracode.com/apm/v1/assets')
    'http'
    >>> get_scheme_from_url('https://api.veracode.com:12345/apm/v1/assets')
    'https'
    >>> get_scheme_from_url('ftp://api.veracode.com:12345/apm/v1/assets')
    'ftp'
    >>> get_scheme_from_url('whackabacka')
    ''
    """
    scheme = urlparse(url).scheme
    return scheme
