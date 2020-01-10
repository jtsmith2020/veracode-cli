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

""" The generic details of creating the client-side HMAC signature, to call Veracode APIs."""
from hashlib import sha256
import hmac
import codecs
import sys

from veracode_api_signing.exceptions import UnsupportedAuthSchemeException
from veracode_api_signing.formatters import format_signing_data, format_veracode_hmac_header
from veracode_api_signing.utils import get_current_timestamp, generate_nonce


DEFAULT_AUTH_SCHEME = 'VERACODE-HMAC-SHA-256'


def generate_veracode_hmac_header(host, path, method, api_key_id, api_key_secret, auth_scheme=DEFAULT_AUTH_SCHEME):
    """
    Create the authorization header value to send in an HTTP request.

    Args:
        host (str): The host of the request. For example: `api.veracode.com`
        path (str): The path of the request. For example: `/v1/results`
        method (str): The method of the request. For example: `GET` or `POST`
        api_key_id (str): The user's API key
        api_key_secret (str): The user's API secret key
        auth_scheme (str): What authentication algorithm will be used to create the signature of the request. This will
            also be placed in the resulting header.

    Returns:
        str: The value of Veracode compliant HMAC header
    """
    signing_data = format_signing_data(api_key_id, host, path, method)
    timestamp = get_current_timestamp()
    nonce = generate_nonce()
    signature = create_signature(auth_scheme, api_key_secret, signing_data, timestamp, nonce)
    return format_veracode_hmac_header(auth_scheme, api_key_id, timestamp, nonce, signature)


def create_signature(auth_scheme, api_key_secret, signing_data, timestamp, nonce):
    """
    Create a request signature according to given authentication scheme.

    Args:
        auth_scheme (str): Used to describe what algorithm to use when creating the signature. Currently the only
            supported algorithm is HMAC-SHA-256, which can be used by passing 'VERACODE-HMAC-SHA-256' as the value of
            this parameter.
        api_key_secret (str): The user's API Secret Key
        signing_data (str): The data to be signed (usually consists of host, path, request method and other data)
        timestamp (int): A unix timestamp to millisecond precision
        nonce (str): A random value to prevent replay attacks

    Returns:
        str: The signature according to algorithm specified
    """
    if auth_scheme == 'VERACODE-HMAC-SHA-256':
        signature = create_hmac_sha_256_signature(api_key_secret, signing_data, timestamp, nonce)
    else:
        raise UnsupportedAuthSchemeException('Auth scheme {auth_scheme} not supported'.format(auth_scheme=auth_scheme))
    return signature


def create_hmac_sha_256_signature(api_key_secret, signing_data, timestamp, nonce):
    """
    Create an HMAC signature using the SHA 256 algorithm

    Args:
        api_key_secret (str): The API Secret key
        signing_data (str): The data to be signed
        timestamp (int): A Unix timestamp to millisecond precision
        nonce (str): A random value to prevent replay attacks

    Returns:
        str: An HMAC-SHA-256 signature
    """
    key_nonce = \
        hmac.new(codecs.decode(api_key_secret, 'hex_codec'), codecs.decode(nonce, 'hex_codec'), sha256).digest()
    key_date = hmac.new(key_nonce, str(timestamp).encode(), sha256).digest()
    signature_key = hmac.new(key_date, u'vcode_request_version_1'.encode(), sha256).digest()
    return hmac.new(signature_key, signing_data.encode(), sha256).hexdigest()
