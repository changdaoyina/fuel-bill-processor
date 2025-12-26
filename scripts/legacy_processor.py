#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传统规则模式的燃油账单处理器
使用硬编码规则进行表格识别和数据处理
"""

import pandas as pd
import requests
import json
import re
from datetime import datetime
from pathlib import Path


class LegacyBillProcessor:
    """传统规则模式的燃油账单处理器

    使用固定规则进行处理：
    - 表头检测：前15行关键词匹配
    - 列名识别：配置文件模糊匹配
    - 日期解析：预定义格式列表
    """

    def __init__(self, config):
        """初始化处理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.column_map = {}

    def fuzzy_match_column(self, column_name, candidates):
        """模糊匹配列名

        Args:
            column_name: 待匹配的列名
            candidates: 候选列名列表

        Returns:
            bool: 是否匹配成功
        """
        column_name = str(column_name).strip()

        # 移除换行符和多余空格
        column_name = re.sub(r'\s+', '', column_name)

        for candidate in candidates:
            candidate_clean = re.sub(r'\s+', '', candidate)
            if candidate_clean in column_name or column_name in candidate_clean:
                return True
        return False

    def identify_columns(self, df):
        """智能识别Excel列

        Args:
            df: pandas DataFrame

        Returns:
            dict: 字段名到列名的映射
        """
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
                if self.fuzzy_match_column(col_str, candidates):
                    # 如果已经为其他字段识别过此列，跳过
                    if col not in identified.values():
                        identified[field] = col
                        break

        return identified

    def find_header_row(self, file_path, engine):
        """智能查找表头行

        仅扫描前15行，使用关键词匹配

        Args:
            file_path: Excel文件路径
            engine: pandas引擎名称

        Returns:
            int: 表头行索引（从0开始）
        """
        # 尝试读取前15行
        df_raw = pd.read_excel(file_path, engine=engine, header=None, nrows=15)

        best_match = 0
        best_score = 0

        for idx in range(len(df_raw)):
            row = df_raw.iloc[idx]
            row_str = ' '.join([str(x) for x in row if pd.notna(x)])

            # 计算匹配分数
            score = 0
            keywords = ['航班日期', '航段', '航班号', '燃油差价费', '燃油消耗']

            for keyword in keywords:
                if keyword in row_str:
                    score += 1

            # 如果这一行包含至少3个关键词，认为是表头
            if score >= 3 and score > best_score:
                best_score = score
                best_match = idx

        return best_match

    def detect_file_format(self, file_path):
        """检测文件格式

        Args:
            file_path: 文件路径

        Returns:
            str: pandas引擎名称（'xlrd' 或 'openpyxl'）

        Raises:
            ValueError: 不支持的文件格式
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.xls':
            return 'xlrd'
        elif file_ext == '.xlsx':
            return 'openpyxl'
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    def read_excel_smart(self, file_path):
        """智能读取Excel文件

        Args:
            file_path: Excel文件路径

        Returns:
            pd.DataFrame: 读取的数据
        """
        print(f"\n正在读取文件: {file_path}")

        # 检测文件格式
        engine = self.detect_file_format(file_path)
        print(f"检测到文件格式: {engine}")

        # 查找表头行
        header_row = self.find_header_row(file_path, engine)
        print(f"检测到表头行: 第{header_row + 1}行")

        # 读取数据
        df = pd.read_excel(file_path, engine=engine, header=header_row)

        # 识别列
        self.column_map = self.identify_columns(df)
        print(f"识别到的列映射: {self.column_map}")

        if len(self.column_map) < 4:
            print("警告: 未能识别所有必需的列")
            print("可用列名:", list(df.columns))

        return df

    def extract_airline(self, flight_no):
        """提取航司代码

        Args:
            flight_no: 航班号

        Returns:
            str or None: 航司代码（大写字母）
        """
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

        # 尝试不同的分隔符
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
        """转换日期格式

        Args:
            date_val: 日期值（多种类型）

        Returns:
            str: 格式化的日期字符串（YYYY-MM-DD）或原值
        """
        if pd.isna(date_val):
            return None

        # 如果已经是datetime对象
        if isinstance(date_val, pd.Timestamp) or isinstance(date_val, datetime):
            return date_val.strftime('%Y-%m-%d')

        date_str = str(date_val).strip()

        # 尝试不同的日期格式
        for fmt in self.config['date_formats']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue

        # 如果都失败，尝试智能解析
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
        """调用API获取合同号

        Args:
            origin: 始发港代码
            destination: 目的港代码
            std_str: 航班日期（YYYY-MM-DD）
            air_code: 航司代码

        Returns:
            str or None: 合同号
        """
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
        """过滤无效数据

        Args:
            df: 输入DataFrame

        Returns:
            pd.DataFrame: 过滤后的数据
        """
        if 'flight_date' not in self.column_map:
            return df

        # 过滤空行
        date_col = self.column_map['flight_date']
        df = df[df[date_col].notna()].copy()

        # 过滤汇总行
        df = df[~df[date_col].astype(str).str.contains('合计|注：|注释|说明', na=False)]

        # 过滤必需字段为空的行
        for key in ['route', 'flight_no', 'fuel_price', 'origin', 'destination']:
            if key in self.column_map:
                col = self.column_map[key]
                df = df[df[col].notna()]

        return df

    def _merge_consecutive_routes(self, df):
        """合并连续航段

        针对 YG 航司等特殊情况：
        - 同一航班号的连续航段（如 HGH→TSE→BUD）合并为 HGH→BUD
        - 支持跨日期合并（如 10-12 的 HGH→TSE 和 10-13 的 TSE→BUD）
        - 费用相加

        Args:
            df: 输入DataFrame

        Returns:
            pd.DataFrame: 合并后的数据
        """
        # 检查是否有分离的始发站/到达站列
        if 'origin' not in self.column_map or 'destination' not in self.column_map:
            return df

        origin_col = self.column_map['origin']
        dest_col = self.column_map['destination']
        flight_no_col = self.column_map['flight_no']
        flight_date_col = self.column_map['flight_date']
        fuel_price_col = self.column_map['fuel_price']

        merged_rows = []
        skip_indices = set()

        i = 0
        while i < len(df):
            if i in skip_indices:
                i += 1
                continue

            row1 = df.iloc[i]

            # 尝试查找下一行进行合并
            merged = False
            if i + 1 < len(df):
                row2 = df.iloc[i + 1]

                # 检查是否是同一航班号
                if row1[flight_no_col] == row2[flight_no_col]:
                    # 检查是否是连续航段（前一行的到达站 == 后一行的起飞站）
                    if row1[dest_col] == row2[origin_col]:
                        # 合并这两行，使用第一行的日期
                        new_row = row1.copy()
                        new_row['_merged_origin'] = row1[origin_col]
                        new_row['_merged_destination'] = row2[dest_col]
                        new_row['_merged_price'] = round(row1[fuel_price_col] + row2[fuel_price_col], 2)
                        merged_rows.append(new_row)
                        skip_indices.add(i)
                        skip_indices.add(i + 1)
                        merged = True

            if not merged:
                # 为未合并的行设置合并列（使用原始值）
                row = row1.copy()
                row['_merged_origin'] = row[origin_col]
                row['_merged_destination'] = row[dest_col]
                row['_merged_price'] = row[fuel_price_col]
                merged_rows.append(row)

            i += 1

        if merged_rows:
            result_df = pd.DataFrame(merged_rows).reset_index(drop=True)
            if len(result_df) < len(df):
                print(f"合并了 {len(df) - len(result_df)} 条连续航段")
            return result_df

        return df

    def process(self, input_file, output_file=None):
        """处理账单文件

        Args:
            input_file: 输入Excel文件路径
            output_file: 输出Excel文件路径（可选）

        Returns:
            pd.DataFrame: 处理后的数据
        """
        print("="*60)
        print("智能燃油账单处理器 (传统模式)")
        print("="*60)

        # 读取文件
        df_input = self.read_excel_smart(input_file)

        # 过滤数据
        df_input = self.filter_data(df_input)
        print(f"\n有效数据行数: {len(df_input)}")

        if len(df_input) == 0:
            print("错误: 没有找到有效数据")
            return None

        # 预处理：合并连续航段（针对 YG 航司等）
        df_input = self._merge_consecutive_routes(df_input)

        # 处理每一行
        output_data = []
        total_rows = len(df_input)

        for idx, row in df_input.iterrows():
            print(f"\n处理 {len(output_data)+1}/{total_rows} ...", end='')

            # 提取数据
            flight_date = self.convert_date(row[self.column_map['flight_date']])
            airline = self.extract_airline(row[self.column_map['flight_no']])

            # 解析航段 - 支持分离格式和合并格式
            origin_val = row.get('_merged_origin') if '_merged_origin' in row else row.get(self.column_map.get('origin')) if 'origin' in self.column_map else None
            dest_val = row.get('_merged_destination') if '_merged_destination' in row else row.get(self.column_map.get('destination')) if 'destination' in self.column_map else None
            route_val = row.get(self.column_map.get('route')) if 'route' in self.column_map else None

            origin, destination = self.parse_route(route_val, origin_val, dest_val)
            fuel_price = round(row.get('_merged_price', row[self.column_map['fuel_price']]), 2)

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
            # 自动生成输出文件名
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
