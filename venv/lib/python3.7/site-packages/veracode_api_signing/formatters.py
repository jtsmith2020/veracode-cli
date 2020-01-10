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


def format_signing_data(api_key_id, host, url, method):
    """ Format the input data for signing to the exact specification.

    Mainly, handles case-sensitivity where it must be handled.

    >>> format_signing_data('0123456789abcdef', 'veracode.com', '/home', 'GET')
    'id=0123456789abcdef&host=veracode.com&url=/home&method=GET'
    >>> format_signing_data('0123456789abcdef', 'VERACODE.com', '/home', 'get')
    'id=0123456789abcdef&host=veracode.com&url=/home&method=GET'
    """
    # Ensure some things are in the right case.
    # Note that path (url) is allowed to be case-sensitive (because path is sent along verbatim)
    # This is an HTTP fact, not a rule of our own design. stackoverflow.com/a/17113291/884640
    api_key_id = api_key_id.lower()
    host = host.lower()
    method = method.upper()

    # BTW we do not use a stdlib urlencode thing, because it is NOT exactly URL-encoded!
    return 'id={api_key_id}&host={host}&url={url}&method={method}'.format(api_key_id=api_key_id, host=host, url=url,
                                                                          method=method)


def format_veracode_hmac_header(auth_scheme, api_key_id, timestamp, nonce, signature):
    """ Given all the piecs including signature, just fit into the specified format.

    (This should _NOT_ manipulate case and so-on, that would likely break things.)

    >>> format_veracode_hmac_header(auth_scheme='VERACODE-HMAC-SHA-256', api_key_id='702a1650', \
                                    timestamp='1445452792746', nonce='3b1974fbaa7c97cc', \
                                    signature='b81c0315b8df360778083d1b408916f8')
    'VERACODE-HMAC-SHA-256 id=702a1650,ts=1445452792746,nonce=3b1974fbaa7c97cc,sig=b81c0315b8df360778083d1b408916f8'
    """
    return '{auth_scheme} id={id},ts={ts},nonce={nonce},sig={sig}'.format(auth_scheme=auth_scheme, id=api_key_id,
                                                                          ts=timestamp, nonce=nonce, sig=signature)
