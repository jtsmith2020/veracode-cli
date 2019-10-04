from datetime import datetime
import scanners
import results_handlers
from helpers.api import VeracodeAPI
from helpers.base_scanner import Scanner
from helpers.base_results_handler import ResultsHandler
import argparse
import xml.etree.ElementTree as ET
import json
import yaml




########################################################################################################################
# configure()
#   parameters:
#     api         : Veracode API Instance
#
# Interactive configuration process which guides the user through the necessary steps and writes the
# veracode.config file
#
def configure(api):
    print("")
    print("Veracode Activities Configuration")
    print("==================================")
    print("")
    print("The Veracode Activities tool can be configured with any number of named Activities.")
    print("Each Activity is made up of the following elements:")
    print(" - An Application Profile")
    print(" - A Scanner (optional)")
    print(" - A set of Results Handlers")
    print("")
    app_id = None
    app_name = None
    finished = False
    first_app = True
    config = []


    """ Configuration Loop for Activities """
    while finished == False:

        print("New Activity")
        activity = dict()
        config.append(activity)

        activity["name"] = ""
        while activity["name"] == "":
            activity["name"] = input("  Activity Name: ")

        print("Application Profile")
        activity["app_id"] = None
        while activity["app_id"] is None:
            activity["app_name"] = ""
            while activity["app_name"] == "":
                activity["app_name"] = input("  Application Name: ")
            activity["app_id"] = api.get_app_id_by_name(activity["app_name"])
            if activity["app_id"] is None:
                print("    Error: Application Profile not found")

        """ OK, we have an Application Profile, lets configure the scanner.. """
        print("Scanner")
        print("  Available Scanners:")
        i=0
        for scanner_class in Scanner.scanners:
            print("    " + str(i) + ". " + scanner_class.display_name)
            i = i + 1
        print("    " + str(i) + ". No Scanner Required")
        s = int(-1)
        while not(0 <= s < len(Scanner.scanners)+1):
            s = int(input("    Choose (0-" + str(len(Scanner.scanners)) + "): "))
        if s != len(Scanner.scanners):
            activity["scanner"] = Scanner.scanners[s].configure(api)
        else:
            activity["scanner"] = None

        """ Lets add any results handlers """
        print("Results Handler(s)")
        activity["results_handlers"] = []
        while "y" == input("  Add a Results Handler? (y/n):"):
            print("  Available Results Handlers:")
            i=0
            for handler_class in ResultsHandler.handlers:
                print("    " + str(i) + ". " + handler_class.display_name)
                i = i + 1
            while not (0 <= s < len(ResultsHandler.handlers)):
                s = int(input("    Choose (0-" + str(len(ResultsHandler.handlers)-1) + "): "))
            activity["results_handlers"].append(ResultsHandler.handlers[s].configure(api))

        if "y" != input("Add another Activity? (y/n): "):
            finished = True

    """ Write the configuration to the veracode.config file """
#    with open('veracode.config', 'w') as outfile:
#        json.dump(config, outfile)

    """ Write the configuration to the veracode.yml file """
    with open('veracode.yaml', 'w') as outfile:
        yaml.dump(config, outfile)


########################################################################################################################
# execute()
#   parameters:
#     api         : Veracode API Instance
#     activities  : Name of an activity to perform (if None then execute all activities)
#
#  Reads the veracode.config file and then executes the required Activities
#
def execute(api, activities):
    print("")
    print("Veracode Activities Tool")
    print("========================")
    print("")

    config = []
#    with open('veracode.config') as json_file:
#        config = json.load(json_file)

    with open('veracode.yaml') as yaml_file:
        config = yaml.load(yaml_file)

    for activity in config:
        if activities is None or activities == activity["name"]:
            if activity["scanner"] is not None:
                scanner = __import__("scanners")
                scanner = getattr(scanner, activity["scanner"]["type"])
                scanner = getattr(scanner, activity["scanner"]["type"])
                scanner.execute(scanner, api, activity, activity["scanner"])

            for handler_config in activity["results_handlers"]:
                handler = __import__("results_handlers")
                handler = getattr(handler, handler_config["type"])
                handler = getattr(handler, handler_config["type"])
                handler.execute(handler, api, activity, handler_config)


########################################################################################################################
# Main entry point
# Handles command line arguments and initiates one of 3 functions:
#  - credentials() : allows the user to configure a credentials file
#  - configure()   : allows the user to configure Activities (app profile + scanner + results handlers) and store as
#                    veracode.config
#  - execute()     : executes the configured Activities (either all Activities or one specific named Activity)
#
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--vid", type=str, help="API ID for the Veracode Platform user")
        parser.add_argument("-k", "--vkey", type=str, help="API Key for the Veracode Platform user")
        parser.add_argument("-s", "--setup", type=str, choices=["credentials", "configure"], help="Setup the tool")
        parser.add_argument("-a", "--activity", type=str, help="Execute one or more Activities. If not specified then all Activities will be executed")
        args = parser.parse_args()

        api = VeracodeAPI(None, args.vid, args.vkey)
        if args.setup == "credentials":
            print("setup credentials")
        elif args.setup == "configure":
            configure(api)
        else:
            execute(api, args.activity)


        # main()
    except KeyboardInterrupt:
        date_print("Exiting...")
