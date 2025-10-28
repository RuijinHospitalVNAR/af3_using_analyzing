#!/bin/bash
################################################################################
# AF3 预测结果完整质量分析脚本
################################################################################
# 
# 功能：
#   1. 提取 pLDDT 值（局部结构质量）
#   2. 提取 PTM/iPTM 值（全局结构质量）
#   3. 合并所有指标到一个文件
#   4. 生成质量分类
#
# 使用方法：
#   bash run_full_analysis.sh /path/to/af3_results /path/to/output_dir
#
# 示例：
#   bash run_full_analysis.sh \
#     /mnt/share/chufan/CY_col/rxfp3__results_2 \
#     /mnt/share/chufan/CY_col/analysis
#
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数检查
if [ $# -lt 1 ]; then
    echo -e "${RED}错误: 缺少参数${NC}"
    echo "使用方法: $0 <AF3_RESULTS_DIR> [OUTPUT_DIR]"
    echo ""
    echo "示例:"
    echo "  $0 /mnt/share/chufan/CY_col/rxfp3__results_2"
    echo "  $0 /mnt/share/chufan/CY_col/rxfp3__results_2 /output/dir"
    exit 1
fi

RESULTS_DIR="$1"
OUTPUT_DIR="${2:-./af3_analysis_output}"

# 检查输入目录是否存在
if [ ! -d "$RESULTS_DIR" ]; then
    echo -e "${RED}错误: 输入目录不存在: $RESULTS_DIR${NC}"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    AlphaFold3 预测结果质量分析${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}输入目录:${NC} $RESULTS_DIR"
echo -e "${GREEN}输出目录:${NC} $OUTPUT_DIR"
echo ""

# ============================================================================
# 步骤 1: 提取 pLDDT 值
# ============================================================================
echo -e "${YELLOW}[1/4] 提取 pLDDT 值（局部结构质量）...${NC}"
python calc_af3_plddt_batch_improved.py \
  --input_dir "$RESULTS_DIR" \
  --output_csv "$OUTPUT_DIR/plddt_scores.csv"

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: pLDDT 提取失败${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 步骤 2: 提取 PTM/iPTM 值
# ============================================================================
echo -e "${YELLOW}[2/4] 提取 PTM/iPTM 值（全局结构质量）...${NC}"
python calc_af3_ptm_batch_improved.py \
  --input_dir "$RESULTS_DIR" \
  --fields ptm iptm ranking_score \
  --output_csv "$OUTPUT_DIR/confidence_scores.csv"

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: PTM 提取失败${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 步骤 3: 合并数据
# ============================================================================
echo -e "${YELLOW}[3/4] 合并所有指标...${NC}"
python combine_analysis.py \
  --plddt_csv "$OUTPUT_DIR/plddt_scores.csv" \
  --ptm_csv "$OUTPUT_DIR/confidence_scores.csv" \
  --output "$OUTPUT_DIR/combined_scores.csv"

if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 数据合并失败${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 步骤 4: 生成汇总报告
# ============================================================================
echo -e "${YELLOW}[4/4] 生成分析报告...${NC}"

REPORT_FILE="$OUTPUT_DIR/analysis_report.txt"

{
    echo "═══════════════════════════════════════════════════════"
    echo "  AlphaFold3 预测结果质量分析报告"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "分析时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "输入目录: $RESULTS_DIR"
    echo "输出目录: $OUTPUT_DIR"
    echo ""
    echo "───────────────────────────────────────────────────────"
    echo "生成的文件:"
    echo "───────────────────────────────────────────────────────"
    echo "1. plddt_scores.csv        - pLDDT 值（局部质量）"
    echo "2. confidence_scores.csv   - PTM/iPTM 值（全局质量）"
    echo "3. combined_scores.csv     - 综合评分"
    echo "4. analysis_report.txt     - 本报告"
    echo ""
    echo "───────────────────────────────────────────────────────"
    echo "文件统计:"
    echo "───────────────────────────────────────────────────────"
    
    # 统计样本数量
    if [ -f "$OUTPUT_DIR/combined_scores.csv" ]; then
        TOTAL_SAMPLES=$(tail -n +2 "$OUTPUT_DIR/combined_scores.csv" | wc -l)
        echo "总样本数: $TOTAL_SAMPLES"
        
        # 统计质量分布（如果有 Quality 列）
        if head -1 "$OUTPUT_DIR/combined_scores.csv" | grep -q "Quality"; then
            echo ""
            echo "质量分布:"
            tail -n +2 "$OUTPUT_DIR/combined_scores.csv" | cut -d',' -f-1000 | \
              awk -F',' '{print $NF}' | sort | uniq -c | \
              awk '{printf "  %-10s: %d 个样本\n", $2, $1}'
        fi
    fi
    
    echo ""
    echo "───────────────────────────────────────────────────────"
    echo "质量评估标准:"
    echo "───────────────────────────────────────────────────────"
    echo "pLDDT (局部质量):"
    echo "  > 90  : 高度可信"
    echo "  > 70  : 可信"
    echo "  > 50  : 低置信度"
    echo "  < 50  : 不可信"
    echo ""
    echo "PTM (全局质量):"
    echo "  > 0.7 : 高度可信"
    echo "  > 0.5 : 可能可靠"
    echo "  < 0.5 : 可能不准确"
    echo ""
    echo "综合质量分类:"
    echo "  High   : pLDDT > 70 且 PTM > 0.7"
    echo "  Medium : pLDDT > 70 且 PTM > 0.5 或 pLDDT > 50 且 PTM > 0.7"
    echo "  Low    : 其他情况"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    
} > "$REPORT_FILE"

cat "$REPORT_FILE"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ 分析完成！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}结果文件:${NC}"
echo "  📊 $OUTPUT_DIR/plddt_scores.csv"
echo "  📊 $OUTPUT_DIR/confidence_scores.csv"
echo "  📊 $OUTPUT_DIR/combined_scores.csv"
echo "  📄 $OUTPUT_DIR/analysis_report.txt"
echo ""
echo -e "${BLUE}提示: 查看综合结果${NC}"
echo "  cat $OUTPUT_DIR/combined_scores.csv"
echo ""


