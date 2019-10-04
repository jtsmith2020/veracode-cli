from .base_service import Service

class Ticketing(Service):
    def __init__(self):
        self.display_name = "Ticketing Service"
        self.description = "Veracode Ticketing Integration Service"
        self.DEBUG = False

    def add_parser(self, parsers):
        ticketing_parser = parsers.add_parser('ticketing', help='the ticketing service...')
        ticketing_parser.add_argument("-b", "--branch", type=str, help="The branch name used to select configuration settings")


    def execute(self, api, activity, config):
        print("execute called")



