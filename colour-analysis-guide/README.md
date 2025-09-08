# Colour Trend Tracker — EDITED API

This script analyses colour trends for fashion retailers by querying the EDITED Query API. It focuses on **new colours introduced** and **current colour presence** for selected retailers, genders, and product types.

## Purpose

To identify and track both total and new product colour introductions by **Brand (retailer)**,  **Gender (eg. boys, girls)**, **Product Category (eg. Tops, Bottoms)** and **Predominant Colour (eg Blue, Pink, Black)**

The output provides
- Option Count
- New In Option Count

## How It Works

1. Defines a filterset for each retailer, gender and product_search being queried.
2. Loops through all combinations by date and queries:
   - The number of options by predomninant color
   - The number of new options by predominant colour
3. Merges all metrics for each combination of output fields.
4. Prints the sample output in a readable table in the console.

## API Info

### Terms Endpoint

Queries the `terms` endpoint twice for each granularity, retailer, gender and product_search. The first request gets total option count by predominant colour. The second request adds a filter for `"actions": ["new"]` to get new in option count by predominant colour.

- **Endpoint Used**:  
  `POST /query/v1/apparel/stats/terms`
- **Headers**:
  - `X-API-KEY`: Your EDITED API key
- **Parameters Supported**:
  - `rewind_date` - The first day of the period for each granularity
  - `period` - Set to the granularity required
  - `bucket` - Set to `predominant_colour`
- **Metrics Supported**:
  - `Option Count` — Total option count during the reporting period
  - `New In Option Count` — Count of options that have had a `new` action during the reporting period.

## Configuration

This script uses the following configurable parameters
- `START_DATE`: First day to pull data for (format yyyy-MM-dd)
- `END_DATE`: The last date to pull data for (format yyyy-MM-dd)
- `GRANULARITY`: The requested granularity (day, week or month)
- `RETAILERS`: The list of retailers to analyse
- `GENDERS`: The list of genders to analyse
- `PRODUCT_SEARCHES`: The list of EDITED categories to analyse
- `OTHER_FILTERS`: Additional filters that you might want applied to each request.

## Output Example

| Date       | Granularity | Retailer     | Gender | Category | Colour | Option Count | New In Option Count |
|------------|-------------|--------------|--------|----------|--------|--------------|---------------------|
| 2025-06-08 | week        | Carters (US) | Boys   | Tops     | aqua   | 20           | 0                   |
| 2025-06-08 | week        | Carters (US) | Boys   | Tops     | black  | 22           | 1                   |
| 2025-06-08 | week        | Carters (US) | Boys   | Tops     | blue   | 86           | 8                   |
| 2025-06-08 | week        | Carters (US) | Boys   | Tops     | brown  | 36           | 10                  |

