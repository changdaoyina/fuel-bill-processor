#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证器
验证处理后的燃油账单数据是否符合要求
"""

import pandas as pd
import re


class OutputValidator:
    """输出数据验证器"""

    # 必填字段列表
    REQUIRED_FIELDS = [
        '*空运业务单',
        '*航司',
        '*始发港',
        '*目的港',
        '*费用名称',
        '*结算对象名称',
        '*单价'
    ]

    # 可选字段列表
    OPTIONAL_FIELDS = [
        '合同号',
        '航班日期'
    ]

    def __init__(self, strict_mode=False):
        """初始化验证器

        Args:
            strict_mode: 严格模式（可选字段也必须验证通过）
        """
        self.strict_mode = strict_mode
        self.validation_errors = []

    def validate_output_row(self, row):
        """验证单行输出数据

        Args:
            row: 数据行（dict或pandas Series）

        Returns:
            tuple: (是否通过, 问题列表)
        """
        issues = []

        # 必填字段检查
        for field in self.REQUIRED_FIELDS:
            if field not in row:
                issues.append(f"缺失必填字段: {field}")
            elif pd.isna(row[field]) or str(row[field]).strip() == '':
                issues.append(f"必填字段为空: {field}")

        # 航班日期格式检查
        if '航班日期' in row and pd.notna(row['航班日期']):
            date_str = str(row['航班日期'])
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                issues.append(f"日期格式错误（应为YYYY-MM-DD）: {date_str}")

        # 金额格式检查
        if '*单价' in row and pd.notna(row['*单价']):
            try:
                price = float(row['*单价'])
                # 检查是否保留两位小数
                if abs(price - round(price, 2)) > 0.001:
                    issues.append(f"价格精度错误（应保留两位小数）: {price}")
            except (ValueError, TypeError):
                issues.append(f"价格格式错误: {row['*单价']}")

        # 航司代码格式检查（应为大写字母）
        if '*航司' in row and pd.notna(row['*航司']):
            airline = str(row['*航司'])
            if not re.match(r'^[A-Z]{2,3}$', airline):
                issues.append(f"航司代码格式错误（应为2-3个大写字母）: {airline}")

        # 机场代码格式检查（应为3个大写字母）
        for field in ['*始发港', '*目的港']:
            if field in row and pd.notna(row[field]):
                code = str(row[field])
                if not re.match(r'^[A-Z]{3}$', code):
                    issues.append(f"{field}代码格式错误（应为3个大写字母）: {code}")

        return len(issues) == 0, issues

    def validate_dataframe(self, df):
        """验证整个DataFrame

        Args:
            df: pandas DataFrame

        Returns:
            tuple: (是否通过, 详细报告dict)
        """
        self.validation_errors = []
        total_rows = len(df)
        passed_rows = 0
        failed_rows = []

        for idx, row in df.iterrows():
            is_valid, issues = self.validate_output_row(row)
            if is_valid:
                passed_rows += 1
            else:
                failed_rows.append({
                    'row_index': idx,
                    'row_number': idx + 1,  # 从1开始计数
                    'issues': issues
                })
                self.validation_errors.extend(issues)

        report = {
            'total_rows': total_rows,
            'passed_rows': passed_rows,
            'failed_rows': len(failed_rows),
            'pass_rate': passed_rows / total_rows if total_rows > 0 else 0,
            'failed_details': failed_rows[:10],  # 只返回前10条错误详情
            'total_issues': len(self.validation_errors)
        }

        return passed_rows == total_rows, report

    def print_report(self, report):
        """打印验证报告

        Args:
            report: validate_dataframe()返回的报告dict
        """
        print("\n" + "="*60)
        print("数据验证报告")
        print("="*60)
        print(f"总行数: {report['total_rows']}")
        print(f"通过验证: {report['passed_rows']}")
        print(f"验证失败: {report['failed_rows']}")
        print(f"通过率: {report['pass_rate']:.1%}")
        print(f"总问题数: {report['total_issues']}")

        if report['failed_details']:
            print("\n前10条错误详情:")
            for detail in report['failed_details']:
                print(f"\n  行 {detail['row_number']}:")
                for issue in detail['issues']:
                    print(f"    - {issue}")

        print("="*60)
