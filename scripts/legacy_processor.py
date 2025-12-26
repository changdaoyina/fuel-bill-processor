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

        for col in df.columns:
            col_str = str(col)

            # 识别航班日期
            if self.fuzzy_match_column(col_str, mappings['flight_date']):
                identified['flight_date'] = col

            # 识别航段
            elif self.fuzzy_match_column(col_str, mappings['route']):
                identified['route'] = col

            # 识别航班号
            elif self.fuzzy_match_column(col_str, mappings['flight_no']):
                identified['flight_no'] = col

            # 识别燃油差价费
            elif self.fuzzy_match_column(col_str, mappings['fuel_price']):
                identified['fuel_price'] = col

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

    def parse_route(self, route):
        """解析航段

        Args:
            route: 航段字符串（如"郑州-布达佩斯"）

        Returns:
            tuple: (始发港代码, 目的港代码) 或 (None, None)
        """
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
        for key in ['route', 'flight_no', 'fuel_price']:
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

        # 处理每一行
        output_data = []
        total_rows = len(df_input)

        for idx, row in df_input.iterrows():
            print(f"\n处理 {len(output_data)+1}/{total_rows} ...", end='')

            # 提取数据
            flight_date = self.convert_date(row[self.column_map['flight_date']])
            airline = self.extract_airline(row[self.column_map['flight_no']])
            origin, destination = self.parse_route(row[self.column_map['route']])
            fuel_price = round(row[self.column_map['fuel_price']], 2)

            # 获取合同号
            contract_no = None
            if airline and origin and destination and flight_date:
                contract_no = self.get_contract_no(origin, destination, flight_date, airline)
                if contract_no:
                    print(f" ✓ {contract_no}")
                else:
                    print(" ✗ API返回空")

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
                '*结算对象名称': output_fields['settlement_name'],
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
