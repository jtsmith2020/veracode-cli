import datetime
import time
import os
from antfs import AntPatternDirectoryScanner
from services.base_service import Service
from helpers.api import VeracodeAPI
import json
import logging
import re

from helpers.exceptions import VeracodeError
from helpers.input import choice
from helpers.input import free_text
from helpers.input import patterns_list

class static(Service):
    def __init__(self):
        self.display_name = "Static Service"
        self.description = "Veracode Static Analysis"
        self.DEBUG = False

    def add_parser(self, parsers):
        static_parser = parsers.add_parser('static', help='the static service provides access to the Veracode SAST scans (including Policy Scans, Sandbox Scans, DevOps Scans and Greenlight)')
        """ add sub-parsers for each of the commands """
        command_parsers = static_parser.add_subparsers(dest='command', help='Static Service Command description')
        """ start """
        start_parser = command_parsers.add_parser('start', help='start a static scan')
        """ await """
        await_parser = command_parsers.add_parser('await', help='wait for a static scan to complete')
        """ skeleton """
        configure_parser = command_parsers.add_parser('configure', help='configure the static config blocks in the veracode.config file')
        """ optional parameters """
        static_parser.add_argument("-n", "--name", type=str, help="the name of the scan")
        static_parser.add_argument("-s", "--sandbox", type=str, help="the name of the sandbox to use (if scan type is sandbox)")

    def execute(self, args, config, api):
        logging.debug("static service executed")
        if args.command == "configure":
            return self.configure(args, config, api)
        elif args.command == "start":
            return self.start(args, config, api)
        elif args.command == "await":
            return self.wait(args, config, api)
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
                branch_type["static_config"]["sandbox_naming"] = choice("Sandbox Naming Convention", branch_type["static_config"]["sandbox_naming"], ["timestamp", "env", "param", "branch"])
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

    def start(self, args, config, api):
        for branch_type in config:
            if re.match("^"+branch_type["branch_pattern"]+"$", str(args.branch)):
                """ This is the config to use... """
                """ generate the scan name """
                scan_name = ""
                if branch_type["static_config"]["scan_naming"] == "timestamp":
                    scan_name = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S UTC]")
                elif branch_type["static_config"]["scan_naming"] == "env":
                    scan_name = os.environ.get(config["scan_name_env"])
                elif branch_type["static_config"]["scan_naming"] == "param":
                    scan_name = args.name
                elif branch_type["static_config"]["scan_naming"] == "git":
                    """ need to generate a GIT scan name"""
                    scan_name = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S UTC]")
                else:
                    """ no valid scan name """
                    logging.error("No Valid Scan Name")

                print("Creating new Scan with name: " + scan_name)
                build_id = api.create_build(branch_type["portfolio"]["app_id"], scan_name)
                if build_id is None:
                    raise VeracodeError("Cannot Create New Build")
                print("  (scan id = " + build_id + ")")

                """ Upload the files """
                print("Uploading Files")
                ds = AntPatternDirectoryScanner(".", branch_type["static_config"]["upload_include_patterns"], branch_type["static_config"]["upload_exclude_patterns"])
                for filename in ds.scan():
                    print(" " + filename)
                    api.upload_file(branch_type["portfolio"]["app_id"], filename)

                """ enable AutoScan and lets get going """
                print("Pre-Scan Starting. Auto-Scan is enabled - Full Scan will start automatically.")
                api.begin_prescan(branch_type["portfolio"]["app_id"], "true")
                return "Scan Started with Auto-Scan Enabled"

    def wait(self, args, config, api):
        match_pattern = args.branch
        if match_pattern is None:
            match_pattern = ".*"
        print("await  functionality not implemented")
        return []


