from helpers.base_results_handler import ResultsHandler
from antfs import AntPatternDirectoryScanner

class SynchroniseJIRA(ResultsHandler):
    def __init__(self):
        self.display_name = "Synchronise Flaws with JIRA"
        self.description = "Manage tickets in a JIRA project based on scan results."

    def configure(self, api):
        config = dict()
        config["type"] = type(self).__name__
        config["display_name"] = self.display_name
        print("      Configuring " + self.display_name)
        config["jira_base_url"] = input("        JIRA Base URL: ")
        config["jira_project"] = input("        JIRA Project: ")
        print("        Synchronisation Strategy Options:")
        print("          0. All Flaws")
        print("          1. Policy Affecting Flaws")
        print("          2. Unmitigated Policy Affecting Flaws")
        o = int(-1)
        while not (0 <= o < 3):
            o = int(input("        Choose (0-2): "))
        if o==0:
            config["sync_strategy"] = "all"
        elif o == 1:
            config["sync_strategy"] = "policy_affecting"
        elif o == 2:
            config["sync_strategy"] = "unmitigated_policy_affecting"

        return config

    def execute(self, api, activity, config):
        print("")
        print("Executing results handler SynchroniseJIRA with:")
        for key, value in config.items():
            print("  " + key + " = " + str(value))
        return False

