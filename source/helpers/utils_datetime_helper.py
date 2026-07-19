# Import datetime to handle time related data
from datetime import datetime

#========== DATETIME CONFIGURATION ==========

dt_format = "%Y-%m-%d"

def dt_to_string(dt: datetime) -> str:
    """
    Converts datetime object to string in fixed dt_format

    Returns:
        datetime_string (str): input datetime in fixed dt_format
    """

    if not isinstance(dt,datetime):
        raise ValueError("input is not a datetime")
    else:
        return dt.strftime(dt_format)

def string_to_dt(dt_string: str) -> datetime:
    """
    Converts string that contains date information to datetime object in accordance with the fixed dt_format

    Returns:
        date (datetime): returns the corresponding datetime to the input dt_string
    """

    if not isinstance(dt_string,str):
        raise ValueError("input is not a string")
    else:
        return datetime.strptime(dt_string,dt_format)