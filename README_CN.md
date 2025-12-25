# 智能燃油账单处理器 Skill

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)

一个智能的航空燃油差价费账单处理工具，专门设计用于处理可能存在格式差异的账单文件。

[English](README.md) | 简体中文

</div>

## ✨ 功能特性

### 智能适应能力
- 🔍 **自动表头检测** - 智能识别Excel文件中的表头行位置
- 🎯 **模糊列名匹配** - 自动识别不同格式的列名（即使有微小变化）
- 📅 **灵活日期解析** - 支持多种日期格式自动转换
- 📁 **多格式支持** - 同时支持 .xls 和 .xlsx 文件
- 🔌 **API集成** - 自动调用航班API获取合同号
- ⚙️  **高度可配置** - 通过配置文件轻松自定义处理规则

### 数据质量保证
- ✅ 自动验证必填字段
- ✅ 智能过滤无效数据（空行、汇总行等）
- ✅ 生成符合标准模板的输出

## 🚀 快速开始

### 安装依赖

```bash
pip install pandas openpyxl xlrd requests
```

### 基本使用

```bash
# 最简单的用法
python3 process.py 输入文件.xls

# 指定输出文件
python3 process.py 输入文件.xls -o 输出文件.xlsx

# 使用自定义配置
python3 process.py 输入文件.xls -c my_config.json
```

### 实际示例

```bash
python3 process.py "账单2025年10月.xls" -o "10月处理结果.xlsx"
```

## 📊 输出格式

生成的Excel文件包含9列标准格式：

| 列名 | 数据来源 | 示例 |
|------|----------|------|
| *空运业务单 | 固定值 | 航班 |
| *航司 | 从航班号提取 | GI |
| 合同号 | API获取 | GI-25-159 |
| *始发港 | 从航段解析 | CGO |
| *目的港 | 从航段解析 | BUD |
| 航班日期 | 格式化日期 | 2025-10-02 |
| *费用名称 | 固定值 | 燃油附加费 |
| *结算对象名称 | 固定值 | 龙浩 |
| *单价 | 燃油差价费金额 | -113892.67 |

## ⚙️ 配置说明

配置文件 `config.json` 包含以下部分：

### API配置
```json
{
  "api": {
    "url": "http://api.flymeta.online:64231/transportschedule/edge/flight/get",
    "timeout": 10
  }
}
```

### 城市代码映射
```json
{
  "city_codes": {
    "郑州": "CGO",
    "布达佩斯": "BUD"
  }
}
```

添加新城市时，只需在此处添加映射即可。

### 列名映射
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

每个字段支持多个可能的列名，处理器会自动匹配。

### 输出字段固定值
```json
{
  "output_fields": {
    "business_type": "航班",
    "fee_name": "燃油附加费",
    "settlement_name": "龙浩"
  }
}
```

## 🎯 智能特性详解

### 1. 列名模糊匹配

即使列名有以下变化也能正确识别：
- 多余的空格或换行符
- 不同的括号样式
- 轻微的文字差异

例如：
- `航班日期` ✅
- `航 班 日 期` ✅ (包含空格)
- `飞行日期` ✅ (配置的别名)

### 2. 自动表头检测

自动查找包含关键字的行作为表头，无需手动指定跳过行数。

### 3. 智能数据过滤

自动过滤：
- 空行
- 汇总行（包含"合计"、"注："等）
- 必需字段为空的行

### 4. 多种日期格式支持

自动识别并转换：
- `25-10-02` → `2025-10-02`
- `2025-10-02` → `2025-10-02`
- `2025/10/02` → `2025-10-02`

## 📝 处理流程

```
输入Excel文件
    ↓
1. 智能检测文件格式 (.xls / .xlsx)
    ↓
2. 自动查找表头位置
    ↓
3. 模糊匹配识别所需列
    ↓
4. 过滤无效数据行
    ↓
5. 提取航司、始发港、目的港等
    ↓
6. 调用API获取每条记录的合同号
    ↓
7. 生成标准格式输出
    ↓
输出Excel文件
```

## 🔧 扩展性

### 添加新的城市

编辑 `config.json`：
```json
{
  "city_codes": {
    "郑州": "CGO",
    "布达佩斯": "BUD",
    "北京": "PEK"  // 新增
  }
}
```

### 添加新的列名变体

编辑 `config.json`：
```json
{
  "column_mappings": {
    "flight_date": ["航班日期", "日期", "飞行日期", "起飞日期"]  // 添加新变体
  }
}
```

### 修改固定值

编辑 `config.json`：
```json
{
  "output_fields": {
    "settlement_name": "新的结算对象名称"  // 修改
  }
}
```

## 💻 在代码中使用

```python
from process import FuelBillProcessor

# 创建处理器
processor = FuelBillProcessor()

# 处理文件
result = processor.process('input.xls', 'output.xlsx')

# 使用自定义配置
processor = FuelBillProcessor(config_path='my_config.json')
result = processor.process('input.xls', 'output.xlsx')
```

## 🐛 故障排查

### 列识别失败

如果提示"未能识别所有必需的列"，检查：
1. 配置文件中的 `column_mappings` 是否包含实际列名的变体
2. Excel文件的表头是否正确

### API调用失败

检查：
1. 网络连接
2. API地址是否正确
3. 参数格式是否正确

### 日期解析失败

添加新的日期格式到 `config.json` 的 `date_formats` 中。

## 📦 文件结构

```
fuel-bill-processor/
├── process.py              # 主处理脚本
├── config.json             # 用户配置文件
├── config.template.json    # 配置模板
├── skill.json              # Skill元数据
├── README.md              # 英文文档
├── README_CN.md           # 中文文档
├── LICENSE                # 许可证
└── .gitignore            # Git忽略文件
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [提交问题](https://github.com/changdaoyina/fuel-bill-processor/issues)
- GitHub: [@changdaoyina](https://github.com/changdaoyina)

## 🙏 致谢

感谢所有贡献者和使用者的支持！

---

**注意**: 本工具设计用于处理航空燃油差价费账单。使用前请确保已正确配置API地址和城市代码映射。
