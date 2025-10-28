#!/usr/bin/env bash
# 安全选项：遇错退出、未定义变量报错（通用）
set -eu
# 若为 bash，开启 errtrace（-E）以便 trap 传播
if [ -n "${BASH_VERSION:-}" ]; then
  set -E
fi
# 尝试开启 pipefail（在不支持的 shell 上静默跳过）
if (set -o pipefail) 2>/dev/null; then
  set -o pipefail
fi
#=====================================================
# run_af3_parallel.sh (精简：单次目录运行，镜像你的示例)
#=====================================================

# ---------------- 配置区域 ----------------
AF3_SCRIPT=/data/AlphaFold/alphafold3/run_alphafold.py
INPUT_DIR=/mnt/share/chufan/CY_col/outputs_3/
OUTPUT_DIR=/mnt/share/chufan/CY_col/rxfp3__results_2/
LOG_FILE=/mnt/share/chufan/CY_col/rxfp3_log/rxfp3_log
MAX_TEMPLATE_DATE=3000-12-01
MAX_CONCURRENT_JOBS=8  # CPU-only 模式的最大并发任务数
# -------------------------------------------

# 创建输出与日志目录
mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# 基础校验
if ! command -v python >/dev/null 2>&1; then
  echo "未找到 python，请确保已安装并在 PATH 中。" >&2
  exit 1
fi
if [ ! -f "$AF3_SCRIPT" ]; then
  echo "未找到 AF3 脚本: $AF3_SCRIPT" >&2
  exit 1
fi
if [ ! -d "$INPUT_DIR" ]; then
  echo "输入目录不存在: $INPUT_DIR" >&2
  exit 1
fi

# GPU 检测与配置
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
else
  GPU_COUNT=0
fi

# 若用户已预设 CUDA_VISIBLE_DEVICES，则尊重之
if [ -n "${CUDA_VISIBLE_DEVICES:-}" ]; then
  IFS=',' read -r -a GPU_IDS <<< "$CUDA_VISIBLE_DEVICES"
  GPU_COUNT=${#GPU_IDS[@]}
  echo "[INFO] 使用预设 CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES (${GPU_COUNT} GPU)"
else
  echo "[INFO] 检测到 $GPU_COUNT 个 GPU"
fi

# 打印关键信息
echo "[INFO] INPUT_DIR=$INPUT_DIR"
echo "[INFO] OUTPUT_DIR=$OUTPUT_DIR"
echo "[INFO] MAX_TEMPLATE_DATE=$MAX_TEMPLATE_DATE"
echo "[INFO] LOG_FILE=$LOG_FILE"

# 并行逐 JSON 文件：仅扫描顶层 *.json（如需递归可改为 find）
shopt -s nullglob
JSON_FILES=("$INPUT_DIR"/*.json)
shopt -u nullglob

TOTAL_FILES=${#JSON_FILES[@]}
echo "[INFO] 待处理文件数量: $TOTAL_FILES (目录: $INPUT_DIR)"
if [ "$TOTAL_FILES" -eq 0 ]; then
  echo "[ERROR] 未在 $INPUT_DIR 顶层发现 JSON 文件。请检查路径与扩展名。" >&2
  exit 1
fi

# GPU 分配计数
GPU_INDEX=0

for JSON_FILE in "${JSON_FILES[@]}"; do
  # 解析为绝对路径，避免相对路径导致的找不到问题
  JSON_ABS=$(python - "$JSON_FILE" << 'PY'
import os, sys
p = sys.argv[1]
print(os.path.abspath(p))
PY
)
  base_name=$(basename "$JSON_ABS" .json)
  log_path="$(dirname "$LOG_FILE")/${base_name}.log"

  # GPU 分配
  if [ "$GPU_COUNT" -gt 0 ]; then
    if [ -n "${CUDA_VISIBLE_DEVICES:-}" ]; then
      # 使用预设的 CUDA_VISIBLE_DEVICES
      export CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"
      gpu_info="GPU $CUDA_VISIBLE_DEVICES"
    else
      # 轮转分配 GPU
      export CUDA_VISIBLE_DEVICES=$GPU_INDEX
      GPU_INDEX=$(( (GPU_INDEX + 1) % GPU_COUNT ))
      gpu_info="GPU $CUDA_VISIBLE_DEVICES"
    fi
  else
    unset CUDA_VISIBLE_DEVICES
    gpu_info="CPU"
  fi

  echo "[INFO] 运行: $JSON_ABS -> $gpu_info -> 日志: $log_path"

  # 为该任务创建临时输入目录，拷贝 JSON 进去；为输出创建独立子目录
  TMP_DIR="$(mktemp -d)"
  cp "$JSON_ABS" "$TMP_DIR/"
  JOB_OUT_DIR="$OUTPUT_DIR/$base_name"
  mkdir -p "$JOB_OUT_DIR"

  # 在子 shell 中运行并在结束时清理临时目录
  (
    python "$AF3_SCRIPT" \
      --input_dir "$TMP_DIR" \
      --output_dir "$JOB_OUT_DIR" \
      --max_template_date "$MAX_TEMPLATE_DATE"
    rc=$?
    rm -rf "$TMP_DIR"
    exit $rc
  ) > "$log_path" 2>&1 &

  # 智能并发控制
  if [ "$GPU_COUNT" -gt 0 ]; then
    # 有 GPU：按 GPU 数量限制并发
    while [ "$(jobs -r | wc -l)" -ge "$GPU_COUNT" ]; do
      sleep 2
    done
  else
    # 无 GPU：按 CPU 并发限制
    while [ "$(jobs -r | wc -l)" -ge "$MAX_CONCURRENT_JOBS" ]; do
      sleep 2
    done
  fi

done

wait
echo "[INFO] 所有任务完成。日志目录: $(dirname "$LOG_FILE")"
