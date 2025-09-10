# Historical Options — EDITED Jobs API

Based on user feedback regarding the challenges of landing large datasets with our legacy API (specifically the `options` endpoint), EDITED has introduced a new paradigm for collecting option or homeware sku level data. This paradigm moves to defining a "job" that encompasses the date ranges and filters being requested. Jobs can be managed with different endpoints. See the full documentation and spec for more details.

This script demonstrates the basic workflow for using EDITED Jobs API to download historical option level documents (NDJSON gzip compressed) for a given filter set ID.

## Purpose

To download larger sets of historical option level documents across a given date range and granularity

## How It Works

1. Loads API credentials and filterset ID from `config.ini`.
2. Submits a job to the API for a given date range and granularity
3. Polls the status of the API every 30 seconds
4. Downloads NDJSON gzipped files as data becomes available
5. Completes once all data is downloaded

## API Info

### Options History Submit Job Endpoint

Sends a request to the `submit` endpoint to start a historical pull of option level data.

- **Endpoint**:  
  `POST /v1/options/history/submit`
- **Headers**:
  - `X-API-KEY`: Your EDITED API key
- **Request Body**:
  - `name` - Name of the job to be started
  - `start_date` — Start of the date range (yyyy-MM-dd)
  - `end_date` — End of the date range (yyyy-MM-dd)
  - `granularity` — Granularity of the reporting window (e.g. D, W , M)
  - `filterset_id` — Filter set used to pull option data
  - `vertical` — The vertical to run the job against (i.e. apparel)

### Options History Result Files Endpoint

Sends a request to the `result-files` endpoint to check status of the job and download any completed file uploads

- **Endpoint**:  
  `POST v1/jobs/<job_id>/result-files`
- **Headers**:
  - `X-API-KEY`: Your EDITED API key
- **Request Parameters**:
  - `next` - The next_token for use in paginating through completed file uploads

## Configuration

This script uses the following configurable parameters (set in `config.ini`):

- `api_key`: Your EDITED API key
- `filterset_id`: ID of the filterset containing your filters
- `log_level`: Logging level (e.g. INFO)

Hardcoded parameters in the script:

- `START_DATE`: Start of the analysis window (format yyyy-MM-dd)
- `END_DATE`: End of the analysis window (format yyyy-MM-dd)
- `GRANULARITY`: The granularity of reporting (e.g. D, W, M)
- `OUTPUT_DIR`: The directory to save the downloaded output files.

## Output Example

```
$ ls -al results/
total 61456
drwxr-xr-x  2 user group     4096 Aug 23 10:19 .
drwxr-xr-x 11 user group     4096 Aug 23 09:00 ..
-rw-r--r--  1 user group 10160894 Aug 23 10:19 job_output_2025-06-01_2025-06-01_0.ndjson.gz
-rw-r--r--  1 user group  5837403 Aug 23 10:19 job_output_2025-06-01_2025-06-01_1.ndjson.gz
-rw-r--r--  1 user group 10174424 Aug 23 10:19 job_output_2025-06-02_2025-06-02_0.ndjson.gz
-rw-r--r--  1 user group  5446350 Aug 23 10:19 job_output_2025-06-02_2025-06-02_1.ndjson.gz
-rw-r--r--  1 user group 10169044 Aug 23 10:19 job_output_2025-06-03_2025-06-03_0.ndjson.gz
-rw-r--r--  1 user group  5582503 Aug 23 10:19 job_output_2025-06-03_2025-06-03_1.ndjson.gz
-rw-r--r--  1 user group 10178981 Aug 23 10:19 job_output_2025-06-04_2025-06-04_0.ndjson.gz
-rw-r--r--  1 user group  5358363 Aug 23 10:19 job_output_2025-06-04_2025-06-04_1.ndjson.gz
```
