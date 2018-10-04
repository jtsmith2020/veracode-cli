from helpers.base_scanner import Scanner


class SastSandboxScanner(Scanner):
    def __init__(self):
        self.display_name = "SAST Sandbox Scan"
        self.description = "Run a Sandbox Scan using Veracode SAST"

    def configure(self, api):

        return False

    def execute(self, api, activity, config):
        return False

