from helpers.base_scanner import Scanner


class DastRescanScanner(Scanner):
    def __init__(self):
        self.display_name = "DAST Vulnerability Rescan"
        self.description = "Run a Dynamic Vulnerability Rescan using Veracode DAST"

    def configure(self, api):

        return False

    def execute(self, api, activity, config):
        return False

