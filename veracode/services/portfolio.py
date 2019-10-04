from .base_service import Service

class Portfolio(Service):
    def __init__(self):
        self.display_name = "Portfolio Service"
        self.description = "Veracode Platform Application Portfolio"
        self.DEBUG = False

    def add_parser(self, parsers):
        portfolio_parser = parsers.add_parser('portfolio', help='the portfolio service provides access to Veracode Application Profiles and allows you to list, create, modify and delete them')
        """ add sub-parsers for each of the commands """
        command_parsers = portfolio_parser.add_subparsers(dest='command', help='Portfolio Service Command description')
        """ list """
        list_parser = command_parsers.add_parser('list', help='list all application profiles')
        """ get """
        get_parser = command_parsers.add_parser('get', help='get the details of a specific application profiles. use -n or -id to select correct app.')
        portfolio_parser.add_argument("-n", "--name", type=str, help="the name of the application")
        portfolio_parser.add_argument("-id", "--app_id", type=str, help="the application id of the application")
        portfolio_parser.add_argument("-c", "--criticality", type=str, help="the business criticality of the application")
        """ create """
        create_parser = command_parsers.add_parser('create', help='create a new application profiles. use -n to provide a name for the profile. use -c to provide a business criticality.')



    def execute(self, api, activity, config):
        print("execute called")



