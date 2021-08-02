#!/usr/bin/python3

import os
from typing import ItemsView
from apigroups.client.apis import WorkloadV1Api
from apigroups.client import configuration, api_client
from tabulate import tabulate
import argparse
from datetime import timezone
import datetime
import warnings
import re

warnings.simplefilter("ignore")

HOME = os.environ['HOME']


configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
configuration.verify_ssl = False

client = api_client.ApiClient(configuration)
api_instance = WorkloadV1Api(client)

#output recent 8 weeks' workloads when user does not input age
parser = argparse.ArgumentParser()
parser.add_argument(dest = "Quick Command", action='store_true', 
help = "'find_workload.py --age 1w' prints workload from recent one week")
parser.add_argument("--age", dest="age", default="8w", help="creation date: <number>d|w|m")
parser.add_argument("--dsc", dest="dsc", help = "name of DSC" )
parser.add_argument("--label", dest="label", help = 'label of workload, e.g. --label key:value')
parser.add_argument("--host", dest="host", help = 'host name of workload')
parser.add_argument("--tenant", dest="tenant", help = 'tenant name, if not specified, default')
parser.add_argument("--json", dest="json", action="store_true", help = 'output in json format')
args = parser.parse_args()


if args.tenant:
    tenant = args.tenant
else:
    tenant = 'default'
workload = api_instance.list_workload(o_tenant = tenant)
items = workload['items']
workload_list = []
new_item_list =[]

current_time = datetime.datetime.now(timezone.utc)
desired_time = datetime.datetime.now()


if args.age:
    #if user does not specify time length, the default unit is weeks
    if args.age.isnumeric():
        print("Since no time unit is specified, recent workload from " + args.age + " weeks are returned.")
        desired_time = current_time - datetime.timedelta(weeks = int(args.age))
    elif args.age.isalpha():
        print("Please enter valid input. e.g. --age 3d")
        exit()
    else:
        date_type = "".join(re.split("[^a-zA-Z]*", args.age))
        date_number = "".join(re.split("[^0-9]*", args.age))
        if date_type == "m" or "month" in date_type:
            desired_time = current_time - datetime.timedelta(days = ( int(date_number) * 31 ))
        elif date_type == "w" or "week" in date_type:
            desired_time = current_time - datetime.timedelta(weeks = int(date_number))
        elif date_type == "d" or "day" in date_type:
            desired_time = current_time - datetime.timedelta(days = int(date_number))
        elif date_type == "h" or "hour" in date_type:
            desired_time = current_time - datetime.timedelta(hours = int(date_number))
        else:
            print("Please enter valid input. e.g. --age 5w")
            exit()
    for x in items:
        if desired_time < x['meta']['creation_time']: 
            workload_list.append(x)   


if args.dsc:
    new_item_list = workload_list
    workload_list = []
    for item in new_item_list:
        if args.dsc in item['spec']['interfaces'][0]['mac_address']:
            workload_list.append(item)


if args.host:
    new_item_list = workload_list
    workload_list = []
    for item in new_item_list:
        if args.host in item['spec']['host_name']:
            workload_list.append(item)


if args.label:
    if args.label.find(':') == -1:
        print('Please input label in correct format e.g. --label key:value')
        exit()
    else:
        key = args.label.split(":")[0]
        value = args.label.split(":")[1]
        new_item_list = workload_list
        workload_list = []
        for item in new_item_list:
            if item['meta'].get('labels'):
                label = item['meta']['labels']
                if label and key in label.keys():
                    if value in label.get(key):
                        workload_list.append(item)


if workload_list:
    if args.json:
        print(workload_list)
    else:
        final_dict = []
        for item in workload_list:
            workloads = []
            workloads.append(item['meta']['name'])
            workloads.append(item['meta']['creation_time'])
            if item['meta'].get('labels'):
                string_label = ""
                for key, value in item['meta']['labels'].items():
                    string_label += key + ':' + value + "   "
                workloads.append(string_label)
            else:
                workloads.append("n/a")
            if args.tenant:
                workloads.append(item['meta']['tenant'])
            workloads.append(item['spec']['host_name'])
            workloads.append(item['spec']['interfaces'][0]['mac_address'])
            if item['status']['interfaces'][0].get('ip_addresses'):
                string_ip = ""
                for ips in item['status']['interfaces'][0]['ip_addresses']:
                    string_ip += ips + " "
                workloads.append(string_ip)
            else:
                workloads.append('n/a')
            workloads.append(item['status']['interfaces'][0]['network'])
            final_dict.append(workloads)
        if args.tenant:
            print(tabulate(final_dict, headers=["workload-name", "creation-time", "labels", "tenant", "host-name", "mac-address", "ip-address", "network"]))
        else:
            print(tabulate(final_dict, headers=["workload-name", "creation-time", "labels", "host-name", "mac-address", "ip-address", "network"]))
else:
    print('There are no workloads matching the descriptions.')
