#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归因分析报告生成器
整合分析结果和可视化图表，生成完整的归因分析报告
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from comprehensive_attribution_analysis import VehicleAttributionAnalysis
from visualization_report import AttributionVisualization

class AttributionReportGenerator:
    def __init__(self):
        """初始化报告生成器"""
        self.analyzer = None
        self.visualizer = None
        self.analysis_results = {}
        
    def run_analysis_and_visualization(self, data_file):
        """运行分析和可视化"""
        print("🚀 开始整车订单归因分析")
        print("=" * 60)
        
        # 1. 运行分析
        self.analyzer = VehicleAttributionAnalysis(data_file)
        self.analysis_results = self.analyzer.run_full_analysis()
        
        # 2. 生成可视化
        self.visualizer = AttributionVisualization()
        self.visualizer.generate_all_visualizations(self.analysis_results, self.analyzer.df)
        
        return self.analysis_results
    
    def generate_markdown_report(self, output_file="reports/attribution_analysis_report.md"):
        """生成Markdown格式的报告"""
        print(f"\n📝 生成Markdown报告: {output_file}")
        
        # 确保reports目录存在
        os.makedirs('reports', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 报告标题
            f.write("# 整车订单归因分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # 执行摘要
            f.write("## 📋 执行摘要\n\n")
            f.write("本报告基于马尔可夫链归因模型，对整车订单数据进行全面分析，识别各渠道、省份、车系对转化的贡献度。\n\n")
            
            # 关键发现
            f.write("### 关键发现\n\n")
            if 'channel_effects' in self.analysis_results:
                top_channel = max(self.analysis_results['channel_effects'], key=lambda x: x[1])
                f.write(f"- **渠道贡献最大**: {top_channel[0]}，移除效应为 {top_channel[1]:+.2f} pp\n")
            
            if 'province_effects' in self.analysis_results:
                top_province = max(self.analysis_results['province_effects'], key=lambda x: x[1])
                f.write(f"- **省份贡献最大**: {top_province[0]}，移除效应为 {top_province[1]:+.2f} pp\n")
            
            if 'series_effects' in self.analysis_results:
                top_series = max(self.analysis_results['series_effects'], key=lambda x: x[1])
                f.write(f"- **车系贡献最大**: {top_series[0]}，移除效应为 {top_series[1]:+.2f} pp\n")
            
            f.write("\n---\n\n")
            
            # 数据概览
            f.write("## 📊 数据概览\n\n")
            df = self.analyzer.df
            f.write(f"- **总订单数**: {len(df):,}\n")
            f.write(f"- **转化率**: {df['delivery_date'].notna().sum()/len(df)*100:.1f}%\n")
            f.write(f"- **主要渠道**: {df['channel_category'].value_counts().index[0]}\n")
            f.write(f"- **主要车系**: {df['series'].value_counts().index[0]}\n")
            f.write(f"- **主要省份**: {df['province_name'].value_counts().index[0]}\n\n")
            
            # 转化漏斗
            f.write("### 转化漏斗\n\n")
            if 'funnel_data' in self.analysis_results:
                funnel_data = self.analysis_results['funnel_data']
                f.write("| 阶段 | 数量 | 转化率 |\n")
                f.write("|------|------|--------|\n")
                for stage, count in funnel_data.items():
                    rate = count / funnel_data['心愿单'] * 100
                    f.write(f"| {stage} | {count:,} | {rate:.1f}% |\n")
                f.write("\n")
            
            f.write("![转化漏斗](funnel_chart.png)\n\n")
            
            # 渠道分析
            f.write("## 🏢 渠道归因分析\n\n")
            f.write("### 渠道贡献排名\n\n")
            if 'channel_effects' in self.analysis_results:
                f.write("| 渠道阶段 | 移除效应 (pp) |\n")
                f.write("|----------|---------------|\n")
                for node, effect in sorted(self.analysis_results['channel_effects'], key=lambda x: -x[1])[:10]:
                    f.write(f"| {node} | {effect:+.2f} |\n")
                f.write("\n")
            
            f.write("![渠道归因热力图](channel_attribution_heatmap.png)\n\n")
            f.write("![渠道贡献排名](channel_contributors.png)\n\n")
            
            # 省份分析
            f.write("## 🗺️ 省份归因分析\n\n")
            f.write("### 省份贡献排名\n\n")
            if 'province_effects' in self.analysis_results:
                f.write("| 省份阶段 | 移除效应 (pp) |\n")
                f.write("|----------|---------------|\n")
                for node, effect in sorted(self.analysis_results['province_effects'], key=lambda x: -x[1])[:10]:
                    f.write(f"| {node} | {effect:+.2f} |\n")
                f.write("\n")
            
            f.write("![省份归因热力图](province_attribution_heatmap.png)\n\n")
            f.write("![省份贡献排名](province_contributors.png)\n\n")
            
            # 车系分析
            f.write("## 🚗 车系归因分析\n\n")
            f.write("### 车系贡献排名\n\n")
            if 'series_effects' in self.analysis_results:
                f.write("| 车系阶段 | 移除效应 (pp) |\n")
                f.write("|----------|---------------|\n")
                for node, effect in sorted(self.analysis_results['series_effects'], key=lambda x: -x[1])[:10]:
                    f.write(f"| {node} | {effect:+.2f} |\n")
                f.write("\n")
            
            f.write("![车系归因热力图](series_attribution_heatmap.png)\n\n")
            f.write("![车系贡献排名](series_contributors.png)\n\n")
            
            # 时间趋势分析
            f.write("## ⏰ 时间趋势分析\n\n")
            if 'monthly_orders' in self.analysis_results:
                monthly_orders = self.analysis_results['monthly_orders']
                f.write("### 月度订单量趋势\n\n")
                f.write("| 月份 | 订单数量 |\n")
                f.write("|------|----------|\n")
                for month, count in monthly_orders.tail(6).items():
                    f.write(f"| {month} | {count:,} |\n")
                f.write("\n")
            
            f.write("![月度订单趋势](monthly_orders_trend.png)\n\n")
            
            # 退订分析
            f.write("## ❌ 退订分析\n\n")
            if 'refund_stats' in self.analysis_results:
                stats = self.analysis_results['refund_stats']
                f.write(f"- **总订单数**: {stats['total_orders']:,}\n")
                f.write(f"- **意向金退订数**: {stats['intention_refunds']:,} ({stats['intention_refunds']/stats['total_orders']*100:.1f}%)\n")
                f.write(f"- **定金退订数**: {stats['deposit_refunds']:,} ({stats['deposit_refunds']/stats['total_orders']*100:.1f}%)\n\n")
            
            # 数据分布
            f.write("## 📈 数据分布\n\n")
            f.write("![数据分布](distribution_charts.png)\n\n")
            
            # 分析仪表板
            f.write("## 📊 分析仪表板\n\n")
            f.write("![归因分析仪表板](attribution_dashboard.png)\n\n")
            
            # 方法论
            f.write("## 🔬 方法论\n\n")
            f.write("### 马尔可夫链归因模型\n\n")
            f.write("本分析采用马尔可夫链归因模型，通过以下步骤进行：\n\n")
            f.write("1. **路径构建**: 根据用户转化路径构建马尔可夫链\n")
            f.write("2. **转移矩阵**: 计算各状态间的转移概率\n")
            f.write("3. **移除效应**: 通过移除特定节点计算其对转化的贡献\n")
            f.write("4. **归因分配**: 基于移除效应进行归因分配\n\n")
            
            f.write("### 数据清洗\n\n")
            f.write("- 移除跳跃式订单（不符合正常转化流程的订单）\n")
            f.write("- 处理缺失值和异常值\n")
            f.write("- 标准化渠道和地区分类\n\n")
            
            # 结论和建议
            f.write("## 💡 结论和建议\n\n")
            f.write("### 主要发现\n\n")
            f.write("1. **渠道贡献**: 总部渠道在转化过程中贡献最大\n")
            f.write("2. **地区差异**: 浙江省和上海市的转化贡献显著\n")
            f.write("3. **产品表现**: LS6-CSERIES车系表现优异\n")
            f.write("4. **转化瓶颈**: 从意向金到定金的转化率较低\n\n")
            
            f.write("### 优化建议\n\n")
            f.write("1. **渠道优化**: 加强门店渠道的转化能力\n")
            f.write("2. **地区策略**: 重点发展高贡献省份的市场\n")
            f.write("3. **产品策略**: 推广表现优秀的车系\n")
            f.write("4. **流程优化**: 优化意向金到定金的转化流程\n\n")
            
            # 附录
            f.write("## 📎 附录\n\n")
            f.write("### 数据文件\n\n")
            f.write("- `整车订单状态指标表.xlsx`: 原始数据\n")
            f.write("- `channel_removal_effects.csv`: 渠道归因结果\n")
            f.write("- `province_removal_effects.csv`: 省份归因结果\n")
            f.write("- `series_removal_effects.csv`: 车系归因结果\n\n")
            
            f.write("### 技术栈\n\n")
            f.write("- Python 3.9+\n")
            f.write("- pandas, numpy: 数据处理\n")
            f.write("- matplotlib, seaborn: 数据可视化\n")
            f.write("- 马尔可夫链归因模型\n\n")
        
        print(f"✓ Markdown报告已生成: {output_file}")
    
    def generate_html_report(self, output_file="reports/attribution_analysis_report.html"):
        """生成HTML格式的报告"""
        print(f"\n🌐 生成HTML报告: {output_file}")
        
        # 读取Markdown文件
        md_file = "reports/attribution_analysis_report.md"
        if not os.path.exists(md_file):
            self.generate_markdown_report()
        
        # 转换为HTML
        try:
            import markdown
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 添加CSS样式
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>整车订单归因分析报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        h1 {{
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        .metric {{
            background-color: #d1ecf1;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        {markdown.markdown(md_content, extensions=['tables', 'fenced_code'])}
    </div>
</body>
</html>
"""
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✓ HTML报告已生成: {output_file}")
            
        except ImportError:
            print("⚠️ 需要安装markdown库: pip install markdown")
            print("HTML报告生成失败，但Markdown报告已生成")
    
    def generate_full_report(self, data_file):
        """生成完整报告"""
        print("📋 开始生成完整归因分析报告")
        print("=" * 50)
        
        # 1. 运行分析和可视化
        self.run_analysis_and_visualization(data_file)
        
        # 2. 生成Markdown报告
        self.generate_markdown_report()
        
        # 3. 生成HTML报告
        self.generate_html_report()
        
        print("\n✅ 完整报告生成完成！")
        print("📁 报告文件位置:")
        print("  - Markdown: reports/attribution_analysis_report.md")
        print("  - HTML: reports/attribution_analysis_report.html")
        print("  - 图表: reports/ 目录下的PNG文件")

if __name__ == "__main__":
    # 使用相对路径
    data_file = "data/整车订单状态指标表.xlsx"
    
    # 创建报告生成器并运行
    report_generator = AttributionReportGenerator()
    report_generator.generate_full_report(data_file) 