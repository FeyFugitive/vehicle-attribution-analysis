#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整车订单归因分析一键运行脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_data_file():
    """检查数据文件是否存在"""
    data_file = "data/整车订单状态指标表.xlsx"
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        print("请将Excel数据文件放在 data/整车订单状态指标表.xlsx")
        return False
    return True

def check_dependencies():
    """检查依赖包是否已安装"""
    required_packages = ["pandas", "numpy", "matplotlib", "seaborn", "openpyxl", "scipy"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: python install_dependencies.py")
        return False
    
    return True

def run_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    try:
        result = subprocess.run([sys.executable, "test_markov.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 单元测试通过")
            return True
        else:
            print("❌ 单元测试失败")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False

def run_analysis():
    """运行分析"""
    print("🚀 开始整车订单归因分析...")
    try:
        # 运行优化版本的分析
        result = subprocess.run([
            sys.executable, "scripts/optimized_attribution_analysis.py"
        ])
        
        if result.returncode == 0:
            print("✅ 分析完成！")
            return True
        else:
            print("❌ 分析失败")
            return False
    except Exception as e:
        print(f"❌ 运行分析时出错: {e}")
        return False

def show_results():
    """显示结果文件"""
    print("\n📊 分析结果:")
    
    # 检查CSV结果文件
    csv_files = [
        "data/channel_removal_effects.csv",
        "data/province_removal_effects.csv", 
        "data/series_removal_effects.csv",
        "data/data_quality_report.csv"
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"✅ {csv_file}")
        else:
            print(f"❌ {csv_file} (未生成)")
    
    # 检查报告文件
    report_files = [
        "reports/attribution_analysis_report.html",
        "reports/attribution_analysis_report.md"
    ]
    
    for report_file in report_files:
        if os.path.exists(report_file):
            print(f"✅ {report_file}")
        else:
            print(f"❌ {report_file} (未生成)")

def main():
    """主函数"""
    print("🎯 整车订单归因分析 - 一键运行")
    print("=" * 50)
    
    # 1. 检查数据文件
    print("📁 检查数据文件...")
    if not check_data_file():
        return
    
    # 2. 检查依赖包
    print("📦 检查依赖包...")
    if not check_dependencies():
        return
    
    # 3. 运行测试
    print("🧪 运行测试...")
    if not run_tests():
        print("⚠️  测试失败，但继续运行分析...")
    
    # 4. 运行分析
    print("🚀 运行分析...")
    if not run_analysis():
        return
    
    # 5. 显示结果
    show_results()
    
    print("\n🎉 分析完成！")
    print("\n📋 查看结果:")
    print("- CSV结果文件: data/ 目录")
    print("- 可视化报告: reports/ 目录")
    print("- 详细日志: 查看终端输出")

if __name__ == "__main__":
    main() 