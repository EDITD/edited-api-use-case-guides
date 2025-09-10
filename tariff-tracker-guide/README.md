# Tariff Tracker — EDITED API

When EDITED launched the [Tariff Tracker](https://edited.com/tariff-tracker/), we received many questions about how to operationalize the same kind of information but make it specific to a retailer's business. While many of the questions can be answered using the UI, the API enables the iteration and scale you might need for certain types of analysis. This use case guide focuses on those aspects where we found iteration and scale were key.

This code is intended to enable analysis of pricing and discounting architecture over time at a category+retailer level. You can use this data to discover where competitors are making price adjustments gradually over time. The configuration enables you to choose to focus on advertised price / discount or actual price / discount as well as looking at the values broken into intervals, to find the details hidden in the averages. 

It is easy to copy and modify the code if you need a slightly different lens such as brand, gender, or other aggregates. Feel free to let us know if you need additional guidance.

## Purpose

To identify and track option counts, pricing percentiles and pricing and discount buckets over time by **Brand (retailer)** and **Product Category (eg. Tops, Bottoms)**

The output provides:
- Total Options
- New Options
- Options that have reached their highest price ever
- Options that have reduced in price
- Options that have been restocked
- Pricing Quartiles (configurable by current, full, advertised full or first price points)
- Discount Percentage Buckets (configurable by actual or advertised discounts)
- Pricing Buckets (configurable by current, full, advertised full or first price points)

## How It Works

1. Defines a filterset for each retailer being queried.
2. Sets up a pivot on the product_searches in the analysis.
3. Loops through all date and retailer combinations and queries various stats endpoints for:
   - actions that have occurred
   - pricing percentiles
   - discounting buckets
   - priceogram buckets
4. Merges all metrics for each combination of output fields.
5. Prints the sample output in a readable table in the console.
6. Saves the full result set to a TSV file.

## API Info

### Actions Endpoint

Queries this endpoint once for each retailer across the entire required date range.

- **Endpoint Used**:  
  `POST /query/v1/apparel/stats/actions`
- **Headers**:
  - `X-API-KEY`: Your EDITED API key
- **Parameters Supported**:
  - `startDate` - Set to the first date of the analysis
  - `endDate` - Set to the last date of the analysis
  - `period` - Set to the granularity required
- **Metrics Supported**:
  - `New In Options` — Count of options that have had a `new` action during the reporting period.
  - `New Full Price Options` — Count of options that have had a `price-up` action during the reporting period.
  - `Price Down Options` - Count of options that have had a `price-down` action during the reporting period.
  - `Restock Options` - Count of options that have had a `restock` action during the reporting period.

### Pricing Endpoint(s)

Queries one of four possible pricing endpoints (configurable) for each retailer by each separate granularity

- **Endpoint Used**:  
  `POST /query/v1/apparel/stats/pricing`

  `POST /query/v1/apparel/stats/pricing_full`

  `POST /query/v1/apparel/stats/pricing_inferred_full`
  
  `POST /query/v1/apparel/stats/pricing_first`
- **Headers**:
  - `X-API-KEY`: Your EDITED API key
- **Parameters Supported**:
  - `rewind_date` - The first day of the period for each granularity
  - `period` - Set to the granularity required
- **Metrics Supported**:
  - `Total Options` — Count of options during the reporting granularity/period.
  - `Q1 Price` — 25th percentile price during the reporting granularity/period.
  - `Median Price` - Median price during the reporting granularity/period.
  - `Q3 Price` - 75th percential price during the reporting granularity/period.
  - `Average Price` - Average price during the reporting granularity/period.

### Discount Endpoint(s)

Queries one of two possible discount endpoints (configurable) for each retailer by each separate granularity

- **Endpoint Used**:  
  `POST /query/v1/apparel/stats/discounts`

  `POST /query/v1/apparel/stats/advertised_discounts`
- **Headers**:
  - `X-API-KEY`: Your EDITED API key
- **Parameters Supported**:
  - `rewind_date` - The first day of the period for each granularity
  - `period` - Set to the granularity required
- **Metrics Supported**:
  - `##=##% Discounted` — Count of options that fit into each discount interval bucket (i.e. 0-10% Discounted, 10-20 Discounted, ..., 90-100% Discounted)

### Priceogram Endpoint(s)

Queries one of four possible priceogram endpoints (configurable) for each retailer by each separate granularity

- **Endpoint Used**:  
  `POST /query/v1/apparel/stats/priceogram`

  `POST /query/v1/apparel/stats/priceogram_full`

  `POST /query/v1/apparel/stats/priceogram_inferred_full`

  `POST /query/v1/apparel/stats/priceogram_first`
- **Headers**:
  - `X-API-KEY`: Your EDITED API key
- **Parameters Supported**:
  - `rewind_date` - The first day of the period for each granularity
  - `period` - Set to the granularity required
- **Metrics Supported**:
  - `Priced ##-##` — Count of options that fit into each pricing interval bucket (i.e. Priced 0-25, Priced 25-50, ..., Priced over 250)

## Configuration

This script uses the following configurable parameters
- `START_DATE`: First day to pull data for (format yyyy-MM-dd).
- `END_DATE`: The last date to pull data for (format yyyy-MM-dd).
- `GRANULARITY`: The requested granularity (day, week or month).
- `DISCOUNT_TYPE`: Valid values: ACTUAL, ADVERTISED
- `DISCOUNT_INTERVAL`: The size of each discount bucket (must be divisible by 100).
- `PRICE_TYPE`: Valid values: CURRENT, FULL, ADVERTISED_FULL, FIRST
- `PRICE_INTERVAL`: The size of each pricing bucket.
- `PRICE_OVERFLOW_VALUE`: Sets an upper limit on the price buckets. All options above this price point are grouped together.
- `OUTPUT_FILE`: Location to save the output TSV data.
- `RETAILERS`: The list of retailers to analyse.
- `PRODUCT_SEARCHES`: The list of EDITED categories to analyse.
- `OTHER_FILTERS`: Additional filters that you might want applied to each request.

## Output Example

```
Date                              2024-01-01            2024-01-01            2024-01-01            2024-01-01            2024-01-01            2024-01-01
Granularity                            month                 month                 month                 month                 month                 month
Retailer                Columbia Sports (US)  Columbia Sports (US)  Columbia Sports (US)  Columbia Sports (US)  Columbia Sports (US)  Columbia Sports (US)
Category                                Tops             Outerwear               Bottoms           Accessories                  Swim              Footwear
Total Options                           3841                  3745                  1357                  1251                    98                   997
New In Options                           484                   227                   202                    53                    27                    74
New Full Price Options                     4                     1                     3                     3                     0                     1
Price Down Options                      1568                  1906                   236                   603                     6                   155
Restock Options                          241                   152                    78                     9                     3                   174
Q1 Price                                45.0                  75.0                  45.0                  30.0                  25.0                70.125
Median Price                            50.0                 110.0                 59.99                  32.0                  30.0                  90.0
Q3 Price                                65.0                 185.0                  75.0                  35.0                  35.0                 110.0
Average Price                       54.13084             132.40122              62.54598              35.44563               33.3652              93.26813
Not Discounted                          1613                   608                   632                   509                    79                   443
0-10% Discounted                          30                     0                    15                    74                     0                    41
10-20% Discounted                        150                    41                    39                     3                     1                    76
20-30% Discounted                        209                   576                   157                   139                     1                    91
30-40% Discounted                        279                   329                   142                    14                     5                    63
40-50% Discounted                        478                   907                   124                   196                     4                    90
50-60% Discounted                        714                   840                   129                   313                     0                   191
60-70% Discounted                        361                   421                   110                     3                     8                     2
70-80% Discounted                          7                    23                     9                     0                     0                     0
80-90% Discounted                          0                     0                     0                     0                     0                     0
90-100% Discounted                         0                     0                     0                     0                     0                     0
Priced 0-25                              147                     1                    41                    85                    12                     0
Priced 25-50                            1441                   356                   369                  1023                    76                    64
Priced 50-75                            1753                   564                   600                   119                    10                   190
Priced 75-100                            405                   565                   233                    11                     0                   259
Priced 100-125                            85                   523                    49                     6                     0                   320
Priced 125-150                             6                   252                    29                     0                     0                   115
Priced 150-175                             4                   313                    27                     2                     0                    49
Priced 175-200                             0                   371                     5                     3                     0                     0
Priced 200-225                             0                   327                     3                     1                     0                     0
Priced 225-250                             0                   162                     0                     1                     0                     0
Priced Over 250                            0                   311                     1                     0                     0                     0
```
