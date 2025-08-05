#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整车订单归因分析使用示例
"""

import pandas as pd
import numpy as np
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ANALYSIS_CONFIG, DATA_CONFIG
from utils import (
    build_optimized_paths, 
    removal_effect_optimized, 
    safe_category_mapping,
    validate_data_quality,
    log_analysis_progress
)

def create_sample_data():
    """创建示例数据"""
    print("📊 创建示例数据...")
    
    # 创建示例数据
    n_records = 100
    sample_data = pd.DataFrame({
        'wish_create_time': pd.date_range('2023-01-01', periods=n_records, freq='D'),
        'intention_payment_time': pd.date_range('2023-01-01', periods=n_records, freq='D'),
        'deposit_payment_time': pd.date_range('2023-01-01', periods=n_records, freq='D'),
        'lock_time': pd.date_range('2023-01-01', periods=n_records, freq='D'),
        'final_payment_time': pd.date_range('2023-01-01', periods=n_records, freq='D'),
        'delivery_date': pd.date_range('2023-01-01', periods=n_records, freq='D'),
        'big_channel_name': ['门店'] * 60 + ['总部'] * 40,
        'province_name': ['浙江省'] * 40 + ['江苏省'] * 30 + ['广东省'] * 30,
        'series': ['LS6'] * 50 + ['LS7'] * 30 + ['LS8'] * 20,
        'order_status': ['已完成'] * 40 + ['进行中'] * 60
    })
    
    # 添加一些缺失值，让部分订单不完成转化
    sample_data.loc[10:20, 'intention_payment_time'] = None
    sample_data.loc[30:40, 'deposit_payment_time'] = None
    sample_data.loc[50:70, 'delivery_date'] = None  # 让部分订单不完成转化
    
    return sample_data

def demonstrate_path_building():
    """演示路径构建功能"""
    print("\n🔗 演示路径构建功能")
    print("=" * 40)
    
    # 创建示例数据
    df = create_sample_data()
    
    # 添加渠道分类
    df["channel_category"] = df["big_channel_name"].apply(
        lambda x: safe_category_mapping(x, ANALYSIS_CONFIG['CHANNEL_MAPPING'])
    )
    
    # 构建路径
    paths = build_optimized_paths(df, "channel_category")
    
    print(f"构建了 {len(paths)} 条路径")
    print("示例路径:")
    for i, path in enumerate(paths[:3]):
        print(f"  路径 {i+1}: {' -> '.join(path)}")
    
    return paths, df

def demonstrate_removal_effect():
    """演示移除效应计算"""
    print("\n🎯 演示移除效应计算")
    print("=" * 40)
    
    paths, df = demonstrate_path_building()
    
    # 定义测试节点
    test_nodes = [
        f"Intention{ANALYSIS_CONFIG['PATH_SEPARATOR']}STORE",
        f"Deposit{ANALYSIS_CONFIG['PATH_SEPARATOR']}HQ"
    ]
    
    # 计算移除效应
    effects = removal_effect_optimized(paths, test_nodes)
    
    print("移除效应结果:")
    for node, effect in effects:
        print(f"  {node}: {effect:+.2f} pp")
    
    return effects

def demonstrate_data_validation():
    """演示数据质量验证"""
    print("\n🔍 演示数据质量验证")
    print("=" * 40)
    
    df = create_sample_data()
    
    # 验证数据质量
    validation = validate_data_quality(df)
    
    print("数据质量报告:")
    print(f"  总行数: {validation['total_rows']}")
    print(f"  重复行数: {validation['duplicate_rows']}")
    
    if validation['missing_values']:
        print("  缺失值:")
        for col, count in validation['missing_values'].items():
            print(f"    {col}: {count}")
    
    print("  唯一值数量:")
    for col, count in validation['unique_values'].items():
        print(f"    {col}: {count}")

def demonstrate_config_usage():
    """演示配置使用"""
    print("\n⚙️ 演示配置使用")
    print("=" * 40)
    
    print("分析配置:")
    print(f"  Top N省份: {ANALYSIS_CONFIG['TOP_PROVINCES']}")
    print(f"  Top N车系: {ANALYSIS_CONFIG['TOP_SERIES']}")
    print(f"  路径分隔符: '{ANALYSIS_CONFIG['PATH_SEPARATOR']}'")
    print(f"  未知类别: '{ANALYSIS_CONFIG['UNKNOWN_CATEGORY']}'")
    
    print("\n数据处理配置:")
    print(f"  清洗跳跃式订单: {DATA_CONFIG['CLEAN_JUMP_ORDERS']}")
    print(f"  处理缺失值: {DATA_CONFIG['HANDLE_MISSING_VALUES']}")
    print(f"  使用稀疏矩阵: {DATA_CONFIG['USE_SPARSE_MATRIX']}")

def demonstrate_error_handling():
    """演示错误处理"""
    print("\n🛡️ 演示错误处理")
    print("=" * 40)
    
    # 测试空值处理
    print("空值处理测试:")
    mapping = {"门店": "STORE", "总部": "HQ"}
    
    test_values = ["门店", "总部", None, "", "   ", "其他"]
    for value in test_values:
        result = safe_category_mapping(value, mapping)
        print(f"  '{value}' -> '{result}'")
    
    # 测试边界情况
    print("\n边界情况测试:")
    empty_df = pd.DataFrame()
    paths = build_optimized_paths(empty_df, "channel_category")
    print(f"  空数据框路径数: {len(paths)}")

def main():
    """主函数"""
    print("🎯 整车订单归因分析 - 使用示例")
    print("=" * 50)
    
    try:
        # 1. 演示路径构建
        demonstrate_path_building()
        
        # 2. 演示移除效应计算
        demonstrate_removal_effect()
        
        # 3. 演示数据质量验证
        demonstrate_data_validation()
        
        # 4. 演示配置使用
        demonstrate_config_usage()
        
        # 5. 演示错误处理
        demonstrate_error_handling()
        
        print("\n✅ 所有示例运行完成！")
        print("\n📋 下一步:")
        print("1. 准备真实数据文件")
        print("2. 运行: python run_analysis.py")
        print("3. 查看分析结果")
        
    except Exception as e:
        print(f"❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 