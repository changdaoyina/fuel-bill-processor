#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
燃油账单Excel结构分析工具
用于分析Excel文件结构并生成处理命令
"""

import pandas as pd
import sys
from pathlib import Path


def detect_file_format(file_path):
    """检测文件格式"""
    file_ext = Path(file_path).suffix.lower()
    if file_ext == '.xls':
        return 'xlrd'
    elif file_ext == '.xlsx':
        return 'openpyxl'
    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")


def column_index_to_letter(index):
    """将列索引转换为字母（0=A, 1=B, ...）"""
    result = ""
    index += 1
    while index > 0:
        index -= 1
        result = chr(index % 26 + ord('A')) + result
        index //= 26
    return result


def analyze_excel(file_path, max_rows=20):
    """分析Excel文件结构

    Args:
        file_path: Excel文件路径
        max_rows: 显示的最大行数
    """
    print("=" * 80)
    print(f"分析文件: {file_path}")
    print("=" * 80)

    # 检测文件格式
    engine = detect_file_format(file_path)
    print(f"文件格式: {engine}\n")

    # 读取原始数据（不设置header）
    df_raw = pd.read_excel(file_path, engine=engine, header=None, nrows=max_rows)

    print(f"前 {len(df_raw)} 行内容:")
    print("-" * 80)

    for idx, row in df_raw.iterrows():
        # 显示行号和列字母
        line = f"第{idx + 1:2d}行: "

        # 计算该行的列数
        non_null_count = row.notna().sum()
        if non_null_count == 0:
            line += "(空行)"
        else:
            # 显示每列的内容（带列字母）
            for col_idx in range(min(len(row), 15)):  # 最多显示15列
                col_letter = column_index_to_letter(col_idx)
                val = row.iloc[col_idx]
                if pd.notna(val):
                    val_str = str(val)[:20]  # 限制每个单元格显示20个字符
                    line += f"[{col_letter}:{val_str}] "
            if len(row) > 15:
                line += "..."

        print(line)

    print("-" * 80)
    print()

    # 智能分析
    print("智能分析:")
    print("-" * 80)

    # 检测表头行
    header_keywords = ['航班日期', '航段', '航班号', '燃油差价费', '燃油消耗', '日期', '航线']
    best_header_row = 0
    best_score = 0

    for idx in range(len(df_raw)):
        row = df_raw.iloc[idx]
        row_str = ' '.join([str(x) for x in row if pd.notna(x)])

        score = sum(1 for kw in header_keywords if kw in row_str)
        if score > best_score:
            best_score = score
            best_header_row = idx

    if best_score >= 2:
        print(f"✓ 检测到表头行: 第{best_header_row + 1}行 (包含{best_score}个关键词)")
    else:
        print(f"? 未明确检测到表头行，建议: 第{best_header_row + 1}行")

    # 读取带表头的数据来分析列
    df_with_header = pd.read_excel(file_path, engine=engine, header=best_header_row, nrows=1)

    print(f"\n表头行 (第{best_header_row + 1}行) 的列名:")
    for col_idx, col_name in enumerate(df_with_header.columns):
        col_letter = column_index_to_letter(col_idx)
        print(f"  [{col_letter}] {col_name}")

    print()

    # 列映射建议
    column_mapping = {
        'flight_date': ['航班日期', '日期', '飞行日期', '起飞日期'],
        'route': ['航段', '航线', '路线', '起止'],
        'flight_no': ['航班号', '航班', '班次号', '班次'],
        'fuel_price': ['燃油差价费', '燃油差价费（元）', '差价费', '燃油费', '燃油附加费']
    }

    detected = {}
    for field, keywords in column_mapping.items():
        for col_idx, col_name in enumerate(df_with_header.columns):
            col_str = str(col_name).strip()
            for kw in keywords:
                if kw in col_str:
                    col_letter = column_index_to_letter(col_idx)
                    detected[field] = col_letter
                    break
            if field in detected:
                break

    print("列映射建议:")
    field_names = {
        'flight_date': '航班日期',
        'route': '航段',
        'flight_no': '航班号',
        'fuel_price': '燃油差价费'
    }
    for field, col_letter in detected.items():
        print(f"  {field_names[field]}: 列 {col_letter}")

    print()
    print("=" * 80)
    print("建议的处理命令:")
    print("=" * 80)

    # 生成命令
    cmd_parts = [
        f"python3 scripts/process.py {file_path}",
        f"--header-row {best_header_row}"
    ]

    if 'flight_date' in detected:
        cmd_parts.append(f"--date-column {detected['flight_date']}")
    if 'route' in detected:
        cmd_parts.append(f"--route-column {detected['route']}")
    if 'flight_no' in detected:
        cmd_parts.append(f"--flight-column {detected['flight_no']}")
    if 'fuel_price' in detected:
        cmd_parts.append(f"--price-column {detected['fuel_price']}")

    print(" \\\n    ".join(cmd_parts))
    print()

    # 如果检测不完整，提示手动指定
    if len(detected) < 4:
        print("注意: 未检测到所有必需列，请根据上面的表格内容手动指定缺失的列")
        print()


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/analyze.py <excel_file>")
        print()
        print("示例:")
        print("  python3 scripts/analyze.py 燃油账单.xls")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"错误: 文件不存在: {file_path}")
        sys.exit(1)

    try:
        analyze_excel(file_path)
    except Exception as e:
        print(f"分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
