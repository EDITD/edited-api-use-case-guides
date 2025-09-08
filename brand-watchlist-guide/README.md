# Brand Watchlist — EDITED API

This script analyses product actions (such as `new-in`, `removed`, etc.) by brand using the EDITED Query API. It focuses on tracking product lifecycle events across brands and categories over a given time window.

## Purpose

To identify and track product-level changes across multiple brands using a saved EDITED filterset. The output provides:

- Date
- Granularity (e.g. week)
- Brand Name
- Product Category
- Product Action (e.g. new-in, removed)
- Option Count

## How It Works

1. Loads API credentials and filterset ID from `config.ini`.
2. Retrieves the list of brands and product search categories from the saved filterset.
3. Queries the `actions` endpoint for each brand.
4. Extracts all product actions across the specified date window.
5. Maps the product search ID to its category name using the schema.
6. Outputs results into a DataFrame with relevant metadata.

## API Info

### Actions Endpoint

Queries the `actions` endpoint by brand and product category over a defined date range and granularity.

- **Endpoint Used**:  
  `POST /query/v1/apparel/stats/actions`
- **Headers**:
  - `X-API-KEY`: Your EDITED API key
- **Parameters Supported**:
  - `start_date` — Start of the date range (yyyy-MM-dd)
  - `end_date` — End of the date range (yyyy-MM-dd)
  - `period` — Granularity of the reporting window (e.g. week)
  - `filters` — Pulled from a saved filterset
  - `pivots` — Includes product searches to map category names

## Configuration

This script uses the following configurable parameters (set in `config.ini`):

- `api_key`: Your EDITED API key
- `filterset_id`: ID of the filterset containing your brands
- `log_level`: Logging level (e.g. INFO)

Hardcoded parameters in the script:

- `START_DATE`: Start of the analysis window (format yyyy-MM-dd)
- `END_DATE`: End of the analysis window (format yyyy-MM-dd)
- `GRANULARITY`: The granularity of reporting (e.g. week)

## Output Example

## Output Example

| Date       | Granularity | Brand            | Category   | Action              | Option Count |
|------------|-------------|------------------|------------|---------------------|---------------|
| 2025-06-01 | week        | Adidas Originals | Footwear   | first-price-down    | 6             |
| 2025-06-01 | week        | Adidas Originals | Footwear   | new                 | 21            |
| 2025-06-01 | week        | Adidas Originals | Footwear   | price-down          | 75            |
| 2025-06-01 | week        | Adidas Originals | Footwear   | price-down-vs-last  | 101           |
| 2025-06-29 | week        | Nike             | Footwear   | price-up-vs-last    | 11            |
| 2025-06-29 | week        | Nike             | Footwear   | restock             | 10            |
| 2025-06-29 | week        | Nike             | Footwear   | stock-in            | 940           |
| 2025-06-29 | week        | Nike             | Footwear   | stock-out           | 1865          |


## Notes

- The script filters out `any-change` and `sold-out` actions to reduce noise.
- A saved filterset with `brand_slug` and `product_searches` filters is required.
- The category name is resolved from product search schema using the `pivots` parameter.
- Logs are printed to the console based on the `log_level` set in the config file.
