from helpers.base_scanner import Scanner


class DastPolicyScanner(Scanner):
    def __init__(self):
        self.display_name = "DAST Policy Scan"
        self.description = "Run a Policy Scan using Veracode DAST"

    def configure(self, api):

        return False

    def execute(self, api, activity, config):
        return False

