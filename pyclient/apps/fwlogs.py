#!/usr/bin/python3

import os
from typing import ItemsView
from apigroups.client.apis import FwlogV1Api, WorkloadV1Api
from apigroups.client import configuration, api_client
from utils.datatime_utils import time_delta_from_now
from tabulate import tabulate
import logging 
import sys
import datetime
from datetime import timezone
from apigroups.client.models import FwlogFwLogQuery
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
help = "'fwlogs.py --from dc22-vm102 --age 1h' show firewall logs from the workload in past 1hr")
parser.add_argument("--source", dest="source", help="source workload name or a part of the workload name")
parser.add_argument("--destination", dest="dest", help = "destination workload name or a part of the workload name" )
parser.add_argument("--age", dest="age", default="12", help = 'firewall logs in past age: <number>h')
parser.add_argument("--tenant", dest="tenant", default = "default", help = 'tenant name, if not specified, default')
parser.add_argument("--json", dest="json", action="store_true", help = 'output in json format')
args = parser.parse_args()

current_time = datetime.datetime.now(timezone.utc)
desired_time = time_delta_from_now(args.age, current_time)
time_diff = current_time - desired_time 

if time_diff.days >= 1:
    logging.error('Only recent 24h logs can be searched.')
    sys.exit()

query = FwlogFwLogQuery(start_time = desired_time)
fw_list = api_instance.post_get_logs(body = query)
if not fw_list.get('items'):
    logging.error('There are no logs present.')
    sys.exit()
items = fw_list.items
workload_list = workload_instance.list_workload(o_tenant = args.tenant)
workloads = workload_list.items
new_list = []   

if args.source:
    source_workload = args.source
    for workload in workloads:
        if source_workload in workload.meta.name:
            workload_addresses = workload.spec.interfaces[0].ip_addresses 
            for log in items:
                if log.source_ip in workload_addresses:
                    ind_log = {}
                    ind_log['fwlog'] = log
                    ind_log['source_name'] = workload.meta.name
                    new_list.append(ind_log)
else:
    for workload in workloads:
        for log in items:
            if workload.spec.interfaces[0].get('ip_addresses'):
                workload_addresses = workload.spec.interfaces[0].ip_addresses 
                if log.source_ip in workload_addresses:
                        ind_log = {}
                        ind_log['fwlog'] = log
                        ind_log['source_name'] = workload.meta.name
                        new_list.append(ind_log)                   

if args.dest:
    dest_workload = args.dest
    for workload in workloads:
        if dest_workload in workload.meta.name:
            if workload.spec.interfaces[0].get('ip_addresses'):
                workload_addresses = workload.spec.interfaces[0].ip_addresses 
                for log in new_list:
                    if log['fwlog'].destination_ip in workload_addresses:
                        log['destination_name'] = workload.meta.name
else:
    for workload in workloads:
        for log in new_list:
            if workload.spec.interfaces[0].get('ip_addresses'):
                workload_addresses = workload.spec.interfaces[0].ip_addresses 
                if log['fwlog'].destination_ip in workload_addresses:
                    log['destination_name'] = workload.meta.name

for log in new_list[:]:
    if not log.get('destination_name'):
        new_list.remove(log)
    if desired_time > log['fwlog'].meta.creation_time: 
            new_list.remove(log)

if new_list:
    if args.json:
        print(new_list)
    else:
        final_fwlog = []
        log_num = 0
        for item in new_list:
            log_num += 1 
            fwlogs = []
            fwlogs.append(item['fwlog'].meta.creation_time)
            fwlogs.append(item['source_name'])
            fwlogs.append(item['fwlog'].source_ip)
            fwlogs.append(item['destination_name'])
            fwlogs.append(item['fwlog'].destination_ip)
            fwlogs.append(item['fwlog'].protocol)
            fwlogs.append(item['fwlog'].reporter_id)
            final_fwlog.append(fwlogs)
        print(tabulate(final_fwlog, headers=["creation time", "source workload", "source ip", "destination workload", "destination ip", "protocol", "reporter id"]))
        print("There are " + str(log_num) + " matching firewall logs total.")
else:
    print("There are no firewall logs matching the descriptions.")
