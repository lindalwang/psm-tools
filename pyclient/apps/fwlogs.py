#!/usr/bin/python3

import os
from typing import ItemsView
from apigroups.client.apis import FwlogV1Api, WorkloadV1Api
from apigroups.client import configuration, api_client
import datetime, re
from datetime import timezone
from tabulate import tabulate
import argparse
import warnings

warnings.simplefilter("ignore")

HOME = os.environ['HOME']

configuration = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
configuration.verify_ssl = False

client = api_client.ApiClient(configuration)
api_instance = FwlogV1Api(client)
workload_instance = WorkloadV1Api(client)

parser = argparse.ArgumentParser()
parser.add_argument(dest = "Quick Command", action='store_true', 
help = "'fwlogs.py --from dc22-vm102 --duration 1h' show firewall logs from a workload in past 1hr")
parser.add_argument("--from", dest="source", help="source workload name")
parser.add_argument("--to", dest="dest", help = "destination workload name" )
parser.add_argument("--duration", dest="duration", default="1d", help = 'firewall logs in past duration: <number>h|d|w')
parser.add_argument("--tenant", dest="tenant", help = 'tenant name, if not specified, default')
parser.add_argument("--json", dest="json", action="store_true", help = 'output in json format')

args = parser.parse_args()

fw_list = api_instance.get_get_logs1()
new_list = []
items = fw_list['items']
source_names = []
dest_names = []

current_time = datetime.datetime.now(timezone.utc)
desired_time = datetime.datetime.now()

if args.tenant:
    tenant = args.tenant
else:
    tenant = 'default'

    
workload_list = workload_instance.list_workload(o_tenant = tenant)
workloads = workload_list['items']    

if args.source:
    source_workload = args.source
    for workload in workloads:
        if source_workload in workload['meta']['name']:
            for address in workload['spec']['interfaces'][0]['ip_addresses']:
                ip_address = address
                for log in items:
                    if log['source_ip']==ip_address:
                        ind_log = {}
                        ind_log["fwlog"] = log
                        ind_log['source_name'] = workload['meta']['name']
                        new_list.append(ind_log)
else:
    for workload in workloads:
        for log in items:
            if workload['spec']['interfaces'][0].get('ip_addresses'):
                for address in workload['spec']['interfaces'][0]['ip_addresses']:
                    if log['source_ip'] == address:
                        ind_log = {}
                        ind_log["fwlog"] = log
                        ind_log['source_name'] = workload['meta']['name']
                        new_list.append(ind_log)                   

if args.dest:
    dest_workload = args.dest
    for workload in workloads:
        if dest_workload in workload['meta']['name']:
            if workload['spec']['interfaces'][0].get('ip_addresses'):
                for address in workload['spec']['interfaces'][0]['ip_addresses']:
                    ip_address = address
                    for log in new_list:
                        if log['fwlog']['destination_ip']==ip_address:
                            log['destination_name'] = workload['meta']['name']

else:
    for workload in workloads:
        for log in new_list:
            if workload['spec']['interfaces'][0].get('ip_addresses'):
                for address in workload['spec']['interfaces'][0]['ip_addresses']:
                    if log['fwlog']['destination_ip'] == address:
                        log['destination_name'] = workload['meta']['name']

for log in new_list[:]:
    if not log.get('destination_name'):
        new_list.remove(log)


if args.duration:
    #if user does not specify time length, the default unit is days
    if args.duration.isnumeric():
        print("Since no time unit is specified, recent firewall logs within " + args.age + " hours are returned.")
        desired_time = current_time - datetime.timedelta(hours = int(args.age))
    elif args.duration.isalpha():
        print("Please enter valid input. e.g. --duration 3d")
        exit()
    else:
        date_type = "".join(re.split("[^a-zA-Z]*", args.duration))
        date_number = "".join(re.split("[^0-9]*", args.duration))
        if date_type == "h" or "hour" in date_type:
            desired_time = current_time - datetime.timedelta(hours = ( int(date_number)))
        elif date_type == "w" or "week" in date_type:
            desired_time = current_time - datetime.timedelta(weeks = int(date_number))
        elif date_type == "d" or "day" in date_type:
            desired_time = current_time - datetime.timedelta(days = int(date_number))
        else:
            print("Please enter valid input. e.g. --duration 5h")
            exit()
    for log in new_list[:]:
        if desired_time > log['fwlog']['meta']['creation_time']: 
            new_list.remove(log)

if new_list:
    if args.json:
        print(new_list)
    else:
        final_fwlog = []
        for item in new_list:
            fwlogs = []
            fwlogs.append(item['fwlog']['meta']['creation_time'])
            fwlogs.append(item['source_name'])
            fwlogs.append(item['fwlog']['source_ip'])
            fwlogs.append(item['destination_name'])
            fwlogs.append(item['fwlog']['destination_ip'])
            fwlogs.append(item['fwlog']['protocol'])
            fwlogs.append(item['fwlog']['reporter_id'])
            final_fwlog.append(fwlogs)
        print(tabulate(final_fwlog, headers=["creation time", "source workload", "source ip", "destination workload", "destination ip", "protocol", "reporter id"]))
else:
    print("There are no firewall logs matching the descriptions.")



