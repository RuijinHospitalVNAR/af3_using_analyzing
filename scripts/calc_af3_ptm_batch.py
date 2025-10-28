#!/usr/bin/env python3
"""
批量提取 AlphaFold 3 输出结果的 PTM 值
-----------------------------------------
1. 自动遍历主输出目录中的子文件夹
2. 每个子文件夹中读取 summary_confidences.json 文件
3. 提取 ptm 值
4. 输出一个 CSV 文件，包含每个样本及其 PTM 值

运行命令：python calc_af3_ptm_batch.py \
  --input_dir /mnt/share/chufan/CY_col/rxfp3__results_2 \
  --output_csv ptm_summary.csv

"""

import os
import csv
import json

def extract_ptm_from_json(json_file):
    """从 summary_confidences.json 文件中提取 PTM 值"""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            ptm = data.get('ptm', None)
            return ptm
    except Exception as e:
        print(f"  ⚠️  读取 JSON 文件失败: {e}")
        return None


def find_summary_json(folder_path):
    """
    在指定文件夹的一级目录中查找 summary_confidences.json 文件
    支持带前缀的文件名，如: rxfp3_ins_at_327_len0_none_summary_confidences.json
    """
    # 先查找标准文件名
    json_file = os.path.join(folder_path, "summary_confidences.json")
    if os.path.isfile(json_file):
        return json_file
    
    # 查找带前缀的文件名（以 _summary_confidences.json 结尾）
    try:
        for filename in os.listdir(folder_path):
            if filename.endswith("_summary_confidences.json"):
                json_file = os.path.join(folder_path, filename)
                if os.path.isfile(json_file):
                    return json_file
    except Exception:
        pass
    
    return None


def batch_extract_ptm(main_output_dir, csv_output_path):
    """
    遍历主目录下的所有子文件夹，提取每个的 PTM 值。
    """
    results = []
    subdirs = [d for d in os.listdir(main_output_dir)
               if os.path.isdir(os.path.join(main_output_dir, d))]

    print(f"🧭 检测到 {len(subdirs)} 个预测结果文件夹。正在分析...")

    for subdir in sorted(subdirs):
        subdir_path = os.path.join(main_output_dir, subdir)
        json_file = find_summary_json(subdir_path)

        if json_file:
            ptm = extract_ptm_from_json(json_file)
            if ptm is not None:
                print(f"✅ {subdir}: PTM = {ptm:.4f}")
                results.append((subdir, ptm))
            else:
                print(f"⚠️ {subdir}: 未找到 PTM 数据")
        else:
            print(f"⚠️ {subdir}: 未找到 summary_confidences.json 文件")

    # 保存为 CSV
    with open(csv_output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Sample", "PTM"])
        writer.writerows(results)

    print(f"\n📊 已生成结果文件: {csv_output_path}")
    print(f"共提取 {len(results)} 个有效 PTM 值。")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="批量提取 AlphaFold3 输出结果的 PTM 值")
    parser.add_argument("--input_dir", required=True, help="AF3 主输出目录")
    parser.add_argument("--output_csv", default="ptm_summary.csv", help="结果 CSV 文件名")
    args = parser.parse_args()

    batch_extract_ptm(args.input_dir, args.output_csv)

