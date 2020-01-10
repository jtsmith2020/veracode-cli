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

""" Plugin for the popular `httpie` library (an alternative to `curl`)

At the time of writing, this is how you would use with < 0.9.9 version of HTTPie:
    http --auth-type=veracode_hmac --auth=':' https://api.veracode.io/apm/v1/

For HTTPie version >= 0.9.9:
    http --auth-type=veracode_hmac https://api.veracode.io/apm/v1/
or later:
    http -A veracode_hmac https://api.veracode.io/apm/v1/

"""
# noinspection PyUnresolvedReferences
from httpie.plugins import AuthPlugin

from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC


class HttpiePluginVeracodeHmacAuth(AuthPlugin):
    """ Plugin for HTTPie. (Extremely thin compatibility layer around the Requests plugin.)
    """

    name = 'Veracode HMAC auth'
    auth_type = 'veracode_hmac'
    description = 'Sign requests using an HMAC authentication method comparable to that ' \
                  'used by AWS.'

    # Set to `False` to make it possible to invoke this auth
    # plugin without requiring the user to specify credentials
    # through `--auth, -a`.
    auth_require = False

    # By default the `-a` argument is parsed for `username:password`.
    # Set this to `False` to disable the parsing and error handling.
    auth_parse = False

    def get_auth(self, access_key=None, secret_key=None):
        # This detail might change after this Pull Request is merged:
        #   https://github.com/jkbrzt/httpie/pull/433
        # ... because the access_key/ secret_key arg being given here, is really only
        # coming in from the command-line.

        if access_key or secret_key:
            raise ValueError('Please do not provide credentials on the command-line. '
                             'Instead, please set your credentials up in a credentials '
                             'file or environment variables. ')

        return RequestsAuthPluginVeracodeHMAC(access_key, secret_key)
