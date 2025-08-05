#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归因分析可视化报告生成器
生成各种图表来展示分析结果
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8')

class AttributionVisualization:
    def __init__(self):
        """初始化可视化器"""
        self.fig_size = (12, 8)
        self.colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6B5B95']
        
    def create_funnel_chart(self, funnel_data):
        """创建转化漏斗图"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        stages = list(funnel_data.keys())
        counts = list(funnel_data.values())
        rates = [count/counts[0]*100 for count in counts]
        
        # 创建漏斗图
        y_pos = np.arange(len(stages))
        bars = ax.barh(y_pos, rates, color=self.colors[:len(stages)])
        
        # 添加数值标签
        for i, (bar, count, rate) in enumerate(zip(bars, counts, rates)):
            ax.text(rate + 1, bar.get_y() + bar.get_height()/2, 
                   f'{count:,} ({rate:.1f}%)', 
                   va='center', ha='left', fontsize=10)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(stages, fontsize=12)
        ax.set_xlabel('转化率 (%)', fontsize=12)
        ax.set_title('整车订单转化漏斗', fontsize=16, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('reports/funnel_chart.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ 转化漏斗图已保存")
    
    def create_attribution_heatmap(self, effects_data, title, filename):
        """创建归因热力图"""
        # 处理数据
        df = pd.DataFrame(effects_data)
        df[['Stage', 'Category']] = df['node'].str.split('_', expand=True)
        
        # 创建透视表
        pivot_df = df.pivot(index='Category', columns='Stage', values='effect')
        
        # 创建热力图
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(pivot_df, annot=True, fmt='.2f', cmap='RdYlBu_r', 
                   center=0, cbar_kws={'label': '移除效应 (pp)'}, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('转化阶段', fontsize=12)
        ax.set_ylabel('分类', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(f'reports/{filename}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {title}已保存")
    
    def create_top_contributors_chart(self, effects_data, title, filename, top_n=10):
        """创建Top贡献者柱状图"""
        # 排序并取前N个
        sorted_effects = sorted(effects_data, key=lambda x: x[1], reverse=True)[:top_n]
        
        categories = [item[0] for item in sorted_effects]
        effects = [item[1] for item in sorted_effects]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(range(len(categories)), effects, 
                      color=[self.colors[0] if x > 0 else self.colors[3] for x in effects])
        
        # 添加数值标签
        for i, (bar, effect) in enumerate(zip(bars, effects)):
            ax.text(effect + (0.01 if effect > 0 else -0.01), bar.get_y() + bar.get_height()/2,
                   f'{effect:+.2f}', va='center', 
                   ha='left' if effect > 0 else 'right', fontsize=10)
        
        ax.set_yticks(range(len(categories)))
        ax.set_yticklabels(categories, fontsize=10)
        ax.set_xlabel('移除效应 (pp)', fontsize=12)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'reports/{filename}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {title}已保存")
    
    def create_time_series_chart(self, monthly_data, title, filename):
        """创建时间序列图"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        months = [str(m) for m in monthly_data.index]
        values = monthly_data.values
        
        ax.plot(months, values, marker='o', linewidth=2, markersize=8, color=self.colors[0])
        ax.fill_between(months, values, alpha=0.3, color=self.colors[0])
        
        # 添加数值标签
        for i, (month, value) in enumerate(zip(months, values)):
            ax.text(i, value + max(values)*0.02, f'{value:,.0f}', 
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('订单数量', fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'reports/{filename}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ {title}已保存")
    
    def create_distribution_charts(self, df):
        """创建分布图"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 车系分布
        series_counts = df['series'].value_counts().head(8)
        axes[0,0].pie(series_counts.values, labels=series_counts.index, autopct='%1.1f%%')
        axes[0,0].set_title('车系分布 (Top 8)', fontsize=14, fontweight='bold')
        
        # 省份分布
        province_counts = df['province_name'].value_counts().head(8)
        axes[0,1].bar(range(len(province_counts)), province_counts.values, color=self.colors[1])
        axes[0,1].set_xticks(range(len(province_counts)))
        axes[0,1].set_xticklabels(province_counts.index, rotation=45, ha='right')
        axes[0,1].set_title('省份分布 (Top 8)', fontsize=14, fontweight='bold')
        axes[0,1].set_ylabel('订单数量')
        
        # 渠道分布
        channel_counts = df['channel_category'].value_counts()
        axes[1,0].pie(channel_counts.values, labels=channel_counts.index, autopct='%1.1f%%')
        axes[1,0].set_title('渠道分布', fontsize=14, fontweight='bold')
        
        # 订单状态分布
        status_counts = df['order_status'].value_counts().head(6)
        axes[1,1].bar(range(len(status_counts)), status_counts.values, color=self.colors[2])
        axes[1,1].set_xticks(range(len(status_counts)))
        axes[1,1].set_xticklabels(status_counts.index, rotation=45, ha='right')
        axes[1,1].set_title('订单状态分布 (Top 6)', fontsize=14, fontweight='bold')
        axes[1,1].set_ylabel('订单数量')
        
        plt.tight_layout()
        plt.savefig('reports/distribution_charts.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ 分布图已保存")
    
    def create_summary_dashboard(self, analysis_results):
        """创建总结仪表板"""
        fig = plt.figure(figsize=(16, 12))
        
        # 创建网格布局
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. 关键指标
        ax1 = fig.add_subplot(gs[0, :])
        
        # 获取数据
        total_orders = analysis_results.get('total_orders', 0)
        conversion_rate = analysis_results.get('conversion_rate', 0)
        top_channel = analysis_results.get('top_channel', 'N/A')
        top_series = analysis_results.get('top_series', 'N/A')
        
        metrics = [
            f"总订单数: {total_orders:,}" if isinstance(total_orders, int) else f"总订单数: {total_orders}",
            f"转化率: {conversion_rate:.1f}%" if isinstance(conversion_rate, (int, float)) else f"转化率: {conversion_rate}",
            f"主要渠道: {top_channel}",
            f"主要车系: {top_series}"
        ]
        
        ax1.text(0.1, 0.8, '关键指标', fontsize=16, fontweight='bold')
        for i, metric in enumerate(metrics):
            ax1.text(0.1, 0.6 - i*0.15, metric, fontsize=12)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        
        # 2. 转化漏斗
        ax2 = fig.add_subplot(gs[1, 0])
        if 'funnel_data' in analysis_results:
            funnel_data = analysis_results['funnel_data']
            stages = list(funnel_data.keys())
            rates = [funnel_data[stage]/funnel_data['心愿单']*100 for stage in stages]
            ax2.barh(stages, rates, color=self.colors[:len(stages)])
            ax2.set_title('转化漏斗', fontsize=12, fontweight='bold')
            ax2.set_xlabel('转化率 (%)')
        
        # 3. 渠道贡献
        ax3 = fig.add_subplot(gs[1, 1])
        if 'channel_effects' in analysis_results:
            channel_effects = analysis_results['channel_effects'][:5]  # Top 5
            categories = [item[0] for item in channel_effects]
            effects = [item[1] for item in channel_effects]
            colors = [self.colors[0] if x > 0 else self.colors[3] for x in effects]
            ax3.barh(range(len(categories)), effects, color=colors)
            ax3.set_yticks(range(len(categories)))
            ax3.set_yticklabels(categories, fontsize=8)
            ax3.set_title('渠道贡献 (Top 5)', fontsize=12, fontweight='bold')
            ax3.set_xlabel('移除效应 (pp)')
        
        # 4. 省份贡献
        ax4 = fig.add_subplot(gs[1, 2])
        if 'province_effects' in analysis_results:
            province_effects = analysis_results['province_effects'][:5]  # Top 5
            categories = [item[0] for item in province_effects]
            effects = [item[1] for item in province_effects]
            colors = [self.colors[1] if x > 0 else self.colors[3] for x in effects]
            ax4.barh(range(len(categories)), effects, color=colors)
            ax4.set_yticks(range(len(categories)))
            ax4.set_yticklabels(categories, fontsize=8)
            ax4.set_title('省份贡献 (Top 5)', fontsize=12, fontweight='bold')
            ax4.set_xlabel('移除效应 (pp)')
        
        # 5. 时间趋势
        ax5 = fig.add_subplot(gs[2, :])
        if 'monthly_orders' in analysis_results:
            monthly_orders = analysis_results['monthly_orders']
            months = [str(m) for m in monthly_orders.index[-6:]]  # 最近6个月
            values = monthly_orders.values[-6:]
            ax5.plot(months, values, marker='o', linewidth=2, color=self.colors[0])
            ax5.fill_between(months, values, alpha=0.3, color=self.colors[0])
            ax5.set_title('月度订单趋势', fontsize=12, fontweight='bold')
            ax5.set_xlabel('月份')
            ax5.set_ylabel('订单数量')
            plt.setp(ax5.get_xticklabels(), rotation=45)
        
        plt.suptitle('整车订单归因分析仪表板', fontsize=18, fontweight='bold')
        plt.savefig('reports/attribution_dashboard.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ 分析仪表板已保存")
    
    def generate_all_visualizations(self, analysis_results, df):
        """生成所有可视化图表"""
        print("🎨 开始生成可视化图表...")
        
        # 确保reports目录存在
        import os
        os.makedirs('reports', exist_ok=True)
        
        # 1. 转化漏斗图
        if 'funnel_data' in analysis_results:
            self.create_funnel_chart(analysis_results['funnel_data'])
        
        # 2. 渠道归因热力图
        if 'channel_effects' in analysis_results:
            self.create_attribution_heatmap(
                [{'node': item[0], 'effect': item[1]} for item in analysis_results['channel_effects']],
                '渠道归因热力图',
                'channel_attribution_heatmap'
            )
        
        # 3. 省份归因热力图
        if 'province_effects' in analysis_results:
            self.create_attribution_heatmap(
                [{'node': item[0], 'effect': item[1]} for item in analysis_results['province_effects']],
                '省份归因热力图',
                'province_attribution_heatmap'
            )
        
        # 4. 车系归因热力图
        if 'series_effects' in analysis_results:
            self.create_attribution_heatmap(
                [{'node': item[0], 'effect': item[1]} for item in analysis_results['series_effects']],
                '车系归因热力图',
                'series_attribution_heatmap'
            )
        
        # 5. Top贡献者图表
        if 'channel_effects' in analysis_results:
            self.create_top_contributors_chart(
                analysis_results['channel_effects'],
                '渠道贡献排名 (Top 10)',
                'channel_contributors',
                10
            )
        
        if 'province_effects' in analysis_results:
            self.create_top_contributors_chart(
                analysis_results['province_effects'],
                '省份贡献排名 (Top 10)',
                'province_contributors',
                10
            )
        
        if 'series_effects' in analysis_results:
            self.create_top_contributors_chart(
                analysis_results['series_effects'],
                '车系贡献排名 (Top 10)',
                'series_contributors',
                10
            )
        
        # 6. 时间序列图
        if 'monthly_orders' in analysis_results:
            self.create_time_series_chart(
                analysis_results['monthly_orders'],
                '月度订单量趋势',
                'monthly_orders_trend'
            )
        
        # 7. 分布图
        self.create_distribution_charts(df)
        
        # 8. 总结仪表板
        self.create_summary_dashboard(analysis_results)
        
        print("✅ 所有可视化图表生成完成！")

if __name__ == "__main__":
    # 这里可以添加测试代码
    print("可视化模块已加载") 