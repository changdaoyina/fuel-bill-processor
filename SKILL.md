---
name: fuel-bill-processor
description: Process aviation fuel surcharge bills from Excel files. Supports both automatic detection and Claude-assisted modes. Detects headers, matches columns, parses dates/routes, and fetches contract numbers via API. Use when working with aviation fuel bills, Excel file processing, or when user mentions fuel surcharges,航空燃油账单, or 燃油差价费.
---

# Fuel Bill Processor v2.0

An intelligent tool for processing aviation fuel surcharge bills from Excel files. Supports automatic format detection, **Claude-assisted mode**, data transformation, and API integration.

## 🆕 What's New in v2.0

- **Claude-Assisted Mode**: Claude can analyze Excel structure and provide precise parameters
- **Flexible Processing**: Accepts runtime configuration for complex Excel formats
- **Modular Architecture**: Separated into extraction, API calls, and data assembly steps

## Quick Start

### Mode 1: Automatic Detection (Default)
```bash
# Process a file with automatic header/column detection
python3 scripts/process.py input_file.xls

# Specify output file
python3 scripts/process.py input_file.xls -o output.xlsx

# Use custom configuration
python3 scripts/process.py input_file.xls -c config.json
```

### Mode 2: Claude-Assisted (Recommended for Complex Files)
When Claude processes a fuel bill, it can:
1. Read and analyze the Excel file structure
2. Identify the exact header row and column positions
3. Pass this information to the processor for accurate extraction

```bash
# Claude provides runtime configuration
python3 scripts/process.py input_file.xls --runtime-config /tmp/runtime.json

# Or Claude specifies parameters directly
python3 scripts/process.py input_file.xls \
  --header-row 2 \
  --date-column B \
  --route-column C \
  --flight-column D \
  --price-column E
```

## Features

- **Auto Header Detection**: Intelligently identifies header row position in Excel files
- **Fuzzy Column Matching**: Automatically recognizes column names with variations
- **Flexible Date Parsing**: Supports multiple date formats (YY-MM-DD, YYYY-MM-DD, YYYY/MM/DD)
- **Route Parsing**: Extracts origin/destination city codes from route strings
- **API Integration**: Fetches contract numbers from flight API
- **Data Validation**: Filters empty rows, summary rows, and invalid data

## Instructions for Claude

When a user asks to process fuel bill files:

### Step 1: Try Automatic Mode First (Recommended)

**IMPORTANT**: In most cases, automatic mode works well. Always try it first!

```bash
python3 scripts/process.py input_file.xls
```

The automatic processor can:
- Detect header rows within the first 15 rows
- Fuzzy match common column names (航班日期, 航段, 航班号, 燃油差价费)
- Handle standard Excel formats (.xls, .xlsx)

### Step 2: Use Claude-Assisted Mode ONLY if Automatic Mode Fails

**Only use Claude-Assisted Mode if:**
- Automatic mode fails or produces incorrect results
- Header row is beyond row 15
- Column names are highly non-standard
- Complex table structure (merged cells, multi-level headers)

### Step 3: Execute Claude-Assisted Mode (If Needed)

**First, analyze the Excel structure:**
```python
# Read first 30 rows to identify structure
import pandas as pd
df = pd.read_excel('input_file.xls', header=None, nrows=30)
# Identify: header row index and column positions
```

**Then, create runtime config with EXACT format:**

⚠️ **IMPORTANT**: Only include these fields - no extra fields!

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

# Run with runtime config
python3 scripts/process.py input_file.xls --runtime-config /tmp/runtime.json
```

**Runtime Configuration Format:**
- `header_row`: 0-based row index (e.g., if header is in row 3, use 2)
- `columns`: Column mapping with Excel column letters (A, B, C...) or column names
  - `flight_date`: Flight date column
  - `route`: Route/segment column
  - `flight_no`: Flight number column
  - `fuel_price`: Fuel surcharge amount column

**DO NOT include**: route_format, origin_col, destination_col, or any other fields

### Step 4: Handle Issues
- If column recognition fails: Adjust column mappings in runtime config
- If API calls fail: Check network connectivity and API URL
- If date parsing fails: The script handles multiple formats automatically

## Configuration File Structure

The `config.json` file (create from `config.template.json`) contains:

```json
{
  "api": {
    "url": "http://api.example.com/endpoint",
    "timeout": 10
  },
  "city_codes": {
    "郑州": "CGO",
    "布达佩斯": "BUD"
  },
  "column_mappings": {
    "flight_date": ["航班日期", "日期", "飞行日期"],
    "route": ["航段", "航线", "路线"],
    "flight_no": ["航班号", "航班", "班次号"],
    "fuel_price": ["燃油差价费（元）", "燃油差价费", "差价费"]
  },
  "output_fields": {
    "business_type": "航班",
    "fee_name": "燃油附加费",
    "settlement_name": "龙浩"
  },
  "date_formats": ["%y-%m-%d", "%Y-%m-%d", "%Y/%m/%d"]
}
```

## Output Format

The processor generates an Excel file with standardized columns:

| Column | Description | Example |
|--------|-------------|---------|
| *空运业务单 | Fixed business type | 航班 |
| *航司 | Airline code from flight number | GI |
| 合同号 | Contract number from API | GI-25-159 |
| *始发港 | Origin city code | CGO |
| *目的港 | Destination city code | BUD |
| 航班日期 | Formatted flight date | 2025-10-02 |
| *费用名称 | Fee name | 燃油附加费 |
| *结算对象名称 | Settlement entity | 龙浩 |
| *单价 | Fuel surcharge amount | -113892.67 |

## Example Workflow for Claude

**User Request:** "Please process this fuel bill: /path/to/bill.xls"

**Claude's Workflow:**

1. **Try automatic mode first (ALWAYS):**
   ```bash
   python3 scripts/process.py /path/to/bill.xls
   ```

2. **If automatic mode succeeds:**
   - Verify the output file was created
   - Report success to user
   - **DONE** - no need for Claude-assisted mode!

3. **Only if automatic mode fails, analyze the file:**
   ```python
   # Read first 30 rows to identify structure
   import pandas as pd
   df = pd.read_excel('/path/to/bill.xls', header=None, nrows=30)
   # Identify: Header at row 3 (index 2)
   # Columns: B=日期, C=航段, D=航班号, E=燃油费
   ```

4. **Create runtime config (only if needed):**
   ```bash
   cat > /tmp/bill_config.json <<'EOF'
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

5. **Execute with runtime config:**
   ```bash
   python3 scripts/process.py /path/to/bill.xls --runtime-config /tmp/bill_config.json
   ```

6. **Verify results and report to user**

## Troubleshooting

**Column not recognized**: Add alternative column names to `column_mappings` in config
**Date parsing fails**: Add the date format to `date_formats` array
**API returns empty**: Verify API URL and check network connectivity
**Empty output file**: Check if input file has valid data rows

For detailed API reference and advanced usage, see [REFERENCE.md](REFERENCE.md).
