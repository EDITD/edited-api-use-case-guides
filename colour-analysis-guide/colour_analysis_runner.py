# color_analysis_runner.py
# -----------------------------------------
# Add in summary of what this script does

import pandas as pd
import logging
from editedapi.configloader import get
from editedapi.statsquery import stats_query
from editedapi.rewinddates import rewind_dates

# === CONFIGURATION FROM CONFIG FILE ===
LOG_LEVEL = get("api", "log_level")
API_KEY = get("api", "api_key")

# === SETUP LOGGING ===
numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logger = logging.getLogger("tariff_tracker_runner")
logging.basicConfig(level=numeric_level)

# === DATE RANGE ===
GRANULARITY = "week"
START_DATE = "2025-06-08"
END_DATE = "2025-06-22"

# === REQUEST CONFIGURATION ===
HEADERS = {'X-API-KEY': API_KEY}

#List of retailers to query
RETAILERS = {
    "Carters (US)": "carters-us",
    "Osh Kosh B'Gosh (US)": "oshkosh-us",
    "Childrens Place (US)": "childrensplace-us",
    "GAP (US)": "gap",
    "Old Navy (US)": "oldnavy",
    "Zara (US)": "zara-us",
    "Target (US)": "target"
}

#List of genders to query
GENDERS = {
    "Boys": "boys",
    "Girls": "girls",
    "Unisex (Kids)": "unisex-kids"
}

#List of categories to query
PRODUCT_SEARCHES = {
    "Dresses": 138,
    "Tops": 221,
    "Bottoms": 535,
    "Outerwear": 553,
    "All-in-ones": 554,
    "Underwear": 556,
    "Sleepwear": 558,
    "Suits/Sets": 699
}

#Filters to add for all requests - not iterated over
OTHER_FILTERS = {}

# === MAIN LOGIC STARTS HERE ===
def main():
    #Setup a Data Frame to hold the data.
    column_names=["Date","Granularity","Retailer","Gender","Category","Predominant Colour","Option Count", "New In Option Count"]
    df = pd.DataFrame(columns=column_names)

    #Get the list of dates to loop through based on our configured granularity, start and end date
    date_list=rewind_dates(granularity=GRANULARITY, startdate=START_DATE, enddate=END_DATE)

    #For each date required
    for rewind_date in date_list:
        #For each retailer required
        for retailer in RETAILERS:
            #For each gender required
            for gender in GENDERS:
                #For each search required
                for search in PRODUCT_SEARCHES:
                    logger.info(f" Collecting Data for date: {rewind_date}, retailer: {retailer}, gender: {gender}, category: {search}")
                    
                    #Filterset to send into the terms API stats endpoint to get the unique count of options by predominant_colour
                    count_filterset = {
                        "filters": {
                            "retailer": [RETAILERS[retailer]],
                            "gender": [GENDERS[gender]],
                            "product_searches": [PRODUCT_SEARCHES[search]]
                        }
                    }
                    count_filterset['filters'].update(OTHER_FILTERS)

                    #Send the request to the terms API stats endpoint
                    option_count_data, option_count_meta = stats_query(
                        endpoint="terms", 
                        filterset=count_filterset, 
                        headers=HEADERS,
                        params={'rewind_date': rewind_date, 'period': GRANULARITY, 'bucket': 'predominant_colour'})
                
                    #Create a list of the predominant colours found for the filterset
                    colour_pivot=list(option_count_data['predominant_colour__terms'].keys())

                    #If we matched no options, then there is no need to make the second API call
                    if not colour_pivot: continue               

                    #Filteret to send into the actions API stats endpoint. This mimics the previous filter, but ads a pivot
                    #to enable us to get the number of 'new' options by predominant color for the given granularity
                    new_filterset = {
                        "filters": {
                            "retailer": [RETAILERS[retailer]],
                            "gender": [GENDERS[gender]],
                            "product_searches": [PRODUCT_SEARCHES[search]],
                            "actions": ["new"]
                        }
                    }
                    
                    new_filterset['filters'].update(OTHER_FILTERS)

                    #Send the request to the actions API stats endpoint
                    newin_data, newin_meta = stats_query(
                        endpoint="terms", 
                        filterset=new_filterset, 
                        headers=HEADERS,
                        params={'rewind_date': rewind_date, 'period': GRANULARITY, 'bucket': 'predominant_colour'})

                    #Loop through each color returned by the first terms api endpoint call                    
                    for colour in colour_pivot:
                        #Create a data record for each date, granularity, retailer, gender, category and color combination
                        newin_count=0
                        if colour in newin_data['predominant_colour__terms']: 
                            newin_count=newin_data['predominant_colour__terms'][colour]

                        data = {
                        'Date': rewind_date,
                        'Granularity': GRANULARITY,
                        'Retailer': retailer,
                        'Gender': gender,
                        'Category': search,
                        'Predominant Colour': colour,
                        'Option Count': option_count_data['predominant_colour__terms'][colour],
                        'New In Option Count': newin_count
                        }

                        #Add record to the data frame
                        df.loc[len(df)] = data 

    #Print a sample of the final output data   
    print("\nSample Data Set:\n")             
    print(df)          

if __name__ == "__main__":
    main()

