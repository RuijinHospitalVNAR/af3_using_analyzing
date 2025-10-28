# AF3 PTM 值提取脚本使用指南

## 📖 概述

这是一个批量提取 AlphaFold3 预测结果中置信度指标的工具，主要提取 `summary_confidences.json` 文件中的 **PTM**、**iPTM** 等值。

---

## 🚀 快速开始

### 基本用法

```bash
# 原始版本（只提取 PTM）
python calc_af3_ptm_batch.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2/ \
  --output_csv ptm_summary.csv

# 改进版本（只提取 PTM）
python calc_af3_ptm_batch_improved.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2/
```

### 高级用法（改进版专属）

```bash
# 提取 PTM 和 iPTM
python calc_af3_ptm_batch_improved.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2/ \
  --fields ptm iptm

# 提取多个指标
python calc_af3_ptm_batch_improved.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2/ \
  --fields ptm iptm ranking_score \
  --output_csv confidence_scores.csv

# 启用详细日志
python calc_af3_ptm_batch_improved.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2/ \
  --fields ptm iptm \
  --verbose
```

---

## 📋 参数说明

### 原始版本

| 参数 | 必需？ | 默认值 | 说明 |
|-----|-------|-------|------|
| `--input_dir` | ✅ 必需 | - | AF3 结果主目录 |
| `--output_csv` | ⬜ 可选 | `ptm_summary.csv` | 输出 CSV 文件路径 |

### 改进版本

| 参数 | 必需？ | 默认值 | 说明 |
|-----|-------|-------|------|
| `--input_dir` | ✅ 必需 | - | AF3 结果主目录 |
| `--output_csv` | ⬜ 可选 | `confidence_summary.csv` | 输出 CSV 文件路径 |
| `--fields` | ⬜ 可选 | `ptm` | 要提取的字段（可多个） |
| `--verbose` / `-v` | ⬜ 可选 | 关闭 | 显示详细日志 |

---

## 📁 目录结构要求

脚本期望的目录结构：

```
input_dir/
├── sample_001/
│   └── summary_confidences.json
├── sample_002/
│   └── summary_confidences.json
└── sample_003/
    └── summary_confidences.json
```

### summary_confidences.json 示例

```json
{
  "ptm": 0.59,
  "iptm": 0.45,
  "ranking_score": 0.52,
  "fraction_disordered": 0.1,
  "has_clash": false
}
```

---

## 📊 输出示例

### 控制台输出

#### 原始版本
```
🧭 检测到 3 个预测结果文件夹。正在分析...
✅ sample_001: PTM = 0.5900
✅ sample_002: PTM = 0.7234
✅ sample_003: PTM = 0.4156

📊 已生成结果文件: ptm_summary.csv
共提取 3 个有效 PTM 值。
```

#### 改进版本（单字段）
```
🧭 检测到 3 个预测结果文件夹。正在分析...
📋 提取字段: ptm

[1/3] 处理: sample_001
  ✅ ptm=0.5900
[2/3] 处理: sample_002
  ✅ ptm=0.7234
[3/3] 处理: sample_003
  ✅ ptm=0.4156

📊 已生成结果文件: confidence_summary.csv
✅ 成功提取: 3 个样本
```

#### 改进版本（多字段）
```
🧭 检测到 3 个预测结果文件夹。正在分析...
📋 提取字段: ptm, iptm, ranking_score

[1/3] 处理: sample_001
  ✅ ptm=0.5900, iptm=0.4500, ranking_score=0.5200
[2/3] 处理: sample_002
  ✅ ptm=0.7234, iptm=0.6800, ranking_score=0.7000
[3/3] 处理: sample_003
  ✅ ptm=0.4156, iptm=0.3900, ranking_score=0.4000

📊 已生成结果文件: confidence_scores.csv
✅ 成功提取: 3 个样本
```

### CSV 输出格式

#### 单字段（PTM）
```csv
Sample,PTM
sample_001,0.59
sample_002,0.7234
sample_003,0.4156
```

#### 多字段（PTM + iPTM + Ranking Score）
```csv
Sample,PTM,IPTM,RANKING_SCORE
sample_001,0.59,0.45,0.52
sample_002,0.7234,0.68,0.70
sample_003,0.4156,0.39,0.40
```

---

## 🔍 可提取的字段

AlphaFold3 的 `summary_confidences.json` 通常包含以下字段：

| 字段名 | 说明 | 推荐提取 |
|-------|------|---------|
| `ptm` | Predicted TM-score（预测 TM 分数） | ⭐ 推荐 |
| `iptm` | Interface PTM（界面 PTM，用于复合物） | ⭐ 推荐 |
| `ranking_score` | 排序分数（综合评分） | ⭐ 推荐 |
| `fraction_disordered` | 无序区域比例 | ⬜ 可选 |
| `has_clash` | 是否有冲突 | ⬜ 可选 |

### 使用示例

```bash
# 只提取 PTM
python calc_af3_ptm_batch_improved.py \
  --input_dir /path/to/results/ \
  --fields ptm

# 提取 PTM 和 iPTM（推荐用于蛋白复合物）
python calc_af3_ptm_batch_improved.py \
  --input_dir /path/to/results/ \
  --fields ptm iptm

# 提取所有主要指标
python calc_af3_ptm_batch_improved.py \
  --input_dir /path/to/results/ \
  --fields ptm iptm ranking_score fraction_disordered
```

---

## 🆚 两个版本对比

| 特性 | 原始版本 | 改进版本 |
|-----|---------|---------|
| PTM 提取 | ✅ | ✅ |
| 多字段提取 | ❌ | ✅ ⭐ |
| 错误处理 | ⚠️ 基本 | ✅ 完善 |
| 进度显示 | ⚠️ 简单 | ✅ 详细 |
| 日志系统 | ❌ | ✅ |
| 统计信息 | ⚠️ 基本 | ✅ 详细 |
| 自定义字段 | ❌ | ✅ ⭐ |

---

## 💡 使用场景

### 场景 1: 快速提取 PTM
```bash
# 使用原始版本
python calc_af3_ptm_batch.py \
  --input_dir /path/to/results/
```

### 场景 2: 分析蛋白复合物（PTM + iPTM）
```bash
# 使用改进版本
python calc_af3_ptm_batch_improved.py \
  --input_dir /path/to/results/ \
  --fields ptm iptm \
  --output_csv complex_scores.csv
```

### 场景 3: 完整置信度分析
```bash
# 提取所有主要指标
python calc_af3_ptm_batch_improved.py \
  --input_dir /path/to/results/ \
  --fields ptm iptm ranking_score \
  --output_csv full_confidence.csv \
  --verbose
```

### 场景 4: 大规模批处理
```bash
# 处理 1000+ 个样本
python calc_af3_ptm_batch_improved.py \
  --input_dir /path/to/large_results/ \
  --fields ptm iptm ranking_score \
  --output_csv batch_results.csv
```

---

## 📈 与 pLDDT 脚本配合使用

您可以同时运行两个脚本来获得完整的质量评估：

```bash
# 1. 提取 pLDDT 值（局部质量）
python calc_af3_plddt_batch_improved.py \
  --input_dir /path/to/results/ \
  --output_csv plddt_scores.csv

# 2. 提取 PTM/iPTM 值（全局质量）
python calc_af3_ptm_batch_improved.py \
  --input_dir /path/to/results/ \
  --fields ptm iptm \
  --output_csv ptm_scores.csv
```

然后合并 CSV 文件进行综合分析：

```python
import pandas as pd

# 读取两个 CSV 文件
plddt_df = pd.read_csv('plddt_scores.csv')
ptm_df = pd.read_csv('ptm_scores.csv')

# 合并数据
merged_df = pd.merge(plddt_df, ptm_df, on='Sample')

# 查看综合结果
print(merged_df)

# 输出:
#        Sample  Average_pLDDT    PTM   IPTM
# 0  sample_001          85.23  0.590  0.450
# 1  sample_002          78.45  0.723  0.680
# 2  sample_003          92.10  0.416  0.390
```

---

## ⚠️ 常见问题

### Q1: 如果某个样本缺少 summary_confidences.json 怎么办？

**A**: 脚本会跳过该样本并显示警告：
```
⚠️  sample_004: 未找到 summary_confidences.json 文件
```

### Q2: 如果 JSON 文件中没有某个字段怎么办？

**A**: 改进版本会在 CSV 中将该值设为空（None），原始版本会跳过该样本。

### Q3: PTM 和 pLDDT 有什么区别？

**A**: 
- **pLDDT** (per-residue confidence): 每个残基的局部置信度，范围 0-100
- **PTM** (predicted TM-score): 全局结构置信度，范围 0-1
- **iPTM**: 界面置信度，用于评估蛋白复合物的结合界面

### Q4: 什么是 iPTM？

**A**: iPTM (interface predicted TM-score) 专门用于评估蛋白质复合物中不同链之间的界面质量。如果您预测的是单链蛋白，可能没有 iPTM 值。

### Q5: 如何判断预测质量好坏？

**A**: 一般经验：
- **PTM > 0.5**: 预测结构可能可靠
- **PTM > 0.7**: 预测结构高度可信
- **PTM < 0.5**: 预测结构可能不准确

同时结合 pLDDT 值：
- **pLDDT > 70**: 该区域结构可信
- **pLDDT > 90**: 该区域结构高度可信

---

## 🔧 技术细节

### JSON 数据结构

`summary_confidences.json` 文件示例：

```json
{
  "ptm": 0.5900,
  "iptm": 0.4500,
  "ranking_score": 0.5200,
  "fraction_disordered": 0.1234,
  "has_clash": false,
  "chain_pair_iptm": {
    "A_B": 0.4500
  },
  "chain_ptm": {
    "A": 0.6200,
    "B": 0.5600
  }
}
```

### 提取逻辑

```python
# 原始版本：只提取 PTM
with open(json_file, 'r') as f:
    data = json.load(f)
    ptm = data.get('ptm', None)

# 改进版本：提取多个字段
with open(json_file, 'r') as f:
    data = json.load(f)
    results = {
        'ptm': data.get('ptm'),
        'iptm': data.get('iptm'),
        'ranking_score': data.get('ranking_score')
    }
```

---

## 📦 依赖要求

```bash
# 无需额外依赖，只需 Python 标准库
# Python 3.6+
```

### 验证环境

```bash
python --version  # 确保 Python >= 3.6
```

---

## 🎯 版本选择建议

| 场景 | 推荐版本 |
|-----|---------|
| ⚡ 快速提取 PTM | `calc_af3_ptm_batch.py` (原始版) |
| 🚀 提取多个指标 | `calc_af3_ptm_batch_improved.py` (改进版) ⭐ |
| 📊 大规模处理 | `calc_af3_ptm_batch_improved.py` (改进版) ⭐ |
| 🔍 需要调试 | `calc_af3_ptm_batch_improved.py` + `--verbose` ⭐ |
| 🧪 蛋白复合物分析 | `calc_af3_ptm_batch_improved.py` + `--fields ptm iptm` ⭐ |

---

## 📝 脚本组合使用示例

创建一个完整的分析流程：

```bash
#!/bin/bash
# AF3 结果完整分析脚本

RESULTS_DIR="/mnt/share/chufan/CY_col/rxfp3__results_2"
OUTPUT_DIR="/mnt/share/chufan/CY_col/analysis"

mkdir -p $OUTPUT_DIR

echo "🧬 开始分析 AlphaFold3 预测结果..."

# 1. 提取 pLDDT 值（局部质量）
echo "📊 提取 pLDDT 值..."
python calc_af3_plddt_batch_improved.py \
  --input_dir $RESULTS_DIR \
  --output_csv $OUTPUT_DIR/plddt_scores.csv

# 2. 提取 PTM/iPTM 值（全局质量）
echo "📊 提取 PTM/iPTM 值..."
python calc_af3_ptm_batch_improved.py \
  --input_dir $RESULTS_DIR \
  --fields ptm iptm ranking_score \
  --output_csv $OUTPUT_DIR/confidence_scores.csv

echo "✅ 分析完成！"
echo "结果文件:"
echo "  - $OUTPUT_DIR/plddt_scores.csv"
echo "  - $OUTPUT_DIR/confidence_scores.csv"
```

---

## 🎉 总结

这个工具可以快速批量提取 AlphaFold3 预测结果的置信度指标，帮助您：

1. ✅ 快速评估预测质量
2. ✅ 筛选高质量预测结果
3. ✅ 进行大规模批量分析
4. ✅ 结合 pLDDT 进行综合评估

**推荐使用改进版本** 以获得最佳体验！

---

*最后更新: 2025-10-13*

