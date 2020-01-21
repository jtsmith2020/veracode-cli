from .base_service import Service
import logging
import xmltodict
import datetime
import os
import re
import pprint
import json


class ticketing(Service):
    def __init__(self):
        self.display_name = "Ticketing Service"
        self.description = "Veracode Ticketing Integration Service"
        self.DEBUG = False
        self.ticket_actions = {"application": {"type": "create", "flaws": []},
                               "severities": [],
                               "categories": [],
                               "cwes": [],
                               "flaws": []}

    def add_parser(self, parsers):
        ticketing_parser = parsers.add_parser('ticketing', help='the ticketing service...')
        """ add sub-parsers for each of the commands """
        command_parsers = ticketing_parser.add_subparsers(dest='command', help='Ticketing Service Command description')
        """ synchronize """
        sync_parser = command_parsers.add_parser('synchronize', help='Synchronise the latest scan results with the Ticketing System')
        """ configure """
        configure_parser = command_parsers.add_parser('configure', help='configure the ticketing config blocks in the veracode.config file')
        """ optional parameters """
        ticketing_parser.add_argument("-b", "--branch", type=str, help="The branch name used to select configuration settings")


    def execute(self, args, config, api):
        logging.debug("ticketing service executed")
        if args.command == "configure":
            return self.configure(args, config, api)
        elif args.command == "synchronise":
            return self.synchronise(args, config, api)
        else:
            print("unknown command: "+ args.command)


    def configure(self, args, config, api):
        logging.debug("configure called")

    def synchronise(self, args, config, api):
        print("Service: Ticketing")
        print("Command: Synchronize")
        branch_type = None
        for segment in config:
            if re.match("^"+segment["branch_pattern"]+"$", str(args.branch)):
                """ This is the config to use... """
                branch_type = segment
                break
        if branch_type is None:
            return "No Static Scan Configuration found for branch '" + str(args.branch) + "'"


        """ Is this a sandbox scan branch ? """
        sandbox_name = None
        sandbox_id = None
        if branch_type["static_config"]["scan_type"] == "sandbox":
            sandbox_name = None
            if branch_type["static_config"]["sandbox_naming"] == "branch":
                sandbox_name = str(args.branch)
            elif the_config["static_config"]["sandbox_naming"] == "env":
                sandbox_name = os.environ.get(the_config["static_config"]["sandbox_naming_env"])
            elif the_config["static_config"]["sandbox_naming"] == "param":
                sandbox_name = str(args.sandbox)
            if sandbox_name is None:
                """ we cannot do a sandbox scan without a name """
                print("Unable to generate the name for the sandbox.")
                return "start static scan failed"
            """ find the id for the sandbox """
            sandbox_id = api.get_sandbox_id(the_config["portfolio"]["app_id"], sandbox_name)
            if sandbox_id is None:
                """ try creating the sandbox """
                print("Sandbox not found. Trying to create...")
                sandbox_id = api.create_sandbox(the_config["portfolio"]["app_id"], sandbox_name)
                if sandbox_id is None:
                    """ we cannot do a sandbox scan without an id """
                    print("Unable to generate the name for the sandbox.")
                    return "Unabkle to find the sandbox_id"
            print('Using Sandbox "'+ sandbox_name + '" (sandbox_id="' + sandbox_id + '")')

        """ download the detailed report and convert to Dict """
        build_id = api.get_latest_build_id(the_config["portfolio"]["app_id"], sandbox_id)
        detailed_report_xml = api.get_detailed_report(build_id)
        results = xmltodict.parse(detailed_report_xml)
        """ DEBUG: output the results to a file """
        with open('results.json', 'w') as outfile:
            json.dump(results, outfile, indent=2)
        """ synchronise the tickets """
        #self.sync_results(self, the_config, results)
        return "Complete"

    def parse_results(self, config, res, severity=None, category=None, cwe=None, flaw=None):
        if flaw is not None:
            """ is this a flaw that needs to be synched? """

            """ build the flaw dictionary? """
            the_flaw = self.build_flaw_dictionary(flaw)
            """ update the application action """
            self.ticket_actions["application"]["app_name"] = res["detailedreport"]["@app_name"]
            self.ticket_actions["application"]["app_id"] = res["detailedreport"]["@app_id"]
            self.ticket_actions["application"]["sandbox_name"] = res["detailedreport"]["@sandbox_name"]
            self.ticket_actions["application"]["sandbox_id"] = res["detailedreport"]["@sandbox_id"]
            self.ticket_actions["application"]["policy_name"] = res["detailedreport"]["@app_name"]
            self.ticket_actions["application"]["scan_name"] = res["detailedreport"]["@version"]
            self.ticket_actions["application"]["flaws"].append(the_flaw)
            """ update the severity action """
            if severity["@level"] in self.ticket_actions["severities"]:
                """ add the flaw """
                self.ticket_actions["severities"]["flaws"].append(the_flaw)
            else:
                """ create the severity action """
                """ add the flaw """
            """ update the category action """
            if category["@categoryname"] in self.ticket_actions["categories"]:
                """ add the flaw """
                self.ticket_actions["categories"]["flaws"].append(the_flaw)
            else:
                """ create the category action """
                """ add the flaw """
            """ update the cwe action """
            if category["@cwename"] in self.ticket_actions["cwes"]:
                """ add the flaw """
                self.ticket_actions["cwes"]["flaws"].append(the_flaw)
            else:
                """ create the cwe action """
                """ add the flaw """
            """ add the flaw action """
            """ add the flaw """



        elif cwe is not None:
            """ parse the cwe """
            for k, v in cwe:
                if k == "staticflaws":
                    for f in v["flaw"]:
                        """ SHOULD WE BE DECIDING WHETHER OR NOT TO TICKET THE FLAW HERE? 
                            COULD BE BASED ON POLICY AFFECTING OR NEW   """
                        self.parse_results(res, severity, category, cwe, f)
        elif category is not None:
            """ parse the category """
            for k, v in  category:
                if k == "cwe":
                    self.parse_results(res, severity, category, v)
        elif severity is not None:
            """ parse the severity """
            for cat in severity["category"]:
                self.parse_results(res, severity, cat)
        else:
            """ parse the root """
            for k, v in res.iteritems():
                if k == "severity":
                    """ this is the severities """
                    for severity in v:
                        self.parse_results(res, severity)




