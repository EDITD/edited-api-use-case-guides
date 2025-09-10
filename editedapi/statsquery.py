#Import modules used in the function

import logging
import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)

def stats_query(endpoint=None, attempt_number=1, filterset=None, params=None, headers=None):
    """
    Makes a POST request to a specified Edited Market API stats endpoint with retry logic and error handling.

    Args:
        endpoint: The full URL to which the POST request should be made.
        attempt_number: Internal use for retry tracking. Defaults to 1.
        filterset: A dictionary of filters to include in the body of the POST request (usually obtained from a filterset call).
        params: Optional query parameters to include in the request URL.
        headers: A dictionary containing the key/value pair of 'x-api-key' and your API key.

    Returns:
        A tuple containing:
            - data: The response's 'data' field as a dictionary or list.
            - meta: The response's 'meta' field, often containing pagination or summary info.

    Raises:
        ValueError: If the response is missing expected 'data' or 'meta' fields, or if JSON decoding fails repeatedly.
        requests.RequestException: If the HTTP request encounters an error that cannot be recovered from via retries.
    """
    try:
        session = requests.Session()
        retries = Retry(
            total=4,
            backoff_factor=5,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        response = session.post(
            url=f"https://apis.edited.com/query/v1/apparel/stats/{endpoint}",
            json=filterset,
            headers=headers,
            params=params,
            timeout=(30, 60),
        )

        response.raise_for_status()  # Raises HTTPError for bad responses

        try:
            response_data = response.json()
        except ValueError as e:
            logger.warning(f"Attempt {attempt_number}: Failed to parse JSON - {e}")
            if attempt_number < 3:
                return stats_query(endpoint, attempt_number+1, filterset, params, headers)
            raise

        data = response_data.get("data")
        meta = response_data.get("meta")
        if data is None or meta is None:
            raise ValueError("Missing 'data' or 'meta' in response")

        return data, meta

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise
