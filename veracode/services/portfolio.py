from .base_service import Service
from git import Repo
import os
import logging
import json


class portfolio(Service):
    def __init__(self):
        self.display_name = "Portfolio Service"
        self.description = "Veracode Platform Application Portfolio"
        self.DEBUG = False

    def add_parser(self, parsers):
        portfolio_parser = parsers.add_parser('portfolio', help='the portfolio service provides access to Veracode Application Profiles and allows you to list, create, modify and delete them')
        """ add sub-parsers for each of the commands """
        command_parsers = portfolio_parser.add_subparsers(dest='command', help='Portfolio Service Command description')
        """ onboard """
        onboard_parser = command_parsers.add_parser('onboard', help='onboard a new application')
        """ list """
        list_parser = command_parsers.add_parser('list', help='list all application profiles')
        """ get """
        get_parser = command_parsers.add_parser('get', help='get the details of a specific application profiles. use -n or -id to select correct app.')
        portfolio_parser.add_argument("-n", "--name", type=str, help="the name of the application")
        portfolio_parser.add_argument("-id", "--app_id", type=str, help="the application id of the application")
        portfolio_parser.add_argument("-c", "--criticality", type=str, help="the business criticality of the application")
        """ create """
        create_parser = command_parsers.add_parser('create', help='create a new application profiles. use -n to provide a name for the profile. use -c to provide a business criticality.')



    def execute(self, args, config, api):
        if args.command == 'onboard':
            """ onboard a new application """
            """ first we need to get the current repo"""
            logging.debug(2, "getting the current repo based on the current directory")
            repo = Repo(os.path.curdir)
            if not repo.bare:
                logging.debug(2, "the repo is not bare. get the name of the app")
                app_name = ""
                """ was a name supplied as a parameter? """
                if args.name is not None:
                    app_name = args.name
                else:
                    """ find the name from the url of the remote 'origin' """
                    logging.debug(2, "finding the name from the url of the remote 'origin'")
                    app_name = repo.remote('origin').url.rsplit('/', 1)[-1]
                logging.debug(1, "the name of the app is " + app_name)
                """ create a team for this app """
                print("Creating Team for this Application : " + app_name)
                resp = api.create_team(app_name, "")
                logging.debug(2, "response from create_team:")
                logging.debug(2, str(resp))
                """ create the app """
                print("Creating Application Profile : " + app_name)
                app_id = api.create_app(app_name, "created by veracode-cli", "High", "", app_name)
                #app_id = "12345"
                logging.debug(2, "response from create_app:")
                logging.debug(2, str(app_id))

                """ sort out the branching strategy """
                print("  ")
                print("Choose your branch scanning strategy:")
                print("  ")
                print("  1. Policy Scan on specific branch (typically 'master')")
                print("     Sandbox Scan for other branches")
                print("  ")
                print("  2. Sandbox Scan for all branches")
                print("     Promote Sandbox to Policy Scan manually")
                print("  ")
                print("  3. Custom (only a skeleton veracode.config file will be created")
                print("  ")
                bss = int(0)
                while not (1 <= bss <= 3):
                    bss = int(input("    Choose (1-3): "))

                if bss == 1:
                    """ select branch for Policy Scan """
                    print("Choose the branch for Policy Scanning:")
                    print("")
                    repo_heads = repo.heads
                    i=0
                    for head in repo_heads:
                        i = i+1
                        print(" %3d %s" %(i, head.name))
                    print("")
                    bss = int(0)
                    while not (1 <= bss <= i):
                        bss = int(input("    Choose (1-"+str(i)+"): "))

                    """ create the config """
                    config = []
                    """ add the master skeleton config elements """
                    master_skeleton = dict()
                    master_skeleton["branch_pattern"] = repo_heads[i-1].name
                    master_static_skeleton = dict()
                    master_static_skeleton["scan_type"] = "policy"
                    master_static_skeleton["scan_naming"] = "git"
                    master_static_skeleton["upload_include_patterns"] = []
                    master_static_skeleton["upload_include_patterns"].append("**/**.war")
                    master_static_skeleton["upload_exclude_patterns"] = []
                    master_skeleton["config_name"] = "Policy Scanning on master"
                    master_skeleton["static_config"] = master_static_skeleton
                    master_skeleton["portfolio"] = dict()
                    master_skeleton["portfolio"]["app_id"] = app_id
                    master_skeleton["portfolio"]["app_name"] = app_name
                    config.append(master_skeleton)
                    """ add the other branch config elements"""
                    other_skeleton = dict()
                    other_skeleton["branch_pattern"] = ".*"
                    other_static_skeleton = dict()
                    other_static_skeleton["scan_type"] = "sandbox"
                    other_static_skeleton["sandbox_naming"] = "branch"
                    other_static_skeleton["scan_naming"] = "git"
                    other_static_skeleton["upload_include_patterns"] = []
                    other_static_skeleton["upload_include_patterns"].append("**/**.war")
                    other_static_skeleton["upload_exclude_patterns"] = []
                    other_skeleton["config_name"] = "Sandbox Scanning on branch"
                    other_skeleton["static_config"] = other_static_skeleton
                    other_skeleton["portfolio"] = dict()
                    other_skeleton["portfolio"]["app_id"] = app_id
                    other_skeleton["portfolio"]["app_name"] = app_name
                    config.append(other_skeleton)
                    """ write the config file """
                    print("")
                    print("Creating veracode.config file:")
                    print("")
                    with open('veracode.config', 'w') as outfile:
                        json.dump(config, outfile, indent=2)
                    return json.dumps(config, indent=2)
                elif bss == 2:
                    """ create the config """
                    config = []
                    """ add the other branch config elements"""
                    other_skeleton = dict()
                    other_skeleton["match_pattern"] = ".*"
                    other_static_skeleton = dict()
                    other_static_skeleton["scan_type"] = "sandbox"
                    other_static_skeleton["sandbox_naming"] = "branch"
                    other_static_skeleton["scan_naming"] = "git"
                    other_static_skeleton["upload_include_patterns"] = []
                    other_static_skeleton["upload_include_patterns"].append("**/**")
                    other_static_skeleton["upload_exclude_patterns"] = []
                    master_skeleton["config_name"] = "Sandbox Scanning on branches"
                    other_skeleton["static"] = other_static_skeleton
                    other_skeleton["portfolio"] = dict()
                    other_skeleton["portfolio"]["app_id"] = app_id
                    other_skeleton["portfolio"]["app_name"] = app_name
                    config.append(other_skeleton)
                    """ write the config file """
                    with open('veracode.config', 'w') as outfile:
                        json.dump(config, outfile, indent=2)
                    return json.dumps(config, indent=2)
                elif bss == 3:
                    """ create the config """
                    config = []
                    """ write the config file """
                    with open('veracode.config', 'w') as outfile:
                        json.dump(config, outfile, indent=2)
                    return json.dumps(config, indent=2)
            else:
                print('Repo not loaded.')

        else:
            print("execute called")



