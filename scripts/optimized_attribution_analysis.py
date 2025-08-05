#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整车订单归因分析 - 优化版本
包含所有改进：路径构建优化、空值处理增强、性能优化、异常处理强化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ANALYSIS_CONFIG, VISUALIZATION_CONFIG, DATA_CONFIG, OUTPUT_CONFIG
from utils import (
    build_optimized_paths, 
    removal_effect_optimized, 
    safe_category_mapping,
    validate_data_quality,
    parallel_removal_effect,
    log_analysis_progress
)

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = VISUALIZATION_CONFIG['CHINESE_FONT']
plt.rcParams['axes.unicode_minus'] = False

class OptimizedVehicleAttributionAnalysis:
    """优化版本的整车订单归因分析器"""
    
    def __init__(self, data_file):
        """初始化分析器"""
        self.data_file = data_file
        self.df = None
        self.analysis_results = {}
        self.validation_results = {}
        
    def load_and_clean_data(self):
        """加载和清洗数据"""
        log_analysis_progress("📊 正在加载数据...")
        
        try:
            self.df = pd.read_excel(self.data_file, engine="openpyxl")
            log_analysis_progress(f"原始数据形状: {self.df.shape}")
            
            # 数据质量验证
            self.validation_results = validate_data_quality(self.df)
            log_analysis_progress(f"数据质量验证完成: {self.validation_results['total_rows']} 行数据")
            
            if self.validation_results['missing_values']:
                log_analysis_progress(f"发现缺失值: {self.validation_results['missing_values']}")
            
            # 数据清洗 - 方案B：移除跳跃式订单
            if DATA_CONFIG['CLEAN_JUMP_ORDERS']:
                jump = (
                    (self.df["deposit_payment_time"].notna() & self.df["intention_payment_time"].isna()) |
                    (self.df["lock_time"].notna() & self.df["deposit_payment_time"].isna()) |
                    (self.df["final_payment_time"].notna() & self.df["lock_time"].isna()) |
                    (self.df["delivery_date"].notna() & self.df["final_payment_time"].isna())
                )
                self.df = self.df[~jump]
                log_analysis_progress(f"清洗后数据形状: {self.df.shape}")
            
            # 添加渠道分类
            if DATA_CONFIG['NORMALIZE_CATEGORIES']:
                self.df["channel_category"] = self.df["big_channel_name"].apply(
                    lambda x: safe_category_mapping(x, ANALYSIS_CONFIG['CHANNEL_MAPPING'])
                )
            
            return self.df
            
        except Exception as e:
            log_analysis_progress(f"数据加载失败: {e}", 'error')
            raise
    
    def basic_data_exploration(self):
        """基础数据探索"""
        log_analysis_progress("\n🔍 基础数据探索")
        print("=" * 50)
        
        # 订单状态分布
        print("订单状态分布:")
        status_counts = self.df["order_status"].value_counts()
        print(status_counts)
        
        # 车系分布
        print("\n车系分布 (Top 10):")
        series_counts = self.df["series"].value_counts().head(10)
        print(series_counts)
        
        # 省份分布
        print("\n省份分布 (Top 10):")
        province_counts = self.df["province_name"].value_counts().head(10)
        print(province_counts)
        
        # 渠道分布
        print("\n渠道分布:")
        channel_counts = self.df["channel_category"].value_counts()
        print(channel_counts)
        
        # 转化漏斗
        print("\n转化漏斗:")
        funnel_data = {
            "心愿单": self.df["wish_create_time"].notna().sum(),
            "意向金": self.df["intention_payment_time"].notna().sum(),
            "定金": self.df["deposit_payment_time"].notna().sum(),
            "锁单": self.df["lock_time"].notna().sum(),
            "尾款": self.df["final_payment_time"].notna().sum(),
            "交付": self.df["delivery_date"].notna().sum()
        }
        
        for stage, count in funnel_data.items():
            rate = count / funnel_data["心愿单"] * 100
            print(f"{stage}: {count:,} ({rate:.1f}%)")
        
        self.analysis_results["funnel_data"] = funnel_data
        return funnel_data
    
    def markov_attribution_analysis(self):
        """马尔可夫链归因分析"""
        log_analysis_progress("\n🎯 马尔可夫链归因分析")
        print("=" * 50)
        
        # 渠道分析
        log_analysis_progress("渠道归因分析...")
        paths_channel = build_optimized_paths(self.df, "channel_category")
        channel_nodes = [
            f"{stage}{ANALYSIS_CONFIG['PATH_SEPARATOR']}{ch}" 
            for ch in ["HQ", "STORE"] 
            for _, stage in ANALYSIS_CONFIG['STAGE_COLS'][1:]
        ]
        
        channel_effects = removal_effect_optimized(
            paths_channel, 
            channel_nodes, 
            use_sparse=DATA_CONFIG['USE_SPARSE_MATRIX']
        )
        
        print("渠道归因分析:")
        for node, effect in sorted(channel_effects, key=lambda x: -x[1]):
            print(f"  {node:<25}: {effect:+.2f} pp")
        
        # 省份分析
        log_analysis_progress("省份归因分析...")
        top_provinces = self.df["province_name"].value_counts().head(ANALYSIS_CONFIG['TOP_PROVINCES']).index.tolist()
        self.df["province_cat"] = self.df["province_name"].apply(
            lambda x: safe_category_mapping(x, {p: p for p in top_provinces})
        )
        
        paths_province = build_optimized_paths(self.df, "province_cat")
        province_nodes = [
            f"{stage}{ANALYSIS_CONFIG['PATH_SEPARATOR']}{prov}" 
            for prov in top_provinces 
            for _, stage in ANALYSIS_CONFIG['STAGE_COLS'][1:]
        ]
        
        province_effects = removal_effect_optimized(
            paths_province, 
            province_nodes, 
            use_sparse=DATA_CONFIG['USE_SPARSE_MATRIX']
        )
        
        print(f"\n省份归因分析 (Top {ANALYSIS_CONFIG['TOP_PROVINCES']}):")
        for node, effect in sorted(province_effects, key=lambda x: -x[1])[:10]:
            print(f"  {node:<25}: {effect:+.2f} pp")
        
        # 车系分析
        log_analysis_progress("车系归因分析...")
        top_series = self.df["series"].value_counts().head(ANALYSIS_CONFIG['TOP_SERIES']).index.tolist()
        self.df["series_cat"] = self.df["series"].apply(
            lambda x: safe_category_mapping(x, {s: s for s in top_series})
        )
        
        paths_series = build_optimized_paths(self.df, "series_cat")
        series_nodes = [
            f"{stage}{ANALYSIS_CONFIG['PATH_SEPARATOR']}{series}" 
            for series in top_series 
            for _, stage in ANALYSIS_CONFIG['STAGE_COLS'][1:]
        ]
        
        series_effects = removal_effect_optimized(
            paths_series, 
            series_nodes, 
            use_sparse=DATA_CONFIG['USE_SPARSE_MATRIX']
        )
        
        print(f"\n车系归因分析 (Top {ANALYSIS_CONFIG['TOP_SERIES']}):")
        for node, effect in sorted(series_effects, key=lambda x: -x[1])[:10]:
            print(f"  {node:<25}: {effect:+.2f} pp")
        
        self.analysis_results["channel_effects"] = channel_effects
        self.analysis_results["province_effects"] = province_effects
        self.analysis_results["series_effects"] = series_effects
        
        return channel_effects, province_effects, series_effects
    
    def parallel_analysis(self):
        """并行分析（大数据集优化）"""
        log_analysis_progress("\n⚡ 并行归因分析")
        print("=" * 50)
        
        # 准备并行分析数据
        paths_list = []
        nodes_list = []
        
        # 渠道分析
        paths_channel = build_optimized_paths(self.df, "channel_category")
        channel_nodes = [
            f"{stage}{ANALYSIS_CONFIG['PATH_SEPARATOR']}{ch}" 
            for ch in ["HQ", "STORE"] 
            for _, stage in ANALYSIS_CONFIG['STAGE_COLS'][1:]
        ]
        paths_list.append(paths_channel)
        nodes_list.append(channel_nodes)
        
        # 省份分析
        top_provinces = self.df["province_name"].value_counts().head(ANALYSIS_CONFIG['TOP_PROVINCES']).index.tolist()
        self.df["province_cat"] = self.df["province_name"].apply(
            lambda x: safe_category_mapping(x, {p: p for p in top_provinces})
        )
        paths_province = build_optimized_paths(self.df, "province_cat")
        province_nodes = [
            f"{stage}{ANALYSIS_CONFIG['PATH_SEPARATOR']}{prov}" 
            for prov in top_provinces 
            for _, stage in ANALYSIS_CONFIG['STAGE_COLS'][1:]
        ]
        paths_list.append(paths_province)
        nodes_list.append(province_nodes)
        
        # 车系分析
        top_series = self.df["series"].value_counts().head(ANALYSIS_CONFIG['TOP_SERIES']).index.tolist()
        self.df["series_cat"] = self.df["series"].apply(
            lambda x: safe_category_mapping(x, {s: s for s in top_series})
        )
        paths_series = build_optimized_paths(self.df, "series_cat")
        series_nodes = [
            f"{stage}{ANALYSIS_CONFIG['PATH_SEPARATOR']}{series}" 
            for series in top_series 
            for _, stage in ANALYSIS_CONFIG['STAGE_COLS'][1:]
        ]
        paths_list.append(paths_series)
        nodes_list.append(series_nodes)
        
        # 执行并行分析
        results = parallel_removal_effect(paths_list, nodes_list)
        
        if len(results) >= 3:
            channel_effects, province_effects, series_effects = results[:3]
            
            print("并行分析结果:")
            print("渠道归因:")
            for node, effect in sorted(channel_effects, key=lambda x: -x[1]):
                print(f"  {node:<25}: {effect:+.2f} pp")
            
            print(f"\n省份归因 (Top {ANALYSIS_CONFIG['TOP_PROVINCES']}):")
            for node, effect in sorted(province_effects, key=lambda x: -x[1])[:10]:
                print(f"  {node:<25}: {effect:+.2f} pp")
            
            print(f"\n车系归因 (Top {ANALYSIS_CONFIG['TOP_SERIES']}):")
            for node, effect in sorted(series_effects, key=lambda x: -x[1])[:10]:
                print(f"  {node:<25}: {effect:+.2f} pp")
            
            self.analysis_results["parallel_channel_effects"] = channel_effects
            self.analysis_results["parallel_province_effects"] = province_effects
            self.analysis_results["parallel_series_effects"] = series_effects
            
            return channel_effects, province_effects, series_effects
        
        return [], [], []
    
    def time_series_analysis(self):
        """时间序列分析"""
        log_analysis_progress("\n⏰ 时间序列分析")
        print("=" * 50)
        
        # 按月统计订单量
        self.df["order_month"] = pd.to_datetime(self.df["order_create_time"]).dt.to_period('M')
        monthly_orders = self.df.groupby("order_month").size()
        
        print("月度订单量趋势:")
        for month, count in monthly_orders.tail(6).items():
            print(f"  {month}: {count:,} 订单")
        
        # 月度转化率
        monthly_conversion = self.df.groupby("order_month").apply(
            lambda x: x["delivery_date"].notna().sum() / len(x) * 100
        )
        
        print("\n月度转化率趋势:")
        for month, rate in monthly_conversion.tail(6).items():
            print(f"  {month}: {rate:.2f}%")
        
        self.analysis_results["monthly_orders"] = monthly_orders
        self.analysis_results["monthly_conversion"] = monthly_conversion
        
        return monthly_orders, monthly_conversion
    
    def cancellation_analysis(self):
        """退订分析"""
        log_analysis_progress("\n❌ 退订分析")
        print("=" * 50)
        
        # 意向金退订率
        intention_cancelled = self.df[
            (self.df["intention_payment_time"].notna()) & 
            (self.df["deposit_payment_time"].isna())
        ].shape[0]
        intention_total = self.df["intention_payment_time"].notna().sum()
        intention_cancel_rate = intention_cancelled / intention_total * 100 if intention_total > 0 else 0
        
        print(f"意向金退订率: {intention_cancel_rate:.2f}% ({intention_cancelled:,}/{intention_total:,})")
        
        # 定金退订率
        deposit_cancelled = self.df[
            (self.df["deposit_payment_time"].notna()) & 
            (self.df["lock_time"].isna())
        ].shape[0]
        deposit_total = self.df["deposit_payment_time"].notna().sum()
        deposit_cancel_rate = deposit_cancelled / deposit_total * 100 if deposit_total > 0 else 0
        
        print(f"定金退订率: {deposit_cancel_rate:.2f}% ({deposit_cancelled:,}/{deposit_total:,})")
        
        # Hold原因分析
        if "hold_reason" in self.df.columns:
            hold_reasons = self.df["hold_reason"].value_counts().head(5)
            print("\nHold原因分析 (Top 5):")
            for reason, count in hold_reasons.items():
                print(f"  {reason}: {count:,}")
        
        self.analysis_results["intention_cancel_rate"] = intention_cancel_rate
        self.analysis_results["deposit_cancel_rate"] = deposit_cancel_rate
        
        return intention_cancel_rate, deposit_cancel_rate
    
    def generate_summary_report(self):
        """生成分析总结报告"""
        log_analysis_progress("\n📋 生成分析总结报告")
        print("=" * 50)
        
        # 关键发现
        print("🔍 关键发现:")
        
        if "channel_effects" in self.analysis_results:
            top_channel = max(self.analysis_results["channel_effects"], key=lambda x: x[1])
            print(f"  渠道贡献最大: {top_channel[0]}, 移除效应为 {top_channel[1]:+.2f} pp")
        
        if "province_effects" in self.analysis_results:
            top_province = max(self.analysis_results["province_effects"], key=lambda x: x[1])
            print(f"  省份贡献最大: {top_province[0]}, 移除效应为 {top_province[1]:+.2f} pp")
        
        if "series_effects" in self.analysis_results:
            top_series = max(self.analysis_results["series_effects"], key=lambda x: x[1])
            print(f"  车系贡献最大: {top_series[0]}, 移除效应为 {top_series[1]:+.2f} pp")
        
        # 数据质量总结
        print(f"\n📊 数据质量总结:")
        print(f"  总数据行数: {self.validation_results['total_rows']:,}")
        print(f"  重复行数: {self.validation_results['duplicate_rows']:,}")
        if self.validation_results['missing_values']:
            print(f"  缺失值列数: {len(self.validation_results['missing_values'])}")
        
        # 转化漏斗总结
        if "funnel_data" in self.analysis_results:
            funnel = self.analysis_results["funnel_data"]
            print(f"\n🔄 转化漏斗总结:")
            print(f"  心愿单到交付转化率: {funnel['交付']/funnel['心愿单']*100:.1f}%")
            print(f"  意向金到交付转化率: {funnel['交付']/funnel['意向金']*100:.1f}%")
    
    def save_results(self):
        """保存分析结果"""
        log_analysis_progress("\n💾 保存分析结果")
        
        # 创建输出目录
        os.makedirs("data", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        
        # 保存渠道归因结果
        if "channel_effects" in self.analysis_results:
            channel_df = pd.DataFrame(
                self.analysis_results["channel_effects"], 
                columns=["node", "removal_effect"]
            )
            channel_df.to_csv("data/channel_removal_effects.csv", index=False, encoding=OUTPUT_CONFIG['CSV_ENCODING'])
            log_analysis_progress("渠道归因结果已保存到 data/channel_removal_effects.csv")
        
        # 保存省份归因结果
        if "province_effects" in self.analysis_results:
            province_df = pd.DataFrame(
                self.analysis_results["province_effects"], 
                columns=["node", "removal_effect"]
            )
            province_df.to_csv("data/province_removal_effects.csv", index=False, encoding=OUTPUT_CONFIG['CSV_ENCODING'])
            log_analysis_progress("省份归因结果已保存到 data/province_removal_effects.csv")
        
        # 保存车系归因结果
        if "series_effects" in self.analysis_results:
            series_df = pd.DataFrame(
                self.analysis_results["series_effects"], 
                columns=["node", "removal_effect"]
            )
            series_df.to_csv("data/series_removal_effects.csv", index=False, encoding=OUTPUT_CONFIG['CSV_ENCODING'])
            log_analysis_progress("车系归因结果已保存到 data/series_removal_effects.csv")
        
        # 保存数据质量报告
        validation_df = pd.DataFrame([
            {"metric": k, "value": str(v)} 
            for k, v in self.validation_results.items()
        ])
        validation_df.to_csv("data/data_quality_report.csv", index=False, encoding=OUTPUT_CONFIG['CSV_ENCODING'])
        log_analysis_progress("数据质量报告已保存到 data/data_quality_report.csv")
    
    def run_full_analysis(self):
        """运行完整分析"""
        log_analysis_progress("🚀 开始整车订单归因分析")
        print("=" * 60)
        
        try:
            # 1. 数据加载和清洗
            self.load_and_clean_data()
            
            # 2. 基础数据探索
            self.basic_data_exploration()
            
            # 3. 马尔可夫链归因分析
            self.markov_attribution_analysis()
            
            # 4. 并行分析（可选）
            if len(self.df) > 10000:  # 大数据集使用并行分析
                log_analysis_progress("检测到大数据集，启用并行分析...")
                self.parallel_analysis()
            
            # 5. 时间序列分析
            self.time_series_analysis()
            
            # 6. 退订分析
            self.cancellation_analysis()
            
            # 7. 生成总结报告
            self.generate_summary_report()
            
            # 8. 保存结果
            self.save_results()
            
            log_analysis_progress("✅ 分析完成！")
            print("=" * 60)
            
        except Exception as e:
            log_analysis_progress(f"❌ 分析过程中出现错误: {e}", 'error')
            raise

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="整车订单归因分析 - 优化版本")
    parser.add_argument("--data", default="data/整车订单状态指标表.xlsx", help="数据文件路径")
    parser.add_argument("--parallel", action="store_true", help="启用并行分析")
    parser.add_argument("--sparse", action="store_true", help="使用稀疏矩阵")
    
    args = parser.parse_args()
    
    # 更新配置
    if args.sparse:
        DATA_CONFIG['USE_SPARSE_MATRIX'] = True
    
    # 创建分析器并运行
    analyzer = OptimizedVehicleAttributionAnalysis(args.data)
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main() 