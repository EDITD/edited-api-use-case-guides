# Job Output → Products CSV — EDITED API

This guide explains how to turn **Jobs API output** (the `*.ndjson.gz` files you
download or receive over SFTP) into a CSV that mirrors the **Products** tab of a
standard EDITED UI list export.

The accompanying script, [`products_export_runner.py`](products_export_runner.py),
reads one or more job-output files and writes that CSV.

## Purpose

The UI export and the Jobs API are two views of the same product data, but they
differ in three ways:

1. **Field names** — the API uses machine field names (`predominant_colour`,
   `cs_grp`, `tier`); the export uses friendly headers (`Normalized Color`,
   `Category`, `Segment`).
2. **Value formatting** — capitalisation, enum → label mapping, list joining,
   price scaling, and percentage scaling all differ.
3. **A few UI columns are computed, not stored** — target-currency prices, the
   Product Types hierarchy, and sellout timing are **not present** in a single
   job-output record and cannot be reproduced exactly from it (see
   [Known limitations](#known-limitations)).

Everything in this guide was verified field-by-field against a real export
(Massimo Dutti IT, 8 Jul 2026, 3,565 products). Every column marked ✅ below
reproduces the export **exactly** across all 3,565 rows.

## How It Works

1. Reads every `*.ndjson.gz` file in your results directory (one JSON product
   record per line).
2. Applies the transformation for each column (see the mapping table below).
3. Writes a single UTF-8 CSV with one row per product.

There is one job-output record per product **option**, and one export row per
product — so the mapping is 1:1. No filtering or aggregation is applied: the
job output already reflects the filters that were set on the job (e.g. *In
stock*, *Exclude second hand*, retailer, rewind date).

## Field mapping

Prices deserve special attention, so they have [their own section](#prices--currency)
below. `S(x)` = capitalise first letter only; `T(x)` = title case.

| Products column | Job-output field | Transformation | Exact? |
|---|---|---|---|
| Name (click to view on EDITED) | `name` | as-is (the hyperlink target is `url`) | ✅ |
| Retailer | `retailer_brand`, `market` | `"{retailer_brand} ({market})"` → `Massimo Dutti (IT)` | ✅ |
| Brand | `brand` | as-is | ✅ |
| Segment | `tier` | `T(tier)` → `mass` → `Mass` | ✅ |
| Gender | `gender` | `T(gender)` → `women` → `Women` | ✅ |
| Category | `cs_grp` | replace `-` with space, then `S()` → `suits-sets` → `Suits sets` | ✅ |
| Product Types | `product_searches_data` (IDs) + searches schema | hierarchy rebuilt from the taxonomy; **set of paths exact, comma order is a UI detail**, see below | ✅* |
| Details | `product_details` | `", ".join(...)` | ✅ |
| Normalized Color | `predominant_colour` | `T()` → `silver` → `Silver` | ✅ |
| Color Option Name | `colour_name` | `S()` → `argento_808` → `Argento_808` | ✅ |
| Activewear | `lifestyle_activewear` | enum map: `not-activewear` → `Non-activewear` | ✅ |
| Pattern | `predominant_pattern` | `S()`; when the field is missing → `Product has no pattern data` | ✅ |
| Full / Current / First Price (display) | `_full_price` / `_price` / `_first_price` | **÷ 100**; job must be run in that currency, see below | ✅ |
| Original Currency | `currency` | as-is | ✅ |
| Full / Current / First Price (original currency) | `_full_price_original` / `_price_original` / `_first_price_original` | **÷ 100** (stored in minor units) | ✅ |
| Current Discount Percentage | `discount_percentage` | **÷ 100** → stored as a 0–1 ratio, shown as a % cell | ✅ |
| Advertised Previous Price (display) | `_advertised_previous_price` | ÷ 100 | ✅ |
| Advertised Previous Price (original currency) | `_advertised_previous_price_original` | ÷ 100 | ✅ |
| Advertised Discount Percentage | `advertised_discount_percentage` | ÷ 100 | ✅ |
| Date First Discounted | `date_first_discount` | date part only | ✅ |
| SKUs Available | `sku_count_current`, `sku_count` | `"{current}/{total}"` → `8/8` | ✅ |
| Date First Seen | `date_found` | date part only | ✅ |
| Num Replenishments | `restock_count` | as-is | ✅ |
| Days to Majority SKU sellout | `days_to_first_majority_sku_sellout` | as-is (null until the product sells out) | ✅ |
| Days to First sellout | `days_to_first_sellout` | as-is (null until the product sells out) | ✅ |
| EDITED Product ID | `option_id` | as-is | ✅ |
| Retailer Product ID | `retailer_product_id` | as-is | ✅ |
| Season | `season` | as-is | ✅ |
| Description | `description` (list) | `" ".join(...)` — the leading `[product code]:` prefix, when present, is kept | ✅ |
| Care information | `care` (list) | `"\n".join(...)` (literal `%%` is preserved) | ✅ |
| Date Last Seen | `date_seen` | as-is (full timestamp) | ✅ |
| Sizes | `skus[].size` | `", ".join(...)` → `35, 36, 37, ...` | ✅ |

### Transformations that are *not* just renaming

These are the ones worth calling out when explaining the export to someone:

- **Prices are stored in minor units.** Every `_..._original` price field (and
  the `_price`/`_full_price` family) is ×100 — `4000` means `40.00`. Divide by
  100 to get the value the UI shows.
- **Discount percentages are stored as ratios.** `discount_percentage = 2.067`
  becomes the cell value `0.02067`; the UI just formats it as `2.07%`.
- **Enum → label mapping.** `lifestyle_activewear` values map to friendly
  labels (`not-activewear` → `Non-activewear`).
- **Capitalisation is inconsistent by design.** `Category` and
  `Color Option Name` capitalise only the first letter (`Suits sets`,
  `Green bottle_594`), while `Gender`, `Segment`, and `Normalized Color` use
  title case.
- **Missing-data placeholders.** A product with no pattern data shows the literal
  string `Product has no pattern data`, not a blank cell.
- **List fields are flattened** with different separators: `Details` and
  `Sizes` use `", "`, `Description` uses a space, `Care information` uses
  newlines.

## Prices & currency

The single most important thing to get right. A job-output record carries prices
in three forms, all in **minor units** (÷ 100):

- **Display currency** — `_price`, `_full_price`, `_first_price`,
  `_advertised_previous_price`. Denominated in **whatever currency the job was
  configured with** (the UI export's "Currency" filter). These reproduce the
  `(£)` / `(€)` display columns **exactly**.
- **Original currency** — `_price_original`, `_full_price_original`, etc. The
  retailer's own currency (EUR for Massimo Dutti). These reproduce the
  `(original currency)` columns exactly.
- **Normalised USD** — `price_usd`, `full_price_usd`, etc. A currency-independent
  USD normalisation for cross-retailer comparison.

The FX rates are captured **per product, as-of the rewind date** — not "today":

- `_user_fx_rate` — USD → display currency (`_price = price_usd × _user_fx_rate`).
- `_original_fx_rate` — USD → original currency.
- `_normalisation_fx_rate` — original → USD (`= 1 / _original_fx_rate`).

When the display currency equals the original currency (an EUR export of an EUR
retailer), `_price == _price_original` and `_user_fx_rate == _original_fx_rate`,
so the two price columns are identical.

**The catch that trips people up:** the display-currency prices live in `_price`,
which only exists once you *run the job in that currency*. An EUR job output has
no GBP prices, so you cannot rebuild a GBP export from it — that's a
currency-mismatch, not an FX bug. **Configure the job's currency to match the
currency you want in the CSV**, then set `display_currency` in `config.ini` to
that label. Verified: a GBP-configured job reproduces the GBP export's price
columns 3,565/3,565 to the cent, honouring all per-product FX buckets. (The rate
is genuinely as-of-date: a 6 May export used 0.8536 and an 8 Jul export used
0.8771, both exported on the same day.)

## Known limitations

None material: every Products column reproduces exactly, provided the job is
run **in the currency you want** and (for Product Types) with an `api_key` set.
The only non-deterministic detail is the comma **ordering** within Product Types
(see below) — the set of values is exact.

### Sellout timing is reproducible (watch the field name)

`Days to Majority SKU sellout` and `Days to First sellout` come straight from the
record's `days_to_first_majority_sku_sellout` / `days_to_first_sellout` fields
(both verified 3,565/3,565 against the export). These are populated even when the
product is currently back in stock — a product can sell out, be restocked, and
still report *when it first sold out*. For example, `Suede leather pants with
tie-detail hems` shows `2` days to sellout despite being `4/4` in stock on 8 Jul:
it first sold out on 6 Jul (`date_first_sellout`) and fully restocked on 8 Jul
(`date_full_restock`). **Do not** use `days_to_first_sellthrough` for these
columns — it is a different metric and is null for many of these products.

### Product Types: reconstructed, order aside

`product_searches` is a flat, unordered set of taxonomy tags
(e.g. `["Mule", "Footwear", "Shoes"]`), so on its own it can't produce the UI's
breadcrumb hierarchy (`Shoes, Shoes > Mule`). But the record also carries
`product_searches_data` with the taxonomy **IDs**, and the
`GET /schema/v1/searches` endpoint returns the full category tree
(`id`, `name`, `type`, `parent_id`). With both, the rule is:

- drop every `top_level_category` node;
- emit each `subcategory` name as-is (`Shoes`);
- emit each `style` node as `"<parent subcategory> > <style>"` (`Shoes > Mule`).

When an `api_key` is configured the script fetches the schema once and applies
this rule; otherwise it falls back to the raw tags. Verified against the export
with the live 630-node taxonomy: the **set** of paths matches exactly on all
**3,565 / 3,565** rows. Of those, **1,019 differ only in comma order** — two
products with an identical tag structure can render in a different order in the
UI (`Jewellery, Jewellery > Earrings` vs `Jewellery > Necklaces, Jewellery`),
which tells us the ordering is a UI-side detail not encoded in the record.

## Configuration

Set these in `config.ini` under `[api]`:

- `results_dir` — directory containing the job-output files (`*.ndjson` or
  `*.ndjson.gz`; gzip is auto-detected, so browser-decompressed files work too).
  Reused from the SFTP / jobs guides.
- `products_csv` *(optional)* — output path (default `products_export.csv`).
- `display_currency` *(optional)* — label for the display-currency price columns.
  Set it to match the currency the **job** was run in (the prices come straight
  from `_price`, so the label is cosmetic; the values are already correct).
- `api_key` *(optional)* — enables the Product Types taxonomy lookup. Without it,
  Product Types falls back to the raw `product_searches` tags.

## Running

```
python products-export-guide/products_export_runner.py
```

## Output Example

Two real rows from a Massimo Dutti (IT) export, showing all 37 columns. The CSV
holds one product per row; it is transposed here (columns as rows) so the full
set is readable on the page. `Product Types` is shown as the raw-tag fallback (no
`api_key`); `Description` and `Care information` are truncated.

| Field | Voluminous hoop earrings | Hair on leather clogs with wooden sole |
|---|---|---|
| Name | Voluminous hoop earrings | Hair on leather clogs with wooden sole |
| URL | https://www.massimodutti.com/it/orecchini-a-cerchio-voluminosi-l04605821 | https://www.massimodutti.com/it/sabot-in-pelle-con-pelliccia-sintetica-suola-di-legno-l11406750 |
| Retailer | Massimo Dutti (IT) | Massimo Dutti (IT) |
| Brand | Massimo Dutti | Massimo Dutti |
| Segment | Mass | Mass |
| Gender | Women | Women |
| Category | Accessories | Footwear |
| Product Types | Jewellery, Accessories, Earrings | Footwear, Shoes, Other Shoes |
| Details | Fabrication | Fur (incl. Faux), Heeled, Fabrication, Leather (incl faux leather), Footwear |
| Normalized Color | Gold | Brown |
| Color Option Name | Dorato_303 | Marrone_700 |
| Activewear | Non-activewear | Non-activewear |
| Pattern | Plain | Product has no pattern data |
| Full Price (EUR) | 30.0 | 149.0 |
| Current Price (EUR) | 30.0 | 99.95 |
| First Price (EUR) | 29.95 | 149.0 |
| Original Currency | EUR | EUR |
| Full Price (original currency) | 30.0 | 149.0 |
| Current Price (original currency) | 30.0 | 99.95 |
| First Price (original currency) | 29.95 | 149.0 |
| Current Discount Percentage | 0.0 | 0.3291946308724832 |
| Advertised Previous Price (EUR) |  | 149.0 |
| Advertised Previous Price (original currency) |  | 149.0 |
| Advertised Discount Percentage |  | 0.3291946308724832 |
| Date First Discounted |  | 2026-07-04 |
| SKUs Available | 1/1 | 6/8 |
| Date First Seen | 2026-06-09 | 2026-02-04 |
| Num Replenishments | 1 | 0 |
| Days to Majority SKU sellout |  | 80 |
| Days to First sellout |  |  |
| EDITED Product ID | 17e152b2b7f96f9e904a7edf1a6486b643a1fabe | 1d3c88c4d35c69426ee5109f34ed6af4ca4085ae |
| Retailer Product ID | 61727252 | 57219423 |
| Season | ss26 | ss26 |
| Description | Irregular design hoop earrings. Rounded and voluminous… | PRODUCTS IN SPAGNAP leather cowhide with fur finish Sli… |
| Care information | 100%% Ottone… | 100%% Pelliccia Di Mucca… |
| Date Last Seen | 2026-07-08T08:29:59 | 2026-07-08T07:20:41 |
| Sizes | One Size | 35, 36, 37, 38, 39, 40, 41, 42 |

> The `Product Types` values above are the raw-tag fallback (no `api_key`). With
> a key, the earring renders as the UI does — `Jewellery, Jewellery > Earrings`.
> See [Product Types](#product-types-reconstructed-order-aside).
