# PowerPlantDataframeCleaner Patterns Configuration

This document describes the purpose of each section in the `PowerPlantDataframeCleaner_Patterns.json` file.

---

## 1. `name_drops`
Defines patterns to remove unwanted text from the `name` column. These are regular expressions (regex).

### Examples:
- `"^tbkhh\\s*"`: Removes 'TBKHH' at the start of the name, followed by optional spaces.
- `"power\\s*plant"`: Removes the phrase 'power plant' (with optional spaces between words).
- `"\\(.*?\\)"`: Removes text inside parentheses, e.g., `"Plant A (Local)"` becomes `"Plant A"`.

---

## 2. `province_substitutions`
Maps non-standard province names to standardized names. The keys are regex patterns, and the values are the standardized forms.

### Examples:
- `"ba\\s*ria\\s*[-]?\\s*vung\\s*tau"` → `"ba ria - vung tau"`: Handles variations like 'Ba Ria Vung Tau' or 'Ba Ria-Vung Tau'.
- `"ho\\s*chi\\s*minh\\s*city"` → `"tp ho chi minh"`: Standardizes 'Ho Chi Minh City' to 'TP Ho Chi Minh'.

---

## 3. `fuel_substitutions`
Maps non-standard fuel types to standardized types.

### Examples:
- `"lng"` → `"gas"`: Converts 'LNG' to 'gas'.
- `"(?i).*coal.*"` → `"coal"`: Converts anything containing 'coal' (case-insensitive) to 'coal'.

---

## 4. `status_substitutions`
Maps non-standard power plant statuses to standardized terms.

### Examples:
- `"^\\d+\\s*(.+)$"` → `"\\1"`: Removes leading numbers followed by a space, e.g., `"123 Operating"` becomes `"Operating"`.
- `"construction"` → `"construction"`: Standardizes 'Construction' to lowercase.
- `"shelved"` → `"shelved"`: Keeps the status as 'shelved' but ensures consistency.

---

## Notes
- **Regex Syntax**: Patterns in the JSON use Python's regex syntax. Learn more about regex syntax [here](https://docs.python.org/3/library/re.html).
- **Customizations**: You can add or modify patterns in the JSON file based on your dataset's requirements.