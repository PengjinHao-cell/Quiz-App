"""
初始化题库（从原始文本文件导入）
用法：python init_bank.py

数据来源：data/raw_party.txt → 用 parse_party.py 的解析逻辑
（原版是解析 Windows 上的 PDF，现改为解析已有的 raw_party.txt）
"""
import json
import os
import sys
import uuid
from datetime import datetime

# 本脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
UPLOADS_DIR = os.path.join(SCRIPT_DIR, "uploads")

# 导入 parse_party 的解析逻辑
sys.path.insert(0, SCRIPT_DIR)
from parse_party import parse_raw_text


def main():
    raw_txt = os.path.join(DATA_DIR, "raw_party.txt")
    if not os.path.exists(raw_txt):
        print(f"❌ 未找到原始文本文件: {raw_txt}")
        print("   请将入党积极分子题库文本保存为 data/raw_party.txt")
        sys.exit(1)

    # 读取并解析
    with open(raw_txt, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"📖 读取 raw_party.txt ({len(text)} 字符)")
    questions = parse_raw_text(text)
    print(f"📊 解析出 {len(questions)} 道题目")

    # 统计题型
    types = {}
    for q in questions:
        t = q.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    for t, c in types.items():
        print(f"   {t}: {c}")

    # 保存为 JSON 题库
    bank_id = uuid.uuid4().hex[:12]
    bank_data = {
        "id": bank_id,
        "original_filename": "2026年上半年入党积极分子培训班（文本导入）",
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "questions": questions,
    }

    out_path = os.path.join(DATA_DIR, f"{bank_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bank_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已保存到: {out_path}")
    print(f"   题库 ID: {bank_id}")
    print(f"   进入 http://localhost:5050/quiz/{bank_id} 即可刷题")


if __name__ == "__main__":
    main()