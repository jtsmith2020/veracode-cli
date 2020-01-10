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

""" Plugin for the popular `requests` library"""
from requests.auth import AuthBase

from veracode_api_signing.credentials import get_credentials
from veracode_api_signing.utils import get_host_from_url
from veracode_api_signing.validation import validate_api_key_id, validate_api_key_secret
from veracode_api_signing.veracode_hmac_auth import generate_veracode_hmac_header


class RequestsAuthPluginVeracodeHMAC(AuthBase):
    """
    Use this class to easily sign an HTTP request using the requests module. To sign a request, you can use this class
    like this:

    requests.get(api_url, auth=RequestsAuthPluginVeracodeHMAC())

    and of course if your credentials are not stored on the filesystem or in environment variables, you can pass
    your credentials to the constructor like this:

    requests.get(api_url, auth=RequestsAuthPluginVeracodeHMAC(
        api_key_id=<YOUR_API_KEY>, api_key_secret=<YOUR_API_SECRET_KEY>))
    """

    def __init__(self, api_key_id=None, api_key_secret=None):
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret

    def __call__(self, request):
        if self.api_key_id is None or self.api_key_secret is None:
            self.api_key_id, self.api_key_secret = get_credentials()
        validate_api_key_id(self.api_key_id)
        validate_api_key_secret(self.api_key_secret)
        sign_request(request, self.api_key_id, self.api_key_secret)
        return request


def sign_request(request, api_key_id, api_key_secret):
    """
    Sign a request

    Args:
        request (requests.PreparedRequest): The request to sign with an HMAC header
        api_key_id (str): The user's API key
        api_key_secret (str): The user's API secret key
    """
    host = get_host_from_url(request.url)
    path = request.path_url
    method = request.method
    request.headers['Authorization'] = generate_veracode_hmac_header(
        host, path, method, api_key_id, api_key_secret)
