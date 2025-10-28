# AlphaFold3 批量处理 - 快速开始指南

## 🚀 5分钟快速上手

### 步骤 1: 准备输入文件

```bash
# 生成单个蛋白质的输入JSON
python scripts/af3_json_generator.py \
  --sequences "MKLLILTCLVAVALARPKHPIKHQGLPQEVLNENLLRFFVAPFPEVFGKEKVNEL" \
  --ids "protein_A" \
  --output my_protein.json
```

### 步骤 2: 运行预测

```bash
# 运行AlphaFold3预测
python scripts/af3_runner.py \
  --input_dir ./json_inputs \
  --output_dir ./results \
  --max_concurrent 4
```

### 步骤 3: 分析结果

```bash
# 分析预测质量
python scripts/af3_analysis_tool.py \
  --input_dir ./results \
  --output_dir ./analysis
```

### 步骤 4: 查看结果

```bash
# 查看综合评分
cat analysis/combined_scores.csv

# 查看详细报告
cat analysis/analysis_report.txt
```

## 📋 常用命令

### 批量处理多个序列

```bash
# 1. 从FASTA文件批量生成JSON
python scripts/af3_json_generator.py \
  --batch_input ./fasta_files \
  --batch_output ./json_files

# 2. 批量运行预测
python scripts/af3_runner.py \
  --input_dir ./json_files \
  --output_dir ./results

# 3. 批量分析结果
python scripts/af3_analysis_tool.py \
  --input_dir ./results \
  --output_dir ./analysis
```

### 高级配置

```bash
# 使用更多GPU和自定义参数
python scripts/af3_runner.py \
  --input_dir ./json_files \
  --output_dir ./results \
  --max_concurrent 8 \
  --max_template_date 2023-12-01 \
  --verbose

# 提取特定质量指标
python scripts/af3_analysis_tool.py \
  --input_dir ./results \
  --fields ptm iptm ranking_score confidence \
  --verbose
```

## 🔧 环境配置

### 必需依赖
```bash
pip install biopython
```

### AlphaFold3 环境
确保已正确安装和配置 AlphaFold3 环境。

## 📊 结果解读

### 质量指标含义
- **pLDDT**: 局部结构置信度 (0-100)
- **PTM**: 全局结构置信度 (0-1)
- **iPTM**: 界面置信度 (0-1)
- **Quality**: 综合质量评级 (High/Medium/Low)

### 质量阈值
- **High**: pLDDT > 70 且 PTM > 0.7
- **Medium**: pLDDT > 70 且 PTM > 0.5 或 pLDDT > 50 且 PTM > 0.7
- **Low**: 其他情况

## ❓ 常见问题

### Q: JSON文件格式错误怎么办？
```bash
# 验证JSON文件
python scripts/af3_json_generator.py --validate --input_file your_file.json
```

### Q: GPU内存不足怎么办？
```bash
# 减少并发数
python scripts/af3_runner.py --max_concurrent 2
```

### Q: 如何查看详细日志？
```bash
# 添加 --verbose 参数
python scripts/af3_runner.py --verbose
```

## 📞 获取帮助

- 查看完整文档: [README.md](README.md)
- 查看详细指南: [docs/](docs/)
- 提交问题: [GitHub Issues](https://github.com/RuijinHospitalVNAR/AF3_oversize_batch_selection/issues)