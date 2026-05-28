"""
生成 CET-6 高频词汇数据（使用 DeepSeek API）
分批生成并合并为 vocab_cet6.json

用法：
    python generate_vocab.py                    # 正常生成（批量从 1 到 10）
    python generate_vocab.py --start 5           # 从第 5 批开始（断点续传）
    python generate_vocab.py --batch 1           # 只生成 1 批
"""
import json
import os
import sys
import time
import re
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
OUTPUT = os.path.join(DATA_DIR, "vocab_cet6.json")

# 读取 API Key
api_key = os.environ.get("DEEPSEEK_API_KEY", "")
if not api_key:
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip("\"'")
                    break

if not api_key:
    print("❌ DEEPSEEK_API_KEY 未设置（请放在 .env 文件或环境变量中）")
    sys.exit(1)

# 解析命令行参数
START_BATCH = 1
MAX_BATCHES = 10
SINGLE_BATCH = None

for i, arg in enumerate(sys.argv[1:]):
    if arg == "--start" and i + 1 < len(sys.argv[1:]):
        START_BATCH = int(sys.argv[i + 2])
    elif arg == "--batch" and i + 1 < len(sys.argv[1:]):
        SINGLE_BATCH = int(sys.argv[i + 2])


def call_ai(prompt, max_tokens=4000):
    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个JSON输出机器人，只输出合法JSON数组。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode('utf-8'))
        content = body["choices"][0]["message"]["content"]

    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if m:
        content = m.group(1)

    return json.loads(content)


# 分批提示词
BATCH_PROMPT_TPL = """请生成30个大学英语六级(CET-6)高频词汇，按JSON数组格式返回。

每个词汇包含以下字段：
- word: 英文单词
- phonetic: 音标
- meaning: 中文释义（1-2个最核心的意思）
- example: 英文例句
- translation: 例句中文翻译

要求：
1. 选择真正高频、六级考试常考的词汇
2. 不要和之前生成过的重复
3. 难度覆盖六级核心词汇
4. 例句要体现单词在语境中的用法，长度适中

返回格式严格为JSON数组：
[
  {{"word":"abandon","phonetic":"/əˈbændən/","meaning":"放弃；遗弃","example":"They had to abandon the project due to lack of funds.","translation":"由于缺乏资金，他们不得不放弃这个项目。"}}
]

请开始生成第{BATCH_NUM}批："""

all_words = []
existing_words = set()

# 如果已有输出文件，先加载
if os.path.exists(OUTPUT):
    try:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        for w in existing_data.get("words", []):
            word = w.get("word", "").strip().lower()
            if word:
                existing_words.add(word)
                all_words.append(w)
        print(f"📖 已有词汇: {len(all_words)} 词")
    except Exception:
        print("⚠️  无法读取已有词汇文件，从头开始")

# 确定批次数
if SINGLE_BATCH:
    batches = [SINGLE_BATCH]
else:
    batches = range(START_BATCH, MAX_BATCHES + 1)

for batch in batches:
    print(f"\n=== 生成第 {batch}/{MAX_BATCHES} 批 ===")
    prompt = BATCH_PROMPT_TPL.replace("{BATCH_NUM}", str(batch))

    if existing_words:
        recent = list(existing_words)[-20:]
        prompt += f"\n\n已经生成过的词汇：{', '.join(recent)}\n请确保不要重复。"

    try:
        words = call_ai(prompt)
        print(f"  收到 {len(words)} 个词")

        new_count = 0
        for w in words:
            word = w.get("word", "").strip().lower()
            if word and word not in existing_words:
                existing_words.add(word)
                all_words.append({
                    "word": word,
                    "phonetic": w.get("phonetic", ""),
                    "meaning": w.get("meaning", ""),
                    "example": w.get("example", ""),
                    "translation": w.get("translation", ""),
                })
                new_count += 1

        print(f"  新增: {new_count} 词 | 累计: {len(all_words)} 词")

        # 每批保存一次
        final_data = {
            "id": "vocab_cet6",
            "name": "CET-6 六级高频词汇",
            "total": len(all_words),
            "words": all_words,
        }
        with open(OUTPUT + ".tmp", "w", encoding="utf-8") as f:
            json.dump(all_words, f, ensure_ascii=False, indent=2)
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)

        if batch < max(batches):
            time.sleep(2)

    except Exception as e:
        print(f"  第{batch}批失败: {e}")
        continue

# 清理临时文件
tmp_path = OUTPUT + ".tmp"
if os.path.exists(tmp_path):
    os.remove(tmp_path)

print(f"\n✅ 完成！共 {len(all_words)} 个六级词汇")
print(f"已保存到 {OUTPUT}")
