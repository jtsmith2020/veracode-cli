from helpers.base_scanner import Scanner
from helpers.exceptions import VeracodeError
from antfs import AntPatternDirectoryScanner
from datetime import datetime
import os

class SastPolicyScanner(Scanner):
    def __init__(self):
        self.display_name = "SAST Policy Scan"
        self.description = "Run a Policy Scan using Veracode SAST"
        self.type = type(self).__name__

    def configure(self, api):
        config = dict()
        config["type"] = self.type
        config["display_name"] = self.display_name
        print("    Configuring " + self.display_name)
        print("      Scan Naming Options:")
        print("        0. Use an Environment Variable")
        print("        1. Use a Timestamp")
        o = int(-1)
        while not (0 <= o < 2):
            o = int(input("        Choose (0-1): "))
        if o==0:
            config["scan_name_type"] = "environment"
            config["scan_name_env"] = input("        Environment Variable Name: ")
        elif o==1:
            config["scan_name_type"] = "timestamp"
            config["scan_name_env"] = None

        """ FILES TO UPLOAD """
        print("      Files to Upload (use Ant Style Patterns)")
        finished = False
        while not finished:
            config["upload_include_pattern"] = input("        Upload Include File Pattern: ")
            config["upload_exclude_pattern"] = input("        Upload Exclude File Pattern: ")
            if "" == config["upload_exclude_pattern"]:
                config["upload_exclude_pattern"] = None

            print("      File Upload Preview:")
            ds = AntPatternDirectoryScanner(".", config["upload_include_pattern"], config["upload_exclude_pattern"])
            for filename in ds.scan():
                print("        " + filename)
            finished = "y" == input("      Continue with these patterns? (y/n)")

        """ MODULES TO SELECT """
        print("      Modules to Select (use Ant Style Patterns, leave blank to use Veracode Default)")
        config["module_include_pattern"] = input("        Module Include File Pattern: ")
        if "" == config["module_include_pattern"]:
            config["module_include_pattern"] = None
        config["module_exclude_pattern"] = input("        Module Exclude File Pattern: ")
        if "" == config["module_exclude_pattern"]:
            config[".upload_exclude_pattern"] = None

        """ WAIT FOR SCAN TO COMPLETE """
        config["wait_for_complete"] = "y" == input("      Wait for the scan to complete? (y/n): ")

        """ FAIL IF SCAN FAILS """
        config["fail_if_scan_fails"] = "y" == input("      Fail the Activity if the scan fails? (y/n): ")

        return config

    def execute(self, api, activity, config):
        print("Executing SastPolicyScanner with:")
        for key, value in config.items():
            print("  " + key + " = " + str(value))

        """ Create the Build with the correct Name format """
        scan_name = ""
        if config["scan_name_type"] == "timestamp":
            scan_name = datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S UTC]")
        elif config["scan_name_type"] == "environment":
            scan_name = os.environ.get(config["scan_name_env"])
        if "" == scan_name:
            print("INVALID SCAN NAME")
            raise VeracodeError("Invalid Scan Name")
        activity["build_id"] = api.create_build(activity["app_id"], scan_name)
        if activity["build_id"] is None:
            raise VeracodeError("Cannot Create New Build")
        print("build id = " + activity["build_id"])

        """ Upload the files """
        ds = AntPatternDirectoryScanner(".", config["upload_include_pattern"], config["upload_exclude_pattern"])
        for filename in ds.scan():
            api.upload_file(activity["app_id"], filename)

        """ Should we enable Auto-Scan ? """
        if config["module_include_pattern"] is None:
            """ Yes - enable AutoScan and lets get going """
            print("auto scan route")
            api.begin_prescan(activity["app_id"], "true")
        else:
            """ No - need to wait for pre-scan to complete... """
            print("module selection route")

        print("Pre-Scan In Progress...")
        api.get_prescan_status(activity["app_id"], build_id=activity["build_id"])

        return False

