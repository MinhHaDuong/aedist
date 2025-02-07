# reconcile.py
#
# Minh Ha-Duong, CNRS (2025)
# CC-BY-SA
"""
This module reconciles two power plant datasets by cleaning and grouping the data,
comparing the inventories, and writing the results to a CSV file.
The output CSV is recreated from scratch on every run.
"""

import sys
import os
import argparse
import logging
from dataclasses import replace
import pandas as pd

#from Matching.phased import reconcile
from Matching.lp import reconcile
from PowerPlantDataframeCleaner.cleaner import PowerPlantDataframeCleaner
from utils import ensure_string_columns, ReconciliationContext

# --------------------------------------------------------------------------
# Logging Configuration
# --------------------------------------------------------------------------
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Simple logging format for readability
)


def get_safe_value(row_data: pd.Series, key: str, default):
    """
    Retrieve a value safely from a pandas Series. Returns default if the value is
    missing or NaN.

    Args:
        row_data (pd.Series): The row of data.
        key (str): The key to extract.
        default: The default value if missing/NaN.

    Returns:
        The extracted value or default.
    """
    val = row_data.get(key, default)
    return val if pd.notna(val) else default


def build_csv_row(
    context: ReconciliationContext, row_data: pd.Series, counters: dict
) -> dict:
    """
    Build a CSV row from a reconciled entry and update the corresponding counter.

    Args:
        context (ReconciliationContext): Contains province, fuel, file info.
        row_data (pd.Series): A row from the reconciled DataFrame.
        counters (dict): Dictionary of counters to update.

    Returns:
        dict: Dictionary representing a CSV row.
    """
    status = row_data.get("status", "Unknown")
    name_file1 = get_safe_value(row_data, "name_file1", "Unknown")
    name_file2 = get_safe_value(row_data, "name_file2", "Unknown")
    capacity_file1 = get_safe_value(row_data, "capacity_file1", "N/A")
    capacity_file2 = get_safe_value(row_data, "capacity_file2", "N/A")
    capacity_diff = get_safe_value(row_data, "capacity_difference", "N/A")

    row = {
        "Province": context.province,
        "Fuel": context.fuel,
        "Name (File 1)": name_file1,
        "Name (File 2)": name_file2,
        "Capacity (File 1)": capacity_file1,
        "Capacity (File 2)": capacity_file2,
        "Difference (MW)": capacity_diff,
    }
    if status == "Only in file1":
        counters["only_in_file1"] += 1
        row.update(
            {
                "Status": "Only in File 1",
                "Name (File 2)": "N/A",
                "Capacity (File 2)": "N/A",
                "Difference (MW)": "N/A",
            }
        )
    elif status == "Only in file2":
        counters["only_in_file2"] += 1
        row.update(
            {
                "Status": "Only in File 2",
                "Name (File 1)": "N/A",
                "Capacity (File 1)": "N/A",
                "Difference (MW)": "N/A",
            }
        )
    elif status in ("Matched", "Matched (Fuzzy)"):
        base_status = "Matched" if status == "Matched" else "Matched (Fuzzy)"
        if capacity_diff == 0:
            key = "matched_exact" if status == "Matched" else "matched_fuzzy"
            row["Status"] = base_status
        else:
            key = "matched_exact_diff" if status == "Matched" else "matched_fuzzy_diff"
            row["Status"] = f"{base_status} (Diff)"
        counters[key] += 1
    else:
        row["Status"] = status
    return row


def reconcile_inventories(
    group1: pd.DataFrame, group2: pd.DataFrame, context: ReconciliationContext
) -> dict:
    """
    Reconcile data (inventories) for a given province and fuel, log details, and append
    the resulting rows to a CSV file.

    Args:
        group1 (pd.DataFrame): Data subset from file1.
        group2 (pd.DataFrame): Data subset from file2.
        context (ReconciliationContext): Contains province, fuel, and file info.

    Returns:
        dict: Statistics of the matching process.
    """
    logging.info("   Reconciling inventories for fuel: %s", context.fuel)
    reconciled = reconcile(group1, group2)

    csv_rows = []
    counters = {
        "matched_exact": 0,
        "matched_exact_diff": 0,
        "matched_fuzzy": 0,
        "matched_fuzzy_diff": 0,
        "only_in_file1": 0,
        "only_in_file2": 0,
    }

    for _, row_data in reconciled.iterrows():
        csv_rows.append(build_csv_row(context, row_data, counters))

    total_rows = (
        counters["matched_exact"]
        + counters["matched_exact_diff"]
        + counters["matched_fuzzy"]
        + counters["matched_fuzzy_diff"]
        + counters["only_in_file1"]
        + counters["only_in_file2"]
    )
    if total_rows != len(reconciled):
        logging.warning(
            "Inconsistent totals: %d != %d. Check for data issues.",
            total_rows,
            len(reconciled),
        )

    result_df = pd.DataFrame(csv_rows)
    with open(context.output_csv, mode="a", newline="", encoding="utf-8") as f:
        result_df.to_csv(f, index=False, header=f.tell() == 0)

    logging.info("  Total Rows Processed: %d", len(reconciled))
    logging.info("  Matched (Exact): %d", counters["matched_exact"])
    logging.info(
        "  Matched (Exact, Different capacity): %d", counters["matched_exact_diff"]
    )
    logging.info("  Matched (Fuzzy): %d", counters["matched_fuzzy"])
    logging.info(
        "  Matched (Fuzzy, Different capacity): %d", counters["matched_fuzzy_diff"]
    )
    logging.info("  Only in %s: %d", context.file1, counters["only_in_file1"])
    logging.info("  Only in %s: %d", context.file2, counters["only_in_file2"])

    return {
        "matched": counters["matched_exact"],
        "matched_with_diff": counters["matched_exact_diff"],
        "matched_fuzzy": counters["matched_fuzzy"],
        "matched_fuzzy_with_diff": counters["matched_fuzzy_diff"],
        "only_in_file1": counters["only_in_file1"],
        "only_in_file2": counters["only_in_file2"],
        "total_rows": len(reconciled),
    }


def load_and_clean_data(file1: str, file2: str):
    """
    Reads the input CSV files and cleans the data.

    Args:
        file1 (str): Path to the first CSV file.
        file2 (str): Path to the second CSV file.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Cleaned DataFrames for file1 and file2.
    """
    logging.info("Reading input file: %s", file1)
    df1 = pd.read_csv(file1)
    logging.info("Reading input file: %s", file2)
    df2 = pd.read_csv(file2)

    # Initialize the data cleaner.
    cleaner = PowerPlantDataframeCleaner(
        config_path="PowerPlantDataframeCleaner/config.json"
    )
    logging.info("Cleaning '%s'...", file1)
    cleaned_df1 = cleaner.clean_dataframe(df1)
    logging.info("Cleaning '%s'...", file2)
    cleaned_df2 = cleaner.clean_dataframe(df2)

    # Ensure necessary columns are strings.
    cleaned_df1 = ensure_string_columns(cleaned_df1, ["province_clean", "fuel_clean"])
    cleaned_df2 = ensure_string_columns(cleaned_df2, ["province_clean", "fuel_clean"])
    return cleaned_df1, cleaned_df2


def group_data(cleaned_df1: pd.DataFrame, cleaned_df2: pd.DataFrame):
    """
    Groups both cleaned DataFrames by 'province_clean' and 'fuel_clean' and computes
    the union of all group keys.

    Args:
        cleaned_df1 (pd.DataFrame): Cleaned data from file1.
        cleaned_df2 (pd.DataFrame): Cleaned data from file2.

    Returns:
        Tuple: grouped_df1, grouped_df2, and all_combinations (set of group keys).
    """
    grouped_df1 = cleaned_df1.groupby(["province_clean", "fuel_clean"])
    grouped_df2 = cleaned_df2.groupby(["province_clean", "fuel_clean"])
    all_combinations = set(grouped_df1.groups.keys()).union(grouped_df2.groups.keys())
    return grouped_df1, grouped_df2, all_combinations


def log_overall_statistics(totals: dict, file1: str, file2: str):
    """
    Logs overall reconciliation statistics.

    Args:
        totals (dict): Aggregated reconciliation statistics.
        file1 (str): Filename for file1.
        file2 (str): Filename for file2.
    """
    logging.info("Overall Reconciliation Statistics:")
    logging.info("  Total Rows Processed: %d", totals["total_rows"])
    logging.info("  Matched (Exact): %d", totals["matched"])
    logging.info("  Matched (With Differences): %d", totals["matched_with_diff"])
    logging.info("  Matched (Fuzzy): %d", totals["matched_fuzzy"])
    logging.info(
        "  Matched (Fuzzy With Differences): %d", totals["matched_fuzzy_with_diff"]
    )
    logging.info("  Only in %s: %d", file1, totals["only_in_file1"])
    logging.info("  Only in %s: %d", file2, totals["only_in_file2"])


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments (file paths).
    """
    parser = argparse.ArgumentParser(description="Compare two power plant datasets.")
    parser.add_argument("file1", help="Path to the first CSV file")
    parser.add_argument("file2", help="Path to the second CSV file")
    return parser.parse_args()


def main():
    """
    Main function coordinating the reconciliation process.

    It reads input files, cleans data, groups by province and fuel,
    processes each group inline, and logs the overall results.

    # pylint: disable=too-many-locals
    """
    args = parse_args()
    file1 = args.file1
    file2 = args.file2
    output_csv = "reconciliation_results.csv"

    # Remove any existing output CSV for a fresh run.
    if os.path.exists(output_csv):
        os.remove(output_csv)

    try:
        # Load and clean data.
        cleaned_df1, cleaned_df2 = load_and_clean_data(file1, file2)
        # Group the data.
        grouped_df1, grouped_df2, all_combinations = group_data(
            cleaned_df1, cleaned_df2
        )

        # Build a base context early using constant file values and output.
        base_context = ReconciliationContext(
            province="", fuel="", file1=file1, file2=file2, output_csv=output_csv
        )

        # Inline processing of all (province, fuel) groups.
        totals = {
            "matched": 0,
            "matched_with_diff": 0,
            "matched_fuzzy": 0,
            "matched_fuzzy_with_diff": 0,
            "only_in_file1": 0,
            "only_in_file2": 0,
            "total_rows": 0,
        }
        for province, fuel in sorted(all_combinations):
            logging.info("Processing province: %s, fuel: %s", province, fuel)
            group1 = (
                grouped_df1.get_group((province, fuel))
                if (province, fuel) in grouped_df1.groups
                else pd.DataFrame(columns=cleaned_df1.columns)
            )
            group2 = (
                grouped_df2.get_group((province, fuel))
                if (province, fuel) in grouped_df2.groups
                else pd.DataFrame(columns=cleaned_df2.columns)
            )
            # Create a context for the current group by updating province and fuel.
            context = replace(base_context, province=province, fuel=fuel)
            stats = reconcile_inventories(group1, group2, context)
            for key in totals:
                totals[key] += stats[key]

        # Log overall reconciliation statistics.
        log_overall_statistics(totals, file1, file2)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("An error occurred: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
