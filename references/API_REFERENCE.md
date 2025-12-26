# Fuel Bill Processor - API Reference

Detailed reference for the `FuelBillProcessor` class.

## Table of Contents

- [Class: FuelBillProcessor](#class-fuelbillprocessor)
  - [Constructor](#constructor)
  - [Methods](#methods)
- [Configuration Schema](#configuration-schema)
- [Error Handling](#error-handling)
- [Exit Codes](#exit-codes)

## Class: FuelBillProcessor

### Constructor

```python
FuelBillProcessor(config_path=None)
```

**Parameters:**
- `config_path` (str, optional): Path to configuration file. If not provided, searches for `config.json` or `config.template.json` in the script directory.

### Methods

#### load_config(config_path=None)

Loads configuration from a JSON file.

**Parameters:**
- `config_path` (str, optional): Path to configuration file

**Returns:** Configuration dictionary

#### fuzzy_match_column(column_name, candidates)

Performs fuzzy matching between a column name and a list of candidates.

**Parameters:**
- `column_name` (str): The column name to match
- `candidates` (list): List of candidate column names

**Returns:** `True` if match found, `False` otherwise

#### identify_columns(df)

Identifies and maps Excel columns to standard field names.

**Parameters:**
- `df` (DataFrame): Input pandas DataFrame

**Returns:** Dictionary mapping standard names to actual column names

**Example:**
```python
{
    'flight_date': '航班日期',
    'route': '航段',
    'flight_no': '航班号',
    'fuel_price': '燃油差价费（元）'
}
```

#### find_header_row(file_path, engine)

Intelligently finds the header row in an Excel file by searching for keywords.

**Parameters:**
- `file_path` (str): Path to Excel file
- `engine` (str): Excel engine ('xlrd' or 'openpyxl')

**Returns:** Index of the header row (0-based)

#### detect_file_format(file_path)

Detects the Excel file format based on file extension.

**Parameters:**
- `file_path` (str): Path to Excel file

**Returns:** Engine name ('xlrd' for .xls, 'openpyxl' for .xlsx)

**Raises:** `ValueError` if file format is not supported

#### read_excel_smart(file_path)

Intelligently reads an Excel file with auto header detection and column identification.

**Parameters:**
- `file_path` (str): Path to Excel file

**Returns:** Processed pandas DataFrame

#### extract_airline(flight_no)

Extracts airline code from flight number.

**Parameters:**
- `flight_no` (str): Flight number (e.g., "GI1234")

**Returns:** Airline code (e.g., "GI") or `None` if extraction fails

#### parse_route(route)

Parses route string to extract origin and destination city codes.

**Parameters:**
- `route` (str): Route string (e.g., "郑州-布达佩斯")

**Returns:** Tuple of (origin_code, destination_code) or (None, None)

**Supported separators:** `-`, `=`, `→`, `->`

#### convert_date(date_val)

Converts various date formats to standard YYYY-MM-DD format.

**Parameters:**
- `date_val`: Date value (string, datetime, or pandas Timestamp)

**Returns:** Standardized date string or original value if conversion fails

**Supported formats:**
- YY-MM-DD (e.g., 25-10-02)
- YYYY-MM-DD (e.g., 2025-10-02)
- YYYY/MM/DD (e.g., 2025/10/02)
- YY/MM/DD (e.g., 25/10/02)

#### get_contract_no(origin, destination, std_str, air_code)

Calls the flight API to fetch contract number.

**Parameters:**
- `origin` (str): Origin city code
- `destination` (str): Destination city code
- `std_str` (str): Flight date in YYYY-MM-DD format
- `air_code` (str): Airline code

**Returns:** Contract number string or `None` if API call fails

**API Payload:**
```json
{
  "origin": "CGO",
  "destination": "BUD",
  "stdStr": "2025-10-02",
  "airCode": "GI"
}
```

#### filter_data(df)

Filters out invalid data rows from the DataFrame.

**Parameters:**
- `df` (DataFrame): Input DataFrame

**Returns:** Filtered DataFrame

**Filtered rows:**
- Empty rows (no flight date)
- Summary rows (containing "合计", "注：", etc.)
- Rows with empty required fields

#### process(input_file, output_file=None)

Main processing method that orchestrates the entire bill processing workflow.

**Parameters:**
- `input_file` (str): Path to input Excel file
- `output_file` (str, optional): Path to output Excel file. If not provided, generates automatically.

**Returns:** Processed pandas DataFrame or `None` if processing fails

**Workflow:**
1. Read Excel file with smart detection
2. Filter invalid data
3. Process each row:
   - Extract flight date
   - Extract airline code
   - Parse route
   - Fetch contract number via API
4. Generate output DataFrame
5. Save to Excel file

## Configuration Schema

### api

API endpoint configuration.

```json
{
  "api": {
    "url": "http://api.example.com/endpoint",
    "timeout": 10
  }
}
```

### city_codes

Mapping of city names to IATA airport codes.

```json
{
  "city_codes": {
    "郑州": "CGO",
    "布达佩斯": "BUD"
  }
}
```

### column_mappings

Alternative column names for fuzzy matching.

```json
{
  "column_mappings": {
    "flight_date": ["航班日期", "日期", "飞行日期"],
    "route": ["航段", "航线", "路线"],
    "flight_no": ["航班号", "航班", "班次号"],
    "fuel_price": ["燃油差价费（元）", "燃油差价费", "差价费"]
  }
}
```

### output_fields

Fixed values for output fields.

```json
{
  "output_fields": {
    "business_type": "航班",
    "fee_name": "燃油附加费",
    "settlement_name": "龙浩"
  }
}
```

### date_formats

List of date formats to try when parsing dates.

```json
{
  "date_formats": ["%y-%m-%d", "%Y-%m-%d", "%Y/%m/%d", "%y/%m/%d"]
}
```

## Error Handling

The processor handles various error conditions:

- **File format errors**: Raises `ValueError` for unsupported file types
- **API failures**: Prints error message and continues with `None` contract number
- **Column recognition**: Prints warning but continues with partial column mapping
- **Date parsing**: Falls back to original value if all formats fail

## Exit Codes

When run from command line:
- `0`: Success
- `1`: Processing failure (with traceback printed)
