#!/usr/bin/env python3
"""
AlphaFold3 批量分析工具
========================
统一工具用于批量处理 AlphaFold3 预测结果，包括：
1. pLDDT 值提取（局部结构质量）
2. PTM/iPTM 值提取（全局结构质量）
3. 综合分析报告生成

使用方法:
    python af3_analysis_tool.py --input_dir /path/to/af3_results --output_dir /path/to/output

示例:
    python af3_analysis_tool.py --input_dir ./results --output_dir ./analysis --verbose
"""

import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

try:
    from Bio.PDB import PDBParser, MMCIFParser
except ImportError:
    print("❌ 错误：未找到 Biopython 库")
    print("请运行: pip install biopython")
    sys.exit(1)


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def calculate_average_plddt(structure_file: str) -> Optional[float]:
    """
    计算单个结构文件（PDB 或 CIF）的平均 pLDDT
    
    Args:
        structure_file: 结构文件路径（支持 .pdb 和 .cif 格式）
        
    Returns:
        平均 pLDDT 值，如果计算失败则返回 None
    """
    try:
        # 根据文件扩展名选择合适的解析器
        file_ext = os.path.splitext(structure_file)[1].lower()
        
        if file_ext == '.cif':
            parser = MMCIFParser(QUIET=True)
            logging.debug(f"使用 MMCIFParser 解析 {structure_file}")
        elif file_ext == '.pdb':
            parser = PDBParser(QUIET=True)
            logging.debug(f"使用 PDBParser 解析 {structure_file}")
        else:
            logging.warning(f"不支持的文件格式: {file_ext}")
            return None
        
        structure = parser.get_structure("AF3_model", structure_file)
        plddt_scores = []

        for model in structure:
            for chain in model:
                for residue in chain:
                    # 更严格的 CA 原子检查
                    try:
                        ca_atom = residue["CA"]
                        plddt = ca_atom.bfactor
                        plddt_scores.append(plddt)
                    except KeyError:
                        # 某些残基可能没有 CA 原子（如水分子）
                        continue

        if not plddt_scores:
            logging.warning(f"文件 {structure_file} 中未找到任何 CA 原子")
            return None
            
        avg_plddt = sum(plddt_scores) / len(plddt_scores)
        logging.debug(f"文件 {structure_file} 包含 {len(plddt_scores)} 个 CA 原子")
        return avg_plddt
        
    except Exception as e:
        logging.error(f"解析结构文件 {structure_file} 时出错: {e}")
        return None


def find_best_model_file(folder_path: str) -> Optional[str]:
    """
    返回指定 AlphaFold3 输出目录中一级目录下的最佳结构文件路径
    
    支持格式：.pdb, .cif
    优先级：CIF > PDB，包含 'model' 的文件优先
    """
    try:
        # 查找所有支持的结构文件
        all_files = os.listdir(folder_path)
        structure_files = [f for f in all_files 
                          if (f.endswith(".cif") or f.endswith(".pdb")) 
                          and os.path.isfile(os.path.join(folder_path, f))]
        
        if not structure_files:
            return None
        
        # 优先选择 CIF 文件（AlphaFold3 主要输出格式）
        cif_files = [f for f in structure_files if f.endswith(".cif")]
        pdb_files = [f for f in structure_files if f.endswith(".pdb")]
        
        selected_file = None
        
        # 先尝试 CIF 文件
        if cif_files:
            model_cif = [f for f in cif_files if 'model' in f.lower()]
            if model_cif:
                model_cif.sort()
                selected_file = model_cif[0]
            else:
                cif_files.sort()
                selected_file = cif_files[0]
        # 再尝试 PDB 文件
        elif pdb_files:
            model_pdb = [f for f in pdb_files if 'model' in f.lower()]
            if model_pdb:
                model_pdb.sort()
                selected_file = model_pdb[0]
            else:
                pdb_files.sort()
                selected_file = pdb_files[0]
        
        if selected_file:
            full_path = os.path.join(folder_path, selected_file)
            logging.debug(f"选择结构文件: {selected_file}")
            return full_path
        
        return None
        
    except Exception as e:
        logging.error(f"扫描文件夹 {folder_path} 时出错: {e}")
        return None


def extract_confidence_from_json(
    json_file: str, 
    fields: List[str] = None
) -> Optional[Dict[str, Any]]:
    """
    从 summary_confidences.json 文件中提取置信度指标
    
    Args:
        json_file: JSON 文件路径
        fields: 要提取的字段列表，默认为 ['ptm']
        
    Returns:
        包含提取字段的字典，如果失败则返回 None
    """
    if fields is None:
        fields = ['ptm']
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = {}
        for field in fields:
            value = data.get(field, None)
            results[field] = value
            
        logging.debug(f"成功提取字段: {results}")
        return results
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON 解析错误 {json_file}: {e}")
        return None
    except FileNotFoundError:
        logging.error(f"文件不存在: {json_file}")
        return None
    except Exception as e:
        logging.error(f"读取文件 {json_file} 时出错: {e}")
        return None


def find_summary_json(folder_path: str, filename: str = "summary_confidences.json") -> Optional[str]:
    """
    在指定文件夹的一级目录中查找 summary_confidences.json 文件
    支持带前缀的文件名
    """
    try:
        # 先查找标准文件名
        json_file = os.path.join(folder_path, filename)
        if os.path.isfile(json_file):
            logging.debug(f"找到标准文件: {json_file}")
            return json_file
        
        # 查找带前缀的文件名（以 _summary_confidences.json 结尾）
        for file in os.listdir(folder_path):
            if file.endswith("_summary_confidences.json") or file.endswith("summary_confidences.json"):
                json_file = os.path.join(folder_path, file)
                if os.path.isfile(json_file):
                    logging.debug(f"找到带前缀的文件: {json_file}")
                    return json_file
        
        logging.debug(f"未找到 summary_confidences 文件在: {folder_path}")
        return None
        
    except Exception as e:
        logging.error(f"扫描文件夹 {folder_path} 时出错: {e}")
        return None


def analyze_af3_results(
    main_output_dir: str, 
    output_dir: str,
    fields: List[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    综合分析 AlphaFold3 结果
    
    Args:
        main_output_dir: AF3 主输出目录
        output_dir: 分析结果输出目录
        fields: 要提取的置信度字段
        verbose: 是否显示详细日志
        
    Returns:
        分析结果统计
    """
    if fields is None:
        fields = ['ptm', 'iptm', 'ranking_score']
    
    # 检查输入目录是否存在
    if not os.path.isdir(main_output_dir):
        logging.error(f"输入目录不存在: {main_output_dir}")
        sys.exit(1)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        'plddt_data': [],
        'confidence_data': [],
        'errors': []
    }
    
    try:
        subdirs = [d for d in os.listdir(main_output_dir)
                   if os.path.isdir(os.path.join(main_output_dir, d))]
    except Exception as e:
        logging.error(f"无法读取目录 {main_output_dir}: {e}")
        sys.exit(1)
    
    if not subdirs:
        logging.warning(f"目录 {main_output_dir} 中没有子文件夹")
        return results

    print(f"🧭 检测到 {len(subdirs)} 个预测结果文件夹。正在分析...\n")
    print(f"📋 提取字段: {', '.join(fields)}\n")

    for i, subdir in enumerate(sorted(subdirs), 1):
        subdir_path = os.path.join(main_output_dir, subdir)
        print(f"[{i}/{len(subdirs)}] 处理: {subdir}")
        
        # 提取 pLDDT
        structure_file = find_best_model_file(subdir_path)
        avg_plddt = None
        if structure_file:
            file_ext = os.path.splitext(structure_file)[1]
            avg_plddt = calculate_average_plddt(structure_file)
            if avg_plddt is not None:
                print(f"  ✅ 平均 pLDDT: {avg_plddt:.2f} (格式: {file_ext})")
                results['plddt_data'].append((subdir, avg_plddt))
            else:
                print(f"  ⚠️  无有效 pLDDT 数据")
                results['errors'].append(f"{subdir}: pLDDT提取失败")
        else:
            print(f"  ⚠️  未找到结构文件 (PDB/CIF)")
            results['errors'].append(f"{subdir}: 未找到结构文件")
        
        # 提取置信度指标
        json_file = find_summary_json(subdir_path)
        if json_file:
            confidence_data = extract_confidence_from_json(json_file, fields)
            if confidence_data and any(v is not None for v in confidence_data.values()):
                # 构建输出行：样本名 + 各个字段的值
                row = [subdir] + [confidence_data.get(field) for field in fields]
                results['confidence_data'].append(tuple(row))
                
                # 友好的输出显示
                display_values = [f"{field}={confidence_data.get(field):.4f}" 
                                 if confidence_data.get(field) is not None 
                                 else f"{field}=N/A" 
                                 for field in fields]
                print(f"  ✅ {', '.join(display_values)}")
            else:
                print(f"  ⚠️  未找到有效置信度数据")
                results['errors'].append(f"{subdir}: 置信度提取失败")
        else:
            print(f"  ⚠️  未找到 summary_confidences.json 文件")
            results['errors'].append(f"{subdir}: 未找到置信度文件")

    return results


def save_results(results: Dict[str, Any], output_dir: str, fields: List[str]):
    """保存分析结果到CSV文件"""
    
    # 保存 pLDDT 结果
    plddt_csv = os.path.join(output_dir, "plddt_scores.csv")
    with open(plddt_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Sample", "Average_pLDDT"])
        writer.writerows(results['plddt_data'])
    
    # 保存置信度结果
    confidence_csv = os.path.join(output_dir, "confidence_scores.csv")
    with open(confidence_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        header = ["Sample"] + [field.upper() for field in fields]
        writer.writerow(header)
        writer.writerows(results['confidence_data'])
    
    # 合并数据
    combined_csv = os.path.join(output_dir, "combined_scores.csv")
    merge_data(results['plddt_data'], results['confidence_data'], fields, combined_csv)
    
    print(f"\n📊 已生成结果文件:")
    print(f"  📊 {plddt_csv}")
    print(f"  📊 {confidence_csv}")
    print(f"  📊 {combined_csv}")
    print(f"✅ 成功分析: {len(results['plddt_data'])} 个样本")
    
    if results['errors']:
        print(f"⚠️  失败/跳过: {len(results['errors'])} 个样本")


def merge_data(plddt_data: List[Tuple], confidence_data: List[Tuple], fields: List[str], output_file: str):
    """合并 pLDDT 和置信度数据"""
    
    # 转换为字典格式
    plddt_dict = {row[0]: row[1] for row in plddt_data}
    confidence_dict = {row[0]: dict(zip(fields, row[1:])) for row in confidence_data}
    
    # 获取所有样本名称
    all_samples = set(plddt_dict.keys()) | set(confidence_dict.keys())
    
    # 合并数据
    merged_data = []
    for sample in sorted(all_samples):
        row = [sample]
        
        # 添加 pLDDT 数据
        row.append(plddt_dict.get(sample))
        
        # 添加置信度数据
        for field in fields:
            row.append(confidence_dict.get(sample, {}).get(field))
        
        # 添加质量分类
        plddt = plddt_dict.get(sample)
        ptm = confidence_dict.get(sample, {}).get('ptm')
        
        if plddt is not None and ptm is not None:
            if plddt > 70 and ptm > 0.7:
                quality = 'High'
            elif (plddt > 70 and ptm > 0.5) or (plddt > 50 and ptm > 0.7):
                quality = 'Medium'
            else:
                quality = 'Low'
        else:
            quality = 'Unknown'
        
        row.append(quality)
        merged_data.append(row)
    
    # 保存合并结果
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        header = ["Sample", "Average_pLDDT"] + [field.upper() for field in fields] + ["Quality"]
        writer.writerow(header)
        writer.writerows(merged_data)


def main():
    parser = argparse.ArgumentParser(
        description="AlphaFold3 批量分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本分析
  python %(prog)s --input_dir /path/to/af3_results --output_dir ./analysis
  
  # 提取特定字段
  python %(prog)s --input_dir /path/to/af3_results --fields ptm iptm ranking_score
  
  # 详细日志
  python %(prog)s --input_dir /path/to/af3_results --verbose
        """
    )
    parser.add_argument(
        "--input_dir", 
        required=True, 
        help="AF3 主输出目录"
    )
    parser.add_argument(
        "--output_dir", 
        default="./af3_analysis", 
        help="分析结果输出目录（默认: ./af3_analysis）"
    )
    parser.add_argument(
        "--fields",
        nargs='+',
        default=['ptm', 'iptm', 'ranking_score'],
        help="要提取的置信度字段（默认: ptm iptm ranking_score）"
    )
    parser.add_argument(
        "--verbose", 
        "-v",
        action="store_true",
        help="显示详细日志信息"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    print("🔄 开始 AlphaFold3 结果分析...\n")
    
    # 运行分析
    results = analyze_af3_results(
        args.input_dir, 
        args.output_dir, 
        args.fields,
        args.verbose
    )
    
    # 保存结果
    save_results(results, args.output_dir, args.fields)
    
    print("\n✅ 分析完成！")


if __name__ == "__main__":
    main()
