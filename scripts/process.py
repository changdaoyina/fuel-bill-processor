#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能燃油账单处理器
支持自动检测和Claude辅助两种模式
"""

import json
import sys
from pathlib import Path

__version__ = "2.0.0"


def load_config(config_path=None):
    """加载配置文件

    Args:
        config_path: 配置文件路径（可选）

    Returns:
        dict: 配置字典
    """
    if config_path is None:
        # 查找配置文件
        script_dir = Path(__file__).parent
        skill_root = script_dir.parent

        # 优先使用 assets 目录的配置
        config_path = skill_root / "assets" / "config.json"

        # 兼容旧位置：skill 根目录
        if not config_path.exists():
            config_path = skill_root / "config.json"

        # 兼容旧位置：脚本目录
        if not config_path.exists():
            config_path = script_dir / "config.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description=f'智能燃油账单处理器 v{__version__}',
        epilog='''
使用模式：
  1. 自动检测模式（默认）：
     python scripts/process.py input.xls

  2. Claude辅助模式（指定运行时配置）：
     python scripts/process.py input.xls --runtime-config runtime.json

  3. 命令行参数模式：
     python scripts/process.py input.xls --header-row 2 --date-column B --route-column C
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # 基本参数
    parser.add_argument('input', help='输入Excel文件路径')
    parser.add_argument('-o', '--output', help='输出Excel文件路径（可选）')
    parser.add_argument('-c', '--config', help='配置文件路径（可选）')

    # 运行时配置
    parser.add_argument(
        '--runtime-config',
        help='运行时配置文件路径（JSON格式），包含表头行和列映射信息'
    )

    # 单独的运行时参数
    parser.add_argument(
        '--header-row',
        type=int,
        help='表头行号（从0开始，如第3行则传入2）'
    )
    parser.add_argument(
        '--date-column',
        help='航班日期列（列字母如"B"或列名）'
    )
    parser.add_argument(
        '--route-column',
        help='航段列（列字母如"C"或列名）'
    )
    parser.add_argument(
        '--flight-column',
        help='航班号列（列字母如"D"或列名）'
    )
    parser.add_argument(
        '--price-column',
        help='燃油差价费列（列字母如"E"或列名）'
    )

    args = parser.parse_args()

    try:
        # 加载基础配置
        config = load_config(args.config)

        # 构建运行时配置
        runtime_config = None

        # 优先使用 runtime-config 文件
        if args.runtime_config:
            with open(args.runtime_config, 'r', encoding='utf-8') as f:
                runtime_config = json.load(f)
            print(f"✓ 加载运行时配置: {args.runtime_config}")

        # 否则从命令行参数构建
        elif any([args.header_row is not None, args.date_column, args.route_column,
                  args.flight_column, args.price_column]):
            runtime_config = {}

            if args.header_row is not None:
                runtime_config['header_row'] = args.header_row

            if any([args.date_column, args.route_column, args.flight_column, args.price_column]):
                runtime_config['columns'] = {}
                if args.date_column:
                    runtime_config['columns']['flight_date'] = args.date_column
                if args.route_column:
                    runtime_config['columns']['route'] = args.route_column
                if args.flight_column:
                    runtime_config['columns']['flight_no'] = args.flight_column
                if args.price_column:
                    runtime_config['columns']['fuel_price'] = args.price_column

            print(f"✓ 使用命令行参数配置")

        # 选择处理器
        if runtime_config:
            # 使用灵活处理器（Claude辅助模式）
            from flexible_processor import FlexibleBillProcessor
            processor = FlexibleBillProcessor(config, runtime_config)
        else:
            # 使用传统处理器（自动检测模式）
            from legacy_processor import LegacyBillProcessor
            processor = LegacyBillProcessor(config)

        # 处理文件
        processor.process(args.input, args.output)

    except Exception as e:
        print(f"\n处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
