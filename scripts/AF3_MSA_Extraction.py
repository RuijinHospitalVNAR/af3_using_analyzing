"""
AF3 MSA提取脚本
从AlphaFold3 JSON文件中提取MSA并保存为A3M格式

使用方法:
python AF3_MSA_Extraction.py <input_json> <output_dir>

参数说明:
- input_json: AlphaFold3 JSON输入文件路径
- output_dir: 输出目录路径

示例:
python AF3_MSA_Extraction.py input.json ./msa_output
"""
import os
import sys
from alphafold3.common import folding_input

def extract_msa_from_af3_json(input_json_path, output_dir):
    """从AlphaFold3 JSON文件中提取MSA并保存为a3m格式"""
    print(f"正在读取JSON文件: {input_json_path}")
    
    with open(input_json_path, 'rt') as f:
        af_json = f.read()
    
    af_input = folding_input.Input.from_json(af_json)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")
    
    extracted_count = 0
    
    # 处理蛋白质链MSA
    for protein_chain in af_input.protein_chains:
        chain_id = protein_chain.id[0] if protein_chain.id else "unknown"
        
        if protein_chain.unpaired_msa:
            save_path = os.path.join(output_dir, f'chain_{chain_id}_unpaired_msa.a3m')
            with open(save_path, 'wt') as f:
                f.write(protein_chain.unpaired_msa)
            print(f"已提取: {save_path}")
            extracted_count += 1
        
        if protein_chain.paired_msa:
            save_path = os.path.join(output_dir, f'chain_{chain_id}_paired_msa.a3m')
            with open(save_path, 'wt') as f:
                f.write(protein_chain.paired_msa)
            print(f"已提取: {save_path}")
            extracted_count += 1
    
    # 处理RNA链MSA
    for rna_chain in af_input.rna_chains:
        chain_id = rna_chain.id[0] if rna_chain.id else "unknown"
        
        if rna_chain.unpaired_msa:
            save_path = os.path.join(output_dir, f'chain_{chain_id}_unpaired_msa.a3m')
            with open(save_path, 'wt') as f:
                f.write(rna_chain.unpaired_msa)
            print(f"已提取: {save_path}")
            extracted_count += 1
    
    print(f"提取完成！共提取了 {extracted_count} 个MSA文件")
    return extracted_count

def main():
    """主程序入口"""
    if len(sys.argv) != 3:
        print("使用方法: python AF3_MSA_Extraction.py <input_json> <output_dir>")
        print("示例: python AF3_MSA_Extraction.py input.json ./msa_output")
        sys.exit(1)
    
    input_json = sys.argv[1]
    output_dir = sys.argv[2]
    
    # 检查输入文件是否存在
    if not os.path.exists(input_json):
        print(f"错误: 输入文件不存在: {input_json}")
        sys.exit(1)
    
    try:
        extract_msa_from_af3_json(input_json, output_dir)
    except Exception as e:
        print(f"提取失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()