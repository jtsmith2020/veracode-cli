from .base_service import Service

class Admin(Service):
    def __init__(self):
        self.display_name = "Static Service"
        self.description = "Veracode Static Analysis"
        self.DEBUG = False

    def add_parser(self, parsers):
        admin_parser = parsers.add_parser('admin', help='the admin service...')
        admin_parser.add_argument("-b", "--branch", type=str, help="The branch name used to select configuration settings")


    def execute(self, api, activity, config):
        print("execute called")



