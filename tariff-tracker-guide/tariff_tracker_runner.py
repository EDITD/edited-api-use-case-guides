# tariff_tracker_runner.py
# -----------------------------------------
# Tracks option counts, pricing percentiles and pricing and discount buckets over time by granularity, retailer and product_search

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

# === REPORT CONFIGURATION ===
GRANULARITY = "month"
START_DATE = "2024-01-01"
END_DATE = "2025-06-30"
DISCOUNT_INTERVAL = 10 # Used for Discount Percentage Bucketing (i.e. 10 would provide buckets for No Discount, 0-10%, 10-20%,...,90-100%)
DISCOUNT_TYPE = "ACTUAL" # Controls which price is used to calculate the discount (options: ACTUAL or ADVERTISED)
PRICE_INTERVAL = 25 # Used for Price Bucketing (i.e. 25 would provide pricing buckets for 0-25,25-50, etc.)
PRICE_TYPE = "FULL" # Controls which price is used for the price buckets (options: CURRENT, FULL, ADVERTISED_FULL, FIRST)
PRICE_OVERFLOW_VALUE = 250 # Sets an upper limit on the price buckets. All options above this price point are grouped together
OUTPUT_FILE = "./tariff_tracker.tsv" # Location to save TSV output from script


# === REQUEST CONFIGURATION ===
HEADERS = {'X-API-KEY': API_KEY}

#List of retailers to query
RETAILERS = {
    "Columbia Sports (US)": "columbiasportswear-us",
    "Eddie Bauer (US)": "eddiebauer-us",
    "L.L.Bean (US)": "llbean-us",
    "Lands' End (US)": "landsend-us",
    "The North Face (US)": "thenorthface-us"
}

#List of categories to query
PRODUCT_SEARCHES = {
    "Tops": 221,
    "Outerwear": 553,
    "Bottoms": 535,
    "Accessories": 561,
    "Swim": 560,
    "Footwear": 555
}

#Filters to add for all requests - not iterated over
OTHER_FILTERS = {}

# === MAIN LOGIC STARTS HERE ===
def main():
    #Setup a Data Frame to hold the data.
    column_names=[
        "Date",
        "Granularity",
        "Retailer",
        "Category",
        "Total Options",
        "New In Options",
        "New Full Price Options",
        "Price Down Options",
        "Restock Options",
        "Q1 Price",
        "Median Price",
        "Q3 Price",
        "Average Price",
        "Not Discounted"]
    
    #Get the list of discount percentage intervals expected in the output
    discount_intervals = generate_intervals(DISCOUNT_INTERVAL,100)
    for interval in discount_intervals:
        column_names.append(f"{interval[0]}-{interval[1]}% Discounted")

    #Get the list of price intervals expected in the output
    price_intervals = generate_intervals(PRICE_INTERVAL,PRICE_OVERFLOW_VALUE)
    for interval in price_intervals:
        column_names.append(f"Priced {interval[0]}-{interval[1]}")
    column_names.append(f"Priced Over {PRICE_OVERFLOW_VALUE}")
    
    #Build the initial data frame to hold the queried data
    df = pd.DataFrame(columns=column_names)

    #Get the list of dates to loop through based on our configured granularity, start and end date
    date_list = rewind_dates(granularity=GRANULARITY, startdate=START_DATE, enddate=END_DATE)

    #Get the pricing endpoints that we will need to use based on configuration
    pricing_endpoint = get_pricing_endpoint(PRICE_TYPE)
    priceogram_endpoint = get_priceogram_endpoint(PRICE_TYPE)
    discount_level = get_discount_level(DISCOUNT_TYPE)

    #Create a list of all product_searches to be queried for use in our pivot
    product_searches_pivot=list(PRODUCT_SEARCHES.values())

    #For each retailer required
    for retailer in RETAILERS:
        logger.info(f" Collecting Actions Data for all dates: {START_DATE} - {END_DATE}, granularity: {GRANULARITY}, retailer: {retailer}")
            
        #Filterset to send into the stats endpoints
        filterset = {
            "filters": {
                "in_stock": True,
                "retailer": [RETAILERS[retailer]],
                "product_searches": product_searches_pivot
            },
            "pivots": {
                "product_searches_pivot": {
                    "product_searches": product_searches_pivot
                }                
            }
        }
        filterset['filters'].update(OTHER_FILTERS)
        
        #Send the request to the actions API stats endpoint for all dates
        action_data, action_meta = stats_query(
            endpoint="actions", 
            filterset=filterset, 
            headers=HEADERS,
            params={'start_date': START_DATE, 'end_date': END_DATE, 'period': GRANULARITY})
            
        #Loop through rewind_dates
        for rewind_date in date_list:

            #Query the pricing endpoint to get total options and quartiles based on configured price type
            logger.info(f" Collecting Pricing Data for: Date: {rewind_date}, granularity: {GRANULARITY}, retailer: {retailer}")
            pricing_data, pricing_meta = stats_query(
                endpoint=pricing_endpoint,
                filterset=filterset,
                headers=HEADERS,
                params={'rewind_date': rewind_date, 'period': GRANULARITY})
                
            #Query the priceogram endpoint to get pricing intervals based on configured price type and price interval
            logger.info(f" Collecting Priceogram Data for: Date: {rewind_date}, granularity: {GRANULARITY}, retailer: {retailer}")
            priceogram_data, priceogram_meta = stats_query(
                endpoint=priceogram_endpoint,
                filterset=filterset,
                headers=HEADERS,
                params={'rewind_date': rewind_date, 'period': GRANULARITY, 'interval': PRICE_INTERVAL * 100})
                
            #Query the discount endpoint to get discount intervals based on configured discount type and discount interval
            logger.info(f" Collecting Discount Data for: Date: {rewind_date}, granularity: {GRANULARITY}, retailer: {retailer}")
            discount_data, discount_meta = stats_query(
                endpoint='discount',
                filterset=filterset,
                headers=HEADERS,
                params={'rewind_date': rewind_date, 'period': GRANULARITY, 'discount_interval': DISCOUNT_INTERVAL})
            
            #Build the data record for each product_search in the pivot:
            for product_search in product_searches_pivot:

                #Lookup the meta key for the specific product_search in each API dataset returned
                action_meta_key=next((k for k, v in action_meta.items() if isinstance(v, dict) and v.get("pivots", {}).get("product_searches") == product_search),"no_key")
                pricing_meta_key=next((k for k, v in pricing_meta.items() if isinstance(v, dict) and v.get("pivots", {}).get("product_searches") == product_search),"no_key")
                priceogram_meta_key=next((k for k, v in priceogram_meta.items() if isinstance(v, dict) and v.get("pivots", {}).get("product_searches") == product_search),"no_key")
                discount_meta_key=next((k for k, v in discount_meta.items() if isinstance(v, dict) and v.get("pivots", {}).get("product_searches") == product_search),"no_key")
                
                #Gather all the data from the various API responses into a row
                data={}
                #Set the key dimensions                
                data['Date']=rewind_date
                data['Granularity']=GRANULARITY
                data['Retailer']=retailer
                data['Category']=next((k for k, v in PRODUCT_SEARCHES.items() if v == product_search), None)

                # Get Total Options from pricing_meta
                data['Total Options']=int(pricing_meta.get(pricing_meta_key,{}).get("docs",0))

                # Get Action Data from action_data
                data['New In Options'] = int(action_data.get(action_meta_key,{}).get("actions",{}).get(rewind_date, {}).get("new",0))
                data['New Full Price Options'] = int(action_data.get(action_meta_key,{}).get("actions",{}).get(rewind_date, {}).get("price-up",0))
                data['Price Down Options'] = int(action_data.get(action_meta_key,{}).get("actions",{}).get(rewind_date, {}).get("price-down",0))
                data['Restock Options'] = int(action_data.get(action_meta_key,{}).get("actions",{}).get(rewind_date, {}).get("restock",0))

                #Get Pricing Percentiles from pricing_data. Need to handle the possibility of None when dividing by 100
                q1 = pricing_data.get(pricing_meta_key,{}).get(f"{pricing_endpoint}_percentiles",{}).get("q1",None)
                data['Q1 Price']=q1 / 100 if q1 is not None else 0
                median = pricing_data.get(pricing_meta_key,{}).get(f"{pricing_endpoint}_percentiles",{}).get("median",None)
                data['Median Price']=median / 100 if median is not None else 0
                q3 = pricing_data.get(pricing_meta_key,{}).get(f"{pricing_endpoint}_percentiles",{}).get("q3",None)
                data['Q3 Price']= q3 / 100 if q3 is not None else 0
                avg = pricing_data.get(pricing_meta_key,{}).get(f"{pricing_endpoint}_stats",{}).get("avg",None)
                data['Average Price']= avg / 100 if avg is not None else 0

                #Loop through our discount intervals populating columns dynamically
                total_count=0
                for interval in discount_intervals:
                    column_name = f"{interval[0]}-{interval[1]}% Discounted"
                    count=discount_data.get(discount_meta_key,{}).get(discount_level,{}).get(str(interval[0]),0)
                    data[column_name]=count
                    total_count+=count

                #Calculate the remaining options as not discounted
                data[f"Not Discounted"]=data["Total Options"]-total_count

                #Loop through our price intervals populating columns dynamically
                total_count=0
                for interval in price_intervals:
                    column_name = f"Priced {interval[0]}-{interval[1]}"
                    count=priceogram_data.get(priceogram_meta_key,{}).get(priceogram_endpoint, {}).get(str(interval[0] * 100), {}).get("count",0)
                    data[column_name]=count
                    total_count+=count

                #Calculate the remaining options for the overflow bucket
                data[f"Priced Over {PRICE_OVERFLOW_VALUE}"]=data["Total Options"]-total_count
                
                df.loc[len(df)] = data
            
    #Print sample output and save all data to a TSV file
    print("\nSample Data Set:\n") 
    print(df.head(10).T)
    df.to_csv(OUTPUT_FILE, sep='\t', index=False)
    quit()

#Function to dynamically build out the intervals required
def generate_intervals(interval, max):
    if not 1 <= interval <= max:
        raise ValueError(f"Input must be between 1 and {max}.")

    if max % interval != 0:
        raise ValueError(f"{max} is not perfectly divisible by the interval {interval}.")

    intervals = []
    for i in range(0, max, interval):
        intervals.append((i, i + interval))

    return intervals

#Function to return the correct pricing endpoint based on configuration
def get_pricing_endpoint(price_type):
    match price_type:
        case "CURRENT":
            return "pricing"
        case "FULL":
            return "pricing_full"
        case "ADVERTISED_FULL":
            return "pricing_inferred_full"
        case "FIRST": 
            return "pricing_first"
    raise ValueError(f"{price_type} is not one of: CURRENT, FULL, ADVERTISED_FULL or FIRST.")

#Function to return the correct priceogram endpoint based on configuration
def get_priceogram_endpoint(price_type):
    match price_type:
        case "CURRENT":
            return "priceogram"
        case "FULL":
            return "priceogram_full"
        case "ADVERTISED_FULL":
            return "priceogram_inferred_full"
        case "FIRST": 
            return "priceogram_first"
    raise ValueError(f"{price_type} is not one of: CURRENT, FULL, ADVERTISED_FULL or FIRST.")

#Function to return the correct discount endpoint based on configuration
def get_discount_level(discount_type):
    match discount_type:
        case "ACTUAL":
            return "discounts"
        case "ADVERTISED":
            return "advertised_discounts"
    
    raise ValueError(f"{discount_type} is not one of: ACTUAL or ADVERTISED.")

    
if __name__ == "__main__":
    main()
