# brand_watchlist_runner.py
# -------------------------------------------------------
# This script checks for product actions (e.g. new, removed) by brand using the EDITED Query API.
# It reads configuration (API key, filterset ID, log level) from config.ini
# and uses shared utilities from the editedapi package.
# For each brand, it checks if product actions occur starting from a base date, for up to N days forward.

# === IMPORT LIBRARIES ===
import pandas as pd
import logging
from editedapi.configloader import get  # Loads config.ini values
from editedapi.getfilterset import get_filterset  # Loads filters from a saved filterset
from editedapi.statsquery import stats_query #Call to the stats endpoints
from editedapi.getschema import get_schema #Requests the schema from the API

# === LOGGING SETUP ===
LOG_LEVEL = get("api", "log_level")  # Example: INFO
numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logger = logging.getLogger("brand_watchlist_runner")
logging.basicConfig(level=numeric_level)

# === CONFIGURATION FROM config.ini ===
API_KEY = get("api", "api_key")
FILTERSET_ID = get("api", "filterset_id")
HEADERS = {"X-API-KEY": API_KEY}
BASE_URL = "https://apis.edited.com"

# === WINDOW OF ANALYSIS ===
START_DATE = "2025-06-01"  # Starting date to check for product actions
END_DATE = "2025-06-30"
GRANULARITY = "week"

# === MAIN EXECUTION BLOCK ===
def main():
    # Set up an empty DataFrame to store the output
    column_names = ["Date", "Granularity", "Brand", "Category", "Action", "Option Count"]
    df = pd.DataFrame(columns=column_names)
    logger.info(f"Starting brand watchlist scan from {START_DATE} to {END_DATE}")

    # Retrieve the saved filterset object using the provided ID
    filterset_obj = get_filterset(filterset_id=FILTERSET_ID, headers=HEADERS)

    # Retrieve the product_searches schema so we can print the category name and not just the id
    product_searches_schema = get_schema(schema="searches", headers=HEADERS)

    # Retrieve the brands schema so we can print the category name and not just the id
    brands_schema = get_schema(schema="brands", headers=HEADERS)

    brands = filterset_obj.get("filters",{}).get("brand_slug")
    if brands is None:
        logger.error("Filter Set must have a filter for brand_slug")
        quit()

    logger.info(f"Brands found in filterset: {brands}")

    #Product Searches Pivot:
    product_searches = filterset_obj.get("filters",{}).get("product_searches",[])
    product_searches_pivot = {
        "product_searches_pivot": {
            "product_searches": product_searches
        }
    }

    filterset_obj["pivots"]=product_searches_pivot

    # Loop over each brand in the filterset
    for brand in brands:
        logger.info(f"Checking brand: {brand}")
        filterset_obj['filters']['brand_slug'] = [brand]

        brand_name = next((item["name"] for item in brands_schema["brands"] if item["slug"] == brand), "Unknown")

        action_data, action_meta = stats_query(
            endpoint="actions", 
            filterset=filterset_obj, 
            headers=HEADERS,
            params={'start_date': START_DATE, 'end_date': END_DATE, 'period': GRANULARITY})

        for key in action_data:
            #Get the product search id and look up the actual category name.
            #If we had not product_search, then set category name to 'All Categories'
            product_search = action_meta.get(key,{}).get("pivots",{}).get("product_searches", None)
            if product_search is None:
                category = "All Categories"
            else:
                category = next((item["name"] for item in product_searches_schema["searches"] if item["id"] == product_search), "Unknown")

            key_data = action_data.get(key).get('actions',{})
            for date in key_data:
                actions=key_data.get(date)
                for action in actions:
                    if action in ["any-change", "sold-out"]:
                        continue
                    
                    data = {
                        'Date': date,
                        'Granularity': GRANULARITY,
                        'Brand': brand_name,
                        'Category': category,
                        'Action': action,
                        'Option Count': actions.get(action)
                        }
                    #Add record to the data frame
                    df.loc[len(df)] = data

    # === FINAL OUTPUT ===
    print("\nSample Data Set:\n")
    print(df)

if __name__ == "__main__":
    main()