"""
构建离线英汉词库
- 来源：ECDICT（skywind3000/ECDICT）
- 按词频排序取前 20,000 条
- 输出 data/dict_cache.json：{ "word": "abandon", "meaning": "放弃；遗弃" }

用法：
    python build_dict.py                  # 完整构建
    python build_dict.py --top 15000      # 自定义条数
    python build_dict.py --force          # 强制重新下载
"""
import csv
import json
import os
import re
import sys
import urllib.request
import gzip
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
OUTPUT = os.path.join(DATA_DIR, "dict_cache.json")
CSV_PATH = os.path.join(DATA_DIR, "ecdict_full.csv")
CSV_URL = "https://github.com/skywind3000/ECDICT/raw/master/ecdict.csv"

TOP_N = 20000
FORCE = False

args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--top" and i + 1 < len(args):
        TOP_N = int(args[i + 1])
        i += 2
    elif args[i] == "--force":
        FORCE = True
        i += 1
    else:
        i += 1


def download_csv():
    """下载 ECDICT CSV（约 200MB，建议有稳定网络）"""
    if os.path.exists(CSV_PATH) and not FORCE:
        size_mb = os.path.getsize(CSV_PATH) / (1024 * 1024)
        print(f"📦 已有词库文件：{CSV_PATH} ({size_mb:.1f} MB)")
        return

    print(f"⬇️  正在下载 ECDICT（约 200MB，请耐心等待）...")
    print(f"   源：{CSV_URL}")

    try:
        with urllib.request.urlopen(CSV_URL, timeout=600) as resp:
            with open(CSV_PATH, "wb") as f:
                shutil.copyfileobj(resp, f)
        size_mb = os.path.getsize(CSV_PATH) / (1024 * 1024)
        print(f"✅ 下载完成：{size_mb:.1f} MB")
    except Exception as e:
        print(f"❌ 下载失败：{e}")
        print("💡 提示：可以手动下载 ecdict.csv 放到 data/ 目录后重试")
        sys.exit(1)


def build():
    print(f"🔨 构建词库（取词频前 {TOP_N} 条）...")

    # 读取 CSV，收集 (bnc_freq, word, translation)
    entries = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get("word", "").strip()
            translation = row.get("translation", "").strip()
            bnc_str = row.get("bnc", "0").strip()

            # 跳过空词条、短语（含空格）、无翻译
            if not word or " " in word or not translation:
                continue
            # 只保留纯英文单词
            if not all(c.isascii() and (c.isalpha() or c == "-" or c == "'") for c in word):
                continue
            if len(word) < 1:
                continue

            # BNC: 真实值 1~45000（排名，越低越常见），≥50000 是人为编码，排除
            # FRQ: COCA 词频排名，1=最常见
            # Collins: 星级 1-5，越高越重要
            try:
                bnc = int(bnc_str)
            except ValueError:
                bnc = 0

            # 排除人为编码值（>= 45000）
            if bnc >= 45000:
                bnc = 0

            entries.append((bnc, word, translation))

    print(f"   原始条目（过滤后）：{len(entries)} 个")

    # 排序：有 BNC 排名的优先（升序，1=最常见），无排名的排后面
    entries.sort(key=lambda x: (0 if 0 < x[0] < 45000 else 1, x[0]))

    # 取前 TOP_N
    selected = entries[:TOP_N]

    # 构建 {word: meaning} 字典
    result = {}
    for bnc, word, translation in selected:
        # 简化翻译
        meaning = translation
        # 替换 \n（字面量）为分号
        meaning = meaning.replace("\\n", "；")
        # 去掉词性缩写 (n. / vt. / adj. / art. 等)
        meaning = re.sub(r'\b[a-z]+\.\s*', '', meaning)
        # 只取第一义项
        meaning = meaning.split("；")[0].split(";")[0].strip()
        # 限制长度
        if len(meaning) > 100:
            meaning = meaning[:100]
        if meaning:
            result[word] = meaning

    print(f"   有效词条（含释义）：{len(result)} 个")

    # 保存 JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    print(f"✅ 词库构建完成：{OUTPUT}")
    print(f"   词条数：{len(result)}")
    # 示例
    samples = list(result.items())[:5]
    for w, m in samples:
        print(f"   {w}: {m}")


if __name__ == "__main__":
    if not os.path.exists(CSV_PATH) or FORCE:
        download_csv()
    build()
