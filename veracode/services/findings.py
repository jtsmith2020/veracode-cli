from .base_service import Service

class Findings(Service):
    def __init__(self):
        self.display_name = "Findings Service"
        self.description = "Veracode Platform Findings"
        self.DEBUG = False

    def add_parser(self, parsers):
        findings_parser = parsers.add_parser('findings', help='the findings service...')
        """ add sub-parsers for each of the commands """
        command_parsers = findings_parser.add_subparsers(dest='command', help='Findings Service Command description')
        """ report """
        report_parser = command_parsers.add_parser('xml-report', help='get the XML report for the latest scan results')
        """ await """
        passfail_parser = command_parsers.add_parser('passfail', help='get a pass/fail decision based on the latest scan results')
        """ skeleton """
        skeleton_parser = command_parsers.add_parser('skeleton', help='add a skeleton config block to the veracode.config file')
        """ optional parameters """
        #findings_parser.add_argument("-n", "--name", type=str, help="the name of the scan")



        findings_parser.add_argument("-b", "--branch", type=str, help="The branch name used to select configuration settings")


    def execute(self, api, activity, config):
        print("execute called")


