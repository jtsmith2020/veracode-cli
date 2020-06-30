from .base_service import Service
import logging
import xmltodict
import datetime
import os
import re
import pprint
import json


class ticketing(Service):
    def __init__(self):
        self.display_name = "Ticketing Service"
        self.description = "Veracode Ticketing Integration Service"
        self.DEBUG = False
        self.ticket_actions = {"application": {"type": "create", "flaws": []},
                               "severities": [],
                               "categories": [],
                               "cwes": [],
                               "flaws": []}
        self.console = False
        self.console = False

    def add_parser(self, parsers):
        ticketing_parser = parsers.add_parser('ticketing', help='the ticketing service is used to synchronise results from Veracode to a ticketing system such as JIRA or Azure DevOps')
        """ add sub-parsers for each of the commands """
        command_parsers = ticketing_parser.add_subparsers(dest='command', help='Ticketing Service Command description')
        """ synchronize """
        sync_parser = command_parsers.add_parser('synchronize', help='Synchronise the latest scan results with the Ticketing System')
        """ configure """
        configure_parser = command_parsers.add_parser('configure', help='configure the ticketing config blocks in the veracode.config file')
        """ optional parameters """
        ticketing_parser.add_argument("-b", "--branch", type=str, help="The branch name used to select configuration settings")


    def execute(self, args, config, api, context):
        logging.debug("ticketing service executed")
        self.console = args.console
        if args.command == "configure":
            return self.configure(args, config, api, context)
        elif args.command == "synchronize":
            return self.synchronise(args, config, api, context)
        else:
            print("unknown command: "+ args.command)


    def configure(self, args, config, api, context):
        logging.debug("configure called")

    def synchronise(self, args, config, api, context):
        output = {}
        if "results" in context and context["results"] is not None:
            output["results"] = context["results"]
        else:
            output["error"] = f'No results in context'
            if not args.console:
                print(f'{"error":10} : ticketing.synchronise - {output["error"]}')
            return output
        try:
            """ parse the results into Ticket Actions the tickets """
            self.parse_results(config, context["results"])
            output["ticket_actions"] = self.ticket_actions
        except:
            output["error"] = "Unexpected Exception #005 (static.py) : " + str(sys.exc_info()[0])
            return output

        return output





