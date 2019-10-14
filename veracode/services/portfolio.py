from .base_service import Service
from git import Repo
import os

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



    def execute(self, args, config, api, out):
        if args.command == 'onboard':
            """ onboard a new application """
            """ first we need to get the current repo"""
            out.log(2, "getting the current repo based on the current directory")
            repo = Repo(os.path.curdir)
            if not repo.bare:
                out.log(2, "the repo is not bare. get the name of the app")
                app_name = ""
                """ was a name supplied as a parameter? """
                if args.name is not None:
                    app_name = args.name
                else:
                    """ find the name from the url of the remote 'origin' """
                    out.log(2, "finding the name from the url of the remote 'origin'")
                    app_name = repo.remote('origin').url.rsplit('/', 1)[-1]
                out.log(1, "the name of the app is " + app_name)
                """ create a team for this app """
                resp = api.create_team(app_name, "")
                out.log(2, "response from create_team:")
                out.log(2, str(resp))
                """ create the app """
                resp = api.create_app(app_name, "created by veracode-cli", "High", "", app_name)
                out.log(2, "response from create_app:")
                out.log(2, str(resp))
                """ now we need to know who the users are... """


            else:
                print('Repo not loaded.')

        else:
            print("execute called")



