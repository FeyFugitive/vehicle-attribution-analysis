#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整车订单归因分析依赖安装脚本
"""

import subprocess
import sys
import os

def install_package(package):
    """安装单个包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package} 安装失败")
        return False

def main():
    """主安装函数"""
    print("🚀 开始安装整车订单归因分析依赖包")
    print("=" * 50)
    
    # 必需的依赖包
    required_packages = [
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "openpyxl>=3.0.0",
        "markdown>=3.3.0",
        "scipy>=1.7.0"
    ]
    
    # 可选的依赖包
    optional_packages = [
        "jupyter",
        "ipykernel",
        "plotly",
        "dash"
    ]
    
    print("📦 安装必需依赖包...")
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n必需依赖包安装完成: {success_count}/{len(required_packages)} 成功")
    
    if success_count < len(required_packages):
        print("⚠️  部分必需依赖包安装失败，可能影响功能")
    
    # 询问是否安装可选依赖
    print("\n📦 可选依赖包:")
    for package in optional_packages:
        print(f"  - {package}")
    
    response = input("\n是否安装可选依赖包? (y/n): ").lower().strip()
    if response in ['y', 'yes', '是']:
        print("\n安装可选依赖包...")
        for package in optional_packages:
            install_package(package)
    
    print("\n🎉 依赖安装完成！")
    print("\n📋 下一步:")
    print("1. 将数据文件放在 data/整车订单状态指标表.xlsx")
    print("2. 运行: python scripts/optimized_attribution_analysis.py")
    print("3. 查看结果: reports/ 和 data/ 目录")

if __name__ == "__main__":
    main() 