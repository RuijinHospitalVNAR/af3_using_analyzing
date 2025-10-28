#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 RXFP3 (Homo) 在 306-327 位点替换/插入 Bril 的所有变体。
输出: variants.fasta 和 variants_summary.csv
"""

import csv

# ---------- 可在此处修改的参数 ----------
RXFP3_seq = (
    "HHHHHHHHHHQMADAATIATMNKAAGGDKLAELFSLVPDLLEAANKTSGNASLQLPDL"
    "WWELGLELPDGAPPGHPPGSGGAESADTEARVRILISVVYWVVCALGLAGNLLVLYLMKSMQGWRKSSINLFV"
    "TNLALTDFQFVLTLPFWAVENALDFKWPFGKAMCKIVSMVTSMNMYASVFFLTAMSVTRYHSVASALKSHRTRG"
    "HGRGDCCGRSLGDSCCFSAKALCVWIWALAALASLPSAIFSTTVKVMGEELCLVRFPDKLLGRDRQFWLGLYHS"
    "QKVLLGFVLPLGIIILCYLLLVRFIADRRAAGTKGGAAVAGGRPTGASARRLSKVTKSVTIVVLSFFLCWLPNQ"
    "ALTTWSILIKFNAVPFSQEYFLCQVYAFPVSVCLAHSNSCLNPVLYCLVRREFRKALKSLLWRIASPSITSMRP"
    "FTATTKPEHEDQGLQAPAPPHAAAEPDLLYYPPGVVVYSGGRYDLLPSSSAY"
)

Bril_seq = (
    "ADLEDNWETLNDNLKVIEKADNAAQVKDALTKMRAAALDAQKATPPKLEDKSPDSPEMKDFRHGFDILVGQ"
    "IDDALKLANEGKVKEAQAAAEQLKTTRNAYIQKYL"
)

# 目标窗口（1-based，包含两端）——按你要求：306-327（含）
region_start = 306
region_end = 327

# linker（可改）
default_linker_N = "ARRQL"
default_linker_C = "ARSTL"

# linker 模式（4 种）：
# 0 -> no linker
# 1 -> N-term linker only (linker_N + Bril)
# 2 -> C-term linker only (Bril + linker_C)
# 3 -> both (linker + Bril + linker)
linker_modes = {
    0: ("none", "", ""),
    1: ("N_linker", default_linker_N, ""),
    2: ("C_linker", "", default_linker_C),
    3: ("both_linker", default_linker_N, default_linker_C),
}
# -----------------------------------------

# basic checks
L = len(RXFP3_seq)
if not (1 <= region_start <= region_end <= L):
    raise ValueError("region_start/region_end 超出 RXFP3 序列范围或无效。")

# convert to 0-based indices for Python slicing
r0 = region_start - 1
r1 = region_end - 1

variants = []
# We'll iterate deletion_start from r0 .. r1+1
# If deletion_end < deletion_start => zero-length insertion at position deletion_start (between residues)
for deletion_start in range(r0, r1 + 2):  # inclusive of r1+1 to allow zero-length at end
    # deletion_end ranges from deletion_start .. r1 (for length>=1)
    # or deletion_end = deletion_start -1 for zero-length (handled below)
    # handle zero-length case:
    if deletion_start <= r1:
        # zero-length insertion at position deletion_start is represented too
        pass
    # Enumerate deletion_end:
    # for zero-length: deletion_end = deletion_start - 1
    possible_ends = []
    possible_ends.append(deletion_start - 1)  # zero-length
    for de in range(deletion_start, r1 + 1):
        possible_ends.append(de)

    for deletion_end in possible_ends:
        # compute left and right parts (0-based slicing)
        left = RXFP3_seq[:deletion_start]
        right = RXFP3_seq[deletion_end + 1:]  # if deletion_end == deletion_start-1 -> right is full suffix starting at deletion_start

        # record "human" coordinates for naming: convert to 1-based
        if deletion_end >= deletion_start:
            # deletion length >=1
            del_start_1b = deletion_start + 1
            del_end_1b = deletion_end + 1
            del_len = deletion_end - deletion_start + 1
            deletion_desc = f"del_{del_start_1b}_{del_end_1b}_len{del_len}"
        else:
            # zero-length insertion at position deletion_start (between residues deletion_start and deletion_start+1)
            ins_pos = deletion_start + 1  # insertion position in 1-based (between residues ins_pos-1 and ins_pos)
            deletion_desc = f"ins_at_{ins_pos}_len0"

        for mode, (mode_name, n_linker, c_linker) in linker_modes.items():
            insert_seq = f"{n_linker}{Bril_seq}{c_linker}"
            new_seq = left + insert_seq + right
            name = f"RXFP3_{deletion_desc}_{mode_name}"
            variants.append({
                "name": name,
                "del_start": deletion_start + 1 if deletion_end >= deletion_start else "",
                "del_end": deletion_end + 1 if deletion_end >= deletion_start else "",
                "del_len": deletion_end - deletion_start + 1 if deletion_end >= deletion_start else 0,
                "insert_pos_1b": (deletion_start + 1) if deletion_end < deletion_start else "",
                "linker_mode": mode_name,
                "linker_seq": f"N:{n_linker}|C:{c_linker}",
                "sequence": new_seq,
                "seq_length": len(new_seq),
            })

# Sanity: count
total = len(variants)

# Save FASTA and CSV
fasta_path = "variants.fasta"
csv_path = "variants_summary.csv"

with open(fasta_path, "w") as fa:
    for v in variants:
        header = f">{v['name']} | del_len={v['del_len']} | linker={v['linker_mode']} | len={v['seq_length']}"
        fa.write(header + "\n")
        # wrap sequence to 70 chars per line
        seq = v['sequence']
        for i in range(0, len(seq), 70):
            fa.write(seq[i:i+70] + "\n")

with open(csv_path, "w", newline='') as cf:
    writer = csv.DictWriter(cf, fieldnames=[
        "name", "del_start", "del_end", "del_len", "insert_pos_1b",
        "linker_mode", "linker_seq", "seq_length"
    ])
    writer.writeheader()
    for v in variants:
        writer.writerow({
            k: v.get(k, "") for k in writer.fieldnames
        })

print(f"完成。共生成变体: {total}")
print(f"FASTA 文件: {fasta_path}")
print(f"Summary CSV: {csv_path}")

# print calculation check
# 理论上: number_of_positions = sum_{k=0}^{window_len} (window_len - k + 1) = (window_len+1)*(window_len+2)/2 - 1? 
# 更直接：包含0-length的子区间数 = (window_len+1) * (window_len+2) / 2 - ??? (这里不必深究)
# We'll print breakdown:
window_len = r1 - r0 + 1
num_positions = 0
# the count used in script: deletion_start ranges (r0..r1+1)
# for each deletion_start, possible_ends = 1 (zero) + (r1 - deletion_start + 1)
for ds in range(r0, r1 + 2):
    num_positions += 1 + max(0, r1 - ds + 1)
print(f"窗口长度 window_len = {window_len}")
print(f"包含 0-length 的位置总数 = {num_positions}")
print(f"linker 模式数 = {len(linker_modes)}")
print(f"预计总变体 = {num_positions * len(linker_modes)}")
