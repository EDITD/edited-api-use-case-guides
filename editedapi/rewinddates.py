#Import modules used in the function

import logging
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)

def rewind_dates(granularity, startdate, enddate):
    """
    Given a granularity, startdate and enddate returns a list of dates that can be looped through

    Args:
        granularity: valid values are 'day', 'week' and 'month'
        stardate: the first date for analysis
        enddate: the last date for analysis

    Returns:
        A list of string dates based on granularity between the start and end dates
    """

    valid_granularities = ['day', 'week', 'month']

    if granularity not in valid_granularities:
        logger.error (f"{granularity} granularity is not one of: day, week or month")
        exit()

    if not is_valid_date_format(startdate,"%Y-%m-%d"):
        logger.error (f"{startdate} startdate parameter is not valid. Expected yyyy-MM-dd format")
        exit ()

    if not is_valid_date_format(enddate,"%Y-%m-%d"):
        logger.error (f"{enddate} enddate parameter is not valid. Expected yyyy-MM-dd format")
        exit ()

    date_list = []

    current_date = datetime.strptime(startdate, "%Y-%m-%d")
    end_date = datetime.strptime(enddate, "%Y-%m-%d")

    match granularity:
        case "day":
            while current_date <= end_date:
                date_list.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
        case "week":
            current_date -= timedelta(days=(current_date.weekday() + 1) % 7)
            while current_date <= end_date:
                date_list.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(weeks=1)
        case "month":
            year, month = current_date.year, current_date.month
            while (year, month) <= (end_date.year, end_date.month):
                first_of_month = date(year, month, 1)
                date_list.append(first_of_month.strftime("%Y-%m-%d"))
                # Move to next month
                month += 1
                if month > 12:
                    month = 1
                    year += 1
    
    return date_list

def is_valid_date_format(date_string, date_format):
    """
    Checks if a string represents a valid date according to a given format.

    Args:
        date_string (str): The string to validate.
        date_format (str): The expected date format (e.g., "%Y-%m-%d", "%d/%m/%Y").

    Returns:
        bool: True if the string is a valid date in the specified format, False otherwise.
    """
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False