from .base_service import Service

class Static(Service):
    def __init__(self):
        self.display_name = "Dynamic Service"
        self.description = "Veracode Dynamic Analysis"
        self.DEBUG = False

    def add_parser(self, parsers):
        dynamic_parser = parsers.add_parser('dynamic', help='the dynamic service provides access to the Veracode DAST scans')
        dynamic_parser.add_argument("-b", "--branch", type=str, help="The branch name used to select configuration settings")


    def execute(self, api, activity, config):
        print("execute called")



