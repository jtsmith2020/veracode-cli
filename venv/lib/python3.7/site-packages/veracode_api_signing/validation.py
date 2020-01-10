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

from veracode_api_signing.exceptions import VeracodeCredentialsError


def validate_api_key_id(api_key_id):
    """
    >>> validate_api_key_id('3ddaeeb10ca690df3fee5e3bd1c329fa')
    >>> validate_api_key_id('3ddaeeb10ca690df3f') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    VeracodeCredentialsError: API key ... is 18 characters,
    which is not long enough. The API key should be at least 32 characters
    >>> validate_api_key_id('0123456789abcdef'*128) # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    VeracodeCredentialsError: API key ... is 2048 characters,
    which is too long. The API key should not be more than 128 characters
    >>> validate_api_key_id('ZXHQddaeeb10ca690df3fee5e3bd1c329f') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    VeracodeCredentialsError: API key ... does not seem to be hexadecimal
    """
    api_key_id_minimum_length = 32
    api_key_id_maximum_length = 128
    if len(api_key_id) < api_key_id_minimum_length:
        raise VeracodeCredentialsError(
            'API key {key} is {key_length} characters, which is not '
            'long enough. The API key should be at least {minimum_length} '
            'characters'.format(key=api_key_id, key_length=len(api_key_id),
                                minimum_length=api_key_id_minimum_length))
    if len(api_key_id) > api_key_id_maximum_length:
        raise VeracodeCredentialsError(
            'API key {key} is {key_length} characters, which is too '
            'long. The API key should not be more than {maximum_length} '
            'characters'.format(key=api_key_id, key_length=len(api_key_id),
                                maximum_length=api_key_id_maximum_length))
    if not validate_hex(api_key_id):
        raise VeracodeCredentialsError(
            'API key {} does not seem to be hexadecimal'.format(api_key_id))


def validate_api_key_secret(api_key_secret):
    """
    >>> validate_api_key_secret('0123456789abcdef'*8)
    >>> validate_api_key_secret('3ddaeeb10ca690df3f') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    VeracodeCredentialsError: API secret key ... is 18 characters,
    which is not long enough. The API secret key should be at least 128 characters
    >>> validate_api_key_secret('0123456789abcdef'*128) # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    VeracodeCredentialsError: API secret key ... is 2048 characters,
    which is too long. The API secret key should be no more than 1024 characters
    >>> validate_api_key_secret('ghijklmnopqrstuv'*9) # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      ...
    VeracodeCredentialsError: API key ... does not seem to be hexadecimal
    """
    secret_key_minimum_length = 128
    secret_key_maximum_length = 1024
    if len(api_key_secret) < secret_key_minimum_length:
        raise VeracodeCredentialsError(
            'API secret key {secret_key} is {length} characters, which is not long enough. '
            'The API secret key should be at least {min_length} '
            'characters'.format(secret_key=api_key_secret, length=len(api_key_secret),
                                min_length=secret_key_minimum_length))
    if len(api_key_secret) > secret_key_maximum_length:
        raise VeracodeCredentialsError(
            'API secret key {secret_key} is {length} characters, which is too long. '
            'The API secret key should be no more than {max_length} '
            'characters'.format(secret_key=api_key_secret, length=len(api_key_secret),
                                max_length=secret_key_maximum_length))
    if not validate_hex(api_key_secret):
        raise VeracodeCredentialsError(
            'API key {} does not seem to be hexadecimal'.format(api_key_secret))


def validate_hex(hex_string):
    """
    Make sure a string can be hex decoded

    Args:
        hex_string (str): A string of hex characters to check

    Returns:
        boolean: True or False depending on if the string can be hex decoded

    >>> validate_hex('af')
    True
    >>> validate_hex('zh')
    False
    """
    try:
        int(hex_string, 16)
        return True
    except ValueError:
        return False


def validate_scheme(scheme):
    """ Validate that the scheme is identical to scheme(s) we support. (HTTPS.)

    >>> assert validate_scheme('https')
    >>> validate_scheme('http') # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    ValueError: ... HTTPS ...
    >>> validate_scheme('httpss') # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    ValueError: ... HTTPS ...
    >>> validate_scheme(None) # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    ValueError: ... HTTPS ...
    """
    if (scheme or '').lower() == u'https':
        return True
    else:
        raise ValueError("Only HTTPS APIs are supported by Veracode.")
