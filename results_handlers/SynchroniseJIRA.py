from typing import List, Any

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

class SynchroniseJIRA(ResultsHandler):
    def __init__(self):
        self.display_name = "Synchronise Flaws with JIRA"
        self.description = "Manage tickets in a JIRA project based on scan results."

    def configure(self, api):
        config = dict()
        config["type"] = type(self).__name__
        config["display_name"] = self.display_name
        print("      Configuring " + self.display_name)
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
        lenp = len(projects)-1
        while not (0 <= o < lenp):
            o = int(input("        Choose (0-"+str(lenp)+"): "))
        config["jira_project"] = str(projects[o])
        #print("Jira Project is: "+str(config["jira_project"]))
        #config["jira_project"] = input("        JIRA Project: ")
        print("        Synchronisation Strategy Options:")
        print("          0. All Flaws")
        print("          1. Policy Affecting Flaws")
        print("          2. Unmitigated Policy Affecting Flaws")
        o = int(-1)
        while not (0 <= o < 3):
            o = int(input("        Choose (0-2): "))
        if o==0:
            config["sync_strategy"] = "all"
        elif o == 1:
            config["sync_strategy"] = "policy_affecting"
        elif o == 2:
            config["sync_strategy"] = "unmitigated_policy_affecting"

        return config

    ########################################################################################################################
    # process_issue()
    #   parameters:
    #     issue         : a Veracode issue to be added to Jira
    #
    #
    def process_issue(self, auth_jira, config, issue):

        print("")
        print("Process Veracode Issue")
        print("==================================")
        print("")
        issue = issue.strip()
        #re.sub('[^A-Za-z0-9]+', '', issue)
        #issue = issue.replace('&#xd;&#xa;','\n')
        #print("issue is "+issue)
        #issue = issue.replace('&#xa;', ' ')
        #issue = issue.replace('&#xd;', ' ')
        #issue = issue.replace("\n\n","\n")
        dr_dict = xmltodict.parse(str(issue))
        #print("xmltodict\n")
        #for dkey, value in dr_dict.items():
        #     print("  " + dkey + " = " + str(value)+"\n")
        print("Severity is: "+dr_dict['flaw']['@severity'])
        print("Category name is: "+dr_dict['flaw']['@categoryname'])
        print("Count is "+dr_dict['flaw']['@count'])
        print("Issue id is "+dr_dict['flaw']['@issueid'])
        print("Module is "+dr_dict['flaw']['@module'])
        print("Type is "+dr_dict['flaw']['@type'])
        print("Description is "+dr_dict['flaw']['@description'])
        print("Note is "+dr_dict['flaw']['@note'])
        print("CWE id is "+dr_dict['flaw']['@cweid'])
        print("Remediation Effort is " + dr_dict['flaw']['@remediationeffort'])
        print("Exploit Level is " + dr_dict['flaw']['@exploitLevel'])
        print("Category id is " + dr_dict['flaw']['@categoryid'])
        print("PCI related is " + dr_dict['flaw']['@pcirelated'])
        print("Date of first occurrence is " + dr_dict['flaw']['@date_first_occurrence'])
        print("Remediation Status is " + dr_dict['flaw']['@remediation_status'])
        print("cia impact is " + dr_dict['flaw']['@cia_impact'])
        print("Grace Period expirs on " + dr_dict['flaw']['@grace_period_expires'])
        print("Affects policy compliance " + dr_dict['flaw']['@affects_policy_compliance'])
        print("Mitigation status " + dr_dict['flaw']['@mitigation_status'])
        print("Mitigation status description " + dr_dict['flaw']['@mitigation_status_desc'])
        print("Source file is " + dr_dict['flaw']['@sourcefile'])
        print("Line number is " + dr_dict['flaw']['@line'])
        print("Source file path is " + dr_dict['flaw']['@sourcefilepath'])
        print("Scope is " + dr_dict['flaw']['@scope'])
        print("Function protoype is " + dr_dict['flaw']['@functionprototype'])
        print("Function relative location is " + dr_dict['flaw']['@functionrelativelocation'])
        # Veracode
        # Flaw(static): OS
        # Command
        # Injection, Webgoat_Legacy
        # 2016 - 0
        # 9 - 21 - 19: 39:14, 2016 - 0
        # 9 - 21 - 19: 39:14, Flaw
        # 29
        summarystr = "Veracode Flaw: "+str(dr_dict['flaw']['@categoryname'])+" Flaw "+str(dr_dict['flaw']['@issueid'])
        #CWE: 78 Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')
        #
        #Module: WebGoat-6.0.1.war
        #
        #Source: Exec.java:107
        #
        #Attack Vector: java.lang.Runtime.exec
        #
        #Description: This call to java.lang.Runtime.exec() contains a command injection flaw. The argument to the function is constructed using user-supplied input. If an attacker is allowed to specify all or part of the command, it may be possible to execute commands on the server with the privileges of the executing process. The level of exposure depends on the effectiveness of input validation routines, if any. The first argument to exec() contains tainted data from the variable command. The tainted data originated from an earlier call to javax.servlet.servletrequest.getparametervalues.
        #
        #Validate all user-supplied input to ensure that it conforms to the expected format, using centralized data validation routines when possible. When using black lists, be sure that the sanitizing routine performs a sufficient number of iterations to remove all instances of disallowed characters. Most APIs that execute system commands also have a "safe" version of the method that takes an array of strings as input rather than a single string, which protects against some forms of command injection.
        #
        #
        #
        #References: CWE OWASP WASC
        descstr = "CWE: "+str(dr_dict['flaw']['@cweid'])+" "+str(dr_dict['flaw']['@categoryname'])+"\n\nModule: "+str(dr_dict['flaw']['@module'])+"\n\nSource: "+\
                  str(dr_dict['flaw']['@sourcefile'])+":"+str(dr_dict['flaw']['@line'])+"\n\nAttack Vector: "+str(dr_dict['flaw']['@type'])+"\n\nDescription: "+\
                  str(dr_dict['flaw']['@description'])
        new_issue = auth_jira.create_issue(project=config["jira_project"], summary=summarystr,
                                       description=descstr, issuetype={'name': 'Bug'})
                                           #print(dr_dict)
        #new_issue = auth_jira.create_issue(project=config["jira_project"], summary='New issue from jira-python',
        #                               description=str(issue[0:50]), issuetype={'name': 'Story'})

    def execute(self, api, activity, config):
        print("")
        print("Executing results handler SynchroniseJIRA with:")
        for key, value in config.items():
            print("  " + key + " = " + str(value))
        # By default, the client will connect to a JIRA instance started from the Atlassian Plugin SDK
        # (see https://developer.atlassian.com/display/DOCS/Installing+the+Atlassian+Plugin+SDK for details).
        # Override this with the options parameter.
        # We should come up with at better way to get/store the Jira creds
        auth_jira = JIRA(auth=(config["jira_user"], config["jira_password"]),server=config["jira_base_url"])
        #temporarily hardcode the build_id
        activity["build_id"] = "2931860"
        print("activity_build_id: "+activity["build_id"])
        #print(api.get_build_list(activity["app_id"]))
        #print(api.get_build_info(activity["app_id"],activity["build_id"]))
        #print(api.get_detailed_report(activity["build_id"]))
        wait_so_far = 0
        while wait_so_far <= 300:
            if ("No report available") in (str(api.get_detailed_report(activity["build_id"]))):
                print("No report available yet waiting.  Waited "+str(wait_so_far)+" seconds so far\n")
                wait_so_far += 60
                time.sleep(60)
            else:
                break
        # Get all projects viewable by anonymous users.
        #projects = auth_jira.projects()
        # Sort available project keys, then return the second, third, and fourth keys.
        #keys: List[Any] = sorted([project.key for project in projects])
        #print(keys)
        #print(projects)
        # Get and process the issues.
        # First get the detailed report, then convert to a string and look for the flaws
        # Note: later this could be optimized to use a dict maybe to find the static, dynamic, sca, manual flaws separately
        #
        detailed_report = api.get_detailed_report(activity["build_id"])
        strdr = str(detailed_report)
        #get the positions of the flaw starting points
        starts = [match.start() for match in re.finditer(re.escape("<flaw severity"), strdr)]
        for index in starts:
            # for each one look for the end of the flaw
            end = strdr.find("><", index, len(strdr))
            issue = strdr[index:(end+1)]
            # now process the flaw to create an issue
            self.process_issue(self, auth_jira, config, issue)
            #for testing break after one
            #break

        return False

