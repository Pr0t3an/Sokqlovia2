import os
import json
import urllib.request
import prettytable
from prettytable import PrettyTable
import re
import azure.mgmt.resourcegraph as arg
import math
from pandas import json_normalize
from tqdm import tqdm
from azure.mgmt.resource import SubscriptionClient
from azure.identity import AzureCliCredential
from colorama import init, Fore, Back, Style
import pyfiglet
from argparse import ArgumentParser
import shutil
from termcolor import colored



init(autoreset=True)
outputfilename="sokqlovia_output.csv"

def wrap_cell_text(text, width):
    lines = []
    line = ""
    words = text.split()
    for word in words:
        if len(line + word) > width:
            lines.append(line)
            line = ""
        line += word + " "
    lines.append(line)
    return "\n".join(lines)


def manage_configurationfile():
    if os.name == 'nt':
        config_paths = [
            os.path.expandvars('%APPDATA%/sokqlovia/stored_queries.json'),
            os.path.join(os.getcwd(), 'stored_queries.json')
        ]
    else:
        config_paths = [
            os.path.expanduser('~/.config/sokqlovia/stored_queries.json'),
            os.path.join(os.getcwd(), 'stored_queries.json')
        ]

    for path in config_paths:
        if os.path.exists(path):
            configuration_dir = path
            with open(path, 'r') as f:
                config = json.load(f)
            break
    else:
        print(
            "No configuration file found, downloading from https://github.com/Pr0t3an/sokqlovia/blob/main/stored_queries.json")
        config_url = "https://github.com/Pr0t3an/Sokqlovia2/blob/main/stored_queries.json"
        with urllib.request.urlopen(config_url) as response:
            config = json.loads(response.read().decode())
        if os.name == 'nt':
            config_path = os.path.expandvars('%APPDATA%/sokqlovia/stored_queries.json')
            configuration_dir = config_path
        else:
            config_path = os.path.expanduser('~/.config/sokqlovia/stored_queries.json')
            configuration_dir = config_path
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    return config, configuration_dir


def add_search_definition(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    last_id = max(int(search['id']) for search in config['searches'])
    new_id = str(last_id + 1)
    tags = input('Enter tags (comma-separated): ').split(',')
    description = input('Enter description: ')
    kql = input('Enter KQL: ')
    new_search = {'id': new_id, 'tags': tags, 'description': description, 'kql': kql}
    config['searches'].append(new_search)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def search_and_print(config, keyword):
    table = PrettyTable(["id", "tags", "description", "kql"])
    table.hrules = prettytable.ALL
    for search in config['searches']:
        if keyword in search['description'] or keyword in search['tags'] or keyword in search['kql']:
            wrapped_kql = wrap_cell_text(search['kql'], 60)
            table.add_row([search['id'], search['tags'], search['description'], wrapped_kql])
            table.align = "l"
    print(table)


def print_config(config):
    table = PrettyTable(["id", "tags", "description", "kql"])
    table.hrules = prettytable.ALL
    for search in config['searches']:
        wrapped_kql = wrap_cell_text(search['kql'], 50)
        table.add_row([search['id'], search['tags'], search['description'], wrapped_kql])
        table.align = "l"
    print(table)


def retrieve_by_id(config_path, id):
    with open(config_path, 'r') as f:
        config = json.load(f)
    for search in config['searches']:
        if search['id'] == id:
            id = search['id']
            tags = search['tags']
            description = search['description']
            kql = search['kql']
            break
    else:
        print(f"No search found with id: {id}")
        return
    print(f"id: {id}")
    print(f"tags: {tags}")
    print(f"description: {description}")

    somedata_matches = re.findall(r"@(\w+)@", kql)
    if somedata_matches:
        somedata_values = {}
        for match in somedata_matches:
            somedata_values[match] = input(f"Enter a value for {match}: ")
        for key, value in somedata_values.items():
            kql = kql.replace(f"<@{key}@>", value)
    print(f"kql: {kql}")
    getresources(kql)

def getresources( strQuery ):
    # Get your credentials from Azure CLI (development only!) and get your subscription list
    print("\nLaunching Query")
    credential = AzureCliCredential()
    subsClient = SubscriptionClient(credential)
    subsRaw = []
    for sub in subsClient.subscriptions.list():
        subsRaw.append(sub.as_dict())
    subsList = []
    for sub in subsRaw:
        subsList.append(sub.get('subscription_id'))

    # Create Azure Resource Graph client and set options
    argClient = arg.ResourceGraphClient(credential)
    argQueryOptions = arg.models.QueryRequestOptions(result_format="objectArray")

    # Create query
    argQuery = arg.models.QueryRequest(subscriptions=subsList, query=strQuery, options=argQueryOptions)

    # Run query
    argResults = argClient.resources(argQuery)

    print("Results Found: " + str(argResults.total_records))
    print("Return Count: " + str(argResults.count))
    print("Results Trucated:" + str(argResults.result_truncated))
    print("Skip Token: " + str(argResults.skip_token))
    query_num = (math.ceil(argResults.total_records/argResults.count))
    print("Queries Needed: " + str(query_num))
    orderstring = "order by"
    if orderstring in strQuery or query_num==1:
        sf = 1
    else:
        if input((Style.BRIGHT + Back.YELLOW + Fore.RED + "[WARNING] Query will be executed in multiple parts. 'order by' operator not found in query. Recommend terminating script (Y/N)")) == "y":
            exit()

    print("###################################\n")
    # pandas test

    json_a = json.dumps(argResults.data)
    json_b = json.loads(json_a)
    df_full = json_normalize(json_b)
    d = 1
    #print(d)
    newval=1000
    while argResults.skip_token:
        for d in tqdm(range(query_num)):
            argQueryOptions = arg.models.QueryRequestOptions(result_format="objectArray", skip_token=argResults.skip_token, skip=newval)
            argQuery = arg.models.QueryRequest(subscriptions=subsList, query=strQuery, options=argQueryOptions)
            argResults = argClient.resources(argQuery)
            json_a = json.dumps(argResults.data)
            json_b = json.loads(json_a)
            df = json_normalize(json_b)
            df_full = df_full.append(df)
            d += 1
            newval+= 1000
            #print(d)

    if argResults.total_records == 1:
        result = json.loads(json.dumps(argResults.data))[0]
        for key, value in result.items():
            print(key + ": " + str(value))
    else:
        print("Data Preview - full output saved to " + outputfilename)
        print(df_full)
        df_full.to_csv(outputfilename, index=False)



def compulsary_ascii():
    ascii_banner = pyfiglet.figlet_format("soKQLovia2")
    print(colored(ascii_banner.replace("KQL", "\033[33mKQL\033[0m"), 'yellow'))

def ipsearch(ip):
    print("Searching IP: " + ip)
    getresources("Resources | where type contains 'publicIPAddresses' and properties.ipAddress =~ '" + ip + "'")

if __name__ == '__main__':
    compulsary_ascii()
    data,configuration_dir = manage_configurationfile()
    parser = ArgumentParser()
    parser.add_argument("-i", dest="ipsearch", help="quick public ip search", required=False)
    parser.add_argument("-o", dest="outfile", help="Override default output file/path. Default is sokqlovia_output.csv in cwd",
                        required=False)
    parser.add_argument("-q", dest="custom_query", help="Freeform query - Quote encapsulated KQL query to be executed", required=False)
    parser.add_argument("-d", help="Displays all predefined queries",
                        action="store_true", required=False)
    parser.add_argument("-a", help="Add a new saved query",
                        action="store_true", required=False)
    parser.add_argument("-s", dest="search", help="Keyword search of stored queries", required=False)
    parser.add_argument("-u", dest="use", help="Use followed by the ID of the query (need to know which query first using -s or -d", required=False)
    parser.add_argument("-b", dest="backup", help="Backup config file to specified directory", required=False)
    parser.add_argument("-f", action="store_true", help="prints config location", required=False)
    args = parser.parse_args()

    #set output location
    if args.outfile:
        outputfilename = args.outfile

    # run basic ip search
    if args.ipsearch:
        ipsearch(args.ipsearch)

    # custom on the fly query
    if args.custom_query:
        getresources(args.custom_query)

    # Display all saved queries
    if args.d:
        print_config(data)

    if args.f:
        print("Config Location:\n")
        print(configuration_dir)

    # runs specific saved query
    if args.use:
        retrieve_by_id(configuration_dir, args.use)

    # search for a query by keyword
    if args.search:
        keyword = args.search
        print("\n[+] Searching for Keyword: " + keyword)
        print("\n")
        search_and_print(data, keyword)

    #add a new saved query
    if args.a:
        add_search_definition(configuration_dir)

    if args.backup:
        src_file = configuration_dir
        dst_dir = args.backup
        dst_file = os.path.join(dst_dir, "backup_stored_queries.json")

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        shutil.copy(src_file, dst_file)





