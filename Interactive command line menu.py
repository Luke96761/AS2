"""Sales dashboard menu."""

# AI assistance: ChatGPT helped organize the menu. Request (paraphrased): show a
# data summary and hide reports when their required columns are missing.
from sales_data_loader import load_sales_data
import sales_dashboard_reports as reports


def exit_dashboard(data):
    """Print a goodbye message and stop the menu."""
    if not reports.is_valid_data(data):
        return False
    print(f"Goodbye. There are {len(data)} rows in the data.")
    return False


MENU_ITEMS = (
    ("Show the first n rows of sales data", reports.show_first_rows, ()),
    (
        "Total sales by region and order_type",
        reports.show_total_by_region_and_order,
        ("sales_region", "order_type", "quantity", "unit_price"),
    ),
    (
        "Average sales by region, state, and sale type",
        reports.show_average_sales_by_region_state_and_order,
        ("sales_region", "customer_state", "order_type", "quantity", "unit_price"),
    ),
    (
        "Sales by customer type and order type by state",
        reports.show_sales_by_customer_order_type_and_state,
        ("customer_type", "order_type", "customer_state", "quantity", "unit_price"),
    ),
    (
        "Total sales quantity and price by region and product",
        reports.show_quantity_and_sales_by_region_product,
        ("sales_region", "produce_name", "quantity", "unit_price"),
    ),
    (
        "Quantity and sales percentages by region and product",
        reports.show_region_product_percentages,
        ("sales_region", "produce_name", "quantity", "unit_price"),
    ),
    (
        "Total sales quantity and price by order and customer type",
        reports.show_quantity_and_sales_by_order_customer,
        ("order_type", "customer_type", "quantity", "unit_price"),
    ),
    (
        "Max and min sales price by category",
        reports.show_price_range_by_category,
        ("product_category", "unit_price"),
    ),
    (
        "Number of unique employees by region",
        reports.show_unique_employees_by_region,
        ("sales_region", "employee_id"),
    ),
    ("Create a custom pivot table", reports.show_custom_pivot, None),
    ("Exit", exit_dashboard, ()),
)


def menu_item_is_available(data, menu_item):
    """Check that the data has the fields needed by a menu item."""
    required_columns = menu_item[2]

    if required_columns is None:
        row_fields = ["employee_name", "sales_region", "product_category"]
        has_row_field = False
        for field in row_fields:
            if field in data.columns:
                has_row_field = True
        return has_row_field and "quantity" in data.columns

    for column in required_columns:
        if column not in data.columns:
            return False
    return True


def run_menu(data):
    """Display available reports and run the user's selection."""
    if not reports.is_valid_data(data):
        return

    available_items = []
    for item in MENU_ITEMS:
        if menu_item_is_available(data, item):
            available_items.append(item)

    while True:
        print("\n--- Sales Data Dashboard ---")
        if len(available_items) < len(MENU_ITEMS):
            print("Some reports are hidden because required data fields are missing.")

        print("Choose a report by entering its number:")
        for number, item in enumerate(available_items, start=1):
            print(f"{number}. {item[0]}")

        try:
            choice = int(input(f"Your choice (1-{len(available_items)}): "))
        except ValueError:
            print(
                f"Invalid input. Enter a number from 1 to {len(available_items)}."
            )
            continue

        if choice < 1 or choice > len(available_items):
            print(f"Choose a number from 1 to {len(available_items)}.")
            continue

        selected_function = available_items[choice - 1][1]
        if selected_function(data) is False:
            break


def main():
    """Load the sales data, show its summary, and start the menu."""
    data = load_sales_data()
    reports.show_sales_summary(data)
    run_menu(data)


if __name__ == "__main__":
    main()
