# products_export_runner.py
# -------------------------------------------------------
# Reads EDITED Jobs API output (one or more *.ndjson[.gz] files) and writes a CSV
# that mirrors the "Products" tab of the standard EDITED UI list export.
#
# See README.md for a field-by-field explanation of every transformation. Every
# column reproduces exactly, provided the job is run in the currency you want in
# the CSV and (for the Product Types hierarchy) an api_key is set for the schema
# lookup. The only non-deterministic detail is the comma ORDERING within Product
# Types, a UI-side detail — the set of values is exact.

# === IMPORT LIBRARIES ===
import csv
import glob
import gzip
import json
import logging
import os

from editedapi.configloader import get  # Loads config.ini values
from editedapi.getschema import get_schema  # GET /schema/v1/{schema}

# === LOGGING SETUP ===
LOG_LEVEL = get("api", "log_level", default="INFO")
numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logger = logging.getLogger("products_export_runner")
logging.basicConfig(
    level=numeric_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# === CONFIGURATION FROM config.ini ===
# Directory containing the downloaded *.ndjson.gz job output files.
INPUT_DIR = get("api", "results_dir")
# Where to write the resulting CSV.
OUTPUT_CSV = get("api", "products_csv", default="products_export.csv")

# API key is only needed to fetch the category taxonomy for the Product Types
# column. Without it, Product Types falls back to the raw product_searches tags.
API_KEY = get("api", "api_key", default="")

# The display-currency price columns come straight from the record's `_price`
# family, which is denominated in whatever currency the JOB was configured with
# (as-of-date, per-product FX — see README "Prices & currency"). The job output
# does not name that currency, so set this label to match your job's currency.
DISPLAY_CURRENCY = get("api", "display_currency", default="display currency")

# --- Value maps confirmed against a real UI export -----------------------------
ACTIVEWEAR_MAP = {
    "not-activewear": "Non-activewear",
    "activewear": "Activewear",
    "licensed-activewear": "Licensed activewear",
}
NO_PATTERN_TEXT = "Product has no pattern data"


def open_ndjson(path):
    """Open an NDJSON file as text, transparently handling gzip or plain JSON.

    Some job-output files arrive uncompressed despite a .gz extension, so detect
    the gzip magic bytes (0x1f 0x8b) rather than trusting the name.
    """
    with open(path, "rb") as fh:
        is_gzip = fh.read(2) == b"\x1f\x8b"
    if is_gzip:
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "rt", encoding="utf-8")


def build_taxonomy(api_key):
    """Fetch the searches schema and return {id: (name, type, parent_id)}.

    Returns None if no API key is configured, in which case Product Types falls
    back to the raw product_searches tags.
    """
    if not api_key:
        return None
    schema = get_schema("searches", headers={"X-API-KEY": api_key})
    return {
        node["id"]: (node["name"], node["type"], node["parent_id"])
        for node in schema["searches"]
    }


def product_types(record, taxonomy):
    """Render the Product Types column.

    With the taxonomy, mirror the UI: drop top-level categories, emit each
    subcategory name and each style as "<parent subcategory> > <style>". The UI
    orders these entries in a way that is not encoded in the record, so the set
    of paths matches exactly but the comma order may differ. Without the
    taxonomy, fall back to the raw product_searches tags.
    """
    if taxonomy is None:
        return ", ".join(record.get("product_searches") or []) or None

    subs, styles = [], []
    for tag in record.get("product_searches_data") or []:
        node = taxonomy.get(tag["id"])
        if not node:
            continue
        name, node_type, parent_id = node
        if node_type == "subcategory":
            subs.append(name)
        elif node_type == "style":
            parent = taxonomy.get(parent_id)
            styles.append(f"{parent[0] if parent else '?'} > {name}")
        # top_level_category nodes are intentionally dropped
    return ", ".join(subs + styles) or None


def sentence_case(value):
    """Capitalise the first letter only (leaves the rest untouched)."""
    if not isinstance(value, str) or not value:
        return value
    return value[0].upper() + value[1:]


def title_case(value):
    return value.title() if isinstance(value, str) and value else value


def minor_to_major(value):
    """Prices in job output are stored in minor units (x100)."""
    if value is None:
        return None
    return round(value / 100.0, 5)


def ratio(percentage):
    """UI stores discount as a 0-1 ratio and formats it as a percentage cell."""
    if percentage is None:
        return None
    return percentage / 100.0


def clean_date(value):
    """Job output dates are ISO strings; keep the date part for readability."""
    if not value:
        return None
    return value.split("T")[0]


# Column order matches the Products tab of the UI export.
HEADERS = [
    "Name",
    "URL",
    "Retailer",
    "Brand",
    "Segment",
    "Gender",
    "Category",
    "Product Types",
    "Details",
    "Normalized Color",
    "Color Option Name",
    "Activewear",
    "Pattern",
    f"Full Price ({DISPLAY_CURRENCY})",
    f"Current Price ({DISPLAY_CURRENCY})",
    f"First Price ({DISPLAY_CURRENCY})",
    "Original Currency",
    "Full Price (original currency)",
    "Current Price (original currency)",
    "First Price (original currency)",
    "Current Discount Percentage",
    f"Advertised Previous Price ({DISPLAY_CURRENCY})",
    "Advertised Previous Price (original currency)",
    "Advertised Discount Percentage",
    "Date First Discounted",
    "SKUs Available",
    "Date First Seen",
    "Num Replenishments",
    "Days to Majority SKU sellout",
    "Days to First sellout",
    "EDITED Product ID",
    "Retailer Product ID",
    "Season",
    "Description",
    "Care information",
    "Date Last Seen",
    "Sizes",
]


def transform(record, taxonomy=None):
    """Map one job-output record to one Products-tab row."""
    sizes = [s.get("size") for s in record.get("skus", []) if s.get("size")]
    pattern = record.get("predominant_pattern")

    return {
        "Name": record.get("name"),
        "URL": record.get("url"),
        "Retailer": f"{record.get('retailer_brand')} ({record.get('market')})",
        "Brand": record.get("brand"),
        "Segment": title_case(record.get("tier")),
        "Gender": title_case(record.get("gender")),
        # cs_grp is a slug: replace hyphens with spaces, capitalise first letter.
        "Category": sentence_case((record.get("cs_grp") or "").replace("-", " ")) or None,
        # Reconstructed from the searches taxonomy when an API key is set (see
        # product_types); otherwise the raw product_searches tags.
        "Product Types": product_types(record, taxonomy),
        "Details": ", ".join(record.get("product_details") or []) or None,
        "Normalized Color": title_case(record.get("predominant_colour")),
        "Color Option Name": sentence_case(record.get("colour_name")),
        "Activewear": ACTIVEWEAR_MAP.get(
            record.get("lifestyle_activewear"), record.get("lifestyle_activewear")
        ),
        "Pattern": sentence_case(pattern) if pattern else NO_PATTERN_TEXT,
        # Display currency = the record's `_price` family (whatever currency the
        # job was configured with). Exact, as-of-date, per-product FX.
        f"Full Price ({DISPLAY_CURRENCY})": minor_to_major(record.get("_full_price")),
        f"Current Price ({DISPLAY_CURRENCY})": minor_to_major(record.get("_price")),
        f"First Price ({DISPLAY_CURRENCY})": minor_to_major(record.get("_first_price")),
        # Original currency = the retailer's own currency.
        "Original Currency": record.get("currency"),
        "Full Price (original currency)": minor_to_major(record.get("_full_price_original")),
        "Current Price (original currency)": minor_to_major(record.get("_price_original")),
        "First Price (original currency)": minor_to_major(record.get("_first_price_original")),
        "Current Discount Percentage": ratio(record.get("discount_percentage")),
        f"Advertised Previous Price ({DISPLAY_CURRENCY})": minor_to_major(
            record.get("_advertised_previous_price")
        ),
        "Advertised Previous Price (original currency)": minor_to_major(
            record.get("_advertised_previous_price_original")
        ),
        "Advertised Discount Percentage": ratio(record.get("advertised_discount_percentage")),
        "Date First Discounted": clean_date(record.get("date_first_discount")),
        "SKUs Available": f"{record.get('sku_count_current')}/{record.get('sku_count')}",
        "Date First Seen": clean_date(record.get("date_found")),
        "Num Replenishments": record.get("restock_count"),
        # Pre-computed day counts in the record (null until the product sells out).
        "Days to Majority SKU sellout": record.get("days_to_first_majority_sku_sellout"),
        "Days to First sellout": record.get("days_to_first_sellout"),
        "EDITED Product ID": record.get("option_id"),
        "Retailer Product ID": record.get("retailer_product_id"),
        "Season": record.get("season"),
        "Description": " ".join(record.get("description") or []) or None,
        "Care information": "\n".join(record.get("care") or []) or None,
        "Date Last Seen": record.get("date_seen"),
        "Sizes": ", ".join(sizes),
    }


def main():
    input_dir = os.path.abspath(os.path.expanduser(INPUT_DIR))
    files = sorted(
        glob.glob(os.path.join(input_dir, "*.ndjson.gz"))
        + glob.glob(os.path.join(input_dir, "*.ndjson"))
    )
    if not files:
        logger.error(f"No *.ndjson[.gz] files found in {input_dir}")
        return

    logger.info(
        "Display-currency price columns labelled '%s' — set display_currency in "
        "config.ini to match the currency your job was configured with.",
        DISPLAY_CURRENCY,
    )

    taxonomy = build_taxonomy(API_KEY)
    if taxonomy is None:
        logger.info("No api_key set: Product Types will use raw product_searches tags.")
    else:
        logger.info(f"Loaded {len(taxonomy)} taxonomy nodes for Product Types.")

    rows_written = 0
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as out:
        writer = csv.DictWriter(out, fieldnames=HEADERS)
        writer.writeheader()
        for path in files:
            logger.info(f"Reading {os.path.basename(path)}")
            with open_ndjson(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    writer.writerow(transform(json.loads(line), taxonomy))
                    rows_written += 1

    logger.info(f"Wrote {rows_written} rows to {os.path.abspath(OUTPUT_CSV)}")


if __name__ == "__main__":
    main()
