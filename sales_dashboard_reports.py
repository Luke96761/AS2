"""Report calculations shared by the dashboard and standalone report files."""

# AI assistance: ChatGPT helped implement these shared reports. Request
# (paraphrased): display a sales summary and add region/product percentages.
import pandas as pd

from sales_data_utils import get_number, has_columns, is_valid_data, print_table


def _unique_count_or_missing(data, column):
    """Return a unique count, or explain which column is unavailable."""
    if column not in data.columns:
        return f"Unavailable (missing {column})"
    return str(data[column].nunique())


def show_sales_summary(data):
    """Print key totals and identify summary values the data cannot provide."""
    if not is_valid_data(data):
        return

    if "employee_id" in data.columns:
        employee_count = _unique_count_or_missing(data, "employee_id")
    elif "employee_name" in data.columns:
        employee_count = _unique_count_or_missing(data, "employee_name")
    else:
        employee_count = "Unavailable (missing employee_id and employee_name)"

    if "order_date" in data.columns:
        date_column = "order_date"
    elif "sale_date" in data.columns:
        date_column = "sale_date"
    else:
        date_column = None

    if date_column is None:
        date_range = "Unavailable (missing order_date or sale_date)"
    else:
        valid_dates = pd.to_datetime(data[date_column], errors="coerce").dropna()
        if valid_dates.empty:
            date_range = "Unavailable (no valid dates)"
        else:
            first_date = valid_dates.min().strftime("%Y-%m-%d")
            last_date = valid_dates.max().strftime("%Y-%m-%d")
            date_range = f"{first_date} to {last_date}"

    required_sales_columns = ["quantity", "unit_price"]
    missing_sales_columns = []
    for column in required_sales_columns:
        if column not in data.columns:
            missing_sales_columns.append(column)

    if missing_sales_columns:
        total_sales = (
            "Unavailable (missing " + ", ".join(missing_sales_columns) + ")"
        )
    else:
        total_sales_amount = 0
        rows = data.to_dict(orient="records")
        for row in rows:
            quantity = get_number(row["quantity"])
            unit_price = get_number(row["unit_price"])
            total_sales_amount += quantity * unit_price
        total_sales = f"{total_sales_amount:.2f}"

    if "quantity" not in data.columns:
        total_quantity = "Unavailable (missing quantity)"
    else:
        quantity_sum = 0
        for value in data["quantity"]:
            quantity_sum += get_number(value)
        total_quantity = f"{quantity_sum:.2f}"

    summary_rows = [
        ["Total orders", _unique_count_or_missing(data, "order_id")],
        ["Number of employees", employee_count],
        ["Sales regions", _unique_count_or_missing(data, "sales_region")],
        ["Date range of orders", date_range],
        ["Unique customers", _unique_count_or_missing(data, "customer_id")],
        ["Product categories", _unique_count_or_missing(data, "product_category")],
        ["Unique states", _unique_count_or_missing(data, "customer_state")],
        ["Total sales amount", total_sales],
        ["Total quantities sold", total_quantity],
    ]
    print_table("Sales Data Summary", ["Measure", "Value"], summary_rows)


def show_first_rows(data):
    """Display a chosen number of rows, all rows, or no rows."""
    if not is_valid_data(data):
        return

    available_rows = len(data)
    print(f"There are {available_rows} rows available.")

    if available_rows == 0:
        print("There are no rows to display.")
        return

    while True:
        print("Enter rows to display:")
        print(f"- Enter a number 1 to {available_rows}")
        print("- To see all rows, enter 'all'")
        print("- To skip preview, press Enter")
        choice = input("Your choice: ").strip()

        if choice == "":
            print("Preview skipped.")
            return

        if choice.lower() == "all":
            number_of_rows = available_rows
            break

        try:
            number_of_rows = int(choice)
        except ValueError:
            print("Invalid input. Enter a whole number, 'all', or press Enter.")
            continue

        if number_of_rows < 1 or number_of_rows > available_rows:
            print(f"Enter a number from 1 to {available_rows}.")
            continue
        break

    preview_rows = data.head(number_of_rows).to_dict(orient="records")
    table_rows = []
    for row in preview_rows:
        values = []
        for column in data.columns:
            values.append(row[column])
        table_rows.append(values)
    print_table(f"First {number_of_rows} Rows", list(data.columns), table_rows)


def show_total_by_region_and_order(data):
    """Print sales totals for each region and order type."""
    required_columns = ["sales_region", "order_type", "quantity", "unit_price"]
    if not has_columns(data, required_columns):
        return

    totals_by_region = {}
    rows = data.to_dict(orient="records")

    for row in rows:
        region = row["sales_region"]
        order_type = row["order_type"]

        if order_type not in ["Retail", "Wholesale"]:
            print(f"Skipping row with unexpected order type: {order_type}")
            continue

        if region not in totals_by_region:
            totals_by_region[region] = {"Retail": 0, "Wholesale": 0}

        quantity = get_number(row["quantity"])
        unit_price = get_number(row["unit_price"])
        sale_total = quantity * unit_price
        totals_by_region[region][order_type] += sale_total

    report_rows = []
    for region in totals_by_region:
        retail_total = totals_by_region[region]["Retail"]
        wholesale_total = totals_by_region[region]["Wholesale"]
        report_rows.append(
            [region, f"{retail_total:.2f}", f"{wholesale_total:.2f}"]
        )
    print_table(
        "Sales by Region and Order Type",
        ["Region", "Retail", "Wholesale"],
        report_rows,
    )


def show_average_sales_by_region_state_and_order(data):
    """Print average sales for each region, state, and sale type."""
    required_columns = [
        "sales_region",
        "customer_state",
        "order_type",
        "quantity",
        "unit_price",
    ]
    if not has_columns(data, required_columns):
        return

    sale_types = ["Retail", "Wholesale"]
    regions = []
    states = []
    # Keep both the sales total and row count to calculate each average.
    sales_totals = {}
    rows = data.to_dict(orient="records")

    for row in rows:
        region = row["sales_region"]
        state = row["customer_state"]
        sale_type = row["order_type"]

        if sale_type not in sale_types:
            print(f"Skipping row with unexpected sale type: {sale_type}")
            continue

        if region not in regions:
            regions.append(region)
        if state not in states:
            states.append(state)

        quantity = get_number(row["quantity"])
        price = get_number(row["unit_price"])
        sale_value = quantity * price
        group_name = (region, state, sale_type)

        if group_name not in sales_totals:
            sales_totals[group_name] = [0, 0]

        sales_totals[group_name][0] += sale_value
        sales_totals[group_name][1] += 1

    headers = []
    for state in states:
        for sale_type in sale_types:
            headers.append(f"{state} {sale_type}")

    report_rows = []
    for region in regions:
        row_values = []
        for state in states:
            for sale_type in sale_types:
                group_name = (region, state, sale_type)

                if group_name in sales_totals:
                    total_sales = sales_totals[group_name][0]
                    sale_count = sales_totals[group_name][1]
                    average_sales = total_sales / sale_count
                else:
                    average_sales = 0

                row_values.append(f"{average_sales:.2f}")

        report_rows.append([region] + row_values)

    print_table(
        "Average Sales by Region, State, and Sale Type",
        ["Region"] + headers,
        report_rows,
    )


def show_sales_by_customer_order_type_and_state(data):
    """Print sales by customer type and order type, split by state."""
    required_columns = [
        "customer_type",
        "order_type",
        "customer_state",
        "quantity",
        "unit_price",
    ]
    if not has_columns(data, required_columns):
        return

    customer_order_types = []
    states = []
    sales_totals = {}
    rows = data.to_dict(orient="records")

    for row in rows:
        customer_type = row["customer_type"]
        order_type = row["order_type"]
        state = row["customer_state"]
        group_name = (customer_type, order_type)

        if group_name not in customer_order_types:
            customer_order_types.append(group_name)
        if state not in states:
            states.append(state)
        if group_name not in sales_totals:
            sales_totals[group_name] = {}
        if state not in sales_totals[group_name]:
            sales_totals[group_name][state] = 0

        quantity = get_number(row["quantity"])
        price = get_number(row["unit_price"])
        sales_totals[group_name][state] += quantity * price

    report_rows = []
    for group_name in customer_order_types:
        state_totals = []
        for state in states:
            if state in sales_totals[group_name]:
                total = sales_totals[group_name][state]
            else:
                total = 0
            state_totals.append(f"{total:.2f}")

        customer_type = group_name[0]
        order_type = group_name[1]
        report_rows.append([customer_type, order_type] + state_totals)

    state_headers = []
    for state in states:
        state_headers.append(str(state))

    print_table(
        "Sales by Customer Type and Order Type by State",
        ["Customer Type", "Order Type"] + state_headers,
        report_rows,
    )


def _get_region_product_totals(data):
    """Return quantity and sales totals for each region/product pair."""
    totals_by_region_and_product = {}
    rows = data.to_dict(orient="records")

    for row in rows:
        region = row["sales_region"]
        product = row["produce_name"]
        quantity = get_number(row["quantity"])
        unit_price = get_number(row["unit_price"])
        sales_value = quantity * unit_price
        group_name = (region, product)

        if group_name not in totals_by_region_and_product:
            totals_by_region_and_product[group_name] = [0, 0]

        totals_by_region_and_product[group_name][0] += quantity
        totals_by_region_and_product[group_name][1] += sales_value

    return totals_by_region_and_product


def show_quantity_and_sales_by_region_product(data):
    """Print total quantity and sales value for each region and product."""
    required_columns = [
        "sales_region",
        "produce_name",
        "quantity",
        "unit_price",
    ]
    if not has_columns(data, required_columns):
        return

    totals_by_region_and_product = _get_region_product_totals(data)

    report_rows = []
    for group_name in totals_by_region_and_product:
        region = group_name[0]
        product = group_name[1]
        total_quantity = totals_by_region_and_product[group_name][0]
        total_sales = totals_by_region_and_product[group_name][1]
        report_rows.append(
            [region, product, f"{total_quantity:.2f}", f"{total_sales:.2f}"]
        )
    print_table(
        "Sales Quantity and Price by Region and Product",
        ["Region", "Product", "Total Quantity", "Total Sales Price"],
        report_rows,
    )


def show_region_product_percentages(data):
    """Show each product's quantity and sales share within its region."""
    required_columns = [
        "sales_region",
        "produce_name",
        "quantity",
        "unit_price",
    ]
    if not has_columns(data, required_columns):
        return

    totals_by_region_and_product = _get_region_product_totals(data)
    totals_by_region = {}

    for group_name in totals_by_region_and_product:
        region = group_name[0]
        quantity = totals_by_region_and_product[group_name][0]
        sales = totals_by_region_and_product[group_name][1]

        if region not in totals_by_region:
            totals_by_region[region] = [0, 0]
        totals_by_region[region][0] += quantity
        totals_by_region[region][1] += sales

    report_rows = []
    for group_name in totals_by_region_and_product:
        region = group_name[0]
        product = group_name[1]
        quantity = totals_by_region_and_product[group_name][0]
        sales = totals_by_region_and_product[group_name][1]
        region_quantity = totals_by_region[region][0]
        region_sales = totals_by_region[region][1]

        if region_quantity == 0:
            quantity_percent = 0
        else:
            quantity_percent = quantity / region_quantity * 100

        if region_sales == 0:
            sales_percent = 0
        else:
            sales_percent = sales / region_sales * 100

        report_rows.append(
            [
                region,
                product,
                f"{quantity:.2f}",
                f"{quantity_percent:.2f}%",
                f"{sales:.2f}",
                f"{sales_percent:.2f}%",
            ]
        )

    print_table(
        "Quantity and Sales Percentages by Region and Product",
        [
            "Region",
            "Product",
            "Total Quantity",
            "Quantity % of Region",
            "Total Sales",
            "Sales % of Region",
        ],
        report_rows,
    )


def show_quantity_and_sales_by_order_customer(data):
    """Print quantity and sales totals by order type and customer type."""
    required_columns = [
        "order_type",
        "customer_type",
        "quantity",
        "unit_price",
    ]
    if not has_columns(data, required_columns):
        return

    totals_by_type = {}
    rows = data.to_dict(orient="records")

    for row in rows:
        order_type = row["order_type"]
        customer_type = row["customer_type"]
        quantity = get_number(row["quantity"])
        unit_price = get_number(row["unit_price"])
        sales_value = quantity * unit_price
        group_name = (order_type, customer_type)

        if group_name not in totals_by_type:
            totals_by_type[group_name] = [0, 0]

        totals_by_type[group_name][0] += quantity
        totals_by_type[group_name][1] += sales_value

    report_rows = []
    for group_name in totals_by_type:
        order_type = group_name[0]
        customer_type = group_name[1]
        total_quantity = totals_by_type[group_name][0]
        total_sales = totals_by_type[group_name][1]
        report_rows.append(
            [
                order_type,
                customer_type,
                f"{total_quantity:.2f}",
                f"{total_sales:.2f}",
            ]
        )
    print_table(
        "Sales by Order Type and Customer Type",
        ["Order Type", "Customer Type", "Total Quantity", "Total Sales Price"],
        report_rows,
    )


def show_price_range_by_category(data):
    """Print the lowest and highest unit price in each category."""
    required_columns = ["product_category", "unit_price"]
    if not has_columns(data, required_columns):
        return

    prices_by_category = {}
    rows = data.to_dict(orient="records")

    for row in rows:
        category = row["product_category"]
        price = get_number(row["unit_price"])

        if category not in prices_by_category:
            prices_by_category[category] = [price, price]
        else:
            if price < prices_by_category[category][0]:
                prices_by_category[category][0] = price
            if price > prices_by_category[category][1]:
                prices_by_category[category][1] = price

    report_rows = []
    for category in prices_by_category:
        minimum_price = prices_by_category[category][0]
        maximum_price = prices_by_category[category][1]
        report_rows.append(
            [category, f"{minimum_price:.2f}", f"{maximum_price:.2f}"]
        )
    print_table(
        "Minimum and Maximum Sales Price by Category",
        ["Category", "Minimum Sales Price", "Maximum Sales Price"],
        report_rows,
    )


def show_unique_employees_by_region(data):
    """Print the number of unique employees for each region."""
    required_columns = ["sales_region", "employee_id"]
    if not has_columns(data, required_columns):
        return

    employees_by_region = {}
    rows = data.to_dict(orient="records")

    for row in rows:
        region = row["sales_region"]
        employee = row["employee_id"]

        if region not in employees_by_region:
            employees_by_region[region] = []
        if employee not in employees_by_region[region]:
            employees_by_region[region].append(employee)

    report_rows = []
    for region in employees_by_region:
        employee_count = len(employees_by_region[region])
        report_rows.append([region, employee_count])
    print_table(
        "Unique Employees by Region",
        ["Region", "Number of Unique Employees"],
        report_rows,
    )


def choose_items(options, prompt, optional=False):
    """Let the user choose one or more items by entering their numbers."""
    while True:
        for number, option in enumerate(options, start=1):
            print(f"{number}. {option}")

        answer = input(prompt).strip()
        if optional and answer == "":
            return []

        selected_items = []
        valid_answer = True
        for choice in answer.split(","):
            try:
                number = int(choice.strip())
            except ValueError:
                valid_answer = False
                break

            if number < 1 or number > len(options):
                valid_answer = False
                break

            item = options[number - 1]
            if item not in selected_items:
                selected_items.append(item)

        if valid_answer and selected_items:
            return selected_items

        print("Invalid choice. Enter the number of each option you want.")


def make_group_name(row, columns):
    """Make a group name from the selected columns."""
    group_name = []
    for column in columns:
        group_name.append(row[column])
    return tuple(group_name)


def join_items(items):
    """Join values with slashes for display."""
    item_text = []
    for item in items:
        item_text.append(str(item))
    return " / ".join(item_text)


def show_custom_pivot(data):
    """Ask for pivot options and display the results."""
    if not is_valid_data(data):
        return

    available_columns = list(data.columns)
    row_options = []
    for column in ["employee_name", "sales_region", "product_category"]:
        if column in available_columns:
            row_options.append(column)

    column_options = []
    for column in ["order_type", "customer_type"]:
        if column in available_columns:
            column_options.append(column)

    value_options = []
    if "quantity" in available_columns:
        value_options.append("quantity")
    if "quantity" in available_columns and "unit_price" in available_columns:
        value_options.append("sale_price")

    if not row_options:
        print("There are no available row fields for this pivot table.")
        return
    if not value_options:
        print("There are no available numeric fields for this pivot table.")
        return

    print("Select rows:")
    row_fields = choose_items(
        row_options,
        "Enter the number(s) of your choice(s), separated by commas: ",
    )

    print("Select columns (optional):")
    column_fields = choose_items(
        column_options,
        "Enter the number(s) of your choice(s), separated by commas "
        "(press Enter for no grouping): ",
        optional=True,
    )

    print("Select values:")
    value_fields = choose_items(
        value_options,
        "Enter the number(s) of your choice(s), separated by commas: ",
    )

    print("Select aggregation function:")
    aggregations = choose_items(
        ["sum", "mean", "count"],
        "Enter the number(s) of your choice(s), separated by commas: ",
    )

    # Each row/column pair stores a total and a count for the selected values.
    grouped_data = {}
    row_names = []
    column_names = []
    rows = data.to_dict(orient="records")

    for row in rows:
        row_name = make_group_name(row, row_fields)
        column_name = make_group_name(row, column_fields)

        if row_name not in row_names:
            row_names.append(row_name)
        if column_name not in column_names:
            column_names.append(column_name)

        group_name = (row_name, column_name)
        if group_name not in grouped_data:
            grouped_data[group_name] = {}

        for value_field in value_fields:
            if value_field == "quantity":
                value = get_number(row["quantity"])
            else:
                # Sale price is quantity multiplied by unit price.
                quantity = get_number(row["quantity"])
                unit_price = get_number(row["unit_price"])
                value = quantity * unit_price

            if value_field not in grouped_data[group_name]:
                grouped_data[group_name][value_field] = [0, 0]

            grouped_data[group_name][value_field][0] += value
            grouped_data[group_name][value_field][1] += 1

    headers = []
    for column_name in column_names:
        for value_field in value_fields:
            for aggregation in aggregations:
                if column_fields:
                    column_title = join_items(column_name)
                    header = f"{column_title} {value_field} ({aggregation})"
                else:
                    header = f"{value_field} ({aggregation})"
                headers.append(header)

    report_rows = []
    for row_name in row_names:
        results = []
        for column_name in column_names:
            group_name = (row_name, column_name)
            for value_field in value_fields:
                if (
                    group_name in grouped_data
                    and value_field in grouped_data[group_name]
                ):
                    total = grouped_data[group_name][value_field][0]
                    count = grouped_data[group_name][value_field][1]
                else:
                    total = 0
                    count = 0

                for aggregation in aggregations:
                    if aggregation == "count":
                        result = count
                    elif aggregation == "mean" and count > 0:
                        result = total / count
                    else:
                        result = total
                    results.append(f"{result:.2f}")

        report_rows.append([join_items(row_name)] + results)

    print_table("Custom Pivot Table", ["Rows"] + headers, report_rows)
