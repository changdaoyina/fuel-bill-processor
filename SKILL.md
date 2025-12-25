---
name: fuel-bill-processor
description: Process aviation fuel surcharge bills from Excel files. Automatically detects headers, matches columns, parses dates/routes, and fetches contract numbers via API. Use when working with aviation fuel bills, Excel file processing, or when user mentions fuel surcharges,航空燃油账单, or 燃油差价费.
---

# Fuel Bill Processor

An intelligent tool for processing aviation fuel surcharge bills from Excel files. Supports automatic format detection, data transformation, and API integration.

## Quick Start

```bash
# Process a file with default settings
python3 scripts/process.py input_file.xls

# Specify output file
python3 scripts/process.py input_file.xls -o output.xlsx

# Use custom configuration
python3 scripts/process.py input_file.xls -c config.json
```

## Features

- **Auto Header Detection**: Intelligently identifies header row position in Excel files
- **Fuzzy Column Matching**: Automatically recognizes column names with variations
- **Flexible Date Parsing**: Supports multiple date formats (YY-MM-DD, YYYY-MM-DD, YYYY/MM/DD)
- **Route Parsing**: Extracts origin/destination city codes from route strings
- **API Integration**: Fetches contract numbers from flight API
- **Data Validation**: Filters empty rows, summary rows, and invalid data

## Instructions

When processing fuel bill files:

1. **Verify dependencies are installed**:
   ```bash
   pip install pandas openpyxl xlrd requests
   ```

2. **Create configuration file** from the template:
   ```bash
   cp config.template.json config.json
   # Edit config.json with your API settings
   ```

3. **Run the processor** with appropriate input file

4. **Handle common issues**:
   - If column recognition fails: Add column name variants to `column_mappings` in config
   - If API calls fail: Check network connectivity and API URL
   - If date parsing fails: Add date format to `date_formats` in config

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

## Example Usage

```python
import sys
sys.path.insert(0, '.claude/skills/fuel-bill-processor/scripts')
from process import FuelBillProcessor

# Create processor instance
processor = FuelBillProcessor()

# Process file
result = processor.process('bill_2025.xls', 'output.xlsx')
```

## Troubleshooting

**Column not recognized**: Add alternative column names to `column_mappings` in config
**Date parsing fails**: Add the date format to `date_formats` array
**API returns empty**: Verify API URL and check network connectivity
**Empty output file**: Check if input file has valid data rows

For detailed API reference and advanced usage, see [REFERENCE.md](REFERENCE.md).
