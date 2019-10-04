from helpers.base_results_handler import ResultsHandler
from helpers.api import VeracodeAPI
from helpers.base_scanner import Scanner
from helpers.exceptions import VeracodeError
from antfs import AntPatternDirectoryScanner
import time
import xmltodict
from jira import JIRA
import getpass
import re
from abc import ABC
from abc import abstractmethod
from lxml import etree

class BaseSynchroniser(ABC):

    def __init__(self):
        self.display_name = "Base Synchroniser"
        self.description = "Manage tickets"

    def get_flaw_actions(self, api, config):
        flaw_actions = []
        print("Downloading Results...")
        """ get thedetailed report """
        detailed_report_xml = api.get_detailed_report(config["build_id"])
        print("Building list of Flaw actions...")
        """ find all flaws that could be relevant """
        ns = {'vc': 'https://www.veracode.com/schema/reports/export/1.0'}
        #root = ET.fromstring(detailed_report_xml)
        root = etree.fromstring(detailed_report_xml)
        find_categories_query = "./vc:severity/vc:category[vc:cwe/vc:staticflaws/vc:flaw"
        if config["sync_filter"] == "policy_affecting":
            find_categories_query = find_categories_query + "/@affects_policy_compliance='true']"
        else:
            find_categories_query = find_categories_query + "]"
        category_nodes = root.xpath(find_categories_query, namespaces=ns)

        for category_node in category_nodes:
            category_name = category_node.attrib.get("categoryname")

            find_flaws_query = "./vc:cwe/vc:staticflaws/vc:flaw"
            if config["sync_filter"] == "policy_affecting":
                find_flaws_query = find_flaws_query + "[@affects_policy_compliance='true']"
            flaw_nodes = category_node.xpath(find_flaws_query, namespaces=ns)
            """ create the flaw actions (e.g. open, update, close) """
            for flaw_node in flaw_nodes:
                """ get everything we need... """
                remediation_status = flaw_node.attrib.get("remediation_status")
                mitigation_status = flaw_node.attrib.get("mitigation_status")
                find_issue_key_query = "./vc:annotations/vc:annotation[starts-with(@description, '" + config["type"] + " Issue Key: ')]"
                issue_key_nodes = flaw_node.xpath(find_issue_key_query, namespaces=ns)
                issue_key = None
                if issue_key_nodes is not None and len(issue_key_nodes) > 0:
                    issue_key = self.get_issue_key_from_comment(self, config, str(issue_key_nodes[0].attrib.get("description")))
                """ OK, now we can create the action... """
                action = {}
                action["category_name"] = category_name
                action["cwe_name"] = flaw_node.attrib.get("categoryname")
                action["cweid"] = flaw_node.attrib.get("cweid")
                action["attack_vector"] = flaw_node.attrib.get("type")
                action["description"] = flaw_node.attrib.get("description")
                action["module"] = flaw_node.attrib.get("module")
                action["scope"] = flaw_node.attrib.get("scope")
                action["file"] = flaw_node.attrib.get("sourcefile")
                action["path"] = flaw_node.attrib.get("sourcefilepath")
                action["line"] = flaw_node.attrib.get("line")
                action["issueid"] = flaw_node.attrib.get("issueid")
                if issue_key is not None:
                    if issue_key == "T1-11":
                        print("")
                        print("Found T1-11")
                        print("mitigation_status = " + mitigation_status)
                        print("remediation_status = " + remediation_status)
                        print("")
                    if remediation_status == "fixed" or mitigation_status == "accepted":
                        action["type"] = "close"
                        action["issue_key"] = issue_key
                    else:
                        action["type"] = "update"
                        action["issue_key"] = issue_key
                else:
                    if remediation_status != "fixed" and mitigation_status != "accepted":
                        action["type"] = "create"
                flaw_actions.append(action)

        return flaw_actions

    def get_summary_str(self, issue):
        return "Veracode Flaw: " + str(issue['category_name']) + " Flaw " + str(issue['issueid'])

    def get_description_str(self, issue):
        return "CWE: " + str(issue['cweid']) + " " + str(issue['cwe_name']) + "\n\n" + \
               "Module: " + str(issue['module']) + "\n\n" + \
               "Source: " + str(issue['file']) + ":" + str(issue['line']) + "\n\n" + \
               "Attack Vector: " + str(issue['attack_vector']) + "\n\n" + \
               "Description: " + str(issue['description'])

    ##############################################################################
    # These 2 functions need to be a matched pair...                             #
    #                                                                            #
    def get_flaw_comment_str(self, config, issue_key):
        return config["type"] + " Issue Key: " + issue_key

    def get_issue_key_from_comment(self, config, comment):
        return comment.split(config["type"] + " Issue Key: ", 1)[1]
    #                                                                            #
    ##############################################################################

    def configure(self, api):
        config = {}
        config["type"] = type(self).__name__
        config["display_name"] = self.display_name

        print("        Synchronisation Filter Options:")
        print("          0. All Flaws (every flaw will be opened and managed as a separate ticket)")
        print("          1. Policy Affecting Flaws (only Policy Affecting flaws will be opened and managed as separate tickets)")
        o = int(-1)
        while not (0 <= o < 2):
            o = int(input("        Choose (0-2): "))
        if o==0:
            config["sync_filter"] = "all"
        elif o == 1:
            config["sync_filter"] = "policy_affecting"

        print("        Mitigation Handling:")
        print("          0. Change Ticket State when Mitigation Approved (if a mitigation is approved then the ticket state is changed - e.g. to Closed")
        print("          1. None")
        o = int(-1)
        while not (0 <= o < 2):
            o = int(input("        Choose (0-1): "))
        if o==0:
            config["mitigation_handling"] = True
        elif o == 1:
            config["mitigation_handling"] = False

        return config

    @abstractmethod
    def execute(self, api, activity, config):
        pass
