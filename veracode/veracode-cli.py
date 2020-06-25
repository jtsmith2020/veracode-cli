import argparse
import json
import logging
from git import Repo
import os
import sys
import re
import traceback
import services
from services.base_service import Service
from helpers.json_skeletons import JSONSkeleton
from importlib import import_module

from helpers.api import VeracodeAPI
from helpers.exceptions import VeracodeAPIError
from helpers.exceptions import VeracodeError
import configparser

banner = """
                                          _                     _  _ 
 __   __ ___  _ __  __ _   ___  ___    __| |  ___          ___ | |(_)
 \ \ / // _ \| '__|/ _` | / __|/ _ \  / _` | / _ \ _____  / __|| || |
  \ V /|  __/| |  | (_| || (__| (_) || (_| ||  __/|_____|| (__ | || |
   \_/  \___||_|   \__,_| \___|\___/  \__,_| \___|        \___||_||_|

"""

readme = banner + """This Command Line Interface for Veracode is based on 3 key principles:

* Services and Commands: The Veracode functionality is broken up into 
  a set of Services (e.g. static, dynamic, admin, etc.). Each Service
  has a limited set of Commands that can be executed (e.g. start). The 
  Commands represent higher level operations than the underlying API 
  calls (e.g. the start command in the static service will create a 
  scan, upload files and begin the scanning process).

* Configuration : Config information for each Service is stored 
  in a JSON formatted file (veracode-cli.config) which is managed within 
  the Git repository for the application code. Each Service provides 
  a skeleton command which will generate a default configuration 
  block for the Service in the config file.

* Branches : Each Veracode Service can be configured and used 
  differently based on the Git Branch that is being worked on. The 
  config file supports regular expression matching between the Branch 
  Name (supplied as an argument) and the configuration blocks in the file. 

When the CLI is executed it will produce a JSON output which is either
written to a file (veracode-cli.output) or to the console. The default
option is file. The output can also be used as additional input for
subsequent commands. 

For example:
"veracode-cli static start" will produce output that includes the build_id
of the scan that has been started. When "veracode-cli static results" is
executed it will use the build_id to identify which scan to retrieve results
from, and those results will be outputted. Next, when 
"veracode-cli static tickets" is executed it will use those results to 
synchronise with the configured ticketing system.

For more information use the -h option to show Help.
"""

creds_warning = """There don't seem to be any Veracode API credentials configured. If you
don't have any credentials then see the following page on the Veracode
Help Center for more information.

https://help.veracode.com/reader/LMv_dtSHyb7iIxAQznC~9w/RUQ3fCrA~jO2ff1G3t0ctg

Alternatively contact your Veracode Admin team or Security Program Manager.

Once you have your credentials there are 3 ways to supply them:
* As Environment Variables
  Use VID and VKEY
* As arguments on the command line
  veracode-cli --vid=<your_id> --vkey=<your_key> 
* In a Credentials File
  https://help.veracode.com/reader/LMv_dtSHyb7iIxAQznC~9w/1EGRCXxGvHuj5wxn6h3eXA
"""

########################################################################################################################
# Main entry point
#
def run():
    try:
        """ setup the main arugment parser """
        parser = argparse.ArgumentParser(prog='veracode-cli',
                                         description='A Command Line Interface for interacting with Veracode Services using a local JSON configuration file to manage the settings that are used. For more information use the readme service.')
        parser.add_argument("-v", "--vid", type=str, help="API ID for the Veracode Platform user")
        parser.add_argument("-k", "--vkey", type=str, help="API Key for the Veracode Platform user")
        parser.add_argument("-s", "--stage", type=str,
                            help="Stage name to be used to select the activities settings")
        parser.add_argument("-b", "--branch", type=str,
                            help="Branch name to be used to select configuration settings")
        parser.add_argument("-c", "--console", action="store_true",
                            help="Should the output be sent the console. If this is enabled then all other console output will be suppressed")
        parser.add_argument("-e", "--error", action="store_true",
                            help="Should the command fail if the veracode-cli.output file contains an error")
        """ add sub-parsers for each of the services """
        service_parsers = parser.add_subparsers(dest='service', help='Veracode service description')
        readme_parser = service_parsers.add_parser('readme', help='show the detailed readme information')
        for service_class in Service.services:
            service_class.add_parser(service_parsers)

        """ parse the command line """
        args = parser.parse_args()

        """ set up the output_data object """
        output_data = {}

        """ Just show the Readme? """
        if args.service == 'readme':
            """ show the readme file information """
            print(readme)
            return 0

        if not args.console:
            print(banner)

        """ ------------------------------------------------ """
        """ First thing to do is get the VeracodeAPI created """
        """ ------------------------------------------------ """
        try:
            if args.vid is None or args.vkey is None:
                """ OK, lets try the environment variables... """
                args.vid = os.environ.get("VID")
                args.vkey = os.environ.get("VKEY")
                if args.vid is None or args.vid == "" or args.vkey is None or args.vkey == "":
                    """ OK, try for the credentials file instead... """
                    auth_file = os.path.join(os.path.expanduser("~"), '.veracode', 'credentials')
                    if not os.path.exists(auth_file):
                        creds_file = False
                    else:
                        creds = configparser.ConfigParser()
                        creds.read(auth_file)
                        credentials_section_name = os.environ.get("VERACODE_API_PROFILE", "default")
                        args.vid = creds.get(credentials_section_name, "VERACODE_API_KEY_ID")
                        args.vkey = creds.get(credentials_section_name, "VERACODE_API_KEY_SECRET")

            if args.vid is None or args.vid == "" or args.vkey is None or args.vkey == "":
                """ warning and guidance on credentials """
                output_data["error"] = creds_warning
                return


            else:
                try:
                    """ create the Veracode API instance """
                    api = VeracodeAPI(None, args.vid, args.vkey)
                except:
                    """ error message about incorrect credentials """
                    print(f'{"exception":10} : Unexpected Exception #001 : {sys.exc_info()[0]}')
        except UnboundLocalError as ule1:
            """ Unexpected Exception """
            print("Different Unexpected error creating the API object : " + str(ule1))
        except:
            """ Unexpected Exception """
            print(f'{"exception":10} : {"Unexpected Exception #002 :", sys.exc_info()[0]}')

        """ -------------------------------------------------------------- """
        """ Next we need to load the Configuration data for the Branch     """
        """ -------------------------------------------------------------- """
        try:
            with open('veracode-cli.config') as json_file:
                config = json.load(json_file)
        except FileNotFoundError:
            if not args.console:
                print( "The veracode-cli.config file was not found at " +  os.getcwd())
            config = {}
            config["error"] = "Config File not found"
        except:
            """ Unexpected Exception """
            print(f'{"exception":10} : {"Unexpected Exception #003 :", sys.exc_info()[0]}')

        """ what Branch are we working on """
        if args.branch is None:
            """ get the current repository"""
            repo = Repo(os.path.curdir)
            if repo.bare:
                raise VeracodeError("No usable Git Repository found. Unable to identify active branch.")
            args.branch = repo.active_branch
            if not args.console:
                print("Using '" + str(args.branch) + "' as active branch")

        """ Get the Branch Configuration segment """
        branch_config = None

        for segment in config["branches"]:
            if re.match("^"+segment["branch_pattern"]+"$", str(args.branch)):
                """ This is the config to use... """
                branch_config = segment
                break
        if branch_config is None:
            """ """
            raise VeracodeError("No Static Scan Configuration found for branch '" + str(args.branch) + "'")

        """ ------------------------------------------------- """
        """ Next we need to load any Context data that exists """
        """ ------------------------------------------------- """
        if not args.console:
            try:
                with open('veracode-cli.output') as json_file:
                    context = json.load(json_file)
            except FileNotFoundError:
                context = {}
            except:
                """ Unexpected Exception """
                print(f'{"exception":10} : {"Unexpected Exception #004 :", sys.exc_info()[0]}')

        else:
            """ Load the data from stdin """
            context = json.load(sys.stdin.readlines())
        """ initialise the output data with the previous context """
        output_data = context
        """ Was there an error in the previous context? """
        if args.error is True and "error" in context and context["error"] is not None:
            output_data["error"] = f'{"exception":10} : Error in veracode-cli.context - {context["error"]}'
            if not args.console:
                print(output["error"])
            return output

        output_data["error"] = None

        if args.service is None:
            """ ------------------------------------------------------------------------- """
            """ If no Service was provided as an Argument then use Activities from config """
            """ ------------------------------------------------------------------------- """

            """ which Activities should we perform? """
            if args.stage is None:
                if  not args.console:
                    print("No Stage specified. Unable to proceed")
                output_data["error"] = "No Stage specified. Unable to proceed"
            else:
                """ find the right stage in the config """
                stage_activities = None
                for segment in config.stages:
                    if re.match("^" + segment["stage_pattern"] + "$", str(args.stage)):
                        """ This is the config to use... """
                        stage_config = segment
                        break
                if stage_config is None:
                    """ couldn't find the stage """
                    output_data["error"] = ""
                    raise VeracodeError("No Stage Configuration found for stage '" + str(args.stage) + "'")

        else:
            """ --------------------------------------------------------------- """
            """ Service was provided as an Argument so execute that one service """
            """ --------------------------------------------------------------- """
            if not args.console:
                print(f'{"service":10} : {args.service}')
                print(f'{"command":10} : {args.command}')
                for arg in vars(args):
                    if arg is not "service" and arg is not "command" and arg is not "vid" and arg is not "vkey" and arg is not "None":
                        print(f'{arg:10} : {getattr(args, arg)}')
                print(f'{"context":10} : {context}')
                print()
            """ load the relevant service class """
            service = my_import('services.' + args.service + '.' + args.service)
            instance = service()
            """ execute the service """
            output_data = instance.execute(args, branch_config, api, context)

    except KeyboardInterrupt:
        if not args.console:
            print(f'{"exception":10} : {"Keyboard Interrupt. Exiting..."}')
    except VeracodeError as verr:
        output_data["error"] = "Veracode Error occurred: " + str(verr)
        if not args.console:
            print(f'{"exception":10} : {output_data["error"]}')
    except UnboundLocalError as ule:
        if not args.console:
            print(f'{"exception":10} : {"UnboundLocalError -  " + str(ule)}')
    except AttributeError as ae:
        if not args.console:
            print(f'{"exception":10} : {"AttributeError -  " + str(ae)}')
            traceback.print_exc()
    except:
        """ Unexpected Exception """
        print(f'{"exception":10} : Unexpected Exception #005 - {sys.exc_info()[0]}')
        traceback.print_exc()
    finally:
        if not args.console:
            print()
            """ if there's an error then lets print it out"""
            if "error" in output_data:
                if output_data["error"] is not None:
                    print(output_data["error"])

            """ send the output to veracode-cli.output """
            with open('veracode-cli.output', 'w') as outfile:
                json.dump(output_data, outfile, indent=4, sort_keys=True)
        """ Always output to the console """
        print(output_data)
        if "error" in output_data:
            if output_data["error"] is not None:
                return 1
            else:
                return 0
        else:
            return 0


def get_service(name):
    kludge = 'services.' + name + '.' + name
    components = kludge.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def start():
    try:
        return run()
    except KeyboardInterrupt:
        print("\r\nExiting")


if __name__ == "__main__":
    error = start()
    exit(error)
