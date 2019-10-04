# veracode-cli

A Command Line Interface for interacting with Veracode Services using a local
JSON configuration file to manage the settings that are used. For more
information use the readme service.

usage: 

`veracode-cli [-h] [-v VID] [-k VKEY] [-b BRANCH] SERVICE COMMAND`

positional arguments:

 `SERVICE`           the Veracode Service to interact with
 
 `COMMAND`           the Command to execute on the Veracode Service
 
optional arguments:

  `-h, --help`            show the help message and exit
  
  `-v VID, --vid VID`     API ID for the Veracode Platform user
  
  `-k VKEY, --vkey VKEY`  API Key for the Veracode Platform user
  
  `-b BRANCH, --branch BRANCH`
                        Branch name to be used to select configuration
                        settings OR branch name pattern to be used when
                        generating JSON skeleton code
                        
# Veracode Services

`portfolio`             access to the list of Applications, the details
                        of a specific Application and the ability to 
                        create a new application
                        
`static`                access to the Static Analysis technology 
                        encompassing Policy Scanning, Sandbox Scanning
                        and CI Scanning
                        
`dynamic`               access to the Dynamic Analysis technology

`findings`              access to scan results

`admin`                 access to administrative functions

`ticketing`             integration with ticketing systems such as JIRA and Azure DevOps

## `portfolio` Service

The `portfolio` service provides commands to list application profiles, get details of an application profile, update an application profile and create an application profile

### Command List
`list` description

`details` description

`update` description

`create` description


## `static` Service

## `dynamic` Service

## `findings` Service

## `admin` Service

## `ticketing` Service

