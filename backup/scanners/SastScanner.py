from helpers.base_scanner import Scanner
from helpers.exceptions import VeracodeError
from antfs import AntPatternDirectoryScanner
from datetime import datetime
import os
import time

class SastScanner(Scanner):
    verbose = True
    display_name = "SAST Scan"
    description = "Run a Scan using Veracode SAST"

    def __init__(self):
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
        print("      Modules to Select (use REGULAR EXPRESSIONS, leave blank to use Veracode Default)")
        config["module_include_pattern"] = input("        Module Include File Pattern: ")
        if "" == config["module_include_pattern"]:
            config["module_include_pattern"] = None
        config["module_exclude_pattern"] = input("        Module Exclude File Pattern: ")
        if "" == config["module_exclude_pattern"]:
            config["module_exclude_pattern"] = None

        """ WAIT FOR SCAN TO COMPLETE """
        config["wait_for_complete"] = "y" == input("      Wait for the scan to complete? (y/n): ")

        """ FAIL IF SCAN FAILS """
        config["fail_if_scan_fails"] = "y" == input("      Fail the Activity if the scan fails? (y/n): ")

        return config

    def execute(self, api, activity, config):
        if self.verbose:
            print("Executing " + self.display_name + " with:")
            for key, value in config.items():
                print("  " + key + " = " + str(value))
            print("")

        """ Create the Build with the correct Name format """
        scan_name = ""
        if config["scan_name_type"] == "timestamp":
            scan_name = datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S UTC]")
        elif config["scan_name_type"] == "environment":
            scan_name = os.environ.get(config["scan_name_env"])
        if "" == scan_name:
            print("INVALID SCAN NAME")
            raise VeracodeError("Invalid Scan Name")

        print("Creating new Scan with name: " + scan_name)
        activity["build_id"] = api.create_build(activity["app_id"], scan_name)
        if activity["build_id"] is None:
            raise VeracodeError("Cannot Create New Build")
        print("  (scan id = " + activity["build_id"] + ")")

        """ Upload the files """
        print("Uploading Files", end="")
        ds = AntPatternDirectoryScanner(".", config["upload_include_pattern"], config["upload_exclude_pattern"])
        for filename in ds.scan():
            print(".", end="")
            api.upload_file(activity["app_id"], filename)
        print("")

        """ Should we enable Auto-Scan ? """
        print("Pre-Scan Starting", end="")
        if config["module_include_pattern"] is None:
            """ Yes - enable AutoScan and lets get going """
            api.begin_prescan(activity["app_id"], "true")
        else:
            """ No - disable auto-scan and get started  """
            api.begin_prescan(activity["app_id"], "false")
        """ Now we wait for prescan to complete - check every 30 seconds """
        modules = api.get_modules(activity["app_id"], build_id=activity["build_id"])
        while modules is None:
            print(".", end="")
            time.sleep(30)
            modules = api.get_modules(activity["app_id"], build_id=activity["build_id"])
        print("")
        print("Pre-Scan Complete")
        print("Full Scan Starting", end="")
        if config["module_include_pattern"] is not None:
            """ now we need to select the modules and start the scan... """
            print("")
            print("module selection code not writen")

            """ XXXX NOT DONE YET XXXX  """
            print("Full Scan Running", end="")

        """ Do we need to wait for the scan to complete? """
        if config["wait_for_complete"] == True:
            """ OK, now we wait for the scan to complete... """
            results_ready = api.results_ready(activity["app_id"], activity["build_id"])
            while not results_ready:
                print(".", end="")
                time.sleep(30)
                results_ready = api.results_ready(activity["app_id"], activity["build_id"])
            print("")
            print("Full Scan Complete")
        else:
            print("")
            print("Not waiting for Full Scan to Complete")

        return False

