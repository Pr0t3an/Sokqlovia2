# soKQLovia2

*Update to Sokqlvia with a higher focus on ease of use vs programmatic use. Quick way of query Azure via ResourceGrap*

---------

Soqklvoia uses Azure Resource Graph (ARG) to perform KQL based queries against Azure utilising Azure Cli to manage the authentication. Designed to dump this infomation to CSV (though easily modified for json output) and display (if 1 record) in the terminal and saving predefined queries with substitution to make repeat use easier. (All functionality can be done through Azure Console - but may run up against subscription limitations)

-----------
## Quick Start

**Requirements**
-   Python 3.6 or later
-   Azure CLI (for authentication)
-   `prettytable`, `tqdm`, `azure-mgmt-resource`, `azure-mgmt-resourcegraph`, `pandas`, `colorama`, `pyfiglet` and `termcolor` python packages.

## to install Azure-Cli on MAC

brew update && brew install azure-cli
az login --use-device-code

## Setup soKQLovia
git clone https://github.com/Pr0t3an/sokqlovia2.git
cd sokqlovia2
pip3 install -r requirements.txt
python3 sokqlovia.py -h

config shebang/symlink etc as needed - helpful but not required


**

## Saved Queries

Saved queries are stored in one of 2 locations in a json file depending on OS, if it doesn't find a query file in the first directory, will look at the current directory and if it doesn't find one will download to the preferred directory

-   **Windows**: `%APPDATA%/sokqlovia/stored_queries.json` and `./stored_queries.json`
-   **MacOS/Linux**: `~/.config/sokqlovia/stored_queries.json` and `./stored_queries.json`
 
below is an example of a saved query:

        {
      "id": "19",
      "tags": [
        "hostname",
        "web app"
      ],
      "description": "List all hostnames for an Azure Web App",
      "kql": "Resources | where type =~ 'Microsoft.Web/sites/hostnames' and resourceGroup == ('<@resourcegroup@>') | project name, id, type, hostName, resourceGroup, properties.customHostNames | order by hostName"
    },

**Id** - unique id that is auto created through tool, though you can manually increment if you are using txt editor
**tags** - comma seperated, help with searching
**Description** - self explanatory, but searchable also
**KQL** - actual query executed. <@**something**@> signifies substitution, though something can be any text - when selecting a template whatever is between <@ and @> will be the prompt onscreen. **Note if you are running big queries you should use Order statement as there is a limit per query + this joins them together in the order they should be in - otherwise would be incomplete**
**

## Usage

    python3 sokqlovia.py -h
    # will display help

<img width="1019" alt="image" src="https://user-images.githubusercontent.com/22748755/217561318-96e5108e-25e6-463a-9eb2-37b08bfbe6e6.png">


**Simple public ip search**
	

    python3 sokqlovia.py -i x.x.x.x
		

**Display All Saved Queries**

    python3 sokqlovia.py -d

**Search For a Saved Query**

    python3 sokqlovia.py -s <phrase>

**Use a Saved Query**

    python3 sokqlovia.py -u <id>

**Add a new Saved Query**

    python3 sokqlovia.py -a

**Perform a one off query**

    python3 soqklovia.py -q "<adhoc query>"

Whilst have added sample queries - idea would be you build ones that make sense to you - as such some maintainance commands

**Get location of the saved queries file**
    python3 sokqlovia.py -f

**Backup queries file**

    python3 sokqlovia.py -b /save/to/this/dir
