# Purpose:  API utilities
#
# Notes:    API credentials must be enabled on Veracode account and placed in ~/.veracode/credentials like
#
#           [default]
#           veracode_api_key_id = <YOUR_API_KEY_ID>
#           veracode_api_key_secret = <YOUR_API_KEY_SECRET>
#
#           and file permission set appropriately (chmod 600)

import os
import requests
import logging
from requests.adapters import HTTPAdapter

from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC
from helpers.exceptions import VeracodeAPIError
import xml.etree.ElementTree as ET


class VeracodeAPI:
    def __init__(self, proxies=None, vid=None, vkey=None):
        self.baseurl = "https://analysiscenter.veracode.com/api"
        requests.Session().mount(self.baseurl, HTTPAdapter(max_retries=3))
        self.proxies = proxies
        self.api_key_id = os.environ.get("VID")
        self.api_key_secret = os.environ.get("VKEY")

    def _upload_request(self, url, filename, params=None):
        try:
            files = {'file': open(filename, 'rb')}
            r = requests.post(url, auth=RequestsAuthPluginVeracodeHMAC(self.api_key_id, self.api_key_secret),
                             files=files, params=params, proxies=self.proxies)
            if 200 >= r.status_code <= 299:
                if r.content is None:
                    logging.debug("HTTP response body empty:\r\n{}\r\n{}\r\n{}\r\n\r\n{}\r\n{}\r\n{}\r\n"
                                  .format(r.request.url, r.request.headers, r.request.body, r.status_code, r.headers,
                                          r.content))
                    raise VeracodeAPIError("HTTP response body is empty")
                else:
                    return r.content
            else:
                logging.debug("HTTP error for request:\r\n{}\r\n{}\r\n{}\r\n\r\n{}\r\n{}\r\n{}\r\n"
                              .format(r.request.url, r.request.headers, r.request.body, r.status_code, r.headers,
                                      r.content))
                raise VeracodeAPIError("HTTP error: {}".format(r.status_code))
        except requests.exceptions.RequestException as e:
            logging.exception("Connection error")
            raise VeracodeAPIError(e)

    def _get_request(self, url, params=None):
        try:
            r = requests.get(url, auth=RequestsAuthPluginVeracodeHMAC(self.api_key_id, self.api_key_secret),
                             params=params, proxies=self.proxies)
            if 200 >= r.status_code <= 299:
                if r.content is None:
                    logging.debug("HTTP response body empty:\r\n{}\r\n{}\r\n{}\r\n\r\n{}\r\n{}\r\n{}\r\n"
                                  .format(r.request.url, r.request.headers, r.request.body, r.status_code, r.headers,
                                          r.content))
                    raise VeracodeAPIError("HTTP response body is empty")
                else:
                    return r.content
            else:
                logging.debug("HTTP error for request:\r\n{}\r\n{}\r\n{}\r\n\r\n{}\r\n{}\r\n{}\r\n"
                              .format(r.request.url, r.request.headers, r.request.body, r.status_code, r.headers,
                                      r.content))
                raise VeracodeAPIError("HTTP error: {}".format(r.status_code))
        except requests.exceptions.RequestException as e:
            logging.exception("Connection error")
            raise VeracodeAPIError(e)

    def upload_file(self, app_id, filename, sandbox_id=None):
        return self._upload_request(self.baseurl + "/5.0/uploadfile.do", filename, params={"app_id": app_id})

    def create_build(self, app_id, name):
        build_xml = self._get_request(self.baseurl + "/5.0/createbuild.do", params={"app_id": app_id,
                                                                                "version": name})
        root = ET.fromstring(build_xml)
        build_id = root.attrib.get("build_id")
        return build_id

    def begin_prescan(self, app_id, auto_scan, sandbox_id=None):
        return self._get_request(self.baseurl + "/5.0/beginprescan.do", params={"app_id": app_id,
                                                                                "auto_scan": auto_scan})

    def get_prescan_status(self, app_id, build_id=None, sandbox_id=None):
        parameters = {"app_id": app_id}
        if build_id is not None:
            parameters["build_id"] = str(build_id)
        if sandbox_id is not None:
            parameters["sandbox_id"] = str(sandbox_id)
        prescan_xml = self._get_request(self.baseurl + "/5.0/getprescanresults.do", params=parameters)
        print(prescan_xml)
        return True

    def get_app_list(self):
        """Returns all application profiles."""
        return self._get_request(self.baseurl + "/5.0/getapplist.do")

    def get_app_id_by_name(self, app_name):
        """Returns an app_id for the given app_name or None if it isn't found"""
        latest_app_profiles_xml = self.get_app_list()
        ns = {'vc': 'https://analysiscenter.veracode.com/schema/2.0/applist'}
        root = ET.fromstring(latest_app_profiles_xml)
        find_app_id_query = "./vc:app[@app_name='" + app_name + "']"
        app_node = root.findall(find_app_id_query, ns)
        if len(app_node) == 1:
            app_id = app_node[0].attrib.get("app_id")
        else:
            app_id = None
        return app_id

    def get_app_builds(self, report_changed_since):
        """Returns all builds."""
        return self._get_request(self.baseurl + "/4.0/getappbuilds.do", params={"only_latest": False,
                                                                                "include_in_progress": True,
                                                                                "report_changed_since": report_changed_since})

    def get_detailed_report(self, app_id):
        """Returns application profile info for a given app ID."""
        return self._get_request(self.baseurl + "/5.0/detailedreport.do", params={"app_id": app_id})

    def get_app_info(self, app_id):
        """Returns application profile info for a given app ID."""
        return self._get_request(self.baseurl + "/5.0/getappinfo.do", params={"app_id": app_id})

    def get_sandbox_list(self, app_id):
        """Returns a list of sandboxes for a given app ID"""
        return self._get_request(self.baseurl + "/5.0/getsandboxlist.do", params={"app_id": app_id})

    def get_build_list(self, app_id, sandbox_id=None):
        """Returns all builds for a given app ID."""
        if sandbox_id is None:
            params = {"app_id": app_id}
        else:
            params = {"app_id": app_id, "sandbox_id": sandbox_id}
        return self._get_request(self.baseurl + "/5.0/getbuildlist.do", params=params)

    def get_build_info(self, app_id, build_id, sandbox_id=None):
        """Returns build info for a given build ID."""
        if sandbox_id is None:
            params = {"app_id": app_id, "build_id": build_id}
        else:
            params = {"app_id": app_id, "build_id": build_id, "sandbox_id": sandbox_id}
        return self._get_request(self.baseurl + "/5.0/getbuildinfo.do", params=params)

    def get_detailed_report(self, build_id):
        """Returns a detailed report for a given build ID."""
        return self._get_request(self.baseurl + "/5.0/detailedreport.do", params={"build_id": build_id})

    def get_policy_list(self):
        """Returns all policies."""
        return self._get_request(self.baseurl + "/5.0/getpolicylist.do")

    def get_user_list(self):
        """Returns all user accounts."""
        return self._get_request(self.baseurl + "/5.0/getuserlist.do")

    def get_user_info(self, username):
        """Returns user info for a given username."""
        return self._get_request(self.baseurl + "/5.0/getuserinfo.do", params={"username": username})
