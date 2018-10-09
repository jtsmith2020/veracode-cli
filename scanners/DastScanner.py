from helpers.base_scanner import Scanner


class DastScanner(Scanner):
    def __init__(self):
        self.display_name = "DAST Scan"
        self.description = "Run a Scan using Veracode DAST"

    def configure(self, api):

        return False

    def execute(self, api, activity, config):
        return False

