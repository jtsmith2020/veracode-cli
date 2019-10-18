from .base_service import Service

class ticketing(Service):
    def __init__(self):
        self.display_name = "Ticketing Service"
        self.description = "Veracode Ticketing Integration Service"
        self.DEBUG = False

    def add_parser(self, parsers):
        ticketing_parser = parsers.add_parser('ticketing', help='the ticketing service...')
        """ add sub-parsers for each of the commands """
        command_parsers = ticketing_parser.add_subparsers(dest='command', help='Ticketing Service Command description')
        """ synchronise """
        sync_parser = command_parsers.add_parser('synchronise', help='Synchronise the latest scan results with the Ticketing System')
        """ configure """
        configure_parser = command_parsers.add_parser('configure', help='configure the ticketing config blocks in the veracode.config file')
        """ optional parameters """
        ticketing_parser.add_argument("-b", "--branch", type=str, help="The branch name used to select configuration settings")


    def execute(self, api, activity, config):
        print("execute called")



