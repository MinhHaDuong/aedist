# PowerPlantDataframeCleaner

## Overview

`PowerPlantDataframeCleaner` is a Python utility module for cleaning and standardizing power plant data stored in a Pandas DataFrame. It provides functionality to validate the input data, clean text fields, and apply custom cleaning patterns for columns  `name`, `province`, `fuel`, `capacity`, and `status`.

The module dynamically loads cleaning patterns from a configuration file in JSON format, allowing for customizable cleaning rules.

---

## Features

- **Validation**: Ensures the DataFrame is not empty and contains required columns.
- **Text Cleaning**: Standardizes text by removing diacritics, applying substitutions, and cleaning up whitespace.
- **Column-Specific Cleaning**:
  - **`name`**: Removes unwanted patterns and standardizes plant names.
  - **`province`**: Substitutes province names based on a mapping.
  - **`fuel`**: Handles multiple fuel types and standardizes fuel names.
  - **`capacity`**: Extracts numeric values from capacity strings.
  - **`status`**: Standardizes status values based on a mapping.
- **Customizable Cleaning Patterns**: Loads cleaning rules from a JSON configuration file.
- **Command-Line Usage**: Supports reading and cleaning input CSV files via standard input and output.

---

## Installation

Ensure you have the required Python dependencies installed:

```bash
pip install pandas
```

---

## Usage

### Importing the Module

```python
import pandas as pd
from PowerPlantDataframeCleaner.cleaner import PowerPlantDataframeCleaner

# Initialize the cleaner
cleaner = PowerPlantDataframeCleaner(config_path="PowerPlantDataframeCleaner_Patterns.json")

# Load a DataFrame
df = pd.read_csv("input.csv")

# Clean the DataFrame
cleaned_df = cleaner.clean_dataframe(df)

# Save the cleaned DataFrame
cleaned_df.to_csv("output.csv", index=False)
```

### Command-Line Usage

This module can be used directly from the command line to process CSV files. It reads input from `stdin` and writes the cleaned output to `stdout`.

```bash
cat input.csv | python cleaner.py > cleaned_output.csv
```

---

## Configuration

The module requires a JSON configuration file, such as `config.json`, to define cleaning patterns. An example configuration file is shown below:

```json
{
    "name_drops": ["co.", "corp."],
    "province_substitutions": {
        "ontario": "ON",
        "quebec": "QC"
    },
    "fuel_substitutions": {
        "natural gas": "gas",
        "coal-fired": "coal"
    },
    "status_substitutions": {
        "operational": "active",
        "under construction": "construction"
    }
}
```

### Configuration Fields

- **`name_drops`**: A list of regex patterns to be removed from the `name` column.
- **`province_substitutions`**: A mapping of province names to their standardized forms.
- **`fuel_substitutions`**: A mapping of fuel types to standardized forms.
- **`status_substitutions`**: A mapping of plant statuses to standardized forms.

---

## Required Columns

The input DataFrame must contain the following columns:

- `name`
- `province`
- `fuel`
- `capacity`
- `status`

If the `name` column is missing but both `Plant name` and `Unit name` columns are present, they will be concatenated to create the `name` column.

---

## API Reference

### `PowerPlantDataframeCleaner`

#### Constructor

```python
PowerPlantDataframeCleaner(config_path: str = "PowerPlantDataframeCleaner_Patterns.json")
```

- **`config_path`**: Path to the JSON configuration file. Defaults to `PowerPlantDataframeCleaner_Patterns.json`.

---

### Methods

#### `validate_dataframe(df: pd.DataFrame) -> None`

Validates that the input DataFrame contains the required columns and is not empty. If `name` is missing but `Plant name` and `Unit name` exist, it creates the `name` column by concatenating the two.

- **`df`**: Input DataFrame to validate.

Raises:
- `ValueError` if the DataFrame is empty or required columns are missing.

---

#### `clean_text(text: str, drops=None, substitutions=None) -> Optional[str]`

Cleans a text string by applying cleaning patterns and standardizing whitespace.

- **`text`**: Input text to clean.
- **`drops`**: List of regex patterns to remove.
- **`substitutions`**: Dictionary of regex substitutions.

Returns:
- Cleaned text or `None` if the input is `NaN`.

---

#### `clean_name(name: str) -> str`

Cleans the `name` column using `name_drops` patterns.

- **`name`**: Input plant name.

---

#### `clean_province(province: str) -> str`

Cleans the `province` column using `province_substitutions`.

- **`province`**: Input province name.

---

#### `clean_capacity(value: Union[str, float, int]) -> Optional[float]`

Extracts the first numeric value from the `capacity` column.

- **`value`**: Input capacity value (string, float, or integer).

Returns:
- Capacity as a float or `None` if invalid.

---

#### `clean_fuel(fuel: str) -> Optional[str]`

Cleans the `fuel` column, standardizing multiple fuel types.

- **`fuel`**: Input fuel value.

Returns:
- Standardized fuel value or `None`.

---

#### `clean_status(status: str) -> Optional[str]`

Cleans the `status` column using `status_substitutions`.

- **`status`**: Input status value.

---

#### `clean_dataframe(df: pd.DataFrame) -> pd.DataFrame`

Cleans the input DataFrame and returns a new DataFrame with additional cleaned columns.

- **`df`**: Input DataFrame with required columns (`name`, `province`, `fuel`, `capacity`, `status`).

Returns:
- A cleaned DataFrame with additional columns:
  - `name_clean`
  - `province_clean`
  - `capacity_clean`
  - `fuel_clean`
  - `status_clean`

Raises:
- `ValueError` if required columns are missing or the DataFrame is empty.

---

## Logging

The module uses Python's `logging` library for logging messages. By default, the log level is set to `INFO`. Change this to `DEBUG` for more verbose output during debugging.

---

## Error Handling

The module handles common errors, such as:

- Missing configuration file (`FileNotFoundError`).
- Malformed JSON configuration (`JSONDecodeError`).
- Missing required columns in the DataFrame (`ValueError`).

Detailed error messages and stack traces are logged for debugging purposes.

---

## Example

### Input CSV (`input.csv`)

```csv
name,province,fuel,capacity,status
Plant A,Ontario,Natural Gas,500,Operational
Plant B,Quebec,Coal-Fired,1200,Under Construction
```

### Configuration File (`PowerPlantDataframeCleaner_Patterns.json`)

```json
{
    "name_drops": ["plant"],
    "province_substitutions": {
        "ontario": "ON",
        "quebec": "QC"
    },
    "fuel_substitutions": {
        "natural gas": "gas",
        "coal-fired": "coal"
    },
    "status_substitutions": {
        "operational": "active",
        "under construction": "construction"
    }
}
```

### Command

```bash
cat input.csv | python cleaner.py > cleaned_output.csv
```

### Output CSV (`cleaned_output.csv`)

```csv
name,province,fuel,capacity,status,name_clean,province_clean,capacity_clean,fuel_clean,status_clean
Plant A,Ontario,Natural Gas,500,Operational,a,on,500.0,gas,active
Plant B,Quebec,Coal-Fired,1200,Under Construction,b,qc,1200.0,coal,construction
```

---

## License

This module is distributed under the CC-By-SA.