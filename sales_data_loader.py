"""Download and validate the sales CSV used by the dashboard."""

# AI assistance: ChatGPT helped with Drive loading and CSV error handling.
# Request (paraphrased): show load status, fill missing values, and warn about
# unavailable required fields.
from io import BytesIO
from http.client import HTTPException
import time
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd


SALES_DATA_URL = (
    "https://drive.google.com/uc?export=download"
    "&id=1Fv_vhoN4sTrUaozFPfzr0NCyHJLIeXEA"
)

REQUIRED_FIELDS = [
    "employee_name",
    "sales_region",
    "order_type",
    "customer_type",
    "customer_state",
    "product_category",
    "produce_name",
    "employee_id",
    "quantity",
    "unit_price",
]


def load_sales_data():
    """Download the CSV and report file, schema, and data problems."""
    print("Loading sales_data.csv from Google Drive...")
    start_time = time.perf_counter()

    try:
        with urlopen(SALES_DATA_URL, timeout=30) as response:
            file_contents = response.read()
    except URLError as error:
        raise SystemExit(f"Could not download sales_data.csv: {error}") from error
    except (HTTPException, OSError, TimeoutError) as error:
        raise SystemExit(f"Could not read sales_data.csv: {error}") from error

    if not file_contents:
        raise SystemExit("Could not load sales_data.csv: the downloaded file is empty.")

    try:
        data = pd.read_csv(BytesIO(file_contents))
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
        ValueError,
    ) as error:
        raise SystemExit(f"Could not parse sales_data.csv: {error}") from error

    if len(data.columns) == 0:
        raise SystemExit("Could not load sales_data.csv: no columns were found.")
    if not data.columns.is_unique:
        raise SystemExit("Could not load sales_data.csv: duplicate column names were found.")

    found_fields = []
    missing_fields = []
    for field in REQUIRED_FIELDS:
        if field in data.columns:
            found_fields.append(field)
        else:
            missing_fields.append(field)

    if not found_fields:
        raise SystemExit(
            "Could not load sales_data.csv: none of the dashboard's required "
            "columns were found."
        )

    data = data.fillna(0)
    elapsed_time = time.perf_counter() - start_time
    print("Successfully loaded sales_data.csv.")
    print(f"Load time: {elapsed_time:.2f} seconds")
    print(f"Rows of data: {len(data)}")
    available_columns = []
    for column in data.columns:
        available_columns.append(str(column))
    print("Available columns: " + ", ".join(available_columns))

    if data.empty:
        print("Warning: the file has columns but contains no data rows.")
    if missing_fields:
        print(
            "Warning: some analytics may not work. Missing fields: "
            + ", ".join(missing_fields)
        )

    return data
