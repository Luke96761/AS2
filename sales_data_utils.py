"""Shared checks and numeric conversion for the sales dashboard."""

# AI assistance: ChatGPT helped create reusable validation and table-formatting
# helpers. Request (paraphrased): handle invalid data and keep reports readable.
import math


# Shared helpers keep validation and output consistent across every report.
def is_valid_data(data):
    """Check that the value is a table the dashboard can use."""
    if (
        data is None
        or not hasattr(data, "columns")
        or not hasattr(data, "to_dict")
        or not hasattr(data, "head")
    ):
        print("Invalid sales data. Load a sales table before running the dashboard.")
        return False
    return True


def has_columns(data, required_columns):
    """Check that a table has all columns needed for a report."""
    if not is_valid_data(data):
        return False

    missing_columns = []
    for column in required_columns:
        if column not in data.columns:
            missing_columns.append(column)

    if missing_columns:
        print("Missing columns: " + ", ".join(missing_columns))
        return False
    return True


def get_number(value):
    """Convert a value to a finite number, or use zero if it is invalid."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0

    # NaN and infinity convert to floats successfully, but would spoil totals.
    if not math.isfinite(number):
        return 0
    return number


def print_table(title, headers, rows):
    """Print rows with aligned columns and a clear heading."""
    formatted_rows = []
    for row in rows:
        formatted_row = []
        for value in row:
            formatted_row.append(str(value))
        formatted_rows.append(formatted_row)

    # Size each column from its longest value so reports stay aligned.
    column_widths = []
    for number, header in enumerate(headers):
        header_text = str(header).replace("_", " ")
        width = len(header_text)
        for row in formatted_rows:
            if number < len(row) and len(row[number]) > width:
                width = len(row[number])
        column_widths.append(width)

    print(f"\n{title}")
    if not headers:
        print("No columns to display.")
        return

    header_row = []
    for number, header in enumerate(headers):
        header_text = str(header).replace("_", " ")
        header_row.append(header_text.ljust(column_widths[number]))
    print(" | ".join(header_row))

    divider = []
    for width in column_widths:
        divider.append("-" * width)
    print("-+-".join(divider))

    if not formatted_rows:
        print("No rows to display.")
        return

    for row in formatted_rows:
        display_row = []
        for number, width in enumerate(column_widths):
            if number < len(row):
                display_row.append(row[number].ljust(width))
            else:
                display_row.append("".ljust(width))
        print(" | ".join(display_row))
