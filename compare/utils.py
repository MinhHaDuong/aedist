import logging
import pandas as pd
from dataclasses import dataclass

@dataclass
class ReconciliationContext:
    """
    Holds context information for the reconciliation process.
    """
    province: str
    fuel: str
    file1: str
    file2: str
    output_csv: str = "reconciliation_results.csv"


def format_filename(filename, length=20):
    """
    Format the filename to take up exactly `length` characters.
    If the filename is shorter, pad with spaces.
    If it's longer, shorten from the middle and insert '...'.

    Args:
        filename (str): The filename to format.
        length (int): The desired length of the formatted string.

    Returns:
        str: The formatted filename.
    """
    if len(filename) <= length:
        return filename.ljust(length)  # Pad with spaces to the right
    else:
        # Shorten the filename from the middle
        part_length = (length - 3) // 2  # Length of each part (before and after '...')
        return f"{filename[:part_length]}...{filename[-part_length:]}"


def format_fixed_width(text, width=20):
    """
    Format a string to a fixed width by truncating or padding with spaces.

    Args:
        text (str): The input string to format.
        width (int): The fixed width of the output string.

    Returns:
        str: The formatted string.
    """
    return text[:width].ljust(width) if isinstance(text, str) else "".ljust(width)


def ensure_string_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Ensure that each specified column in 'columns' is of type string.
    If non-string values (like float) are found, log a warning and force a cast to str.

    Args:
        df (pd.DataFrame): The DataFrame to validate/fix.
        columns (list): A list of column names (e.g. ["province_clean", "fuel_clean"]).

    Returns:
        pd.DataFrame: The same DataFrame with the target columns guaranteed as strings.
    """
    for col in columns:
        if col not in df.columns:
            logging.warning(
                f"Column '{col}' not found in DataFrame. Skipping string-enforcement for this column."
            )
            continue

        # Identify non-string entries
        non_string_mask = ~df[col].apply(lambda x: isinstance(x, str) or pd.isnull(x))
        if non_string_mask.any():
            logging.warning(
                f"Non-string values detected in column '{col}'. "
                f"Casting {non_string_mask.sum()} entries to string."
            )

        # Force string conversion for all entries in this column
        df[col] = df[col].astype(str)

    return df
