# CIF 格式支持指南

## ✨ 新功能

脚本现已支持 **PDB** 和 **CIF (mmCIF)** 两种格式的结构文件！

### 🎯 主要特性

1. **自动格式识别** - 根据文件扩展名自动选择合适的解析器
2. **CIF 优先** - 优先查找和处理 CIF 文件（AlphaFold3 默认输出格式）
3. **兼容性** - 完全向后兼容，仍支持 PDB 格式
4. **透明处理** - 用户无需手动指定格式

---

## 📁 支持的文件格式

| 格式 | 扩展名 | 解析器 | 优先级 |
|-----|-------|-------|-------|
| **mmCIF** | `.cif` | MMCIFParser | ⭐ 高（优先） |
| **PDB** | `.pdb` | PDBParser | ⭐ 中（备选） |

---

## 🚀 使用方法

### 基本用法（完全相同）

```bash
# 原始版本
python calc_af3_plddt_batch.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2/ \
  --output_csv plddt_summary.csv

# 改进版本
python calc_af3_plddt_batch_improved.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2/ \
  --output_csv plddt_summary.csv

# 查看详细日志（仅改进版）
python calc_af3_plddt_batch_improved.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2/ \
  --output_csv plddt_summary.csv \
  --verbose
```

### ⚠️ 常见错误

**错误示例**：重复输入路径
```bash
# ❌ 错误 - 不要重复输入路径
python calc_af3_plddt_batch_improved.py \
  --input_dir /path/to/results/ \
  /path/to/results/  # ← 这是多余的！

# ✅ 正确
python calc_af3_plddt_batch_improved.py \
  --input_dir /path/to/results/
```

---

## 🔍 文件查找逻辑

### 查找顺序

脚本会在每个子文件夹中按以下顺序查找结构文件：

```
1. 优先查找 .cif 文件
   └─ 如果找到 → 使用 MMCIFParser 解析
   
2. 如果没有 .cif，查找 .pdb 文件
   └─ 如果找到 → 使用 PDBParser 解析
   
3. 如果都没有 → 跳过该样本
```

### 示例目录结构

```
rxfp3__results_2/
├── sample_001/
│   ├── fold_model_0.cif      ← 会选择这个（CIF 优先）
│   └── fold_model_0.pdb
├── sample_002/
│   └── fold_model_0.cif      ← 只有 CIF，选择这个
├── sample_003/
│   └── fold_model_0.pdb      ← 只有 PDB，选择这个
└── sample_004/
    └── other_files.txt       ← 跳过（无结构文件）
```

---

## 📊 输出示例

### 原始版本输出

```
🧭 检测到 100 个预测结果文件夹。正在分析...
✅ sample_001: 85.23
✅ sample_002: 78.45
✅ sample_003: 92.10
⚠️ sample_004: 未找到结构文件 (PDB/CIF)

📊 已生成结果文件: plddt_summary.csv
共分析 3 个有效预测结果。
```

### 改进版本输出

```
🧭 检测到 100 个预测结果文件夹。正在分析...

[1/100] 处理: sample_001
  ✅ 平均 pLDDT: 85.23 (格式: .cif)
[2/100] 处理: sample_002
  ✅ 平均 pLDDT: 78.45 (格式: .cif)
[3/100] 处理: sample_003
  ✅ 平均 pLDDT: 92.10 (格式: .pdb)
[4/100] 处理: sample_004
  ⚠️  未找到结构文件 (PDB/CIF)

📊 已生成结果文件: plddt_summary.csv
✅ 成功分析: 3 个样本
⚠️  失败/跳过: 1 个样本
```

### CSV 输出格式（两个版本相同）

```csv
Sample,Average_pLDDT
sample_001,85.23
sample_002,78.45
sample_003,92.10
```

---

## 🔧 技术细节

### CIF vs PDB 解析

```python
# 自动选择解析器
if structure_file.endswith('.cif'):
    parser = MMCIFParser(QUIET=True)  # CIF 格式
else:
    parser = PDBParser(QUIET=True)    # PDB 格式

structure = parser.get_structure("AF3_model", structure_file)
```

### pLDDT 提取（两种格式相同）

无论是 PDB 还是 CIF 格式，pLDDT 值都存储在 B-factor 字段中：

```python
for residue in chain:
    ca_atom = residue["CA"]
    plddt = ca_atom.bfactor  # B-factor 即 pLDDT
```

---

## 📦 依赖要求

```bash
# 必需：Biopython（用于解析 PDB 和 CIF 文件）
pip install biopython

# 版本要求
# Biopython >= 1.79（推荐最新版本）
```

### 验证安装

```bash
python -c "from Bio.PDB import PDBParser, MMCIFParser; print('✅ Biopython 已安装')"
```

---

## 🆚 两个版本的区别

| 特性 | 原始版本 | 改进版本 |
|-----|---------|---------|
| CIF 支持 | ✅ 有 | ✅ 有 |
| PDB 支持 | ✅ 有 | ✅ 有 |
| 自动格式识别 | ✅ 有 | ✅ 有 |
| 错误处理 | ⚠️ 基本 | ✅ 完善 |
| 进度显示 | ⚠️ 简单 | ✅ 详细 |
| 格式提示 | ❌ 无 | ✅ 有 |
| 日志系统 | ❌ 无 | ✅ 有 |
| 统计信息 | ⚠️ 基本 | ✅ 详细 |

---

## 💡 最佳实践

### 1. AlphaFold3 输出结构

AlphaFold3 默认输出 **CIF** 格式，这是推荐的格式：

- ✅ CIF 格式更现代，支持更多信息
- ✅ 文件更小，解析更快
- ✅ 是 PDB 数据库的标准格式

### 2. 选择合适的版本

```bash
# 快速测试 → 原始版本
python calc_af3_plddt_batch.py --input_dir /path/to/results/

# 生产环境/大规模处理 → 改进版本
python calc_af3_plddt_batch_improved.py \
  --input_dir /path/to/results/ \
  --verbose  # 启用详细日志
```

### 3. 调试问题

如果遇到问题，使用改进版本的详细日志：

```bash
python calc_af3_plddt_batch_improved.py \
  --input_dir /path/to/results/ \
  --verbose
```

这会显示：
- 每个文件使用的解析器
- CA 原子数量
- 详细的错误信息

---

## ❓ 常见问题

### Q1: 脚本会选择哪个文件？

**A**: 按以下优先级：
1. **.cif** 文件优先
2. 如果有多个 .cif，选择排序后的第一个
3. 如果没有 .cif，选择 .pdb
4. 如果都没有，跳过该样本

### Q2: 如果同时有 PDB 和 CIF 怎么办？

**A**: 优先使用 **CIF** 文件，PDB 文件会被忽略。

### Q3: pLDDT 计算结果会不同吗？

**A**: 不会。无论使用 PDB 还是 CIF 格式，pLDDT 值完全相同（都来自 B-factor）。

### Q4: 原始版本需要更新代码吗？

**A**: 不需要。两个版本都已更新，直接使用即可。

### Q5: 如何强制使用 PDB 格式？

**A**: 删除或重命名 .cif 文件，脚本会自动使用 .pdb 文件。

---

## 🔄 升级说明

### 从旧版本升级

如果你之前使用的是只支持 PDB 的版本：

1. ✅ **无需修改代码** - 直接使用新版本
2. ✅ **完全兼容** - 所有原有 PDB 文件仍可正常处理
3. ✅ **自动支持 CIF** - 新的 CIF 文件会自动识别
4. ✅ **命令行不变** - 使用方式完全相同

---

## 📝 更新日志

### v2.0 (支持 CIF)

- ✅ 添加 MMCIFParser 支持
- ✅ 自动格式识别
- ✅ CIF 格式优先
- ✅ 更新文档和错误提示
- ✅ 改进版显示文件格式信息

### v1.0 (原始版本)

- ✅ 基本 PDB 支持
- ✅ 批量处理
- ✅ CSV 输出

---

## 📧 技术支持

如果遇到问题：

1. 检查 Biopython 是否正确安装
2. 确认文件格式正确（.pdb 或 .cif）
3. 使用 `--verbose` 查看详细日志
4. 查看错误提示信息

---

**祝您使用愉快！** 🎉

