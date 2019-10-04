from typing import List, Any

from helpers.base_results_handler import ResultsHandler
from helpers.base_results_sync import BaseSynchroniser
from helpers.api import VeracodeAPI
from helpers.base_scanner import Scanner
from helpers.exceptions import VeracodeError
from antfs import AntPatternDirectoryScanner
import time
import xmltodict
from jira import JIRA
import getpass
import re


class SynchroniseJIRA(ResultsHandler, BaseSynchroniser):
    def __init__(self):
        self.display_name = "Synchronise Flaws with JIRA"
        self.description = "Manage tickets in a JIRA project based on scan results."

    def configure(self, api):
        config = BaseSynchroniser.configure(self, api)

        config["type"] = type(self).__name__
        config["display_name"] = self.display_name
        config["jira_base_url"] = input("        JIRA Base URL: ")
        config["jira_user"] = input("        JIRA User: ")
        config["jira_password"] = getpass.getpass(prompt="        JIRA password: ")
        auth_jira = JIRA(auth=(config["jira_user"], config["jira_password"]),server=config["jira_base_url"])
        # Get all projects viewable by anonymous users.
        projects = auth_jira.projects()
        # Sort available project keys, then return the second, third, and fourth keys.
        keys: List[Any] = sorted([project.key for project in projects])
        print("        Select JIRA project: ")
        #print(keys)
        #print(projects)
        count = 0;
        for proj in projects:
            print("          "+str(count)+". "+str(proj))
            count += 1
        o = int(-1)
        lenp = len(projects)
        while not (0 <= o < lenp):
            o = int(input("        Choose (0-"+str(lenp)+"): "))
        config["jira_project"] = str(projects[o])

        return config

    ########################################################################################################################
    # create_ticket()
    #   parameters:
    #
    def create_ticket(self, api, config, issue,  auth_jira):
        """
        :param auth_jira: JIRA authentication token
        :param config: the ResultsHandler Configuration Dictionary
        :param issue: an Issue to be logged as a ticket
        :return: issue key or None if it fails
        """
        summarystr = BaseSynchroniser.get_summary_str(self, issue)
        descstr = BaseSynchroniser.get_description_str(self, issue)
        new_issue = auth_jira.create_issue(project=config["jira_project"], summary=summarystr,
                                         description=descstr, issuetype={'name': 'Bug'})
        api.add_comment(config["build_id"], issue["issueid"], BaseSynchroniser.get_flaw_comment_str(self, config, str(new_issue)))
        return str(new_issue)

    ########################################################################################################################
    # update_ticket()
    #   parameters:
    #
    def update_ticket(self, api, config, issue,  auth_jira):
        the_issue = auth_jira.issue(issue["issue_key"])
        summarystr = BaseSynchroniser.get_summary_str(self, issue)
        descstr = BaseSynchroniser.get_description_str(self, issue)
        the_issue.update(summary=summarystr, description=descstr)
        return True

    ########################################################################################################################
    # close_ticket()
    #   parameters:
    #
    def close_ticket(self, api, config, issue,  auth_jira):
        the_issue = auth_jira.issue(issue["issue_key"])
        transitions = auth_jira.transitions(the_issue)
        the_transition = ""
        for t in transitions:
            if t["name"] == "Done":
                the_transition = t["id"]
        auth_jira.transition_issue(the_issue, the_transition)
        return True


    def execute(self, api, activity, config):
        print("")
        print("Executing results handler SynchroniseJIRA with:")
        for key, value in config.items():
            print("  " + key + " = " + str(value))
        print("")

        # We should come up with at better way to get/store the Jira creds
        auth_jira = JIRA(auth=(config["jira_user"], config["jira_password"]),server=config["jira_base_url"])

        # Find the build_id and store in the config dictionary
        activity["build_id"] = "2945438"
        """ Get the build id """
        if activity["build_id"] is None:
            activity["build_id"] = api.get_latest_build_id(activity["app_id"])
        if activity["build_id"] is None:
            raise  VeracodeError("Invalid Scan Name")
        config["build_id"] = activity["build_id"]

        # Get and process the issues.
        # First get the detailed report, then convert to a string and look for the flaws
        # Note: later this could be optimized to use a dict maybe to find the static, dynamic, sca, manual flaws separately
        #
        relevant_flaws = BaseSynchroniser.get_flaw_actions(self, api, config)
        for flaw_action in relevant_flaws:
            if flaw_action["type"] == "close":
                print("Closing Ticket : " + flaw_action["issue_key"])
                self.close_ticket(self, api, config, flaw_action, auth_jira)
            elif flaw_action["type"] == "update":
                print("Updating Ticket: " + flaw_action["issue_key"])
                self.update_ticket(self, api, config, flaw_action, auth_jira)
            elif flaw_action["type"] == "create":
                print("Creating Ticket: ", end="")
                print(self.create_ticket(self, api, config, flaw_action, auth_jira))


        return False

