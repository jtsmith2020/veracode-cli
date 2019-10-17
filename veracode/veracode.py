import argparse
import json
import logging
from git import Repo
import os

import services
from services.base_service import Service
from helpers.json_skeletons import JSONSkeleton
from importlib import import_module

from helpers.api import VeracodeAPI


readme = """
Veracode Command Line Interface

This Command Line Interface for Veracode is based on 3 key principles:

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
"""

########################################################################################################################
# Main entry point
# Handles command line arguments and initiates one of 3 functions:
#  - credentials() : allows the user to configure a credentials file
#  - configure()   : allows the user to configure Activities (app profile + scanner + results handlers) and store as
#                    veracode.config
#  - execute()     : executes the configured Activities (either all Activities or one specific named Activity)
#
def run():
    logging.basicConfig(level=logging.WARN)
    try:
        """ setup the main arugment parser """
        parser = argparse.ArgumentParser(prog='veracode-cli', description='A Command Line Interface for interacting with Veracode Services using a local JSON configuration file to manage the settings that are used. For more information use the readme service.')
        parser.add_argument("-v", "--vid", type=str, help="API ID for the Veracode Platform user")
        parser.add_argument("-k", "--vkey", type=str, help="API Key for the Veracode Platform user")
        parser.add_argument("-b", "--branch", type=str, help="Branch name to be used to select configuration settings OR branch name pattern to be used when generating JSON skeleton code.")
        """ add sub-parsers for each of the services """
        service_parsers = parser.add_subparsers(dest='service', help='Veracode service description')
        readme_parser = service_parsers.add_parser('readme', help='show the detailed readme information')
        for service_class in Service.services:
            service_class.add_parser(service_parsers)

        """ parse the command line """
        args = parser.parse_args()

        """ get the current repository"""
        logging.debug("getting the repo in the current working directory")
        repo = Repo(os.path.curdir)
        if not repo.bare:
            logging.debug("got the repository and it is not bare")
        else:
            logging.error("No Git Repository found. Exiting...")
            return -1
        """ what Branch are we working on """
        #branch = args.branch
        if args.branch is None:
            args.branch = repo.active_branch
            logging.debug(args.branch)

        """ create the Veracode API instance """
        api = VeracodeAPI(None, args.vid, args.vkey)
        # should add some error handling here. ideally the VeracodeAPI should automatically check the outage API

        if args.service == 'readme':
            """ show the readme file information """
            print(readme)
        else:
            """ load the config file """
            try:
                json_file = open('veracode.config')
            except FileNotFoundError:
                config = []
            else:
                with json_file:
                    config = json.load(json_file)
            """ load the relevant service class """
            service = my_import('services.'+args.service+'.'+args.service)
            instance = service()
            """ execute """
            print(instance.execute(args, config, api))



        # main()
    except KeyboardInterrupt:
        print("Exiting...")

def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False

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
