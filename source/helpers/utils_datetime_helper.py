# Import datetime to handle time-related data
from datetime import datetime

#========== DATETIME CONFIGURATION ==========

dt_format = "%Y-%m-%d"

def dt_to_string(dt: datetime) -> str:
    # Converts a datetime object to string in the fixed project format

    if not isinstance(dt,datetime):
        raise ValueError("input is not a datetime")
    else:
        return dt.strftime(dt_format)

def string_to_dt(dt_string: str) -> datetime:
    # Converts a string object to datetime in the fixed project format

    if not isinstance(dt_string,str):
        raise ValueError("input is not a string")
    else:
        return datetime.strptime(dt_string,dt_format)