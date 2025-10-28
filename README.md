# AlphaFold3 批量处理工具包

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AlphaFold3](https://img.shields.io/badge/AlphaFold3-Compatible-orange.svg)](https://github.com/deepmind/alphafold3)

一个用于 AlphaFold3 批量预测和结果分析的完整工具包，支持从输入准备到结果分析的完整工作流程。

## 🚀 主要功能

- **📝 JSON 输入生成**: 自动生成符合 AlphaFold3 格式的输入文件
- **🔄 批量预测运行**: 支持并行运行多个预测任务
- **📊 结果分析**: 提取 pLDDT、PTM、iPTM 等质量指标
- **📈 综合分析**: 生成质量评估报告和可视化
- **🧬 序列变体生成**: 支持蛋白质序列变体批量生成

## 📁 项目结构

```
AF3_oversize_batch_selection/
├── scripts/                    # 主要脚本
│   ├── af3_json_generator.py  # JSON输入文件生成工具
│   ├── af3_runner.py          # 批量预测运行工具
│   ├── af3_analysis_tool.py    # 结果分析工具
│   ├── sequence_generation.py   # 序列变体生成
│   ├── AF3_MSA_Extraction.py   # MSA提取工具
│   └── run_*.sh               # Shell运行脚本
├── templates/                  # 模板文件
│   ├── input_template.json     # JSON输入模板
│   └── *.json                 # 示例输入文件
├── examples/                   # 示例和配置文件
├── docs/                       # 文档
└── README.md                   # 本文件
```

## 🛠️ 安装要求

### 系统要求
- Python 3.8+
- AlphaFold3 环境
- CUDA (可选，用于GPU加速)

### Python 依赖
```bash
pip install biopython
```

## 📖 快速开始

### 1. 生成输入文件

```bash
# 单序列输入
python scripts/af3_json_generator.py \
  --sequences "MKLLILTCLVAVALARPKHPIKHQGLPQEVLNENLLRFFVAPFPEVFGKEKVNEL" \
  --ids "protein_A" \
  --output input.json

# 多序列输入
python scripts/af3_json_generator.py \
  --sequences "SEQ1" "SEQ2" \
  --ids "chain_A" "chain_B" \
  --output complex.json

# 从FASTA文件生成
python scripts/af3_json_generator.py \
  --fasta protein.fasta \
  --output protein.json
```

### 2. 运行批量预测

```bash
# 基本批量运行
python scripts/af3_runner.py \
  --input_dir ./json_inputs \
  --output_dir ./results

# 指定并发数和GPU
python scripts/af3_runner.py \
  --input_dir ./json_inputs \
  --output_dir ./results \
  --max_concurrent 8 \
  --verbose
```

### 3. 分析预测结果

```bash
# 综合分析
python scripts/af3_analysis_tool.py \
  --input_dir ./results \
  --output_dir ./analysis

# 提取特定指标
python scripts/af3_analysis_tool.py \
  --input_dir ./results \
  --fields ptm iptm ranking_score \
  --verbose
```

## 🔧 详细使用说明

### JSON 输入生成工具

`af3_json_generator.py` 支持多种输入方式：

```bash
# 命令行序列输入
python scripts/af3_json_generator.py \
  --sequences "MKLLILTCLVAVALARPKHPIKHQGLPQEVLNENLLRFFVAPFPEVFGKEKVNEL" \
  --ids "protein_A" \
  --complex_id "my_protein" \
  --num_seeds 50 \
  --output input.json

# 从FASTA文件批量生成
python scripts/af3_json_generator.py \
  --batch_input ./fasta_files \
  --batch_output ./json_files

# 验证现有JSON文件
python scripts/af3_json_generator.py \
  --validate \
  --input_file existing.json
```

### 批量预测运行工具

`af3_runner.py` 提供智能的批量运行功能：

```bash
# 基本运行
python scripts/af3_runner.py \
  --input_dir ./json_inputs \
  --output_dir ./results \
  --max_concurrent 4

# 高级配置
python scripts/af3_runner.py \
  --input_dir ./json_inputs \
  --output_dir ./results \
  --af3_script /path/to/run_alphafold.py \
  --max_concurrent 8 \
  --max_template_date 2023-12-01 \
  --verbose
```

**特性：**
- 🔍 自动GPU检测和分配
- ⚡ 智能并发控制
- 📊 实时进度监控
- 📝 详细日志记录
- 🛡️ 错误处理和恢复

### 结果分析工具

`af3_analysis_tool.py` 提供全面的结果分析：

```bash
# 完整分析
python scripts/af3_analysis_tool.py \
  --input_dir ./results \
  --output_dir ./analysis

# 自定义字段提取
python scripts/af3_analysis_tool.py \
  --input_dir ./results \
  --fields ptm iptm ranking_score confidence \
  --verbose
```

**输出文件：**
- `plddt_scores.csv`: 局部结构质量 (pLDDT)
- `confidence_scores.csv`: 全局结构质量 (PTM/iPTM)
- `combined_scores.csv`: 综合分析结果
- `analysis_report.txt`: 详细分析报告

### 序列变体生成

`sequence_generation.py` 用于生成蛋白质序列变体：

```bash
python scripts/sequence_generation.py
```

生成：
- `variants.fasta`: 变体序列文件
- `variants_summary.csv`: 变体信息汇总

## 📊 质量评估标准

### pLDDT (局部结构质量)
- **> 90**: 高度可信
- **> 70**: 可信
- **> 50**: 低置信度
- **< 50**: 不可信

### PTM (全局结构质量)
- **> 0.7**: 高度可信
- **> 0.5**: 可能可靠
- **< 0.5**: 可能不准确

### 综合质量分类
- **High**: pLDDT > 70 且 PTM > 0.7
- **Medium**: pLDDT > 70 且 PTM > 0.5 或 pLDDT > 50 且 PTM > 0.7
- **Low**: 其他情况

## 🔄 完整工作流程示例

```bash
# 1. 准备输入文件
python scripts/af3_json_generator.py \
  --sequences "MKLLILTCLVAVALARPKHPIKHQGLPQEVLNENLLRFFVAPFPEVFGKEKVNEL" \
  --ids "protein_A" \
  --output input.json

# 2. 运行预测
python scripts/af3_runner.py \
  --input_dir ./json_inputs \
  --output_dir ./results \
  --max_concurrent 4

# 3. 分析结果
python scripts/af3_analysis_tool.py \
  --input_dir ./results \
  --output_dir ./analysis

# 4. 查看结果
cat analysis/combined_scores.csv
cat analysis/analysis_report.txt
```

## 🐛 故障排除

### 常见问题

1. **JSON格式错误**
   ```bash
   # 验证JSON文件
   python scripts/af3_json_generator.py --validate --input_file your_file.json
   ```

2. **GPU内存不足**
   ```bash
   # 减少并发数
   python scripts/af3_runner.py --max_concurrent 2
   ```

3. **依赖库缺失**
   ```bash
   pip install biopython
   ```

### 日志和调试

使用 `--verbose` 参数获取详细日志：

```bash
python scripts/af3_runner.py --verbose
python scripts/af3_analysis_tool.py --verbose
```

## 📚 文档

- [快速开始指南](docs/QUICK_START.md)
- [CIF格式支持](docs/CIF_SUPPORT_GUIDE.md)
- [PTM提取指南](docs/PTM_EXTRACTION_GUIDE.md)
- [脚本分析说明](docs/SCRIPT_ANALYSIS.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [DeepMind AlphaFold3](https://github.com/deepmind/alphafold3)
- [BioPython](https://biopython.org/)

---

**注意**: 使用本工具包需要有效的 AlphaFold3 许可证和环境配置。
