#!/usr/bin/env python3
"""
AlphaFold3 JSON 输入文件生成工具（官方格式）
================================================
生成符合 google-deepmind/alphafold3 输入规范的 JSON：
- 必含字段：sequences, dialect=alphafold3, version=1
- 支持单序列/多序列、FASTA、批量目录、校验与保存

示例：
  python af3_json_generator.py --sequences SEQ1 SEQ2 --ids A B --output complex.json
  python af3_json_generator.py --fasta sample.fasta --output sample.json
  python af3_json_generator.py --batch_input ./fastas --batch_output ./jsons
  python af3_json_generator.py --validate --input_file templates/input_template.json
"""

import os
import json
import argparse
import random
from typing import List, Dict, Any


def generate_random_seeds(num_seeds: int = 100) -> List[int]:
    return [random.randint(1, 99999) for _ in range(num_seeds)]


def validate_amino_acid_sequence(sequence: str) -> bool:
    valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
    seq = str(sequence).upper()
    return all(aa in valid_aa for aa in seq)


def create_af3_input_json(
    complex_id: str,
    sequences: List[Dict[str, str]],
    num_seeds: int = 100,
) -> Dict[str, Any]:
    formatted_sequences = []
    for seq in sequences:
        formatted_sequences.append({
            "protein": {
                "id": seq["id"],
                "sequence": seq["sequence"]
            }
        })

    af3_input = {
        "name": complex_id,
        "modelSeeds": generate_random_seeds(num_seeds),
        "sequences": formatted_sequences,
        "dialect": "alphafold3",
        "version": 1
    }
    return af3_input


def validate_af3_json(af3_data: Dict[str, Any]) -> bool:
    try:
        for key in ["sequences", "dialect", "version"]:
            if key not in af3_data:
                print(f"❌ 缺少必需字段: {key}")
                return False
        if af3_data.get("dialect") != "alphafold3":
            print("❌ dialect 必须为 alphafold3")
            return False
        seqs = af3_data.get("sequences", [])
        if not isinstance(seqs, list) or not seqs:
            print("❌ sequences 必须为非空列表")
            return False
        for i, s in enumerate(seqs):
            if "protein" not in s or "sequence" not in s["protein"]:
                print(f"❌ 第 {i} 个序列缺少 protein/sequence 字段")
                return False
            if not validate_amino_acid_sequence(s["protein"]["sequence"]):
                print(f"❌ 第 {i} 个序列包含无效氨基酸")
                return False
        print("✅ JSON 校验通过")
        return True
    except Exception as e:
        print(f"❌ 校验异常: {e}")
        return False


def save_json(data: Dict[str, Any], path: str) -> None:
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 已保存: {path}")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_fasta(path: str) -> List[Dict[str, str]]:
    sequences: List[Dict[str, str]] = []
    if not os.path.exists(path):
        print(f"❌ FASTA 不存在: {path}")
        return sequences
    current_id = None
    current_seq = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_id is not None:
                    sequences.append({"id": current_id, "sequence": "".join(current_seq)})
                current_id = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)
        if current_id is not None:
            sequences.append({"id": current_id, "sequence": "".join(current_seq)})
    print(f"📖 读取 FASTA: {path} -> {len(sequences)} 条序列")
    return sequences


def batch_from_fasta_dir(input_dir: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    for name in os.listdir(input_dir):
        if not name.lower().endswith((".fa", ".fasta", ".faa")):
            continue
        fasta_path = os.path.join(input_dir, name)
        base = os.path.splitext(name)[0]
        seqs = read_fasta(fasta_path)
        if not seqs:
            continue
        af3 = create_af3_input_json(base, seqs)
        if validate_af3_json(af3):
            save_json(af3, os.path.join(output_dir, f"{base}.json"))


def main():
    parser = argparse.ArgumentParser(description="AlphaFold3 JSON 输入生成（官方格式）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sequences", nargs="+", help="氨基酸序列列表")
    group.add_argument("--fasta", help="FASTA 文件")
    group.add_argument("--batch_input", help="批量 FASTA 目录")
    group.add_argument("--validate", action="store_true", help="验证现有 JSON")

    parser.add_argument("--ids", nargs="+", help="序列 ID 列表，与 --sequences 对应")
    parser.add_argument("--output", default="af3_input.json", help="输出 JSON 路径")
    parser.add_argument("--batch_output", help="批量输出目录")
    parser.add_argument("--complex_id", default="protein_complex", help="复合物 ID")
    parser.add_argument("--num_seeds", type=int, default=100, help="随机种子数量")
    parser.add_argument("--input_file", help="待验证 JSON 文件")

    args = parser.parse_args()

    if args.validate:
        if not args.input_file:
            print("❌ 需要提供 --input_file 进行验证")
            return
        data = load_json(args.input_file)
        validate_af3_json(data)
        return

    if args.batch_input:
        if not args.batch_output:
            print("❌ 批量模式需要提供 --batch_output")
            return
        batch_from_fasta_dir(args.batch_input, args.batch_output)
        return

    if args.fasta:
        seqs = read_fasta(args.fasta)
        if not seqs:
            return
    else:
        if not args.sequences:
            print("❌ 未提供 --sequences")
            return
        if args.ids and len(args.ids) != len(args.sequences):
            print("❌ --ids 与 --sequences 数量不一致")
            return
        seqs: List[Dict[str, str]] = []
        for i, s in enumerate(args.sequences):
            seq_id = args.ids[i] if args.ids else f"chain_{chr(65+i)}"
            seqs.append({"id": seq_id, "sequence": s})

    af3 = create_af3_input_json(args.complex_id, seqs, args.num_seeds)
    if validate_af3_json(af3):
        save_json(af3, args.output)


if __name__ == "__main__":
    main()


