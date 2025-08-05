# 整车订单归因分析系统使用指南

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装Python 3.9+，然后安装必要的依赖：

```bash
pip3 install pandas numpy matplotlib seaborn openpyxl markdown
```

### 2. 数据准备

将您的Excel数据文件放在 `data/` 目录下，命名为 `整车订单状态指标表.xlsx`。

### 3. 运行分析

#### 方法一：运行完整报告生成
```bash
cd vehicle-attribution-analysis
python3 scripts/generate_report.py
```

#### 方法二：运行单独的分析脚本
```bash
# 综合分析
python3 scripts/comprehensive_attribution_analysis.py

# 渠道分析
python3 scripts/markov_channel.py

# 省份和车系分析
python3 scripts/markov_channel_prov_series.py
```

## 📊 分析内容

### 1. 数据探索
- 订单状态分布
- 车系分布
- 省份分布
- 渠道分布
- 转化漏斗分析

### 2. 马尔可夫链归因分析
- **渠道归因**: 分析总部(HQ)和门店(STORE)的贡献
- **省份归因**: 分析各省份的转化贡献
- **车系归因**: 分析各车系的转化贡献

### 3. 时间序列分析
- 月度订单量趋势
- 月度转化率趋势

### 4. 退订分析
- 意向金退订率
- 定金退订率
- Hold原因分析

## 📁 输出文件

### 分析结果
- `data/channel_removal_effects.csv`: 渠道归因结果
- `data/province_removal_effects.csv`: 省份归因结果
- `data/series_removal_effects.csv`: 车系归因结果

### 可视化图表
- `reports/funnel_chart.png`: 转化漏斗图
- `reports/channel_attribution_heatmap.png`: 渠道归因热力图
- `reports/province_attribution_heatmap.png`: 省份归因热力图
- `reports/series_attribution_heatmap.png`: 车系归因热力图
- `reports/distribution_charts.png`: 数据分布图
- `reports/attribution_dashboard.png`: 分析仪表板

### 报告文件
- `reports/attribution_analysis_report.md`: Markdown格式报告
- `reports/attribution_analysis_report.html`: HTML格式报告

## 🔬 方法论

### 马尔可夫链归因模型

1. **路径构建**: 根据用户转化路径构建马尔可夫链
   - 心愿单 → 意向金 → 定金 → 锁单 → 尾款 → 交付

2. **转移矩阵**: 计算各状态间的转移概率

3. **移除效应**: 通过移除特定节点计算其对转化的贡献
   - 移除效应 = 基准转化率 - 移除节点后的转化率

4. **归因分配**: 基于移除效应进行归因分配

### 数据清洗

- **方案B清洗**: 移除跳跃式订单（不符合正常转化流程的订单）
- 处理缺失值和异常值
- 标准化渠道和地区分类

## 📈 关键指标解读

### 移除效应 (Removal Effect)
- **正值**: 该节点对转化有正面贡献
- **负值**: 该节点对转化有负面影响
- **数值大小**: 表示贡献程度，数值越大贡献越大

### 转化漏斗
- **心愿单**: 用户创建心愿单的数量
- **意向金**: 支付意向金的订单数量
- **定金**: 支付定金的订单数量
- **锁单**: 完成锁单的订单数量
- **尾款**: 支付尾款的订单数量
- **交付**: 完成交付的订单数量

## 💡 分析洞察

### 主要发现示例
1. **渠道贡献**: 总部渠道在转化过程中贡献最大
2. **地区差异**: 浙江省和上海市的转化贡献显著
3. **产品表现**: LS6-CSERIES车系表现优异
4. **转化瓶颈**: 从意向金到定金的转化率较低

### 优化建议示例
1. **渠道优化**: 加强门店渠道的转化能力
2. **地区策略**: 重点发展高贡献省份的市场
3. **产品策略**: 推广表现优秀的车系
4. **流程优化**: 优化意向金到定金的转化流程

## 🔧 自定义配置

### 修改分析参数
在 `scripts/comprehensive_attribution_analysis.py` 中可以修改：

```python
# 修改Top N省份/车系数量
TOP_N = 8  # 改为您需要的数量

# 修改渠道分类规则
def categorize_channel(channel):
    if channel == "门店":
        return "STORE"
    elif channel == "总部":
        return "HQ"
    else:
        return "OTHER"
```

### 添加新的分析维度
可以在 `markov_attribution_analysis` 方法中添加新的分析维度：

```python
# 添加新的分类维度
self.df["new_category"] = self.df["some_column"].apply(your_categorization_function)
paths_new = build_paths(self.df, "new_category")
new_effects = removal_effect(paths_new, new_nodes)
```

## 🐛 常见问题

### Q: 数据文件路径错误
A: 确保Excel文件位于 `data/整车订单状态指标表.xlsx`

### Q: 依赖包安装失败
A: 尝试使用 `pip3 install --user package_name` 或检查Python版本

### Q: 图表显示中文乱码
A: 确保系统安装了中文字体，或修改 `visualization_report.py` 中的字体设置

### Q: 分析结果异常
A: 检查数据质量，确保关键字段（如时间字段）格式正确

## 📞 技术支持

如果遇到问题，请检查：
1. Python版本是否为3.9+
2. 所有依赖包是否正确安装
3. 数据文件格式是否正确
4. 文件路径是否正确

## 📚 参考资料

- [马尔可夫链归因模型](https://en.wikipedia.org/wiki/Markov_chain)
- [归因分析最佳实践](https://www.analyticsvidhya.com/blog/2018/01/attribution-modelling/)
- [Python数据分析](https://pandas.pydata.org/docs/) 