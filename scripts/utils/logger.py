#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统
统一管理燃油账单处理器的日志输出
"""

import logging
from pathlib import Path


def setup_logger(name='FuelBillProcessor', log_file=None, level=logging.INFO):
    """配置日志系统

    Args:
        name: logger名称
        log_file: 日志文件路径（可选）
        level: 日志级别

    Returns:
        logging.Logger: 配置好的logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name='FuelBillProcessor'):
    """获取logger实例

    Args:
        name: logger名称

    Returns:
        logging.Logger: logger实例
    """
    return logging.getLogger(name)
