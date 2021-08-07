import datetime, re
from datetime import timezone
import sys, logging


def time_delta_from_now(age, current_time): 
    if age:
        #if user does not specify time length, the default unit is hours
        if age.isnumeric():
            print("Since no time unit is specified, logs within recent " + age + " hours are returned.")
            desired_time = current_time - datetime.timedelta(hours = int(age))
        elif age.isalpha():
            logging.error("Please enter valid input. e.g. --age 3h")
            sys.exit()
        else:
            date_type = "".join(re.split("[^a-zA-Z]*", age))
            date_number = "".join(re.split("[^0-9]*", age))
            if date_type == "h" or "hour" in date_type:
                desired_time = current_time - datetime.timedelta(hours = ( int(date_number)))
            elif date_type == "w" or "week" in date_type:
                desired_time = current_time - datetime.timedelta(weeks = int(date_number))
            elif date_type == "d" or "day" in date_type:
                desired_time = current_time - datetime.timedelta(days = int(date_number))
            else:
                logging.error("Please enter valid input. e.g. --age 5h")
                sys.exit()
        return desired_time
