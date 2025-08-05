# 整车订单归因分析系统 - 优化版本

基于马尔可夫链归因模型的整车订单转化分析系统，提供全面的渠道、省份、车系归因分析。

## 🚀 新版本改进

### 1. 路径构建逻辑优化
```python
# 优化前
path.append(f"{stage}_{category}")

# 优化后（防止特殊字符导致解析错误）
path.append(f"{stage}||{category}")
```

### 2. 空值处理增强
```python
# 在build_paths函数中添加
if pd.isna(cat):
    cat = "UNKNOWN"
```

### 3. 性能优化
```python
# 大型数据集使用稀疏矩阵
from scipy.sparse import csr_matrix
T = csr_matrix((n, n), dtype=np.float32)
```

### 4. 异常处理强化
```python
# 在removal_effect函数中添加
try:
    N = np.linalg.inv(np.eye(len(Q)) - Q)
except np.linalg.LinAlgError:
    # 处理奇异矩阵情况
    return 0
```

### 5. 配置管理
```python
# config.py
ANALYSIS_CONFIG = {
    'TOP_PROVINCES': 8,
    'TOP_SERIES': 8,
    'CHANNEL_MAPPING': {
        "门店": "STORE",
        "总部": "HQ"
    }
}
```

### 6. 单元测试
```python
# test_markov.py
def test_removal_effect():
    test_paths = [["Start", "A", "Conversion"]]
    test_nodes = ["A"]
    effects = removal_effect(test_paths, test_nodes)
    assert effects[0][1] == 100.0
```

### 7. 并行处理
```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor() as executor:
    results = executor.map(removal_effect, [paths], [nodes])
```

## 🎯 项目概述

本项目基于整车订单数据，使用马尔可夫链归因模型分析各渠道、省份、车系对转化的贡献度，帮助企业优化营销策略和资源配置。

## 📊 分析维度

- **渠道归因**: 分析总部(HQ)和门店(STORE)的转化贡献
- **省份归因**: 分析各省份的转化贡献
- **车系归因**: 分析各车系的转化贡献
- **时间趋势**: 分析订单量和转化率的时间变化
- **退订分析**: 分析退订原因和趋势

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
python install_dependencies.py

# 或手动安装
pip install pandas numpy matplotlib seaborn openpyxl markdown scipy
```

### 2. 数据准备

将Excel数据文件放在 `data/` 目录下，命名为 `整车订单状态指标表.xlsx`。

### 3. 运行分析

```bash
# 一键运行（推荐）
python run_analysis.py

# 或运行优化版本分析
python scripts/optimized_attribution_analysis.py

# 运行单元测试
python test_markov.py
```

## 📁 项目结构

```
vehicle-attribution-analysis/
├── config.py                           # 配置文件
├── utils.py                            # 工具函数
├── test_markov.py                      # 单元测试
├── install_dependencies.py             # 依赖安装脚本
├── run_analysis.py                     # 一键运行脚本
│
├── scripts/                            # 分析脚本
│   ├── optimized_attribution_analysis.py  # 优化版本综合分析
│   ├── comprehensive_attribution_analysis.py  # 原版本
│   ├── markov_channel.py              # 渠道分析
│   ├── markov_channel_prov_series.py # 省份车系分析
│   ├── visualization_report.py        # 可视化生成
│   └── generate_report.py             # 报告生成
│
├── data/                              # 数据文件
│   ├── 整车订单状态指标表.xlsx        # 原始数据
│   ├── channel_removal_effects.csv    # 渠道归因结果
│   ├── province_removal_effects.csv   # 省份归因结果
│   ├── series_removal_effects.csv     # 车系归因结果
│   └── data_quality_report.csv        # 数据质量报告
│
├── reports/                           # 输出报告
│   ├── attribution_analysis_report.md    # Markdown报告
│   ├── attribution_analysis_report.html  # HTML报告
│   ├── funnel_chart.png              # 转化漏斗图
│   ├── channel_attribution_heatmap.png  # 渠道归因热力图
│   ├── province_attribution_heatmap.png # 省份归因热力图
│   ├── series_attribution_heatmap.png   # 车系归因热力图
│   ├── distribution_charts.png        # 数据分布图
│   └── attribution_dashboard.png      # 分析仪表板
│
├── README.md                          # 项目说明
├── README_OPTIMIZED.md                # 优化版本说明
└── USAGE_GUIDE.md                    # 使用指南
```

## 🔧 配置说明

### 分析配置 (config.py)

```python
ANALYSIS_CONFIG = {
    'TOP_PROVINCES': 8,              # Top N省份数量
    'TOP_SERIES': 8,                 # Top N车系数量
    'CHANNEL_MAPPING': {             # 渠道映射
        "门店": "STORE",
        "总部": "HQ",
        "其他": "OTHER"
    },
    'PATH_SEPARATOR': '||',          # 路径分隔符
    'UNKNOWN_CATEGORY': 'UNKNOWN',   # 未知类别默认值
    'MIN_PATH_LENGTH': 2,            # 最小路径长度
    'MAX_PATH_LENGTH': 10            # 最大路径长度
}
```

### 数据处理配置

```python
DATA_CONFIG = {
    'CLEAN_JUMP_ORDERS': True,       # 是否清洗跳跃式订单
    'HANDLE_MISSING_VALUES': True,   # 是否处理缺失值
    'NORMALIZE_CATEGORIES': True,    # 是否标准化分类
    'USE_SPARSE_MATRIX': True,       # 是否使用稀疏矩阵
    'CHUNK_SIZE': 10000              # 大数据集分块处理
}
```

### 错误处理配置

```python
ERROR_CONFIG = {
    'MAX_ITERATIONS': 1000,          # 最大迭代次数
    'TOLERANCE': 1e-6,               # 容差
    'SINGULAR_MATRIX_HANDLING': 'skip',  # 奇异矩阵处理方式
    'LOG_LEVEL': 'INFO'              # 日志级别
}
```

## 📈 分析结果示例

### 关键发现
- **渠道贡献最大**: Deposit||HQ，移除效应为 +0.62 pp
- **省份贡献最大**: Deposit||浙江省，移除效应为 +0.22 pp
- **车系贡献最大**: Deposit||LS6-CSERIES，移除效应为 +0.65 pp

### 转化漏斗
- 心愿单: 5,156 (100.0%)
- 意向金: 16,133 (312.9%)
- 定金: 481 (9.3%)
- 锁单: 445 (8.6%)
- 尾款: 333 (6.5%)
- 交付: 333 (6.5%)

## 🔬 方法论

### 马尔可夫链归因模型

1. **路径构建**: 根据用户转化路径构建马尔可夫链
2. **转移矩阵**: 计算各状态间的转移概率
3. **移除效应**: 通过移除特定节点计算其对转化的贡献
4. **归因分配**: 基于移除效应进行归因分配

### 数据清洗

- **方案B清洗**: 移除跳跃式订单（不符合正常转化流程的订单）
- 处理缺失值和异常值
- 标准化渠道和地区分类

## 🚀 性能优化

### 1. 稀疏矩阵支持
对于大型数据集，自动使用稀疏矩阵提高内存效率：

```python
if DATA_CONFIG['USE_SPARSE_MATRIX']:
    T = csr_matrix((data, (row_indices, col_indices)), shape=(n, n))
```

### 2. 并行处理
大数据集自动启用并行计算：

```python
if len(self.df) > 10000:
    self.parallel_analysis()
```

### 3. 异常处理
增强的异常处理机制：

```python
try:
    N = safe_matrix_inverse(np.eye(len(Q)) - Q)
except np.linalg.LinAlgError:
    # 处理奇异矩阵
    return []
```

## 📊 输出文件说明

### 分析结果CSV文件
- `channel_removal_effects.csv`: 渠道归因结果
- `province_removal_effects.csv`: 省份归因结果
- `series_removal_effects.csv`: 车系归因结果
- `data_quality_report.csv`: 数据质量报告

### 可视化图表
- `funnel_chart.png`: 转化漏斗图
- `channel_attribution_heatmap.png`: 渠道归因热力图
- `province_attribution_heatmap.png`: 省份归因热力图
- `series_attribution_heatmap.png`: 车系归因热力图
- `distribution_charts.png`: 数据分布图
- `attribution_dashboard.png`: 分析仪表板

### 报告文件
- `attribution_analysis_report.md`: Markdown格式报告
- `attribution_analysis_report.html`: HTML格式报告

## 💡 主要功能

### 1. 数据探索
- 订单状态分布分析
- 车系、省份、渠道分布分析
- 转化漏斗分析
- 数据质量验证

### 2. 归因分析
- 马尔可夫链归因模型
- 渠道归因分析
- 省份归因分析
- 车系归因分析
- 并行计算支持

### 3. 时间序列分析
- 月度订单量趋势
- 月度转化率趋势

### 4. 退订分析
- 意向金退订率分析
- 定金退订率分析
- Hold原因分析

### 5. 可视化报告
- 自动生成多种图表
- Markdown和HTML格式报告
- 交互式仪表板

## 🔧 自定义配置

### 修改分析参数
在 `config.py` 中可以修改：
- Top N省份/车系数量
- 渠道分类规则
- 时间范围设置
- 路径分隔符

### 添加新的分析维度
可以轻松添加新的分析维度，如：
- 用户类型分析
- 门店级别分析
- 产品配置分析

## 📚 技术栈

- **Python 3.9+**: 主要编程语言
- **pandas**: 数据处理和分析
- **numpy**: 数值计算
- **scipy**: 科学计算（稀疏矩阵）
- **matplotlib**: 数据可视化
- **seaborn**: 统计图表
- **openpyxl**: Excel文件处理
- **markdown**: 报告生成

## 🧪 测试

运行单元测试：

```bash
python test_markov.py
```

测试覆盖：
- 路径构建功能
- 移除效应计算
- 矩阵求逆
- 数据质量验证
- 边界情况处理

## 🐛 常见问题

### Q: 数据文件路径错误
A: 确保Excel文件位于 `data/整车订单状态指标表.xlsx`

### Q: 依赖包安装失败
A: 运行 `python install_dependencies.py` 或检查Python版本

### Q: 图表显示中文乱码
A: 确保系统安装了中文字体，或修改字体设置

### Q: 分析结果异常
A: 检查数据质量，确保关键字段格式正确

### Q: 内存不足
A: 启用稀疏矩阵模式或减少数据量

### Q: 奇异矩阵错误
A: 检查数据质量，或修改 `ERROR_CONFIG['SINGULAR_MATRIX_HANDLING']`

## 📞 技术支持

如果遇到问题，请检查：
1. Python版本是否为3.9+
2. 所有依赖包是否正确安装
3. 数据文件格式是否正确
4. 文件路径是否正确
5. 运行单元测试验证功能

## 📖 使用指南

详细的使用指南请参考 [USAGE_GUIDE.md](USAGE_GUIDE.md)

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

---

**注意**: 本项目仅用于学习和研究目的，请确保遵守相关数据隐私法规。 