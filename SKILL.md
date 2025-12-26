---
name: fuel-bill-processor
description: Process aviation fuel surcharge bills from Excel files. Supports both automatic detection and Claude-assisted modes. Detects headers, matches columns, parses dates/routes, and fetches contract numbers via API. Use when working with aviation fuel bills, Excel file processing, or when user mentions fuel surcharges,航空燃油账单, or 燃油差价费.
---

# Fuel Bill Processor

Process aviation fuel surcharge bills from Excel files with automatic format detection or Claude-assisted mode.

## Processing Workflow

When a user asks to process fuel bill files, follow this workflow:

### Step 1: Try Automatic Mode First

**IMPORTANT**: Always try automatic mode first. It works for most cases.

```bash
python3 scripts/process.py input_file.xls
```

The automatic processor:
- Detects header rows within the first 15 rows
- Fuzzy matches common column names (航班日期, 航段, 航班号, 燃油差价费)
- Handles .xls and .xlsx formats
- Filters invalid data automatically

Specify output file if needed:
```bash
python3 scripts/process.py input_file.xls -o output.xlsx
```

### Step 2: Use Claude-Assisted Mode (Only if Step 1 Fails)

Only use Claude-Assisted Mode if:
- Automatic mode fails or produces incorrect results
- Header row is beyond row 15
- Column names are highly non-standard
- Complex table structure (merged cells, multi-level headers)

**Process:**

1. Analyze the Excel structure:
   ```python
   import pandas as pd
   df = pd.read_excel('input_file.xls', header=None, nrows=30)
   # Identify: header row index and column positions
   ```

2. Create runtime config with EXACT format (no extra fields):
   ```bash
   cat > /tmp/runtime.json <<'EOF'
   {
     "header_row": 2,
     "columns": {
       "flight_date": "B",
       "route": "C",
       "flight_no": "D",
       "fuel_price": "E"
     }
   }
   EOF
   ```

   **Runtime Configuration Format:**
   - `header_row`: 0-based row index (e.g., if header is in row 3, use 2)
   - `columns`: Column mapping with Excel column letters (A, B, C...) or column names
     - `flight_date`: Flight date column
     - `route`: Route/segment column
     - `flight_no`: Flight number column
     - `fuel_price`: Fuel surcharge amount column

   **DO NOT include**: route_format, origin_col, destination_col, or any other fields

3. Run with runtime config:
   ```bash
   python3 scripts/process.py input_file.xls --runtime-config /tmp/runtime.json
   ```

Alternatively, specify parameters directly:
```bash
python3 scripts/process.py input_file.xls \
  --header-row 2 \
  --date-column B \
  --route-column C \
  --flight-column D \
  --price-column E
```

### Step 3: Verify Results

Check that:
- Output file was created
- Contains expected number of rows
- All required fields are populated

Report results to user.

## Configuration

The processor uses `assets/config.json` which is ready to use out of the box.

Key configuration sections:
- `api`: API endpoint for fetching contract numbers
- `city_codes`: City name to airport code mapping
- `column_mappings`: Alternative column names for fuzzy matching
- `output_fields`: Fixed values for output fields
- `date_formats`: Supported date formats

For detailed configuration reference, see [CONFIGURATION.md](references/CONFIGURATION.md).

## Output

Generates standardized Excel with 9 columns: 空运业务单, 航司, 合同号, 始发港, 目的港, 航班日期, 费用名称, 结算对象名称, 单价.

See [CONFIGURATION.md](references/CONFIGURATION.md) for complete output format details.

## Troubleshooting

**Column not recognized**: Add alternative names to `column_mappings` in config

**Date parsing fails**: Add the format to `date_formats` array

**API returns empty**: Verify API URL and network connectivity

**Empty output file**: Check if input file has valid data rows

## References

- [API_REFERENCE.md](references/API_REFERENCE.md) - Detailed API documentation
- [CONFIGURATION.md](references/CONFIGURATION.md) - Complete configuration guide
