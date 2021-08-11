import os
from utils.datatime_utils import time_delta_from_now
from datetime import timezone
import datetime
import warnings
from apigroups.client import configuration, api_client

warnings.simplefilter("ignore")

HOME = os.environ['HOME']

cfg = configuration.Configuration(
    psm_config_path=HOME+"/.psm/config.json",
    interactive_mode=True
)
cfg.verify_ssl = False
client = api_client.ApiClient(cfg)

current_time = datetime.datetime.now(timezone.utc)

#an integer input without units
print(time_delta_from_now('12', current_time))

#a valid hour input
print(time_delta_from_now('12h', current_time))

#a negative hour input
print(time_delta_from_now('-12h', current_time))

#a decimal hour input
print(time_delta_from_now('1.2h', current_time))

#an extremely small hour input
print(time_delta_from_now('.0000001h', current_time))

#an extremely large hour input
print(time_delta_from_now('100000000', current_time))

#an input not in unit 'hours'
print(time_delta_from_now('12d', current_time))

#an input with 'hours' spelled out
print(time_delta_from_now('12hours', current_time))

#a string input
print(time_delta_from_now('twelvehrs', current_time))
