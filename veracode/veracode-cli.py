import argparse
import json
import logging
from git import Repo
import os
import sys

import services
from services.base_service import Service
from helpers.json_skeletons import JSONSkeleton
from importlib import import_module

from helpers.api import VeracodeAPI
from helpers.exceptions import VeracodeAPIError
from helpers.exceptions import VeracodeError

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
  in a JSON formatted file (veracode.config) which is managed within 
  the Git repository for the application code. Each Service provides 
  a skeleton command which will generate a default configuration 
  block for the Service in the config file.

* Branches : Each Veracode Service can be configured and used 
  differently based on the Git Branch that is being worked on. The 
  config file supports regular expression matching between the Branch 
  Name (supplied as an argument) and the configuration blocks in the file. 

When the CLI is executed it will produce a JSON output which is either
written to a file (veracode.output) or to the console. The default
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
        parser.add_argument("-b", "--branch", type=str,
                            help="Branch name to be used to select configuration settings OR branch name pattern to be used when generating JSON skeleton code.")
        parser.add_argument("-c", "--console", action="store_true",
                            help="Should the output be sent the console. If this is enabled then all other console output will be suppressed")
        """ add sub-parsers for each of the services """
        service_parsers = parser.add_subparsers(dest='service', help='Veracode service description')
        readme_parser = service_parsers.add_parser('readme', help='show the detailed readme information')
        for service_class in Service.services:
            service_class.add_parser(service_parsers)

        """ parse the command line """
        args = parser.parse_args()
        """ Just show the Readme? """
        if args.service == 'readme' or args.service is None:
            """ show the readme file information """
            print(readme)
            return 1

        if not args.console:
            print(banner)

        """ what Branch are we working on """
        if args.branch is None:
            """ get the current repository"""
            repo = Repo(os.path.curdir)
            if repo.bare:
                raise VeracodeError("No usable Git Repository found. Unable to identify active branch.")
            args.branch = repo.active_branch
            if not args.console:
                print("Using '" + str(args.branch) + "' as active branch")

        try:
            """ create the Veracode API instance """
            api = VeracodeAPI(None, args.vid, args.vkey)

            """ load the config file """
            try:
                with open('veracode.config') as json_file:
                    config = json.load(json_file)
            except FileNotFoundError:
                config = []

            """ load the output of previous command """
            if not args.console:
                try:
                    with open('veracode.output') as json_file:
                        data = json.load(json_file)
                except FileNotFoundError:
                    data = []
            else:
                """ Load the data from stdin """
                data = json.load(sys.stdin.readlines())

            """ load the relevant service class """
            if args.service is None:
                print("No service specified. Unable to proceed")
                return 1
            service = my_import('services.' + args.service + '.' + args.service)
            instance = service()

            """ execute the service """
            output_data = instance.execute(args, config, api, data)
            if not args.console:
                print()
                """ send the output to veracode.output """
                with open('veracode.output', 'w') as outfile:
                    json.dump(output_data, outfile)
            """ Always output to the console """
            print(output_data)

        except VeracodeError as err:
            print(" Error creating Veracode API wrapper. ")
            print(err)
            print(".")
            return 1

    except KeyboardInterrupt:
        print("Keyboard Interrupt. Exiting...")
    except VeracodeError as verr:
        print(verr)


def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def start():
    try:
        run()
    except KeyboardInterrupt:
        print("\r\nExiting")


if __name__ == "__main__":
    start()
