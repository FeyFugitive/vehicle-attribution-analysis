#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整车订单归因分析工具函数
"""

import pandas as pd
import numpy as np
import logging
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import inv
import warnings
from config import ANALYSIS_CONFIG, DATA_CONFIG, ERROR_CONFIG

# 设置日志
logging.basicConfig(level=getattr(logging, ERROR_CONFIG['LOG_LEVEL']))
logger = logging.getLogger(__name__)

def safe_category_mapping(value, mapping_dict, unknown_value="UNKNOWN"):
    """
    安全的类别映射，处理空值和异常值
    
    Args:
        value: 输入值
        mapping_dict: 映射字典
        unknown_value: 未知值的默认值
    
    Returns:
        映射后的值
    """
    if pd.isna(value) or value is None:
        return unknown_value
    
    # 处理特殊字符
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return unknown_value
    
    return mapping_dict.get(value, unknown_value)

def build_optimized_paths(df, category_col, stage_cols=None):
    """
    优化的路径构建函数
    
    Args:
        df: 数据框
        category_col: 分类列名
        stage_cols: 阶段列配置
    
    Returns:
        路径列表
    """
    if stage_cols is None:
        stage_cols = ANALYSIS_CONFIG['STAGE_COLS']
    
    separator = ANALYSIS_CONFIG['PATH_SEPARATOR']
    unknown_cat = ANALYSIS_CONFIG['UNKNOWN_CATEGORY']
    
    def row_path(row):
        """构建单行路径"""
        path = ["Start"]
        
        # 安全处理分类值
        cat = row[category_col]
        if pd.isna(cat):
            cat = unknown_cat
        else:
            cat = str(cat).strip()
            if not cat:
                cat = unknown_cat
        
        # 构建路径，使用分隔符防止特殊字符问题
        for col, stage in stage_cols:
            if pd.notna(row[col]):
                path.append(f"{stage}{separator}{cat}")
        
        # 确定最终状态
        if pd.notna(row["delivery_date"]):
            path.append("Conversion")
        else:
            path.append("Null")
        
        return path
    
    if df.empty:
        return []
    paths = df.apply(row_path, axis=1).tolist()
    
    # 过滤无效路径
    min_length = ANALYSIS_CONFIG['MIN_PATH_LENGTH']
    max_length = ANALYSIS_CONFIG['MAX_PATH_LENGTH']
    valid_paths = [p for p in paths if min_length <= len(p) <= max_length]
    
    logger.info(f"构建路径完成: {len(valid_paths)}/{len(paths)} 有效路径")
    return valid_paths

def create_transition_matrix(paths, use_sparse=False):
    """
    创建转移矩阵，支持稀疏矩阵
    
    Args:
        paths: 路径列表
        use_sparse: 是否使用稀疏矩阵
    
    Returns:
        转移矩阵和状态索引
    """
    # 收集所有状态
    states = sorted({s for p in paths for s in p})
    idx = {s: i for i, s in enumerate(states)}
    n = len(states)
    
    if use_sparse and DATA_CONFIG['USE_SPARSE_MATRIX']:
        # 使用稀疏矩阵
        row_indices = []
        col_indices = []
        data = []
        
        for p in paths:
            for a, b in zip(p[:-1], p[1:]):
                row_indices.append(idx[a])
                col_indices.append(idx[b])
                data.append(1)
        
        T = csr_matrix((data, (row_indices, col_indices)), shape=(n, n), dtype=np.float32)
        
        # 归一化
        row_sums = T.sum(axis=1).A1
        T = T.multiply(1.0 / row_sums[:, np.newaxis])
        
    else:
        # 使用密集矩阵
        T = np.zeros((n, n), dtype=np.float32)
        
        # 计算转移次数
        for p in paths:
            for a, b in zip(p[:-1], p[1:]):
                T[idx[a], idx[b]] += 1
        
        # 归一化
        row_sum = T.sum(axis=1, keepdims=True)
        T = np.divide(T, row_sum, out=np.zeros_like(T), where=row_sum != 0)
    
    return T, idx, states

def safe_matrix_inverse(matrix, method='default'):
    """
    安全的矩阵求逆，处理奇异矩阵
    
    Args:
        matrix: 输入矩阵
        method: 处理方法 ('default', 'pseudo_inverse', 'regularize')
    
    Returns:
        逆矩阵或伪逆矩阵
    """
    try:
        if hasattr(matrix, 'toarray'):  # 稀疏矩阵
            matrix = matrix.toarray()
        
        return np.linalg.inv(matrix)
    
    except np.linalg.LinAlgError as e:
        logger.warning(f"矩阵求逆失败: {e}")
        
        if method == 'pseudo_inverse':
            # 使用伪逆
            return np.linalg.pinv(matrix)
        elif method == 'regularize':
            # 正则化
            epsilon = 1e-6
            regularized = matrix + epsilon * np.eye(matrix.shape[0])
            return np.linalg.inv(regularized)
        else:
            # 跳过
            logger.error("无法处理奇异矩阵")
            return None

def removal_effect_optimized(paths, test_nodes, use_sparse=False):
    """
    优化的移除效应计算
    
    Args:
        paths: 路径列表
        test_nodes: 测试节点列表
        use_sparse: 是否使用稀疏矩阵
    
    Returns:
        移除效应结果列表
    """
    if not paths:
        logger.warning("路径列表为空")
        return []
    
    # 创建转移矩阵
    T, idx, states = create_transition_matrix(paths, use_sparse)
    
    # 定义吸收状态
    absorb = ["Conversion", "Null"]
    trans = [s for s in states if s not in absorb]
    
    if not trans:
        logger.warning("没有过渡状态")
        return []
    
    # 提取子矩阵
    trans_indices = [idx[s] for s in trans]
    absorb_indices = [idx[s] for s in absorb]
    
    if use_sparse and DATA_CONFIG['USE_SPARSE_MATRIX']:
        Q = T[trans_indices][:, trans_indices]
        R = T[trans_indices][:, absorb_indices]
    else:
        Q = T[np.ix_(trans_indices, trans_indices)]
        R = T[np.ix_(trans_indices, absorb_indices)]
    
    # 计算基准转化概率
    N = safe_matrix_inverse(np.eye(len(Q)) - Q, ERROR_CONFIG['SINGULAR_MATRIX_HANDLING'])
    if N is None:
        return []
    
    v = np.zeros(len(trans))
    if "Start" in trans:
        v[trans.index("Start")] = 1
    else:
        logger.warning("未找到Start状态")
        return []
    
    baseline = (v @ N @ R)[0]
    
    # 计算移除效应
    results = []
    for node in test_nodes:
        if node not in idx:
            logger.debug(f"节点 {node} 不在状态集中")
            continue
        
        try:
            # 创建移除后的转移矩阵
            Ti = T.copy()
            node_idx = idx[node]
            
            if use_sparse and DATA_CONFIG['USE_SPARSE_MATRIX']:
                Ti[:, node_idx] = 0
                Ti[node_idx, :] = 0
                row_sums = Ti.sum(axis=1).A1
                Ti = Ti.multiply(1.0 / row_sums[:, np.newaxis])
                
                Q2 = Ti[trans_indices][:, trans_indices]
                R2 = Ti[trans_indices][:, absorb_indices]
            else:
                Ti[:, node_idx] = 0
                Ti[node_idx, :] = 0
                row_sum = Ti.sum(axis=1, keepdims=True)
                Ti = np.divide(Ti, row_sum, out=np.zeros_like(Ti), where=row_sum != 0)
                
                Q2 = Ti[np.ix_(trans_indices, trans_indices)]
                R2 = Ti[np.ix_(trans_indices, absorb_indices)]
            
            N2 = safe_matrix_inverse(np.eye(len(Q2)) - Q2, ERROR_CONFIG['SINGULAR_MATRIX_HANDLING'])
            if N2 is None:
                continue
            
            new_conv = (v @ N2 @ R2)[0]
            effect = round((baseline - new_conv) * 100, 2)
            results.append((node, effect))
            
        except Exception as e:
            logger.error(f"计算节点 {node} 移除效应时出错: {e}")
            continue
    
    return results

def parallel_removal_effect(paths_list, nodes_list, max_workers=None):
    """
    并行计算移除效应
    
    Args:
        paths_list: 路径列表的列表
        nodes_list: 节点列表的列表
        max_workers: 最大工作进程数
    
    Returns:
        结果列表
    """
    try:
        from concurrent.futures import ProcessPoolExecutor
        import multiprocessing
        
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), 4)
        
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(removal_effect_optimized, paths, nodes)
                for paths, nodes in zip(paths_list, nodes_list)
            ]
            
            for future in futures:
                try:
                    result = future.result(timeout=300)  # 5分钟超时
                    results.append(result)
                except Exception as e:
                    logger.error(f"并行计算失败: {e}")
                    results.append([])
        
        return results
    
    except ImportError:
        logger.warning("无法导入concurrent.futures，使用串行计算")
        return [
            removal_effect_optimized(paths, nodes)
            for paths, nodes in zip(paths_list, nodes_list)
        ]

def validate_data_quality(df):
    """
    验证数据质量
    
    Args:
        df: 数据框
    
    Returns:
        验证结果字典
    """
    validation_results = {
        'total_rows': len(df),
        'missing_values': {},
        'duplicate_rows': df.duplicated().sum(),
        'data_types': df.dtypes.to_dict(),
        'unique_values': {}
    }
    
    # 检查缺失值
    for col in df.columns:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            validation_results['missing_values'][col] = missing_count
    
    # 检查唯一值数量
    for col in df.select_dtypes(include=['object']).columns:
        validation_results['unique_values'][col] = df[col].nunique()
    
    return validation_results

def log_analysis_progress(message, level='info'):
    """
    记录分析进度
    
    Args:
        message: 消息内容
        level: 日志级别
    """
    getattr(logger, level)(message)
    print(f"[{level.upper()}] {message}") 