#!/usr/bin/env python3
"""
AlphaFold3 批量运行工具
=====================
统一工具用于批量运行 AlphaFold3 预测，支持：
1. 单次运行
2. 并行批量运行
3. GPU/CPU 自动检测和分配
4. 进度监控和日志记录

使用方法:
    python af3_runner.py --input_dir /path/to/json_files --output_dir /path/to/output

示例:
    python af3_runner.py --input_dir ./inputs --output_dir ./results --max_concurrent 4
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def detect_gpu_count() -> int:
    """检测可用GPU数量"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            gpu_count = len(result.stdout.strip().split('\n'))
            logging.info(f"检测到 {gpu_count} 个GPU")
            return gpu_count
    except FileNotFoundError:
        logging.info("未检测到nvidia-smi，将使用CPU模式")
    return 0


def validate_json_file(json_path: str) -> bool:
    """验证JSON文件格式"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查必需字段
        required_fields = ['sequences']
        for field in required_fields:
            if field not in data:
                logging.error(f"JSON文件缺少必需字段: {field}")
                return False
        
        # 检查序列格式
        sequences = data['sequences']
        if not isinstance(sequences, list) or len(sequences) == 0:
            logging.error("sequences必须是非空列表")
            return False
        
        for i, seq in enumerate(sequences):
            if not isinstance(seq, dict):
                logging.error(f"序列 {i} 格式错误")
                return False
            
            # 检查蛋白质序列
            if 'protein' in seq:
                protein = seq['protein']
                if 'sequence' not in protein:
                    logging.error(f"序列 {i} 缺少sequence字段")
                    return False
                
                # 验证氨基酸序列
                sequence = protein['sequence']
                valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
                if not all(aa in valid_aa for aa in sequence):
                    logging.error(f"序列 {i} 包含无效氨基酸")
                    return False
        
        logging.debug(f"JSON文件验证通过: {json_path}")
        return True
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析错误 {json_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"验证文件时出错 {json_path}: {e}")
        return False


def run_single_prediction(
    json_file: str, 
    output_dir: str, 
    af3_script: str,
    max_template_date: str = "3000-12-01",
    gpu_id: Optional[int] = None
) -> Dict[str, any]:
    """
    运行单个AlphaFold3预测
    
    Args:
        json_file: JSON输入文件路径
        output_dir: 输出目录
        af3_script: AF3脚本路径
        max_template_date: 最大模板日期
        gpu_id: GPU ID（None表示CPU模式）
        
    Returns:
        运行结果字典
    """
    base_name = os.path.splitext(os.path.basename(json_file))[0]
    job_output_dir = os.path.join(output_dir, base_name)
    
    # 创建输出目录
    os.makedirs(job_output_dir, exist_ok=True)
    
    # 设置环境变量
    env = os.environ.copy()
    if gpu_id is not None:
        env['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
        gpu_info = f"GPU {gpu_id}"
    else:
        env.pop('CUDA_VISIBLE_DEVICES', None)
        gpu_info = "CPU"
    
    # 构建命令
    cmd = [
        'python', af3_script,
        '--input_dir', os.path.dirname(json_file),
        '--output_dir', job_output_dir,
        '--max_template_date', max_template_date
    ]
    
    start_time = time.time()
    logging.info(f"开始预测: {base_name} -> {gpu_info}")
    
    try:
        # 运行预测
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            logging.info(f"✅ 预测完成: {base_name} (耗时: {duration:.1f}s)")
            return {
                'status': 'success',
                'sample': base_name,
                'output_dir': job_output_dir,
                'duration': duration,
                'gpu_info': gpu_info
            }
        else:
            logging.error(f"❌ 预测失败: {base_name}")
            logging.error(f"错误信息: {result.stderr}")
            return {
                'status': 'failed',
                'sample': base_name,
                'error': result.stderr,
                'duration': duration,
                'gpu_info': gpu_info
            }
            
    except subprocess.TimeoutExpired:
        logging.error(f"⏰ 预测超时: {base_name}")
        return {
            'status': 'timeout',
            'sample': base_name,
            'error': 'Prediction timeout',
            'gpu_info': gpu_info
        }
    except Exception as e:
        logging.error(f"❌ 预测异常: {base_name} - {e}")
        return {
            'status': 'error',
            'sample': base_name,
            'error': str(e),
            'gpu_info': gpu_info
        }


def run_batch_predictions(
    input_dir: str,
    output_dir: str,
    af3_script: str,
    max_concurrent: int = 4,
    max_template_date: str = "3000-12-01",
    verbose: bool = False
) -> Dict[str, List]:
    """
    批量运行AlphaFold3预测
    
    Args:
        input_dir: JSON文件输入目录
        output_dir: 输出目录
        af3_script: AF3脚本路径
        max_concurrent: 最大并发数
        max_template_date: 最大模板日期
        verbose: 是否显示详细日志
        
    Returns:
        批量运行结果统计
    """
    # 检查输入目录
    if not os.path.isdir(input_dir):
        logging.error(f"输入目录不存在: {input_dir}")
        return {'success': [], 'failed': [], 'errors': []}
    
    # 查找JSON文件
    json_files = []
    for file in os.listdir(input_dir):
        if file.endswith('.json'):
            json_path = os.path.join(input_dir, file)
            if validate_json_file(json_path):
                json_files.append(json_path)
            else:
                logging.warning(f"跳过无效JSON文件: {file}")
    
    if not json_files:
        logging.error(f"在 {input_dir} 中未找到有效的JSON文件")
        return {'success': [], 'failed': [], 'errors': []}
    
    logging.info(f"找到 {len(json_files)} 个有效JSON文件")
    
    # 检测GPU
    gpu_count = detect_gpu_count()
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备任务
    tasks = []
    gpu_index = 0
    
    for json_file in json_files:
        if gpu_count > 0:
            gpu_id = gpu_index % gpu_count
            gpu_index += 1
        else:
            gpu_id = None
        
        tasks.append((json_file, gpu_id))
    
    # 运行任务
    results = {'success': [], 'failed': [], 'errors': []}
    
    if gpu_count > 0:
        # GPU模式：按GPU数量限制并发
        max_workers = min(max_concurrent, gpu_count)
    else:
        # CPU模式：按CPU核心数限制并发
        max_workers = min(max_concurrent, os.cpu_count() or 4)
    
    logging.info(f"使用 {max_workers} 个并发工作进程")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(
                run_single_prediction,
                json_file,
                output_dir,
                af3_script,
                max_template_date,
                gpu_id
            ): (json_file, gpu_id)
            for json_file, gpu_id in tasks
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_task):
            json_file, gpu_id = future_to_task[future]
            try:
                result = future.result()
                
                if result['status'] == 'success':
                    results['success'].append(result)
                else:
                    results['failed'].append(result)
                    
            except Exception as e:
                logging.error(f"任务执行异常: {json_file} - {e}")
                results['errors'].append({
                    'sample': os.path.splitext(os.path.basename(json_file))[0],
                    'error': str(e)
                })
    
    return results


def generate_summary_report(results: Dict[str, List], output_dir: str):
    """生成运行总结报告"""
    report_file = os.path.join(output_dir, "run_summary.txt")
    
    total_tasks = len(results['success']) + len(results['failed']) + len(results['errors'])
    success_count = len(results['success'])
    failed_count = len(results['failed'])
    error_count = len(results['errors'])
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("═══════════════════════════════════════════════════════\n")
        f.write("  AlphaFold3 批量运行总结报告\n")
        f.write("═══════════════════════════════════════════════════════\n\n")
        f.write(f"运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"输出目录: {output_dir}\n\n")
        
        f.write("───────────────────────────────────────────────────────\n")
        f.write("运行统计:\n")
        f.write("───────────────────────────────────────────────────────\n")
        f.write(f"总任务数: {total_tasks}\n")
        f.write(f"成功: {success_count}\n")
        f.write(f"失败: {failed_count}\n")
        f.write(f"错误: {error_count}\n")
        f.write(f"成功率: {success_count/total_tasks*100:.1f}%\n\n")
        
        if results['success']:
            f.write("───────────────────────────────────────────────────────\n")
            f.write("成功样本:\n")
            f.write("───────────────────────────────────────────────────────\n")
            for result in results['success']:
                f.write(f"✅ {result['sample']} ({result['gpu_info']}, {result['duration']:.1f}s)\n")
            f.write("\n")
        
        if results['failed']:
            f.write("───────────────────────────────────────────────────────\n")
            f.write("失败样本:\n")
            f.write("───────────────────────────────────────────────────────\n")
            for result in results['failed']:
                f.write(f"❌ {result['sample']} ({result['gpu_info']}) - {result.get('error', 'Unknown error')}\n")
            f.write("\n")
        
        if results['errors']:
            f.write("───────────────────────────────────────────────────────\n")
            f.write("错误样本:\n")
            f.write("───────────────────────────────────────────────────────\n")
            for result in results['errors']:
                f.write(f"⚠️  {result['sample']} - {result['error']}\n")
    
    logging.info(f"总结报告已保存: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="AlphaFold3 批量运行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本批量运行
  python %(prog)s --input_dir ./inputs --output_dir ./results
  
  # 指定并发数和模板日期
  python %(prog)s --input_dir ./inputs --output_dir ./results --max_concurrent 8 --max_template_date 2023-12-01
  
  # 详细日志
  python %(prog)s --input_dir ./inputs --output_dir ./results --verbose
        """
    )
    parser.add_argument(
        "--input_dir", 
        required=True, 
        help="JSON文件输入目录"
    )
    parser.add_argument(
        "--output_dir", 
        required=True, 
        help="预测结果输出目录"
    )
    parser.add_argument(
        "--af3_script",
        default="/data/AlphaFold/alphafold3/run_alphafold.py",
        help="AlphaFold3脚本路径（默认: /data/AlphaFold/alphafold3/run_alphafold.py）"
    )
    parser.add_argument(
        "--max_concurrent",
        type=int,
        default=4,
        help="最大并发任务数（默认: 4）"
    )
    parser.add_argument(
        "--max_template_date",
        default="3000-12-01",
        help="最大模板日期（默认: 3000-12-01）"
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
    
    print("🚀 开始 AlphaFold3 批量预测...\n")
    
    # 检查AF3脚本
    if not os.path.exists(args.af3_script):
        logging.error(f"AlphaFold3脚本不存在: {args.af3_script}")
        sys.exit(1)
    
    # 运行批量预测
    results = run_batch_predictions(
        args.input_dir,
        args.output_dir,
        args.af3_script,
        args.max_concurrent,
        args.max_template_date,
        args.verbose
    )
    
    # 生成总结报告
    generate_summary_report(results, args.output_dir)
    
    # 打印总结
    total = len(results['success']) + len(results['failed']) + len(results['errors'])
    success = len(results['success'])
    
    print(f"\n✅ 批量预测完成！")
    print(f"📊 总任务: {total}, 成功: {success}, 成功率: {success/total*100:.1f}%")
    print(f"📄 详细报告: {os.path.join(args.output_dir, 'run_summary.txt')}")


if __name__ == "__main__":
    main()
