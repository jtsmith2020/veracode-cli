# veracode-cli

A Command Line Interface for interacting with Veracode Services using a local
JSON configuration file to manage the settings that are used. For more
information use the readme service.

usage: `veracode-cli [-h] [-v VID] [-k VKEY] [-b BRANCH] SERVICE COMMAND`

positional arguments:
 `SERVICE`           an integer for the accumulator
 `COMMAND`           an integer for the accumulator
 
optional arguments:
  `-h, --help`            show this help message and exit
  `-v VID, --vid VID`     API ID for the Veracode Platform user
  `-k VKEY, --vkey VKEY`  API Key for the Veracode Platform user
  `-b BRANCH, --branch BRANCH`
                        Branch name to be used to select configuration
                        settings OR branch name pattern to be used when
                        generating JSON skeleton code.