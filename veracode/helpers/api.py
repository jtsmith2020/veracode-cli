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
import re
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC
from helpers.exceptions import VeracodeAPIError
from helpers.exceptions import VeracodeError
import xml.etree.ElementTree as ET
import configparser


class VeracodeAPI:
    def __init__(self, proxies=None, vid=None, vkey=None):
        self.baseurl = "https://analysiscenter.veracode.com/api"
        requests.Session().mount(self.baseurl, HTTPAdapter(max_retries=3))
        self.proxies = proxies
        if vid is None or vkey is None:
            """ OK, lets try the environment variables... """
            self.api_key_id = os.environ.get("VID")
            self.api_key_secret = os.environ.get("VKEY")
            if self.api_key_id is None or self.api_key_id == "" or self.api_key_secret is None or self.api_key_secret == "":
                """ OK, try for the credentials file instead... """
                auth_file = os.path.join(os.path.expanduser("~"), '.veracode', 'credentials')
                if not os.path.exists(auth_file):
                    raise VeracodeError("""Credentials not found. You can supply the credentials as command line arguments, environment variables or by configuring a veracode credentials file. See README.md for more details.""")
                config = configparser.ConfigParser()
                config.read(auth_file)
                credentials_section_name = os.environ.get("VERACODE_API_PROFILE", "default")
                self.api_key_id = config.get(credentials_section_name, "VERACODE_API_KEY_ID")
                self.api_key_secret = config.get(credentials_section_name, "VERACODE_API_KEY_SECRET")
                if self.api_key_id is None or self.api_key_secret is None:
                    raise VeracodeError("Unable to get credentials from the veracode credentials file (~/.veracode/credentials)")
        else:
            """ use the id and key supplied as parameters """
            self.api_key_id = vid
            self.api_key_secret = vkey

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
        if sandbox_id is None:
            return self._upload_request(self.baseurl + "/5.0/uploadfile.do", filename, params={"app_id": app_id})
        else:
            return self._upload_request(self.baseurl + "/5.0/uploadfile.do", filename, params={"app_id": app_id,
                                                                                               "sandbox_id": sandbox_id})

    def create_team(self, name, users):
        return self._get_request(self.baseurl + "/3.0/createteam.do", params={"team_name": name,
                                                                                "user": users})

    def create_app(self, app_name, description, bus_crit, policy, teams):
        app_xml = self._get_request(self.baseurl + "/5.0/createapp.do", params={"app_name": app_name,
                                                                                "business_criticality": bus_crit,
                                                                                "policy": policy,
                                                                                "teams": teams})
        app_id = re.findall('app_id="(.*?)"', str(app_xml))
        # print(app_id)
        return app_id[0]

    def get_sandbox_id(self, app_id, sandbox_name):
        sbl_xml = self._get_request(self.baseurl + "/5.0/getsandboxlist.do", params={"app_id": app_id})
        sb_id = re.findall('sandbox_id="(.*?)" sandbox_name="' + sandbox_name + '"', str(sbl_xml))
        if len(sb_id) == 1:
            return sb_id[0]
        else:
            return None

    def create_sandbox(self, app_id, sandbox_name):
        sb_xml = self._get_request(self.baseurl + "/5.0/createsandbox.do", params={"app_id": app_id,
                                                                                    "sandbox_name": sandbox_name})
        sb_id = re.findall('sandbox_id="(.*?)"', str(sb_xml))
        if len(sb_id) == 1:
            return sb_id[0]
        else:
            return None

    def create_build(self, app_id, name, sandbox_id):
        if sandbox_id is None:
            build_xml = self._get_request(self.baseurl + "/5.0/createbuild.do", params={"app_id": app_id,
                                                                                        "version": name})
        else:
            build_xml = self._get_request(self.baseurl + "/5.0/createbuild.do", params={"app_id": app_id,
                                                                                        "version": name,
                                                                                        "sandbox_id": sandbox_id})
        build_id = re.findall('build_id="(.*?)"', str(build_xml))
        # print(build_xml)
        if len(build_id) > 0:
            return build_id[0]
        else:
            return None

    def begin_prescan(self, app_id, auto_scan, sandbox_id=None):
        if sandbox_id is None:
            return self._get_request(self.baseurl + "/5.0/beginprescan.do", params={"app_id": app_id,
                                                                                    "auto_scan": auto_scan})
        else:
            return self._get_request(self.baseurl + "/5.0/beginprescan.do", params={"app_id": app_id,
                                                                                    "auto_scan": auto_scan,
                                                                                    "sandbox_id": sandbox_id})

    def get_modules(self, app_id, build_id=None, sandbox_id=None):
        parameters = {"app_id": app_id}
        if build_id is not None:
            parameters["build_id"] = str(build_id)
        if sandbox_id is not None:
            parameters["sandbox_id"] = str(sandbox_id)
        prescan_xml = self._get_request(self.baseurl + "/5.0/getprescanresults.do", params=parameters)
        if b"<error>" in prescan_xml:
            return None
        else:
            ns = {'vc': 'https://analysiscenter.veracode.com/schema/2.0/prescanresults'}
            root = ET.fromstring(prescan_xml)
            find_modules_query = "./vc:module[@has_fatal_errors='false']"
            module_nodes = root.findall(find_modules_query, ns)
            retval = {}
            for module_node in module_nodes:
                retval[module_node.attrib.get("name")] = module_node.attrib.get("id")
            return retval

    def results_ready(self, app_id, build_id, sandbox_id=None):
        """ Returns boolean for whether or not the build has results ready."""
        if sandbox_id is None:
            build_info_xml =  self._get_request(self.baseurl + "/5.0/getbuildinfo.do", params={"app_id": app_id,
                                                                                               "build_id": build_id})
        else:
            build_info_xml = self._get_request(self.baseurl + "/5.0/getbuildinfo.do", params={"app_id": app_id,
                                                                                              "build_id": build_id,
                                                                                              "sandbox_id": sandbox_id})
        #print(str(build_info_xml))
        #x = re.search('results_ready="true"', str(build_info_xml))
        #print("x is " + x)
        if re.search('results_ready="true"', str(build_info_xml)) is None:
            return False
        else:
            return True

    def add_comment(self, build_id, flaw_id, comment):
        return self._get_request(self.baseurl + "/updatemitigationinfo.do", params={"build_id": build_id,
                                                                                "action": "comment",
                                                                                "comment": comment,
                                                                                "flaw_id_list": flaw_id})

    def get_latest_build_id(self, app_id, sandbox_id=None):
        if sandbox_id is None:
            build_list_xml = self._get_request(self.baseurl + "/5.0/getbuildlist.do", params={"app_id": app_id})
        else:
            build_list_xml = self._get_request(self.baseurl + "/5.0/getbuildlist.do", params={"app_id": app_id,
                                                                                              "sandbox_id": sandbox_id})
        #print(str(build_list_xml))
        build_ids = re.findall('build_id="(.*?)"', str(build_list_xml))
        #print(build_ids)

        i = len(build_ids) - 1
        build_id = None
        while build_id is None:
            test = str(build_ids[i])
            if self.results_ready(app_id, test, sandbox_id):
                build_id = test
            else:
                i = i - 1
        return build_id



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
