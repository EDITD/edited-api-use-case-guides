# Import modules used in the function
import requests
import logging
import json

# Set up logger
logger = logging.getLogger(__name__)

# Function to pull schema data from the EDITED API
def submit_job(api_key, job_name, start_date, end_date, granularity, newest_first=False, vertical="apparel", currency=None, fields=None, legacy_filters=None, filterset_id=None):
    """Builds a jobs request and submits it to the jobs API

    Args:
        api_key: API Key to run the request
        job_name: Symbolic name of the Job
        start_date: yyyy-MM-dd
        end_date: yyyy-MM-dd
        granularity: Valid Values - D, W or M
        newest_first: Boolean (defaults to False)
        vertical: Valid Values - apparel, homeware
        currency: The currency code to convert all price fields too (defaults to USD)
        fields: The fields to retrieve. If not specified, all fields are retrieved.
        legacy_filters: The filters to submit to the job (Required unless using filterset_id)
        filterset_id: Filter Set ID for the job (Required unless passing in legacy_filters)

    Returns:
        A job id string

    Raises:
        None
    """
    HEADERS = {"X-API-KEY": api_key}

    if legacy_filters is None and filterset_id is None:
        logger.error (f"Must pass at least one of 'legacy_filters' or 'filterset_id' to submit_job()")
        exit() 


    REQUEST = {
        "name": job_name,
        "start_date": start_date,
        "end_date": end_date,
        "granularity": granularity,
        "newest_first": newest_first,
        "vertical": vertical,
        "filterset_id": filterset_id
    }

    if filterset_id is not None:
        REQUEST["filterset_id"] = filterset_id

    if legacy_filters is not None:
        REQUEST['legacy_filters'] = legacy_filters

    if currency is not None:
        REQUEST['currency'] = currency

    if fields is not None:
        REQUEST['fields'] = fields
    
    print(f"Submitting Job Request:") 
    print(json.dumps(REQUEST, indent=4))

    try:
        response = requests.post(
            url="https://api-us.edited.com/v1/options/history/submit",
            headers=HEADERS,
            json=REQUEST,
            timeout=60.0
        )
        
        response.raise_for_status()  # Raises HTTPError for bad responses

        try:
            response_data = response.json()
        except ValueError as e:
            logger.warning(f"Failed to parse JSON - {e}")
            raise

        job_id = response_data.get("job_id")
        if job_id is None:
            raise ValueError("Missing 'job_id' in response")

        print(f"Job Submitted with ID: {job_id}")
        return job_id

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

# Function to pull schema data from the EDITED API
def result_files(api_key, job_id, next_token=None):
    """Polls for status of a currently running job

    Args:
        api_key: API Key to run the request
        job_id: Job ID of the running job
        next_token: Token for the next set of results

    Returns:
        API response

    Raises:
        None
    """
    HEADERS = {"X-API-KEY": api_key}

    try:
        response = requests.get(
            url=f"https://api-us.edited.com/v1/jobs/{job_id}/result-files",
            params={"next": next_token} if next_token else None,
            headers=HEADERS,
            timeout=60.0
        )
        
        response.raise_for_status()  # Raises HTTPError for bad responses

        try:
            response_data = response.json()
        except ValueError as e:
            logger.warning(f"Failed to parse JSON - {e}")
            raise

        return response_data

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

# Function to pull schema data from the EDITED API
def get_file(url, output_file):
    """Downloads a file from a given url to the output_location

    Args:
        url: The URL to download
        output_file: The outputfile to save the contents of the download.

    Returns:
        None

    Raises:
        None
    """
    file_data = requests.get(url)
    with open(output_file, "wb") as file:  # "wb" = write in binary
        file.write(file_data.content)

    return None