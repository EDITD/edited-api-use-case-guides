# historical_options_runner.py
# -------------------------------------------------------
# Reads configuration (API key, filterset ID, log level) from config.ini
# Submits a job request to the /v1/options/history/submit endpoint
# Polls the /v1/jobs/{job_id}/result-files endpoint for completed files
# Downloads files in the current working directory

# === IMPORT LIBRARIES ===
import logging
import os
from time import sleep
from editedapi.configloader import get  # Loads config.ini values
from editedapi.jobsapi import submit_job  # Submits a job to the API
from editedapi.jobsapi import result_files # Checks for results of data from API
from editedapi.jobsapi import get_file # Downloads a file from a specific URL to a location


# === LOGGING SETUP ===
LOG_LEVEL = get("api", "log_level")  # Example: INFO
numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logger = logging.getLogger("historical_options_runner")
logging.basicConfig(level=numeric_level)

# === CONFIGURATION FROM config.ini ===
API_KEY = get("api", "api_key")
FILTERSET_ID = get("api", "filterset_id")
REGION = get("api", "region", default="us") # API region - "us" or "eu"
HEADERS = {"X-API-KEY": API_KEY}

# === WINDOW OF ANALYSIS ===
START_DATE = "2025-06-01"
END_DATE = "2025-06-07"
GRANULARITY = "D"

# === OTHER CONFIG ===
OUTPUT_DIR = "~/results" #Location to download data to

# Confirm that OUTPUT_DIR exists and fail if not
expanded_path = os.path.expanduser(OUTPUT_DIR)
absolute_path = os.path.abspath(expanded_path)
if not os.path.isdir(absolute_path):
    logger.error (f"Error: Output Directory '{absolute_path}' not found.")
    exit()

# Submit job request
job_id = submit_job(
    api_key=API_KEY,
    job_name="Kohl's Footwear",
    start_date=START_DATE,
    end_date=END_DATE,
    granularity=GRANULARITY,
    vertical="apparel",
    filterset_id=FILTERSET_ID,
    region=REGION
    )

next_token=None
idx=0

#Loop every 30 seconds
while True:
    #Poll the status of the job
    job_status = result_files(
        api_key=API_KEY,
        job_id=job_id,
        next_token=next_token,
        region=REGION
    )

    #Get the current job status
    status = job_status.get("job_status")
    print(f"Job {job_id} status: {status}")

    #If we have a failure, detect this and fail
    if status not in ["pending", "queued", "processing", "successful"]:
        print(f"Job {job_id} failed with status: {status}")
        break

    #If we have some results ready for download
    if job_status.get("results_available"):
        start_date = job_status.get("meta", {}).get("start_date")
        end_date = job_status.get("meta", {}).get("end_date")
        urls = job_status.get("urls", [])

        #Loop through all urls that are ready for download and download them to the
        #configured directory
        for url in urls:
            get_file(
                url=url,
                output_file=f"{absolute_path}/job_output_{start_date}_{end_date}_{idx}.ndjson.gz"
            )
            print(f"Result file for {start_date} to {end_date}: {absolute_path}/job_output_{start_date}_{end_date}_{idx}.ndjson.gz")
            idx+=1

    else:
        # No more results available yet, so wait before checking again.
        sleep(30)

    #Get the token for the next set of files
    next_token = job_status.get("next")

    #When we no longer have a next_token we have received all files
    if not next_token:
        # No more results
        print(f"No more results available. job {job_id}. status: {status}.")
        break




