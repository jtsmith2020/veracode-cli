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
        """ configure """
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

    def start(self, args, config, api):
        print("Service: Static")
        print("Command: Start")
        branch_type = None
        for segment in config:
            if re.match("^"+segment["branch_pattern"]+"$", str(args.branch)):
                """ This is the config to use... """
                branch_type = segment
                break
        if branch_type is None:
            return "No Static Scan Configuration found"

        """ Is this a sandbox scan? """
        sandbox_name = None
        sandbox_id = None
        if branch_type["static_config"]["scan_type"] == "sandbox":
            sandbox_name = None
            if branch_type["static_config"]["sandbox_naming"] == "branch":
                sandbox_name = str(args.branch)
            elif branch_type["static_config"]["sandbox_naming"] == "env":
                sandbox_name = os.environ.get("VID")
            elif branch_type["static_config"]["sandbox_naming"] == "param":
                sandbox_name = str(args.sandbox)
            if sandbox_name is None:
                """ we cannot do a sandbox scan without a name """
                return "Unable to generate the name for the sandbox. Start static scan failed"
            """ find the id for the sandbox """
            sandbox_id = api.get_sandbox_id(branch_type["portfolio"]["app_id"], sandbox_name)
            if sandbox_id is None:
                """ try creating the sandbox """
                print("Sandbox with name '" + sandbox_name + "' not found. Trying to create...")
                sandbox_id = api.create_sandbox(branch_type["portfolio"]["app_id"], sandbox_name)
                if sandbox_id is None:
                    """ we cannot do a sandbox scan without an id """
                    print("")
                    return "Unable to create a sandbox with name '" + sandbox_name + "'. Start static scan failed"
            print('Using Sandbox "'+ sandbox_name + '" (sandbox_id="' + sandbox_id + '")')

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
            return "No Valid Scan Name. Start static scan failed"

        print("Creating new Scan with name: " + scan_name)
        build_id = api.create_build(branch_type["portfolio"]["app_id"], scan_name, sandbox_id)
        if build_id.startswith("ERROR"):
            return build_id
        print("  (scan id = " + build_id + ")")

        """ Upload the files """
        print("Uploading Files")
        ds = AntPatternDirectoryScanner(".", branch_type["static_config"]["upload_include_patterns"], branch_type["static_config"]["upload_exclude_patterns"])
        for filename in ds.scan():
            print(" " + filename)
            api.upload_file(branch_type["portfolio"]["app_id"], filename, sandbox_id)

        """ enable AutoScan and lets get going """
        print("Pre-Scan Starting. Auto-Scan is enabled - Full Scan will start automatically.")
        api.begin_prescan(branch_type["portfolio"]["app_id"], "true", sandbox_id)
        return "Scan Started with Auto-Scan Enabled"


    def wait(self, args, config, api):
        match_pattern = args.branch
        if match_pattern is None:
            match_pattern = ".*"
        print("await  functionality not implemented")
        return []


