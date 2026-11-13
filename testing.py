"""Tests for the sales dashboard.

Run them from the project folder with: python -m unittest testing -v
The tests use sample data and fake input/downloads, so they need no internet.
"""

# AI assistance: ChatGPT helped write tests for reports, bad inputs, and loading
# errors. Request (paraphrased): cover the dashboard functions with simple tests.
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import URLError

import pandas as pd

import sales_data_loader
import sales_dashboard_reports as reports
import sales_data_utils


def load_file(file_name):
    """Load a project file whose name contains spaces."""
    path = Path(__file__).parent / file_name
    spec = importlib.util.spec_from_file_location("project_file", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_data():
    """Make four rows with known totals for the tests."""
    return pd.DataFrame(
        {
            "sales_region": ["North", "North", "South", "South"],
            "order_type": ["Retail", "Wholesale", "Retail", "Retail"],
            "customer_state": ["CA", "CA", "NY", "NY"],
            "customer_type": ["Business", "Business", "Individual", "Individual"],
            "produce_name": ["Apples", "Apples", "Oranges", "Apples"],
            "employee_name": ["Alex", "Alex", "Blair", "Casey"],
            "product_category": ["Fruit", "Fruit", "Fruit", "Other"],
            "employee_id": [1, 1, 2, 3],
            "quantity": [2, 3, 1, 4],
            "unit_price": [5, 4, 10, 2],
            "order_id": [100, 101, 102, 102],
            "customer_id": [1, 2, 3, 3],
            "order_date": [
                "2025-01-01",
                "2025-01-02",
                "2025-01-03",
                "2025-01-03",
            ],
        }
    )


def capture_output(function, *args):
    """Run a function and return the text it prints."""
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        function(*args)
    return output.getvalue()


def run_with_input(function, answers, *args):
    """Run a function using pretend answers and capture its output."""
    output = io.StringIO()
    with patch("builtins.input", side_effect=answers):
        with contextlib.redirect_stdout(output):
            function(*args)
    return output.getvalue()


dashboard = load_file("Interactive command line menu.py")


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.data = sample_data()

    def test_shared_data_helpers(self):
        self.assertTrue(sales_data_utils.is_valid_data(self.data))
        self.assertFalse(sales_data_utils.is_valid_data(None))
        self.assertTrue(sales_data_utils.has_columns(self.data, ["quantity"]))
        self.assertFalse(sales_data_utils.has_columns(self.data, ["missing"]))
        self.assertEqual(sales_data_utils.get_number("2.5"), 2.5)
        self.assertEqual(sales_data_utils.get_number("bad"), 0)
        self.assertEqual(sales_data_utils.get_number(float("inf")), 0)

        output = capture_output(
            sales_data_utils.print_table,
            "Example",
            ["A"],
            [[1]],
        )
        self.assertIn("Example", output)
        self.assertIn("1", output)
        self.assertIn(
            "No rows to display.",
            capture_output(sales_data_utils.print_table, "Empty", ["A"], []),
        )

    def test_data_loader_success_and_errors(self):
        csv_data = b"sales_region,quantity,unit_price\nNorth,2,\n"
        with patch.object(
            sales_data_loader,
            "urlopen",
            return_value=io.BytesIO(csv_data),
        ):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                data = sales_data_loader.load_sales_data()
        self.assertEqual(data.loc[0, "unit_price"], 0)
        self.assertIn("Successfully loaded", output.getvalue())
        self.assertIn("Missing fields:", output.getvalue())

        with patch.object(
            sales_data_loader,
            "urlopen",
            side_effect=URLError("offline"),
        ):
            with self.assertRaisesRegex(SystemExit, "Could not download"):
                sales_data_loader.load_sales_data()

        with patch.object(
            sales_data_loader,
            "urlopen",
            return_value=io.BytesIO(b""),
        ):
            with self.assertRaisesRegex(SystemExit, "file is empty"):
                sales_data_loader.load_sales_data()

        with patch.object(
            sales_data_loader,
            "urlopen",
            return_value=io.BytesIO(b"other,value\nx,1\n"),
        ):
            with self.assertRaisesRegex(SystemExit, "none of the dashboard"):
                sales_data_loader.load_sales_data()

    def test_loader_parse_error_and_duplicate_columns(self):
        with patch.object(
            sales_data_loader,
            "urlopen",
            return_value=io.BytesIO(b"header\n"),
        ), patch.object(
            sales_data_loader.pd,
            "read_csv",
            side_effect=pd.errors.ParserError("bad CSV"),
        ):
            with self.assertRaisesRegex(SystemExit, "Could not parse"):
                sales_data_loader.load_sales_data()

        duplicate_data = pd.DataFrame(
            [["North", 1]],
            columns=["sales_region", "sales_region"],
        )
        with patch.object(
            sales_data_loader,
            "urlopen",
            return_value=io.BytesIO(b"sales_region,sales_region\nNorth,1\n"),
        ), patch.object(
            sales_data_loader.pd,
            "read_csv",
            return_value=duplicate_data,
        ):
            with self.assertRaisesRegex(SystemExit, "duplicate column names"):
                sales_data_loader.load_sales_data()

    def test_summary_has_totals_and_missing_field_messages(self):
        output = capture_output(reports.show_sales_summary, self.data)
        for expected in [
            "Total orders",
            "2025-01-01 to 2025-01-03",
            "40.00",
            "10.00",
        ]:
            self.assertIn(expected, output)

        partial_data = pd.DataFrame({"quantity": [2]})
        output = capture_output(reports.show_sales_summary, partial_data)
        self.assertIn("Unavailable (missing order_id)", output)
        self.assertIn("Unavailable (missing customer_id)", output)

    def test_reports_show_expected_results(self):
        reports_to_check = [
            (
                reports.show_total_by_region_and_order,
                ["North", "10.00", "12.00"],
            ),
            (
                reports.show_average_sales_by_region_state_and_order,
                ["Average Sales", "North", "CA"],
            ),
            (
                reports.show_sales_by_customer_order_type_and_state,
                ["Business", "Individual", "CA", "NY"],
            ),
            (
                reports.show_quantity_and_sales_by_region_product,
                ["Apples", "Total Quantity", "22.00"],
            ),
            (
                reports.show_quantity_and_sales_by_order_customer,
                ["Business", "10.00", "12.00"],
            ),
            (
                reports.show_price_range_by_category,
                ["Fruit", "4.00", "10.00"],
            ),
            (
                reports.show_unique_employees_by_region,
                ["North", "South"],
            ),
            (
                reports.show_region_product_percentages,
                ["Quantity % of Region", "20.00%", "55.56%"],
            ),
        ]

        for function, expected in reports_to_check:
            output = capture_output(function, self.data)
            for text in expected:
                self.assertIn(text, output)

    def test_preview_input_and_custom_pivot(self):
        preview = run_with_input(
            reports.show_first_rows,
            ["bad", "2"],
            self.data,
        )
        self.assertIn("Invalid input", preview)
        self.assertIn("First 2 Rows", preview)
        self.assertIn(
            "First 4 Rows",
            run_with_input(reports.show_first_rows, ["all"], self.data),
        )
        self.assertIn(
            "Preview skipped.",
            run_with_input(reports.show_first_rows, [""], self.data),
        )
        self.assertIn(
            "no rows to display",
            capture_output(
                reports.show_first_rows,
                pd.DataFrame(columns=["sales_region"]),
            ),
        )

        pivot = run_with_input(
            reports.show_custom_pivot,
            ["1", "", "1", "1"],
            self.data,
        )
        self.assertIn("Custom Pivot Table", pivot)
        self.assertIn("quantity (sum)", pivot)

        self.assertEqual(
            reports.make_group_name(
                {"sales_region": "North"},
                ["sales_region"],
            ),
            ("North",),
        )
        self.assertEqual(reports.join_items(["North", "Retail"]), "North / Retail")
        with patch("builtins.input", return_value=""):
            self.assertEqual(
                reports.choose_items(["Retail"], "Choose: ", optional=True),
                [],
            )
        with patch("builtins.input", side_effect=["bad", "2"]):
            self.assertEqual(
                reports.choose_items(["Retail", "Wholesale"], "Choose: "),
                ["Wholesale"],
            )
        self.assertIn(
            "no available row fields",
            capture_output(
                reports.show_custom_pivot,
                pd.DataFrame({"other": [1]}),
            ),
        )

    def test_menu_hides_missing_reports_and_runs_all_options(self):
        partial_data = pd.DataFrame({"sales_region": ["North"]})
        output = run_with_input(dashboard.run_menu, ["2"], partial_data)
        self.assertIn("Some reports are hidden", output)
        self.assertIn("2. Exit", output)
        self.assertNotIn("Total sales by region", output)

        answers = [
            "1", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "10", "1", "", "1", "1", "11",
        ]
        output = run_with_input(dashboard.run_menu, answers, self.data)
        self.assertIn("Quantity and Sales Percentages", output)
        self.assertIn("Custom Pivot Table", output)
        self.assertIn("Goodbye.", output)

    def test_menu_errors_and_main_startup(self):
        output = run_with_input(
            dashboard.run_menu,
            ["bad", "99", "2", "11"],
            self.data,
        )
        self.assertIn("Invalid input", output)
        self.assertIn("Sales by Region and Order Type", output)
        self.assertIn("Goodbye.", output)

        self.assertFalse(dashboard.exit_dashboard(self.data))
        with patch.object(
            dashboard,
            "load_sales_data",
            return_value=self.data,
        ), patch.object(dashboard, "run_menu") as run_menu:
            capture_output(dashboard.main)
        run_menu.assert_called_once_with(self.data)

    def test_report_files_use_shared_functions(self):
        report_files = [
            "Show the first n rows of sales data.py",
            "Total sales by region and order_type.py",
            "Average sales by region with average sales by state and sale type.py",
            "Sales by customer type and order type by state.py",
            "Total sales quantity and price by region and product.py",
            "Total sales quantity and price by customer type.py",
            "Max and min sales price of sales by category.py",
            "Number of unique employees by region.py",
            "Sales quantity and sales percentages by region and product.py",
            "Create custom pivot table.py",
        ]
        for file_name in report_files:
            load_file(file_name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
