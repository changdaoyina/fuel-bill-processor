# Fuel Bill Processor - Claude Code Skill

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)

An intelligent aviation fuel surcharge bill processing **Claude Code Skill**, specifically designed to handle bill files with potential format variations.

English | [简体中文](README_CN.md)

</div>

## What is a Claude Code Skill?

This project is a [Claude Code Skill](https://code.claude.com/docs/en/skills) - a modular capability that extends Claude's functionality. Skills are **model-invoked**, meaning Claude automatically uses them when your request matches the skill's description.

## ✨ Features

### Intelligent Adaptation
- 🔍 **Auto Header Detection** - Intelligently identifies header row position in Excel files
- 🎯 **Fuzzy Column Matching** - Automatically recognizes column names even with minor variations
- 📅 **Flexible Date Parsing** - Supports multiple date formats with auto-conversion
- 📁 **Multi-Format Support** - Works with both .xls and .xlsx files
- 🔌 **API Integration** - Automatically fetches contract numbers via flight API
- ⚙️  **Highly Configurable** - Easy customization through configuration files

### Data Quality Assurance
- ✅ Automatic validation of required fields
- ✅ Smart filtering of invalid data (empty rows, summary rows, etc.)
- ✅ Generates output conforming to standard template

## 🚀 Installation

### As a Claude Code Skill

1. **Clone this repository** to your project:
   ```bash
   git clone https://github.com/your-username/fuel-bill-processor.git
   cd fuel-bill-processor
   ```

2. **Install dependencies**:
   ```bash
   pip install pandas openpyxl xlrd requests
   ```

3. **Create configuration file**:
   ```bash
   cd .claude/skills/fuel-bill-processor
   cp config.template.json config.json
   # Edit config.json with your API settings
   ```

4. **The skill is now available** - Claude will automatically discover and use it when processing fuel bills!

### Standalone Usage

You can also use the processor directly from command line:

```bash
# From the skill directory
cd .claude/skills/fuel-bill-processor
python3 scripts/process.py input_file.xls

# Specify output file
python3 scripts/process.py input_file.xls -o output_file.xlsx

# Use custom configuration
python3 scripts/process.py input_file.xls -c my_config.json
```

## 📊 Output Format

Generated Excel file contains 9 standardized columns:

| Column Name | Data Source | Example |
|-------------|-------------|---------|
| *空运业务单 | Fixed value | 航班 |
| *航司 | Extracted from flight number | GI |
| 合同号 | Fetched from API | GI-25-159 |
| *始发港 | Parsed from route | CGO |
| *目的港 | Parsed from route | BUD |
| 航班日期 | Formatted date | 2025-10-02 |
| *费用名称 | Fixed value | 燃油附加费 |
| *结算对象名称 | Fixed value | 龙浩 |
| *单价 | Fuel surcharge amount | -113892.67 |

## ⚙️ Configuration

The `config.json` file (create from `config.template.json`) contains:

### API Configuration
```json
{
  "api": {
    "url": "http://api.flymeta.online:64231/transportschedule/edge/flight/get",
    "timeout": 10
  }
}
```

### City Code Mapping
```json
{
  "city_codes": {
    "郑州": "CGO",
    "布达佩斯": "BUD"
  }
}
```

Simply add new mappings here to support new cities.

### Column Mappings
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

Each field supports multiple possible column names for automatic matching.

## 🎯 Usage with Claude Code

When working with fuel bill files, simply ask Claude:

- "Can you process this fuel bill Excel file?"
- "处理这个燃油账单"
- "Extract data from this aviation fuel surcharge file"

Claude will automatically invoke this skill and process your file!

## 🎯 Smart Features

### 1. Fuzzy Column Matching

Correctly identifies columns even with:
- Extra spaces or newlines
- Different bracket styles
- Minor text variations

Examples:
- `航班日期` ✅
- `航 班 日 期` ✅ (with spaces)
- `飞行日期` ✅ (configured alias)

### 2. Auto Header Detection

Automatically finds header rows containing keywords, no need to manually specify skip rows.

### 3. Smart Data Filtering

Automatically filters:
- Empty rows
- Summary rows (containing "合计", "注：", etc.)
- Rows with empty required fields

### 4. Multiple Date Format Support

Auto-recognizes and converts:
- `25-10-02` → `2025-10-02`
- `2025-10-02` → `2025-10-02`
- `2025/10/02` → `2025-10-02`

## 💻 Use in Code

```python
import sys
sys.path.insert(0, '.claude/skills/fuel-bill-processor/scripts')
from process import FuelBillProcessor

# Create processor
processor = FuelBillProcessor()

# Process file
result = processor.process('input.xls', 'output.xlsx')

# Use custom config
processor = FuelBillProcessor(config_path='my_config.json')
result = processor.process('input.xls', 'output.xlsx')
```

## 🐛 Troubleshooting

### Column Recognition Failed

If you see "Failed to recognize all required columns", check:
1. Whether `column_mappings` in config contains actual column name variants
2. Whether Excel file header is correct

### API Call Failed

Check:
1. Network connection
2. API URL is correct
3. Parameter format is correct

## 📦 File Structure

```
fuel-bill-processor/
├── .claude/
│   └── skills/
│       └── fuel-bill-processor/
│           ├── SKILL.md              # Skill definition (required)
│           ├── REFERENCE.md          # API reference
│           ├── config.template.json  # Configuration template
│           └── scripts/
│               └── process.py        # Main processing script
├── skill.json                        # Project metadata
├── README.md                         # English documentation
├── README_CN.md                      # Chinese documentation
├── LICENSE                           # MIT License
└── .gitignore                        # Git ignore file
```

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📮 Contact

For questions or suggestions, contact via:

- GitHub Issues: [Submit Issue](https://github.com/changdaoyina/fuel-bill-processor/issues)
- GitHub: [@changdaoyina](https://github.com/changdaoyina)

## 🙏 Acknowledgments

Thanks to all contributors and users for their support!

---

**Note**: This skill is designed for processing aviation fuel surcharge bills. Please ensure API address and city code mappings are correctly configured before use.
