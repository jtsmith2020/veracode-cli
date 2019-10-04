import datetime
import os
from antfs import AntPatternDirectoryScanner
from services.base_service import Service
from helpers.api import VeracodeAPI
import json

from helpers.exceptions import VeracodeError


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
        skeleton_parser = command_parsers.add_parser('skeleton', help='add a skeleton config block to the veracode.config file')
        """ optional parameters """
        static_parser.add_argument("-n", "--name", type=str, help="the name of the scan")
        static_parser.add_argument("-s", "--sandbox", type=str, help="the name of the sandbox to use (if scan type is sandbox)")

    def execute(self, args, config, api):
        if args.command == "skeleton":
            return self.skeleton(args, config, api)
        elif args.command == "start":
            return self.start(args, config, api)
        elif args.command == "await":
            return self.wait(args, config, api)
        else:
            print("unknown command: "+ args.command)

    def skeleton(self, args, config, api):
        match_pattern = args.branch
        if match_pattern is None:
            match_pattern = ".*"
        create = True
        for segment in config:
            if segment["match_pattern"] == match_pattern:
                branch = segment
                create = False
        if create:
            branch = dict()
            branch["match_pattern"] = match_pattern
            config.append(branch)
        """ add the skeleton config elements """
        skeleton = dict()
        skeleton["scan_type"] = "required: policy|sandbox|devops"
        skeleton["app_id"] = "required for policy or sandbox scan type: <app_id>"
        skeleton["sandbox_naming"] = "required for sandbox scan type: timestamp|env|param|branch"
        skeleton["scan_naming"] = "required for policy or sandbox scan types: timestamp|env|param"
        skeleton["scan_naming_env"] = "required if scan_naming is env: the name of the environment variable to use"
        skeleton["upload_include_patterns"] = []
        skeleton["upload_include_patterns"].append(
            "one or more ant-style patterns to match files that should be uploaded")
        skeleton["upload_exclude_patterns"] = []
        skeleton["upload_exclude_patterns"].append(
            "zero or more ant-style patterns to match files that should be excluded from uploading")
        branch["static"] = skeleton
        """ write the config file """
        with open('veracode.config', 'w') as outfile:
            json.dump(config, outfile, indent=2)
        return json.dumps(config, indent=2)

    def start(self, args, config, api):
        match_pattern = args.branch
        if match_pattern is None:
            match_pattern = ".*"
        """ generate the scan name """
        scan_name = ""
        if config.scan_naming == "timestamp":
            scan_name = datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S UTC]")
        elif config["scan_naming"] == "env":
            scan_name = os.environ.get(config["scan_name_env"])
        elif config["scan_naming"] == "param":
            scan_name = args.name

        if "" == scan_name:
            print("Invalid scan name: must not be empty")
            raise VeracodeError("Invalid Scan Name")

        print("Creating new Scan with name: " + scan_name)
        build_id = api.create_build(config["portfolio"]["app_id"], scan_name)
        if build_id is None:
            raise VeracodeError("Cannot Create New Build")
        print("  (scan id = " + build_id + ")")

        """ Upload the files """
        print("Uploading Files")
        ds = AntPatternDirectoryScanner(".", config["upload_include_pattern"], config["upload_exclude_pattern"])
        for filename in ds.scan():
            print(" " + filename)
            api.upload_file(activity["app_id"], filename)

        start_time = datetime.now()
        """ Should we enable Auto-Scan ? """
        if config["module_include_pattern"] is None:
            """ Yes - enable AutoScan and lets get going """
            print("Pre-Scan Starting. Auto-Scan is enabled - Full Scan will start automatically.")
            api.begin_prescan(activity["app_id"], "true")
        else:
            """ No - disable auto-scan and get started  """
            api.begin_prescan(activity["app_id"], "false")
            """ Now we wait for prescan to complete - check every 30 seconds """
            modules = api.get_modules(activity["app_id"], build_id=activity["build_id"])
            while modules is None:
                print("Waiting for Pre-Scan to complete...")
                time.sleep(30)
                modules = api.get_modules(activity["app_id"], build_id=activity["build_id"])
            print("Pre-Scan Complete")
            print("Full Scan Starting")
            if config["module_include_pattern"] is not None:
                """ now we need to select the modules and start the scan... """
                print("module selection code not writen")

                """ XXXX NOT DONE YET XXXX  """

            print("Full Scan Running")

    def wait(self, args, config, api):
        match_pattern = args.branch
        if match_pattern is None:
            match_pattern = ".*"
        print("await  functionality not implemented")
        return []


