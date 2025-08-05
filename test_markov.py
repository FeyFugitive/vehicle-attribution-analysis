#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整车订单归因分析单元测试
"""

import unittest
import pandas as pd
import numpy as np
from utils import (
    build_optimized_paths, 
    removal_effect_optimized, 
    safe_category_mapping,
    validate_data_quality,
    safe_matrix_inverse
)
from config import ANALYSIS_CONFIG

class TestMarkovAttribution(unittest.TestCase):
    """马尔可夫链归因测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试数据
        self.test_data = pd.DataFrame({
            'wish_create_time': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'intention_payment_time': ['2023-01-01', None, '2023-01-03'],
            'deposit_payment_time': ['2023-01-02', None, '2023-01-04'],
            'lock_time': ['2023-01-03', None, '2023-01-05'],
            'final_payment_time': ['2023-01-04', None, '2023-01-06'],
            'delivery_date': ['2023-01-05', None, '2023-01-07'],
            'channel_category': ['STORE', 'HQ', 'STORE'],
            'province_name': ['浙江省', '江苏省', '浙江省'],
            'series': ['LS6', 'LS7', 'LS6']
        })
        
        # 转换时间列
        for col in ['wish_create_time', 'intention_payment_time', 'deposit_payment_time', 
                   'lock_time', 'final_payment_time', 'delivery_date']:
            self.test_data[col] = pd.to_datetime(self.test_data[col])
    
    def test_safe_category_mapping(self):
        """测试安全的类别映射"""
        mapping_dict = {"门店": "STORE", "总部": "HQ"}
        
        # 测试正常值
        self.assertEqual(safe_category_mapping("门店", mapping_dict), "STORE")
        self.assertEqual(safe_category_mapping("总部", mapping_dict), "HQ")
        
        # 测试空值
        self.assertEqual(safe_category_mapping(None, mapping_dict), "UNKNOWN")
        self.assertEqual(safe_category_mapping(pd.NA, mapping_dict), "UNKNOWN")
        
        # 测试未知值
        self.assertEqual(safe_category_mapping("其他", mapping_dict), "UNKNOWN")
        
        # 测试空字符串
        self.assertEqual(safe_category_mapping("", mapping_dict), "UNKNOWN")
        self.assertEqual(safe_category_mapping("   ", mapping_dict), "UNKNOWN")
    
    def test_build_optimized_paths(self):
        """测试优化的路径构建"""
        paths = build_optimized_paths(self.test_data, 'channel_category')
        
        # 验证路径数量
        self.assertEqual(len(paths), 3)
        
        # 验证路径格式
        for path in paths:
            self.assertIn("Start", path)
            self.assertIn("Conversion", path)
            self.assertTrue(len(path) >= 3)  # Start + 至少一个阶段 + Conversion
    
    def test_removal_effect(self):
        """测试移除效应计算"""
        paths = build_optimized_paths(self.test_data, 'channel_category')
        test_nodes = ["Intention||STORE", "Deposit||HQ"]
        
        effects = removal_effect_optimized(paths, test_nodes)
        
        # 验证返回格式
        self.assertIsInstance(effects, list)
        for effect in effects:
            self.assertIsInstance(effect, tuple)
            self.assertEqual(len(effect), 2)
            self.assertIsInstance(effect[0], str)
            self.assertIsInstance(effect[1], (int, float))
    
    def test_safe_matrix_inverse(self):
        """测试安全的矩阵求逆"""
        # 测试正常矩阵
        normal_matrix = np.array([[2, 1], [1, 2]])
        inverse = safe_matrix_inverse(normal_matrix)
        self.assertIsNotNone(inverse)
        
        # 测试奇异矩阵
        singular_matrix = np.array([[1, 1], [1, 1]])
        inverse = safe_matrix_inverse(singular_matrix, method='pseudo_inverse')
        self.assertIsNotNone(inverse)
        
        # 测试奇异矩阵（跳过模式）
        inverse = safe_matrix_inverse(singular_matrix, method='skip')
        self.assertIsNone(inverse)
    
    def test_validate_data_quality(self):
        """测试数据质量验证"""
        # 添加一些缺失值
        test_data_with_missing = self.test_data.copy()
        test_data_with_missing.loc[0, 'channel_category'] = None
        
        validation = validate_data_quality(test_data_with_missing)
        
        # 验证返回格式
        self.assertIn('total_rows', validation)
        self.assertIn('missing_values', validation)
        self.assertIn('duplicate_rows', validation)
        self.assertIn('data_types', validation)
        self.assertIn('unique_values', validation)
        
        # 验证数据
        self.assertEqual(validation['total_rows'], 3)
        self.assertIn('channel_category', validation['missing_values'])
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 空数据框
        empty_df = pd.DataFrame()
        paths = build_optimized_paths(empty_df, 'channel_category')
        self.assertEqual(len(paths), 0)
        
        # 只有一列的数据框
        single_col_df = pd.DataFrame({'channel_category': ['STORE']})
        paths = build_optimized_paths(single_col_df, 'channel_category')
        self.assertEqual(len(paths), 1)
        
        # 全为空值的数据框
        null_df = pd.DataFrame({
            'wish_create_time': [None, None],
            'channel_category': [None, None]
        })
        paths = build_optimized_paths(null_df, 'channel_category')
        self.assertEqual(len(paths), 2)
    
    def test_performance_optimization(self):
        """测试性能优化"""
        # 创建大数据集
        large_data = pd.DataFrame({
            'wish_create_time': pd.date_range('2023-01-01', periods=1000, freq='D'),
            'intention_payment_time': pd.date_range('2023-01-01', periods=1000, freq='D'),
            'deposit_payment_time': pd.date_range('2023-01-01', periods=1000, freq='D'),
            'lock_time': pd.date_range('2023-01-01', periods=1000, freq='D'),
            'final_payment_time': pd.date_range('2023-01-01', periods=1000, freq='D'),
            'delivery_date': pd.date_range('2023-01-01', periods=1000, freq='D'),
            'channel_category': ['STORE'] * 500 + ['HQ'] * 500
        })
        
        # 测试稀疏矩阵模式
        paths = build_optimized_paths(large_data, 'channel_category')
        test_nodes = ["Intention||STORE", "Deposit||HQ"]
        
        # 测试密集矩阵
        effects_dense = removal_effect_optimized(paths, test_nodes, use_sparse=False)
        
        # 测试稀疏矩阵
        effects_sparse = removal_effect_optimized(paths, test_nodes, use_sparse=True)
        
        # 验证结果一致性
        self.assertEqual(len(effects_dense), len(effects_sparse))
    
    def test_config_integration(self):
        """测试配置集成"""
        # 验证配置参数
        self.assertIn('TOP_PROVINCES', ANALYSIS_CONFIG)
        self.assertIn('TOP_SERIES', ANALYSIS_CONFIG)
        self.assertIn('CHANNEL_MAPPING', ANALYSIS_CONFIG)
        self.assertIn('PATH_SEPARATOR', ANALYSIS_CONFIG)
        self.assertIn('UNKNOWN_CATEGORY', ANALYSIS_CONFIG)
        
        # 验证路径分隔符
        separator = ANALYSIS_CONFIG['PATH_SEPARATOR']
        self.assertIsInstance(separator, str)
        self.assertNotIn('_', separator)  # 避免与原始下划线冲突

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2) 