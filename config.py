#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整车订单归因分析配置文件
"""

# 分析配置
ANALYSIS_CONFIG = {
    'TOP_PROVINCES': 8,
    'TOP_SERIES': 8,
    'CHANNEL_MAPPING': {
        "门店": "STORE",
        "总部": "HQ",
        "其他": "OTHER"
    },
    'STAGE_COLS': [
        ("wish_create_time", "Wish"),
        ("intention_payment_time", "Intention"),
        ("deposit_payment_time", "Deposit"),
        ("lock_time", "Lock"),
        ("final_payment_time", "Final"),
        ("delivery_date", "Delivery")
    ],
    'PATH_SEPARATOR': '||',  # 防止特殊字符导致解析错误
    'UNKNOWN_CATEGORY': 'UNKNOWN',
    'MIN_PATH_LENGTH': 2,
    'MAX_PATH_LENGTH': 10
}

# 可视化配置
VISUALIZATION_CONFIG = {
    'FIGURE_SIZE': (12, 8),
    'DPI': 300,
    'FONT_SIZE': 12,
    'COLOR_PALETTE': 'viridis',
    'CHINESE_FONT': ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
}

# 数据处理配置
DATA_CONFIG = {
    'CLEAN_JUMP_ORDERS': True,
    'HANDLE_MISSING_VALUES': True,
    'NORMALIZE_CATEGORIES': True,
    'USE_SPARSE_MATRIX': True,  # 大型数据集使用稀疏矩阵
    'CHUNK_SIZE': 10000  # 大数据集分块处理
}

# 输出配置
OUTPUT_CONFIG = {
    'REPORT_FORMATS': ['html', 'md'],
    'CHART_FORMATS': ['png', 'svg'],
    'CSV_ENCODING': 'utf-8-sig',
    'TIMESTAMP_FORMAT': '%Y%m%d_%H%M%S'
}

# 错误处理配置
ERROR_CONFIG = {
    'MAX_ITERATIONS': 1000,
    'TOLERANCE': 1e-6,
    'SINGULAR_MATRIX_HANDLING': 'skip',  # 'skip', 'pseudo_inverse', 'regularize'
    'LOG_LEVEL': 'INFO'
} 