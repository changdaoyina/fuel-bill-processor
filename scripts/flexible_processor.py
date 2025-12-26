#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
灵活的燃油账单处理器
支持参数化配置，可接受外部（如Claude）提供的结构信息
"""

import pandas as pd
import requests
import json
import re
from datetime import datetime
from pathlib import Path


class FlexibleBillProcessor:
    """支持参数化配置的燃油账单处理器

    设计用于Claude辅助模式：
    - Claude 分析 Excel 文件结构
    - 提供精确的表头位置和列映射
    - 此处理器根据提供的参数执行处理
    - 如果未提供参数，则 fallback 到自动检测
    """

    def __init__(self, config, runtime_config=None):
        """初始化处理器

        Args:
            config: 基础配置字典
            runtime_config: 运行时配置（可选），用于覆盖自动检测
                {
                    'header_row': int,  # 表头行号（从0开始）
                    'columns': {
                        'flight_date': 'B',  # 列字母或列名
                        'route': 'C',
                        'flight_no': 'D',
                        'fuel_price': 'E'
                    }
                }
        """
        self.config = config
        self.runtime_config = runtime_config or {}
        self.column_map = {}

    def detect_file_format(self, file_path):
        """检测文件格式"""
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.xls':
            return 'xlrd'
        elif file_ext == '.xlsx':
            return 'openpyxl'
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    def read_excel_with_config(self, file_path):
        """根据配置读取Excel文件

        优先使用 runtime_config 中的信息，如果没有则自动检测
        """
        print(f"\n正在读取文件: {file_path}")

        engine = self.detect_file_format(file_path)
        print(f"检测到文件格式: {engine}")

        # 使用运行时配置的表头行，或自动检测
        if 'header_row' in self.runtime_config:
            header_row = self.runtime_config['header_row']
            print(f"使用指定的表头行: 第{header_row + 1}行")
        else:
            header_row = self._auto_detect_header_row(file_path, engine)
            print(f"自动检测到表头行: 第{header_row + 1}行")

        # 读取数据
        df = pd.read_excel(file_path, engine=engine, header=header_row)

        # 识别列映射
        if 'columns' in self.runtime_config:
            self.column_map = self._map_columns_from_config(df, self.runtime_config['columns'])
            print(f"使用指定的列映射: {self.column_map}")
        else:
            self.column_map = self._auto_identify_columns(df)
            print(f"自动识别的列映射: {self.column_map}")

        if len(self.column_map) < 4:
            print("警告: 未能识别所有必需的列")
            print("可用列名:", list(df.columns))

        return df

    def _auto_detect_header_row(self, file_path, engine):
        """自动检测表头行（fallback逻辑）"""
        df_raw = pd.read_excel(file_path, engine=engine, header=None, nrows=15)

        best_match = 0
        best_score = 0

        for idx in range(len(df_raw)):
            row = df_raw.iloc[idx]
            row_str = ' '.join([str(x) for x in row if pd.notna(x)])

            score = 0
            keywords = ['航班日期', '航段', '航班号', '燃油差价费', '燃油消耗']

            for keyword in keywords:
                if keyword in row_str:
                    score += 1

            if score >= 3 and score > best_score:
                best_score = score
                best_match = idx

        return best_match

    def _map_columns_from_config(self, df, column_config):
        """根据配置映射列

        Args:
            df: DataFrame
            column_config: 列配置 {'flight_date': 'B', 'route': 'C', ...}

        Returns:
            dict: 字段到实际列名的映射
        """
        mapping = {}

        for field, col_indicator in column_config.items():
            # 如果是列字母（如 'B'），转换为列索引
            if isinstance(col_indicator, str) and len(col_indicator) <= 3 and col_indicator.isalpha():
                col_index = self._column_letter_to_index(col_indicator)
                if col_index < len(df.columns):
                    mapping[field] = df.columns[col_index]
                else:
                    print(f"警告: 列 {col_indicator} 超出范围")
            else:
                # 直接使用列名
                if col_indicator in df.columns:
                    mapping[field] = col_indicator
                else:
                    print(f"警告: 列 '{col_indicator}' 不存在")

        return mapping

    def _column_letter_to_index(self, letter):
        """将列字母转换为索引（A=0, B=1, ...）"""
        result = 0
        for char in letter.upper():
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result - 1

    def _auto_identify_columns(self, df):
        """自动识别列（fallback逻辑）"""
        mappings = self.config['column_mappings']
        identified = {}

        # 定义要识别的字段及优先级
        fields_to_identify = ['flight_date', 'route', 'flight_no', 'fuel_price', 'origin', 'destination']

        for field in fields_to_identify:
            # 如果字段不在配置中，跳过
            if field not in mappings and field not in ['origin', 'destination']:
                continue
            if field in ['origin', 'destination'] and field not in mappings:
                continue

            candidates = mappings.get(field, [])

            # 优先匹配更精确的列名（包含完整关键词）
            for col in df.columns:
                col_str = str(col)
                if self._fuzzy_match_column(col_str, candidates):
                    # 如果已经为其他字段识别过此列，跳过
                    if col not in identified.values():
                        identified[field] = col
                        break

        return identified

    def _fuzzy_match_column(self, column_name, candidates):
        """模糊匹配列名"""
        column_name = str(column_name).strip()
        column_name = re.sub(r'\s+', '', column_name)

        for candidate in candidates:
            candidate_clean = re.sub(r'\s+', '', candidate)
            if candidate_clean in column_name or column_name in candidate_clean:
                return True
        return False

    def extract_airline(self, flight_no):
        """提取航司代码"""
        if pd.isna(flight_no):
            return None
        flight_no = str(flight_no).strip()
        airline = ''.join([c for c in flight_no if c.isalpha()])
        return airline.upper() if airline else None

    def parse_route(self, route, origin=None, destination=None):
        """解析航段

        支持两种格式：
        1. 合并格式：route="郑州-布达佩斯"
        2. 分离格式：origin="郑州", destination="布达佩斯"

        Args:
            route: 航段字符串（如"郑州-布达佩斯"）
            origin: 始发站（如"郑州"或"CGO"）
            destination: 目的站（如"布达佩斯"或"BUD"）

        Returns:
            tuple: (始发港代码, 目的港代码) 或 (None, None)
        """
        # 优先使用分离格式
        if origin is not None and destination is not None:
            origin_val = str(origin).strip() if pd.notna(origin) else None
            dest_val = str(destination).strip() if pd.notna(destination) else None

            if origin_val and dest_val:
                # 如果已经是代码（3-4个字母），直接使用
                # 否则从城市名映射
                city_codes = self.config.get('city_codes', {})
                origin_code = origin_val if origin_val.isupper() and len(origin_val) >= 3 else city_codes.get(origin_val, origin_val)
                dest_code = dest_val if dest_val.isupper() and len(dest_val) >= 3 else city_codes.get(dest_val, dest_val)

                return origin_code, dest_code

        # 回退到合并格式
        if pd.isna(route):
            return None, None

        route = str(route).strip()

        for sep in ['-', '=', '→', '->']:
            if sep in route:
                parts = route.split(sep)
                if len(parts) == 2:
                    origin_city = parts[0].strip()
                    dest_city = parts[1].strip()

                    city_codes = self.config['city_codes']
                    origin_code = city_codes.get(origin_city)
                    dest_code = city_codes.get(dest_city)

                    return origin_code, dest_code

        return None, None

    def should_filter_route(self, airline, origin, destination):
        """检查是否应该过滤掉此航段

        Args:
            airline: 航司代码
            origin: 始发港代码
            destination: 目的港代码

        Returns:
            bool: True表示应该过滤掉（不保留），False表示保留
        """
        # 优先使用主要机场配置（方案1）
        major_airports = self.config.get('major_airports_by_airline', {}).get(airline)
        if major_airports:
            # 只保留两端都是主要机场的航段，中转站自动过滤
            is_major_route = origin in major_airports and destination in major_airports
            return not is_major_route  # True = 过滤掉，False = 保留

        # 回退到原有的 route_filters 逻辑（向后兼容）
        route_filters = self.config.get('route_filters', {})
        if airline not in route_filters:
            return False  # 没有过滤规则，保留所有航段

        allowed_routes = route_filters[airline]
        route_str = f"{origin}-{destination}"

        # 如果在允许列表中，则保留
        return route_str not in allowed_routes

    def get_settlement_name(self, airline):
        """根据航司代码获取结算对象名称

        Args:
            airline: 航司代码

        Returns:
            str: 结算对象名称
        """
        settlement_map = self.config.get('settlement_names_by_airline', {})
        return settlement_map.get(airline, settlement_map.get('默认', self.config['output_fields']['settlement_name']))

    def convert_date(self, date_val):
        """转换日期格式"""
        if pd.isna(date_val):
            return None

        if isinstance(date_val, pd.Timestamp) or isinstance(date_val, datetime):
            return date_val.strftime('%Y-%m-%d')

        date_str = str(date_val).strip()

        for fmt in self.config['date_formats']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue

        try:
            parts = re.split(r'[-/]', date_str)
            if len(parts) == 3:
                year, month, day = parts
                if len(year) == 2:
                    year = '20' + year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass

        return date_str

    def get_contract_no(self, origin, destination, std_str, air_code):
        """调用API获取合同号"""
        url = self.config['api']['url']
        timeout = self.config['api']['timeout']

        payload = {
            "origin": origin,
            "destination": destination,
            "stdStr": std_str,
            "airCode": air_code
        }

        try:
            response = requests.post(url, json=payload, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 20000 and data.get('data'):
                    contract_no = data['data'].get('contractNo')
                    return contract_no

            return None
        except Exception as e:
            print(f"  API调用失败: {e}")
            return None

    def filter_data(self, df):
        """过滤无效数据"""
        if 'flight_date' not in self.column_map:
            return df

        date_col = self.column_map['flight_date']
        df = df[df[date_col].notna()].copy()
        df = df[~df[date_col].astype(str).str.contains('合计|注：|注释|说明', na=False)]

        for key in ['route', 'flight_no', 'fuel_price', 'origin', 'destination']:
            if key in self.column_map:
                col = self.column_map[key]
                df = df[df[col].notna()]

        return df

    def process(self, input_file, output_file=None):
        """处理账单文件

        Args:
            input_file: 输入Excel文件路径
            output_file: 输出Excel文件路径（可选）

        Returns:
            pd.DataFrame: 处理后的数据
        """
        mode = "Claude辅助模式" if self.runtime_config else "自动检测模式"
        print("="*60)
        print(f"智能燃油账单处理器 ({mode})")
        print("="*60)

        # 读取文件
        df_input = self.read_excel_with_config(input_file)

        # 过滤数据
        df_input = self.filter_data(df_input)
        print(f"\n有效数据行数: {len(df_input)}")

        if len(df_input) == 0:
            print("错误: 没有找到有效数据")
            return None

        # 处理每一行
        output_data = []
        total_rows = len(df_input)

        for idx, row in df_input.iterrows():
            print(f"\n处理 {len(output_data)+1}/{total_rows} ...", end='')

            # 提取数据
            flight_date = self.convert_date(row[self.column_map['flight_date']])
            airline = self.extract_airline(row[self.column_map['flight_no']])

            # 解析航段 - 支持分离格式和合并格式
            origin_val = row.get(self.column_map.get('origin')) if 'origin' in self.column_map else None
            dest_val = row.get(self.column_map.get('destination')) if 'destination' in self.column_map else None
            route_val = row.get(self.column_map.get('route')) if 'route' in self.column_map else None

            origin, destination = self.parse_route(route_val, origin_val, dest_val)
            fuel_price = round(row[self.column_map['fuel_price']], 2)

            # 航段过滤
            if airline and origin and destination:
                if self.should_filter_route(airline, origin, destination):
                    print(f" ⊘ 航段过滤: {origin}-{destination}")
                    continue

            # 获取合同号
            contract_no = None
            if airline and origin and destination and flight_date:
                contract_no = self.get_contract_no(origin, destination, flight_date, airline)
                if contract_no:
                    print(f" ✓ {contract_no}")
                else:
                    print(" ✗ API返回空")

            # 获取动态结算对象名称（根据航司代码）
            settlement_name = self.get_settlement_name(airline) if airline else self.config['output_fields']['settlement_name']

            # 构建输出行
            output_fields = self.config['output_fields']
            output_row = {
                '*空运业务单': output_fields['business_type'],
                '*航司': airline,
                '合同号': contract_no,
                '*始发港': origin,
                '*目的港': destination,
                '航班日期': flight_date,
                '*费用名称': output_fields['fee_name'],
                '*结算对象名称': settlement_name,
                '*单价': fuel_price
            }

            output_data.append(output_row)

        # 创建输出DataFrame
        df_output = pd.DataFrame(output_data)

        # 保存文件
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_处理结果.xlsx"

        print(f"\n\n保存结果到: {output_file}")
        df_output.to_excel(output_file, index=False, engine='openpyxl')

        # 统计信息
        print("\n" + "="*60)
        print("处理完成!")
        print("="*60)
        print(f"总行数: {len(df_output)}")
        print(f"合同号获取成功: {df_output['合同号'].notna().sum()}/{len(df_output)}")
        print(f"输出文件: {output_file}")

        return df_output
