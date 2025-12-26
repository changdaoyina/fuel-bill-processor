# Configuration Reference

## Configuration File Structure

The `assets/config.json` file contains all settings for the fuel bill processor and is ready to use.

## Configuration Schema

### Complete Example

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

## Configuration Sections

### api

API endpoint configuration for fetching contract numbers.

- `url` (string): API endpoint URL
- `timeout` (number): Request timeout in seconds

### city_codes

Mapping of city names (Chinese) to IATA airport codes.

Add new mappings here to support additional cities:
```json
"city_codes": {
  "郑州": "CGO",
  "布达佩斯": "BUD",
  "新城市": "XXX"
}
```

### column_mappings

Alternative column names for fuzzy matching. Each field supports multiple possible column names.

- `flight_date`: Flight date column names
- `route`: Route/segment column names
- `flight_no`: Flight number column names
- `fuel_price`: Fuel surcharge amount column names

### output_fields

Fixed values for output fields.

- `business_type`: Business type (default: "航班")
- `fee_name`: Fee name (default: "燃油附加费")
- `settlement_name`: Settlement entity name (default: "龙浩")

### date_formats

List of date formats to try when parsing dates. Uses Python's strftime format codes.

Supported formats:
- `%y-%m-%d`: YY-MM-DD (e.g., 25-10-02)
- `%Y-%m-%d`: YYYY-MM-DD (e.g., 2025-10-02)
- `%Y/%m/%d`: YYYY/MM/DD (e.g., 2025/10/02)

## Output Format

The processor generates an Excel file with these standardized columns:

| Column | Source | Example |
|--------|--------|---------|
| *空运业务单 | config.output_fields.business_type | 航班 |
| *航司 | Extracted from flight number | GI |
| 合同号 | Fetched from API | GI-25-159 |
| *始发港 | Parsed from route | CGO |
| *目的港 | Parsed from route | BUD |
| 航班日期 | Formatted flight date | 2025-10-02 |
| *费用名称 | config.output_fields.fee_name | 燃油附加费 |
| *结算对象名称 | config.output_fields.settlement_name | 龙浩 |
| *单价 | Fuel surcharge amount | -113892.67 |

Columns marked with * are required fields.
