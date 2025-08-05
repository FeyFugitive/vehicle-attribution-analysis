#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整车订单归因分析 - 综合版本
包含数据探索、渠道分析、省份分析、车系分析等多个维度
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class VehicleAttributionAnalysis:
    def __init__(self, data_file):
        """初始化分析器"""
        self.data_file = data_file
        self.df = None
        self.analysis_results = {}
        
    def load_and_clean_data(self):
        """加载和清洗数据"""
        print("📊 正在加载数据...")
        self.df = pd.read_excel(self.data_file, engine="openpyxl")
        print(f"原始数据形状: {self.df.shape}")
        
        # 数据清洗 - 方案B：移除跳跃式订单
        jump = (
            (self.df["deposit_payment_time"].notna() & self.df["intention_payment_time"].isna()) |
            (self.df["lock_time"].notna() & self.df["deposit_payment_time"].isna()) |
            (self.df["final_payment_time"].notna() & self.df["lock_time"].isna()) |
            (self.df["delivery_date"].notna() & self.df["final_payment_time"].isna())
        )
        self.df = self.df[~jump]
        print(f"清洗后数据形状: {self.df.shape}")
        
        # 添加渠道分类
        def categorize_channel(channel):
            if channel == "门店":
                return "STORE"
            elif channel == "总部":
                return "HQ"
            else:
                return "OTHER"
        
        self.df["channel_category"] = self.df["big_channel_name"].map(categorize_channel).fillna("OTHER")
        
        return self.df
    
    def basic_data_exploration(self):
        """基础数据探索"""
        print("\n🔍 基础数据探索")
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
        print("\n📈 马尔可夫链归因分析")
        print("=" * 50)
        
        # 定义阶段
        STAGE_COLS = [
            ("wish_create_time", "Wish"),
            ("intention_payment_time", "Intention"),
            ("deposit_payment_time", "Deposit"),
            ("lock_time", "Lock"),
            ("final_payment_time", "Final"),
            ("delivery_date", "Delivery"),
        ]
        
        # 构建路径
        def build_paths(df, category_col):
            def row_path(row):
                path = ["Start"]
                category = row[category_col]
                for col, stage in STAGE_COLS:
                    if pd.notna(row[col]):
                        path.append(f"{stage}_{category}")
                path.append("Conversion" if pd.notna(row["delivery_date"]) else "Null")
                return path
            
            return df.apply(row_path, axis=1).tolist()
        
        # 计算移除效应
        def removal_effect(paths, test_nodes):
            states = sorted({s for p in paths for s in p})
            idx = {s: i for i, s in enumerate(states)}
            n = len(states)
            
            # 转移矩阵
            T = np.zeros((n, n))
            for p in paths:
                for a, b in zip(p[:-1], p[1:]):
                    T[idx[a], idx[b]] += 1
            row_sum = T.sum(1, keepdims=True)
            T = np.divide(T, row_sum, out=np.zeros_like(T), where=row_sum != 0)
            
            # 基准转化概率
            absorb = ["Conversion", "Null"]
            trans = [s for s in states if s not in absorb]
            Q = T[np.ix_([idx[s] for s in trans], [idx[s] for s in trans])]
            R = T[np.ix_([idx[s] for s in trans], [idx[s] for s in absorb])]
            N = np.linalg.inv(np.eye(len(Q)) - Q)
            v = np.zeros(len(trans))
            v[trans.index("Start")] = 1
            baseline = (v @ N @ R)[0]
            
            results = []
            for node in test_nodes:
                if node not in idx:
                    continue
                Ti = T.copy()
                Ti[:, idx[node]] = 0
                Ti[idx[node], :] = 0
                rs = Ti.sum(1, keepdims=True)
                Ti = np.divide(Ti, rs, out=np.zeros_like(Ti), where=rs != 0)
                
                Q2 = Ti[np.ix_([idx[s] for s in trans], [idx[s] for s in trans])]
                R2 = Ti[np.ix_([idx[s] for s in trans], [idx[s] for s in absorb])]
                N2 = np.linalg.inv(np.eye(len(Q2)) - Q2)
                new_conv = (v @ N2 @ R2)[0]
                
                results.append((node, round((baseline - new_conv) * 100, 2)))
            return results
        
        # 渠道分析
        print("渠道归因分析:")
        paths_channel = build_paths(self.df, "channel_category")
        channel_nodes = [f"{stage}_{ch}" for ch in ["HQ", "STORE"] for _, stage in STAGE_COLS[1:]]
        channel_effects = removal_effect(paths_channel, channel_nodes)
        
        for node, effect in sorted(channel_effects, key=lambda x: -x[1]):
            print(f"  {node:<20}: {effect:+.2f} pp")
        
        # 省份分析
        print("\n省份归因分析 (Top 8):")
        top_provinces = self.df["province_name"].value_counts().head(8).index.tolist()
        self.df["province_cat"] = self.df["province_name"].fillna("UNKNOWN").apply(
            lambda x: x if x in top_provinces else "OTHER"
        )
        
        paths_province = build_paths(self.df, "province_cat")
        province_nodes = [f"{stage}_{prov}" for prov in top_provinces for _, stage in STAGE_COLS[1:]]
        province_effects = removal_effect(paths_province, province_nodes)
        
        for node, effect in sorted(province_effects, key=lambda x: -x[1])[:10]:
            print(f"  {node:<20}: {effect:+.2f} pp")
        
        # 车系分析
        print("\n车系归因分析 (Top 8):")
        top_series = self.df["series"].value_counts().head(8).index.tolist()
        self.df["series_cat"] = self.df["series"].fillna("UNKNOWN").apply(
            lambda x: x if x in top_series else "OTHER"
        )
        
        paths_series = build_paths(self.df, "series_cat")
        series_nodes = [f"{stage}_{series}" for series in top_series for _, stage in STAGE_COLS[1:]]
        series_effects = removal_effect(paths_series, series_nodes)
        
        for node, effect in sorted(series_effects, key=lambda x: -x[1])[:10]:
            print(f"  {node:<20}: {effect:+.2f} pp")
        
        self.analysis_results["channel_effects"] = channel_effects
        self.analysis_results["province_effects"] = province_effects
        self.analysis_results["series_effects"] = series_effects
        
        return channel_effects, province_effects, series_effects
    
    def time_series_analysis(self):
        """时间序列分析"""
        print("\n⏰ 时间序列分析")
        print("=" * 50)
        
        # 按月统计订单量
        self.df["order_month"] = pd.to_datetime(self.df["order_create_time"]).dt.to_period('M')
        monthly_orders = self.df.groupby("order_month").size()
        
        print("月度订单量趋势:")
        for month, count in monthly_orders.tail(6).items():
            print(f"  {month}: {count:,} 订单")
        
        # 转化率时间趋势
        monthly_conversion = self.df.groupby("order_month").apply(
            lambda x: x["delivery_date"].notna().sum() / len(x) * 100
        )
        
        print("\n月度转化率趋势:")
        for month, rate in monthly_conversion.tail(6).items():
            print(f"  {month}: {rate:.1f}%")
        
        self.analysis_results["monthly_orders"] = monthly_orders
        self.analysis_results["monthly_conversion"] = monthly_conversion
        
        return monthly_orders, monthly_conversion
    
    def cancellation_analysis(self):
        """退订分析"""
        print("\n❌ 退订分析")
        print("=" * 50)
        
        # 退订率统计
        total_orders = len(self.df)
        intention_refunds = self.df["intention_refund_time"].notna().sum()
        deposit_refunds = self.df["deposit_refund_time"].notna().sum()
        
        print(f"总订单数: {total_orders:,}")
        print(f"意向金退订数: {intention_refunds:,} ({intention_refunds/total_orders*100:.1f}%)")
        print(f"定金退订数: {deposit_refunds:,} ({deposit_refunds/total_orders*100:.1f}%)")
        
        # 退订原因分析
        if "hold_reason" in self.df.columns:
            hold_reasons = self.df["hold_reason"].value_counts()
            print("\nHold原因分布:")
            for reason, count in hold_reasons.head(5).items():
                print(f"  {reason}: {count}")
        
        self.analysis_results["refund_stats"] = {
            "total_orders": total_orders,
            "intention_refunds": intention_refunds,
            "deposit_refunds": deposit_refunds
        }
        
        return self.analysis_results["refund_stats"]
    
    def generate_summary_report(self):
        """生成分析总结"""
        print("\n📋 分析总结")
        print("=" * 50)
        
        summary = {
            "数据概览": {
                "总订单数": f"{len(self.df):,}",
                "转化率": f"{self.df['delivery_date'].notna().sum()/len(self.df)*100:.1f}%",
                "主要渠道": self.df["channel_category"].value_counts().index[0],
                "主要车系": self.df["series"].value_counts().index[0],
                "主要省份": self.df["province_name"].value_counts().index[0]
            },
            "关键发现": []
        }
        
        # 添加关键发现
        if "channel_effects" in self.analysis_results:
            top_channel = max(self.analysis_results["channel_effects"], key=lambda x: x[1])
            summary["关键发现"].append(f"渠道贡献最大的是 {top_channel[0]}，移除效应为 {top_channel[1]:+.2f} pp")
        
        if "province_effects" in self.analysis_results:
            top_province = max(self.analysis_results["province_effects"], key=lambda x: x[1])
            summary["关键发现"].append(f"省份贡献最大的是 {top_province[0]}，移除效应为 {top_province[1]:+.2f} pp")
        
        if "series_effects" in self.analysis_results:
            top_series = max(self.analysis_results["series_effects"], key=lambda x: x[1])
            summary["关键发现"].append(f"车系贡献最大的是 {top_series[0]}，移除效应为 {top_series[1]:+.2f} pp")
        
        print("数据概览:")
        for key, value in summary["数据概览"].items():
            print(f"  {key}: {value}")
        
        print("\n关键发现:")
        for finding in summary["关键发现"]:
            print(f"  • {finding}")
        
        return summary
    
    def save_results(self):
        """保存分析结果"""
        print("\n💾 保存分析结果...")
        
        # 保存渠道分析结果
        if "channel_effects" in self.analysis_results:
            channel_df = pd.DataFrame([
                {"Channel": node.split("_")[-1], "Stage": "_".join(node.split("_")[:-1]), 
                 "Removal_Effect_pp": effect} 
                for node, effect in self.analysis_results["channel_effects"]
            ])
            channel_df.to_csv("data/channel_removal_effects.csv", index=False)
            print("✓ 渠道分析结果已保存到 data/channel_removal_effects.csv")
        
        # 保存省份分析结果
        if "province_effects" in self.analysis_results:
            province_df = pd.DataFrame([
                {"Province": node.split("_")[-1], "Stage": "_".join(node.split("_")[:-1]), 
                 "Removal_Effect_pp": effect} 
                for node, effect in self.analysis_results["province_effects"]
            ])
            province_df.to_csv("data/province_removal_effects.csv", index=False)
            print("✓ 省份分析结果已保存到 data/province_removal_effects.csv")
        
        # 保存车系分析结果
        if "series_effects" in self.analysis_results:
            series_df = pd.DataFrame([
                {"Series": node.split("_")[-1], "Stage": "_".join(node.split("_")[:-1]), 
                 "Removal_Effect_pp": effect} 
                for node, effect in self.analysis_results["series_effects"]
            ])
            series_df.to_csv("data/series_removal_effects.csv", index=False)
            print("✓ 车系分析结果已保存到 data/series_removal_effects.csv")
    
    def run_full_analysis(self):
        """运行完整分析"""
        print("🚀 开始整车订单归因分析")
        print("=" * 60)
        
        # 1. 加载和清洗数据
        self.load_and_clean_data()
        
        # 2. 基础数据探索
        self.basic_data_exploration()
        
        # 3. 马尔可夫链归因分析
        self.markov_attribution_analysis()
        
        # 4. 时间序列分析
        self.time_series_analysis()
        
        # 5. 退订分析
        self.cancellation_analysis()
        
        # 6. 生成总结报告
        summary = self.generate_summary_report()
        
        # 7. 保存结果
        self.save_results()
        
        print("\n✅ 分析完成！")
        return summary

if __name__ == "__main__":
    # 使用相对路径
    data_file = "data/整车订单状态指标表.xlsx"
    
    # 创建分析器并运行
    analyzer = VehicleAttributionAnalysis(data_file)
    results = analyzer.run_full_analysis() 