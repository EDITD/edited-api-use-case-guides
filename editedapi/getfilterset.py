# Import modules used in the function
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Function to use filterset ID to pull in a filterset for use in other API calls
def get_filterset(filterset_id=None, headers=None, attempt_number=1):
    """Uses a filterset id to programmatically pull a filterset from Edited Market for use in other API Calls

    Args:
        filterset_id: An alphanumeric id found in an Edited Market workbook
        headers: A dictionary containing the value/key pair of x-api-key and your API KEY

    Returns:
        A dictionary containing filters that can be used in the body of another API call

    Raises:
        None
    """
    try:
        session = requests.Session()

        # Add retry logic for better fault tolerance
        retries = Retry(
            total=4,
            backoff_factor=5,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["GET"]  # GET is the correct method here
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        response = session.get(
            url=f"https://apis.edited.com/filtersets/v1/{filterset_id}",
            headers=headers,
            timeout=(30, 60),
        )
        response.raise_for_status()  # Raises HTTPError for bad responses

        try:
            response_data = response.json()
        except ValueError as e:
            logger.warning(f"Attempt {attempt_number}: Failed to parse JSON - {e}")
            if attempt_number < 3:
                return get_filterset(filterset_id=filterset_id, headers=headers, attempt_number=attempt_number + 1)
            raise

        return response_data

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise