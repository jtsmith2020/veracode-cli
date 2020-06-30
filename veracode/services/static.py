import datetime
import time
import os
from antfs import AntPatternDirectoryScanner
from services.base_service import Service
from helpers.api import VeracodeAPI
import json
import logging
import re
import time
import xmltodict
import traceback
import sys

from helpers.exceptions import VeracodeError
from helpers.input import choice
from helpers.input import free_text
from helpers.input import patterns_list

class static(Service):
    def __init__(self):
        self.display_name = "Static Service"
        self.description = "Veracode Static Analysis"
        self.DEBUG = False
        self.sandbox_name = None
        self.sandbox_id = None
        self.scan_name = None
        self.parsed_results = {}
        self.console = False


    def add_parser(self, parsers):
        static_parser = parsers.add_parser('static', help='the static service provides access to the Veracode SAST scans (including Policy Scans, Sandbox Scans, DevOps Scans and Greenlight)')
        """ add sub-parsers for each of the commands """
        command_parsers = static_parser.add_subparsers(dest='command', help='Static Service Command description')
        """ start """
        start_parser = command_parsers.add_parser('start', help='start a static scan')
        """ results """
        results_parser = command_parsers.add_parser('results', help='get the results for a static scan. wait for the scan to complete if necessary')
        """ decide """
        decide_parser = command_parsers.add_parser('decide', help='make a decision about the results of a scan')
        """ configure """
        configure_parser = command_parsers.add_parser('configure', help='configure the static config blocks in the veracode.config file')
        """ optional parameters """
        static_parser.add_argument("-n", "--name", type=str, help="the name of the scan")
        static_parser.add_argument("-s", "--sandbox", type=str, help="the name of the sandbox to use (if scan type is sandbox)")
        static_parser.add_argument("-i", "--id", type=str, help="the build ID of the scan to use.")

    def execute(self, args, config, api, context):
        logging.debug("static service executed")
        self.console = args.console
        if args.command == "configure":
            return self.configure(args, config, api, context)
        elif args.command == "start":
            return self.start(args, config, api, context)
        elif args.command == "results":
            return self.results(args, config, api, context)
        elif args.command == "decide":
            return self.decide(args, config, api, context)
        else:
            output_data = {}
            output_data["error"] = "Unknown Command provided to the Static Service (" + args.command + ")"
            return output_data

    def configure(self, args, config, api, context):
        logging.debug("configure called")
        """ for each branch type... """
        for branch_type in config:
            print("")
            print("Configure the Static Service for branches which match \"" + branch_type["branch_pattern"] + "\"")

            branch_type["static_config"]["scan_type"] = choice("Type of scan", branch_type["static_config"]["scan_type"], ["policy", "sandbox"])
            if branch_type["static_config"]["scan_type"] == "sandbox":
                branch_type["static_config"]["sandbox_naming"] = choice("Sandbox Naming Convention", branch_type["static_config"]["sandbox_naming"], ["env", "param", "branch"])
                if branch_type["static_config"]["sandbox_naming"] == "env":
                    branch_type["static_config"]["sandbox_naming_env"] = free_text("Environment Variable to use for Sandbox Name", branch_type["static_config"]["sandbox_naming_env"])
            branch_type["static_config"]["scan_naming"] = choice("Scan Naming Convention", branch_type["static_config"]["scan_naming"], ["timestamp", "env", "param", "git"])
            if branch_type["static_config"]["scan_naming"] == "env":
                branch_type["static_config"]["scan_naming_env"] = free_text("Environment Variable to use for Scan Name", branch_type["static_config"]["scan_naming_env"])
            branch_type["static_config"]["upload_include_patterns"] = patterns_list("Upload Include Patterns", branch_type["static_config"]["upload_include_patterns"])
            branch_type["static_config"]["upload_exclude_patterns"] = patterns_list("Upload Exclude Patterns", branch_type["static_config"]["upload_exclude_patterns"])

        """ write the config file """
        with open('veracode.config', 'w') as outfile:
            json.dump(config, outfile, indent=2)
        return json.dumps(config, indent=2)


    def validate_config(self, args, config, api, create=None):

        """ Is this a sandbox scan? """
        sandbox_name = None
        sandbox_id = None
        if config["static_config"]["scan_type"] == "sandbox":
            self.sandbox_name = None
            if config["static_config"]["sandbox_naming"] == "branch":
                self.sandbox_name = str(args.branch)
            elif config["static_config"]["sandbox_naming"] == "env":
                self.sandbox_name = os.environ.get("VID")
            elif config["static_config"]["sandbox_naming"] == "param":
                self.sandbox_name = str(args.sandbox)
            if self.sandbox_name is None:
                """ we cannot do a sandbox scan without a name """
                raise VeracodeError("Unable to generate the name for the sandbox.")
            """ find the id for the sandbox """
            self.sandbox_id = api.get_sandbox_id(config["portfolio"]["app_id"], self.sandbox_name)
            if self.sandbox_id is None:
                if create is None:
                    raise VeracodeError("Unable to find sandbox '" + self.sandbox_name + "'")
                else:
                    """ try creating the sandbox """
                    print("Sandbox with name '" + self.sandbox_name + "' not found. Trying to create...")
                    self.sandbox_id = api.create_sandbox(config["portfolio"]["app_id"], self.sandbox_name)
                    if self.sandbox_id is None:
                        """ we cannot do a sandbox scan without an id """
                        print("")
                        raise VeracodeError("Unable to create a sandbox with name '" + self.sandbox_name + "'")
        """ generate the scan name """
        if config["static_config"]["scan_naming"] == "timestamp":
            self.scan_name = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S UTC]")
        elif config["static_config"]["scan_naming"] == "env":
            self.scan_name = os.environ.get(config["scan_name_env"])
        elif config["static_config"]["scan_naming"] == "param":
            self.scan_name = args.name
        elif config["static_config"]["scan_naming"] == "git":
            """ need to generate a GIT scan name"""
            self.scan_name = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S UTC]")
        else:
            """ no valid scan name """
            raise VeracodeError("No Valid Scan Name. Start static scan failed")
        """ return the config object """
        return config


    def start(self, args, config, api, context):
        output = {}
        output["branch"] = args.branch

        """ get the static configuration """
        try:
            static_config = self.validate_config(args, config, api, True)
            if not args.console:
                print("Creating new Scan with name: " + self.scan_name)
            output["scan_name"] = self.scan_name
            output["sandbox_id"] = self.sandbox_id
            build_id = api.create_build(static_config["portfolio"]["app_id"], self.scan_name, self.sandbox_id)
            output["build_id"] = build_id
            if not args.console:
                print("  (build_id = " + build_id + ")")

            """ Upload the files """
            if not args.console:
                print("Uploading Files")
            ds = AntPatternDirectoryScanner(".", static_config["static_config"]["upload_include_patterns"],
                                            static_config["static_config"]["upload_exclude_patterns"])
            for filename in ds.scan():
                if not args.console:
                    print("  " + filename)
                api.upload_file(static_config["portfolio"]["app_id"], filename, self.sandbox_id)

            """ enable AutoScan and lets get going """
            if not args.console:
                print("Pre-Scan Starting. Auto-Scan is enabled - Full Scan will start automatically.")
            api.begin_prescan(static_config["portfolio"]["app_id"], "true", self.sandbox_id)
            if not args.console:
                print("Scan Started with Auto-Scan Enabled")
            return output
        except VeracodeError as err:
            output["error"] = str(err)
            return output
        except:
            output["error"] = "Unexpected Exception #005 (static.py) : " + str(sys.exc_info()[0])
            return output




    def results(self, args, config, api, context):
        output = {}

        """ Does the branch match the previous command? """
        if "branch" in context and context["branch"] != args.branch:
            output["error"] = f'Active Branch does not match with veracode-cli.context. Active Branch is {args.branch} but context.branch is {context.branch}'
            if not args.console:
                print(f'{"error":10} : {output["error"]}')
            return output

        try:
            """ validate the static configuration """
            static_config = self.validate_config(args, config, api)

            if not args.console:
                print(f'{"info":10} : Scan type is {static_config["static_config"]["scan_type"]}')

            """ What type of scan? """
            if static_config["static_config"]["scan_type"] == "sandbox" or static_config["static_config"]["scan_type"] == "policy":
                """ It's a policy or sandbox scan """
                sandbox_id = None
                if "sandbox_id" in context and context["sandbox_id"] is not None:
                    sandbox_id = context["sandbox_id"]
                build_id = None
                """ Do we have a build_id  in the context? """
                if "build_id" in context and context["build_id"] is not None:
                    """ don't think anything needs to happen here. """
                    build_id = context["build_id"]
                elif args.id is not None:
                    """ don't think anything needs to happen here either. """
                    build_id = args.id
                else:
                    """ need to find the latest build_id for the type of scan"""
                    if static_config["static_config"]["scan_type"] == "sandbox":
                        if sandbox_id is not None:
                            if not args.console:
                                print(f'{"info":10} : Getting latest build_id (app_id={static_config["portfolio"]["app_id"]}, sandbox_id={sandbox_id})')
                            build_id = api.get_latest_build_id(static_config["portfolio"]["app_id"], sandbox_id)
                        else:
                            """ error - no sandbox id """
                            if not args.console:
                                print(f'{"error":10} : Scan type is sandbox but no sandbox ID could be found {str(err)}')
                            output["error"] = str(err)

                    else:
                        if not args.console:
                            print(f'{"info":10} : Getting latest build_id (app_id={static_config["portfolio"]["app_id"]})')
                            build_id = api.get_latest_build_id(static_config["portfolio"]["app_id"])


                if build_id is None:
                    """ Problem, cannot proceed without a build_id """


                """ wait for the scan results to be ready, up to timeout... """
                print(f'{"info":10} : Current time is {str(int(round(time.time())))}')
                timeout = int(round(time.time())) + static_config["static_config"]["results_timeout"]
                print(f'{"info":10} : Timeout is {str(timeout)}')
                ready = api.results_ready(static_config["portfolio"]["app_id"], build_id, self.sandbox_id)
                if not args.console:
                    if not ready:
                        print(f'{"info":10} : Results not ready. Try again in 15s...')
                    else:
                        print(f'{"info":10} : Results are ready')
                while not ready and timeout > int(round(time.time())):
                    print("sleeping")
                    time.sleep(15)
                    ready = api.results_ready(static_config["portfolio"]["app_id"], context["build_id"], self.sandbox_id)

                """ are the results ready? """
                if not ready:
                    """ We have timed out and the results aren't ready """
                    output["error"] = "Results were not ready within the timeout."
                else:
                    """ download the results as xml and convert to dict """
                    detailed_report_xml = api.get_detailed_report(build_id)
                    raw_results = xmltodict.parse(detailed_report_xml)["detailedreport"]
                    self.parse_results(config, raw_results)
                    output["results"] = self.parsed_results
                    # output["results"] = raw_results

            elif static_config["static_config"]["scan_type"] == "pipeline":
                """ this is where we would handle results for the pipeline scanner"""

            return output
        except VeracodeError as err:
            if not args.console:
                print(f'{"exception":10} : Unexpected Exception (Static.py) #001 : {str(err)}')
            output["error"] = str(err)
        except:
            if not args.console:
                print(f'{"exception":10} : Unexpected Exception (Static.py) #001 : {str(sys.exc_info()[0])}')
            output["error"] = f'Unexpected Exception (Static.py) #001 : {sys.exc_info()[0]}'
            traceback.print_exc()
        finally:
            return output


    def decide(self, args, config, api, context):
        output = {}

        """ Does the branch match the previous command? """
        if "branch" in context and context["branch"] != args.branch:
            output["error"] = f'Active Branch does not match with veracode-cli.context. Active Branch is {args.branch} but context.branch is {context.branch}'
            if not args.console:
                print(f'{"error":10} : {output["error"]}')
            return output

        """ Do we have any results to work with in the context """
        if "results" not in context or context["results"] is None:
            output["error"] = f'No results found in veracode-cli.context'
            if not args.console:
                print(f'{"error":10} : {output["error"]}')
            return output

        """ Need to do some kind of decision making. If the decision is positive then
            we can just return. If the decision is Negative then we put something into
            the error field of the output  """
        output = context
        return output


    def parse_results(self, config, res, severity=None, category=None, cwe=None, flaw=None):
        if flaw is not None:
            if not self.console:
                print(f'{"info":10} : parsing flaw {flaw["@issueid"]}')
            """ create the flaw dictionary """
            the_flaw = {}
            the_flaw["severity"] = flaw["@severity"]
            the_flaw["module"] = flaw["@module"]
            the_flaw["type"] = flaw["@type"]
            the_flaw["description"] = self.parse_text2(flaw["@description"])
            the_flaw["recommendations"] = self.parse_text3(flaw["@description"])
            the_flaw["note"] = flaw["@note"]
            the_flaw["cwe_id"] = flaw["@cweid"]
            the_flaw["remediation_effort"] = flaw["@remediationeffort"]
            the_flaw["exploit_level"] = flaw["@exploitLevel"]
            the_flaw["category_id"] = flaw["@categoryid"]
            the_flaw["pci_related"] = flaw["@pcirelated"]
            the_flaw["date_first_occurrence"] = flaw["@date_first_occurrence"]
            the_flaw["remediation_status"] = flaw["@remediation_status"]
            the_flaw["cia_impact"] = flaw["@cia_impact"]
            the_flaw["grace_period_expires"] = flaw["@grace_period_expires"]
            the_flaw["affects_policy_compliance"] = flaw["@affects_policy_compliance"]
            the_flaw["mitigation_status"] = flaw["@mitigation_status"]
            the_flaw["mitigation_status_desc"] = flaw["@mitigation_status_desc"]
            the_flaw["sourcefile"] = flaw["@sourcefile"]
            the_flaw["sourcefile_path"] = flaw["@sourcefilepath"]
            the_flaw["scope"] = flaw["@scope"]
            the_flaw["function_prototype"] = flaw["@functionprototype"]
            the_flaw["function_relative_location"] = flaw["@functionrelativelocation"]
            if "annotations" in flaw:
                if "annotation" in flaw["annotations"]:
                    the_flaw["comments"] = []
                    if type(flaw["annotations"]["annotation"]) is list:
                        for an in flaw["annotations"]["annotation"]:
                            comment = {}
                            comment["date"] = an["@date"]
                            comment["description"] = an["@description"]
                            comment["user"] = an["@user"]
                            the_flaw["comments"].insert(0, comment)
                    else:
                        comment = {}
                        comment["date"] = flaw["annotations"]["annotation"]["@date"]
                        comment["description"] = flaw["annotations"]["annotation"]["@description"]
                        comment["user"] = flaw["annotations"]["annotation"]["@user"]
                        the_flaw["comments"].insert(0, comment)
            if "mitigations" in flaw:
                if "mitigation" in flaw["mitigations"]:
                    the_flaw["mitigations"] = []
                    if type(flaw["mitigations"]["mitigation"]) is list:
                        for an in flaw["mitigations"]["mitigation"]:
                            comment = {}
                            comment["action"] = an["@action"]
                            comment["date"] = an["@date"]
                            comment["description"] = an["@description"]
                            comment["user"] = an["@user"]
                            the_flaw["mitigations"].insert(0, comment)
                    else:
                        comment = {}
                        comment["action"] = flaw["mitigations"]["mitigation"]["@action"]
                        comment["date"] = flaw["mitigations"]["mitigation"]["@date"]
                        comment["description"] = flaw["mitigations"]["mitigation"]["@description"]
                        comment["user"] = flaw["mitigations"]["mitigation"]["@user"]
                        the_flaw["mitigations"].insert(0, comment)

            """ update the severity results """
            if "flaws" not in self.parsed_results["severities"][severity["@level"]]:
                self.parsed_results["severities"][severity["@level"]]["flaws"] = []
            self.parsed_results["severities"][severity["@level"]]["flaws"].append(flaw["@issueid"])
            self.parsed_results["severities"][severity["@level"]]["count"] += 1
            """ update the category results """
            if "flaws" not in self.parsed_results["categories"][category["@categoryid"]]:
                self.parsed_results["categories"][category["@categoryid"]]["flaws"] = []
            self.parsed_results["categories"][category["@categoryid"]]["flaws"].append(flaw["@issueid"])
            self.parsed_results["categories"][category["@categoryid"]]["count"] += 1
            """ Update the cwe results """
            if "flaws" not in self.parsed_results["cwes"][cwe["@cweid"]]:
                self.parsed_results["cwes"][cwe["@cweid"]]["flaws"] = []
            self.parsed_results["cwes"][cwe["@cweid"]]["flaws"].append(flaw["@issueid"])
            self.parsed_results["cwes"][cwe["@cweid"]]["count"] += 1
            """ add the flaw to the flaws results """
            if "flaws" not in self.parsed_results:
                self.parsed_results["flaws"] = {}
            self.parsed_results["flaws"][flaw["@issueid"]] = the_flaw

        elif cwe is not None:
            if not self.console:
                print(f'{"info":10} : parsing cwe')
            """ add this cwe to the parsed results"""
            if "cwes" not in self.parsed_results:
                self.parsed_results["cwes"] = {}
            if cwe["@cweid"] not in self.parsed_results["cwes"]:
                self.parsed_results["cwes"][cwe["@cweid"]] = {}
                self.parsed_results["cwes"][cwe["@cweid"]]["name"] = cwe["@cwename"]
                if "@pcirelated" in cwe:
                    self.parsed_results["cwes"][cwe["@cweid"]]["pci_related"] = cwe["@pcirelated"]
                else:
                    self.parsed_results["cwes"][cwe["@cweid"]]["pci_related"] = None
                if "@owasp" in cwe:
                    self.parsed_results["cwes"][cwe["@cweid"]]["owasp"] = cwe["@owasp"]
                else:
                    self.parsed_results["cwes"][cwe["@cweid"]]["owasp"] = None
                if "@owasp2013" in cwe:
                    self.parsed_results["cwes"][cwe["@cweid"]]["owasp2013"] = cwe["@owasp2013"]
                else:
                    self.parsed_results["cwes"][cwe["@cweid"]]["owasp2013"] = None
                if "@sans" in cwe:
                    self.parsed_results["cwes"][cwe["@cweid"]]["sans"] = cwe["@sans"]
                else:
                    self.parsed_results["cwes"][cwe["@cweid"]]["sans"] = None
                self.parsed_results["cwes"][cwe["@cweid"]]["description"] = self.parse_text1(cwe["description"])
                self.parsed_results["cwes"][cwe["@cweid"]]["count"] = 0
            """ parse the cwe """
            for k, v in cwe.items():
                if k == "staticflaws":
                    if type(v["flaw"]) is list:
                        for f in v["flaw"]:
                            if not self.console:
                                print(f'{"info":10} : found flaw (and it is a list)')
                            self.parse_results(config, res, severity, category, cwe, f)
                    else:
                        if not self.console:
                            print(f'{"info":10} : found flaw')
                        self.parse_results(config, res, severity, category, cwe, v["flaw"])

        elif category is not None:
            if not self.console:
                print(f'{"info":10} : parsing category {category["@categoryname"]} ({category["@categoryid"]})')
            """ add this category to the p[arsed results """
            if "categories" not in self.parsed_results:
                self.parsed_results["categories"] = {}
            if category["@categoryid"] not in self.parsed_results["categories"]:
                self.parsed_results["categories"][category["@categoryid"]] = {}
                self.parsed_results["categories"][category["@categoryid"]]["name"] = category["@categoryname"]
                self.parsed_results["categories"][category["@categoryid"]]["pci_related"] = category["@pcirelated"]
                self.parsed_results["categories"][category["@categoryid"]]["description"] = self.parse_text1(category["desc"])
                self.parsed_results["categories"][category["@categoryid"]]["recommendations"] = self.parse_text1(category["recommendations"])
                self.parsed_results["categories"][category["@categoryid"]]["count"] = 0
            """ parse the category """
            for k, v in category.items():
                if k == "cwe":
                    if type(v) is list:
                        if not self.console:
                            print(f'{"info":10} : found cwe (and it is a list)')
                        for x in v:
                            self.parse_results(config, res, severity, category, x)
                    else:
                        if not self.console:
                            print(f'{"info":10} : found cwe')
                        self.parse_results(config, res, severity, category, v)
        elif severity is not None:
            if not self.console:
                print(f'{"info":10} : parsing severity {severity["@level"]}')
            """ add this severity to the parsed results """
            if "severities" not in self.parsed_results:
                self.parsed_results["severities"] = {}
            if severity["@level"] not in self.parsed_results["severities"]:
                self.parsed_results["severities"][severity["@level"]] = {}
                if severity["@level"] == "5":
                    self.parsed_results["severities"][severity["@level"]]["name"] = "Very High"
                elif severity["@level"] == "4":
                    self.parsed_results["severities"][severity["@level"]]["name"] = "High"
                elif severity["@level"] == "3":
                    self.parsed_results["severities"][severity["@level"]]["name"] = "Medium"
                elif severity["@level"] == "2":
                    self.parsed_results["severities"][severity["@level"]]["name"] = "Low"
                elif severity["@level"] == "1":
                    self.parsed_results["severities"][severity["@level"]]["name"] = "Very Low"
                elif severity["@level"] == "0":
                    self.parsed_results["severities"][severity["@level"]]["name"] = "Information"
                self.parsed_results["severities"][severity["@level"]]["count"] = 0

            """ parse the severity """
            if "category" in severity:
                if "@categoryid" in severity["category"]:
                    if not self.console:
                        print(f'{"info":10} : found category "{severity["category"]["@categoryname"]}" as the only category')
                        self.parse_results(config, res, severity, severity["category"])
                    else:
                        for cat in severity["category"]:
                            if not self.console:
                                print(f'{"info":10} : found category "{cat["@categoryname"]}"')
                            self.parse_results(config, res, severity, cat)
        else:
            if not self.console:
                print(f'{"info":10} : parsing root')
            self.parsed_results["scan"] = {}
            self.parsed_results["scan"]["app_name"] = res["@app_name"]
            self.parsed_results["scan"]["app_id"] = res["@app_id"]
            self.parsed_results["scan"]["sandbox_id"] = res["@sandbox_id"]
            self.parsed_results["scan"]["policy_name"] = res["@app_name"]
            self.parsed_results["scan"]["scan_name"] = res["@version"]
            self.parsed_results["scan"]["policy_compliance"] = res["@policy_compliance_status"]

            """ parse the root """
            for k, v in res.items():
                if k == "severity":
                    if not self.console:
                        print(f'{"info":10} : found severities')
                    """ this is the severities """
                    for severity in v:
                        self.parse_results(config, res, severity)

    def parse_text1(self, input):
        return input

    def parse_text2(self, input):
        return input

    def parse_text3(self, input):
        return input
