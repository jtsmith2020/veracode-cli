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


    def add_parser(self, parsers):
        static_parser = parsers.add_parser('static', help='the static service provides access to the Veracode SAST scans (including Policy Scans, Sandbox Scans, DevOps Scans and Greenlight)')
        """ add sub-parsers for each of the commands """
        command_parsers = static_parser.add_subparsers(dest='command', help='Static Service Command description')
        """ start """
        start_parser = command_parsers.add_parser('start', help='start a static scan')
        """ await """
        results_parser = command_parsers.add_parser('results', help='get the results for a static scan. wait for the scan to complete if necessary')
        """ ticket """
        ticket_parser = command_parsers.add_parser('ticket', help='synchronize scan results with a ticketing system')
        """ configure """
        configure_parser = command_parsers.add_parser('configure', help='configure the static config blocks in the veracode.config file')
        """ optional parameters """
        static_parser.add_argument("-n", "--name", type=str, help="the name of the scan")
        static_parser.add_argument("-s", "--sandbox", type=str, help="the name of the sandbox to use (if scan type is sandbox)")

    def execute(self, args, config, api, data):
        logging.debug("static service executed")
        if args.command == "configure":
            return self.configure(args, config, api, data)
        elif args.command == "start":
            return self.start(args, config, api, data)
        elif args.command == "results":
            return self.results(args, config, api, data)
        elif args.command == "ticket":
            return self.ticket(args, config, api, data)
        else:
            print("unknown command: "+ args.command)

    def configure(self, args, config, api):
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


    def get_config(self, args, config, api, create=None):
        branch_type = None
        for segment in config:
            if re.match("^"+segment["branch_pattern"]+"$", str(args.branch)):
                """ This is the config to use... """
                branch_type = segment
                break
        if branch_type is None:
            raise VeracodeError("No Static Scan Configuration found for branch '" + str(args.branch) + "'")

        """ Is this a sandbox scan? """
        sandbox_name = None
        sandbox_id = None
        if branch_type["static_config"]["scan_type"] == "sandbox":
            self.sandbox_name = None
            if branch_type["static_config"]["sandbox_naming"] == "branch":
                self.sandbox_name = str(args.branch)
            elif branch_type["static_config"]["sandbox_naming"] == "env":
                self.sandbox_name = os.environ.get("VID")
            elif branch_type["static_config"]["sandbox_naming"] == "param":
                self.sandbox_name = str(args.sandbox)
            if self.sandbox_name is None:
                """ we cannot do a sandbox scan without a name """
                raise VeracodeError("Unable to generate the name for the sandbox.")
            """ find the id for the sandbox """
            self.sandbox_id = api.get_sandbox_id(branch_type["portfolio"]["app_id"], self.sandbox_name)
            if self.sandbox_id is None:
                if create is None:
                    raise VeracodeError("Unable to find sandbox '" + self.sandbox_name + "'")
                else:
                    """ try creating the sandbox """
                    print("Sandbox with name '" + self.sandbox_name + "' not found. Trying to create...")
                    self.sandbox_id = api.create_sandbox(branch_type["portfolio"]["app_id"], self.sandbox_name)
                    if self.sandbox_id is None:
                        """ we cannot do a sandbox scan without an id """
                        print("")
                        raise VeracodeError("Unable to create a sandbox with name '" + self.sandbox_name + "'")
        """ generate the scan name """
        if branch_type["static_config"]["scan_naming"] == "timestamp":
            self.scan_name = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S UTC]")
        elif branch_type["static_config"]["scan_naming"] == "env":
            self.scan_name = os.environ.get(config["scan_name_env"])
        elif branch_type["static_config"]["scan_naming"] == "param":
            self.scan_name = args.name
        elif branch_type["static_config"]["scan_naming"] == "git":
            """ need to generate a GIT scan name"""
            self.scan_name = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S UTC]")
        else:
            """ no valid scan name """
            raise VeracodeError("No Valid Scan Name. Start static scan failed")
        """ return the config object """
        return branch_type


    def start(self, args, config, api, data):
        if not args.console:
            print("Service: Static")
            print("Command: Start")
            print()
        output = {}
        output["branch"] = args.branch

        """ get the static configuration """
        try:
            static_config = self.get_config(args, config, api, True)
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




    def results(self, args, config, api, data):
        if not args.console:
            print("Service: Static")
            print("Command: Results")
            print()
        output = {}

        """ Was there an error in the previous command? """
        if "error" in data:
            output["error"] = "Error in previous command. Unable to proceed. The error was '" + data.error + "'"
            if not args.console:
                print(output.error)
            return output

        """ Does the branch match the previous command? """
        if data["branch"] != args.branch:
            output["error"] = "Active Branch is not the same as the previous command. Active Branch is '" + args.branch + "' but for the previous command it was '" + data.branch + "'"
            if not args.console:
                print(output.error)
            return output

        try:
            """ get the static configuration """
            static_config = self.get_config(args, config, api)

            if not args.console:
                print("Scan type is '" + static_config["static_config"]["scan_type"] + "'")

            """ What type of scan? """
            if static_config["static_config"]["scan_type"] == "sandbox" or static_config["static_config"]["scan_type"] == "policy":
                """ It's a policy or sandbox scan """
                print("DEBUG: its a policy or sandbox scan")
                """ Do we have a build_id ?"""
                if data["build_id"] is not None:
                    """ wait for the scan results to be ready, up to timeout... """
                    print("time is " +str(int(round(time.time()))))
                    timeout = int(round(time.time())) + static_config["static_config"]["results_timeout"]
                    print("timeout is " +str(timeout))
                    ready = api.results_ready(static_config["portfolio"]["app_id"], data["build_id"], self.sandbox_id)
                    if not args.console:
                        if not ready:
                            print("Results are not ready. Waiting for up to " + str(static_config["static_config"]["results_timeout"]) + " seconds...")
                        else:
                            print("Results are ready")
                    while not ready and timeout > int(round(time.time())):
                        print("sleeping")
                        time.sleep(15)
                        ready = api.results_ready(static_config["portfolio"]["app_id"], data["build_id"], self.sandbox_id)

                    """ are the results ready? """
                    if not ready:
                        output["error"] = "Results were not ready within the timeout."

                    """ download the results as xml and convert to dict """
                    detailed_report_xml = api.get_detailed_report(data["build_id"])
                    output["results"] = xmltodict.parse(detailed_report_xml)
                else:
                    """ It's a policy/sandbox scan and we have no build_id"""
                    data["error"] = "No build_id. Unable to get results"
            elif static_config["static_config"]["scan_type"] == "pipeline":
                """ this is where we would handle results for the pipeline scanner"""

            return output
        except VeracodeError as err:
            output["error"] = str(err)
            return output


