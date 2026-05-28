"""
专用解析器：入党积极分子培训班题库导出格式 → JSON 题库

处理的问题：
- 多个选项在同一行 (A、xx B、xx C、xx D、xx)
- "试题类型 单选题题目" 前缀
- "分值2" / "分值 2" 标记
- 判断题无选项 (只有 正确/错误)
- 多选题多答案 (答案: ABC)
- 缺少选项的异常题
- 节标题/说明文字等非题目内容

用法（CLI）：
    python parse_party.py                    # 解析 data/raw_party.txt → party_bank.json
    python parse_party.py <输入文件> [输出文件]  # 自定义路径

用法（作为模块导入）：
    from parse_party import parse_raw_text
    questions = parse_raw_text(你的文本字符串)
"""
import re
import json
import os
import sys


# ========================
# 第一步：逐行分类
# ========================

def classify_line(line):
    """分类一行：question, option, answer, section, ignore"""
    if not line or not line.strip():
        return 'blank'
    
    s = line.strip()
    
    # 答案行
    if re.match(r'^答案[：:]\s*', s):
        return 'answer'
    
    # 选项行（行首是 A、B、C、D、E 等）
    if re.match(r'^[A-E]\s*[、\.\)）]', s):
        return 'option'
    
    # 题目起始行（数字开头 + 顿号/点）
    if re.match(r'^\d+\s*[、,，.]', s):
        # 排除明显的节标题
        if re.search(r'^(单选题|多选题|判断题|填空题|简答题)\s*(分数|题型)', s.replace(' ', '')):
            return 'section'
        if re.search(r'^(注意事项|试卷标题|试卷满分|题型数量|试题类型\s*只)', s):
            return 'ignore'
        if re.search(r'^\d+[、,，.]\s*\d+[\.\）\)]', s):
            return 'section'
        return 'question'
    
    # "试题类型" 格式
    if re.match(r'试题类型\s*(单选|多选|判断|填空|简答)题', s):
        return 'question'
    
    return 'other'


# ========================
# 第二步：提取选项（支持同行多选项）
# ========================

def extract_options_from_line(line):
    """
    从一行中提取所有选项，返回 {letter: text} 或 None
    处理 A、xx B、xx C、xx D、xx 同行多选项
    """
    s = line.strip()
    
    # 尝试多选项提取（优先）
    # 匹配 A、xxx B、xxx C、xxx D、xxx 格式
    opts = re.findall(
        r'([A-E])\s*[、\.\)）]\s*([^A-E]*?)(?=\s*[A-E]\s*[、\.\)）]|$)',
        s
    )
    if len(opts) >= 2:
        result = {}
        for letter, value in opts:
            clean_val = value.strip().rstrip('，,')
            if clean_val:
                result[letter] = clean_val
        if len(result) >= 2:
            return result
    
    # 单选项
    m = re.match(r'^([A-E])\s*[、\.\)）]\s*(.+)$', s)
    if m:
        return {m.group(1): m.group(2).strip()}
    
    return None


def extract_judge_options():
    """判断题的标准选项"""
    return {"A": "正确", "B": "错误"}


# ========================
# 第三步：解析题目文本
# ========================

def clean_question_text(text):
    """清洗题目文本，去掉杂音"""
    # 去掉 "试题类型X选题题目" 前缀
    text = re.sub(r'^试题类型\s*(单选|多选|判断|填空|简答)题\s*', '', text)
    # 去掉 "试题类型X选题" 前缀（另一种格式）
    text = re.sub(r'^试题类型\s*(单选|多选|判断|填空|简答)\s*', '', text)
    # 去掉行尾的 "分值数字" 
    text = re.sub(r'\s*分值\s*\d+(?:\.\d+)?\s*$', '', text)
    # 去掉 "(2、0)" 之类的分值标记
    text = re.sub(r'\s*[（(]\s*\d+\s*[、，,]\s*\d+\s*[）)]\s*$', '', text)
    # 去掉 "。分值2" 
    text = re.sub(r'\s*分值\s*\d+', '', text)
    # 标准化空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def strip_question_number(text):
    """去掉题目前缀编号"""
    return re.sub(r'^\d+\s*[、,，.]\s*', '', text).strip()


# ========================
# 第四步：判断题目类型
# ========================

def determine_type(q_text, options, answer):
    """判断题型：single / multi / judge"""
    # 显式标记
    if any(kw in q_text for kw in ["多选题", "多项选择"]):
        return "multi"
    if any(kw in q_text for kw in ["判断题", "判断对错"]):
        return "judge"
    
    # 答案长度 > 1 且全是 A-F → 多选
    clean_ans = answer.upper().replace(' ', '')
    if len(clean_ans) > 1 and all(c in 'ABCDEFGH' for c in clean_ans):
        return "multi"
    
    # 恰好 2 个选项且是 A/B + 正确/错误 → 判断
    if len(options) == 2 and set(options.keys()) <= {'A', 'B'}:
        vals = [v.strip() for v in options.values()]
        if '正确' in vals and '错误' in vals:
            return "judge"
        if '对' in vals and '错' in vals:
            return "judge"
        return "single"
    
    return "single"


# ========================
# 第五步：主解析函数
# ========================

def normalize_key(text):
    """去重用的归一化键：去除非中文非字母非数字的字符，取前80字符"""
    clean = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9（）()]', '', text)[:80]
    return clean


def parse_raw_text(text):
    """
    解析入党积极分子培训班的原始文本，返回题目列表。

    参数：
        text: 原始文本字符串

    返回：
        [{"id": 1, "type": "single|multi|judge", "text": "...", "options": {"A":"..."}, "answer": "A"}, ...]
    """
    # 截断：只处理第一个完整导出
    duplicate_marker = "\n350、1. 单选题分数60题型数量30"
    if duplicate_marker in text:
        text = text[:text.index(duplicate_marker)]

    lines = text.splitlines()

    # 1. 先分组：找到每道题的起始行
    groups = []
    current_start = None

    for i, line in enumerate(lines):
        cat = classify_line(line)
        if cat == 'question':
            if current_start is not None:
                groups.append((current_start, i - 1))
            current_start = i
        elif cat in ('section', 'ignore'):
            if current_start is not None:
                groups.append((current_start, i - 1))
                current_start = None

    if current_start is not None:
        groups.append((current_start, len(lines) - 1))

    # 2. 解析每组
    parsed_questions = []
    for start, end in groups:
        block_lines = [lines[j] for j in range(start, end + 1)]

        q_text_parts = []
        options = {}
        answer = ""
        has_options = False

        for line in block_lines:
            s = line.strip()
            if not s:
                continue

            cat = classify_line(s)

            if cat == 'question':
                q_line = clean_question_text(s)
                q_text_parts.append(q_line)

            elif cat == 'option':
                opts = extract_options_from_line(s)
                if opts:
                    options.update(opts)
                    has_options = True

            elif cat == 'answer':
                m = re.match(r'^答案[：:]\s*(.+?)\s*$', s)
                if m:
                    raw_ans = m.group(1).strip()
                    answer = re.sub(r'[\s\(\)（）]', '', raw_ans)

            else:
                if not has_options and not re.match(r'^[A-E]\s*[、\.\)）]', s):
                    q_text_parts.append(s)

        q_text = ' '.join(q_text_parts)
        q_text = clean_question_text(q_text)
        q_text = strip_question_number(q_text)

        # 过滤节标题
        skip_patterns = [
            r'^(试卷标题|试卷满分|题型数量|注意事项)',
            r'^[单多判填简]选题\s*(分数|题型)',
            r'^\d+[\.\）\)]\s*[单多判填简]选题',
            r'^试题类型\s*只',
            r'^1\.\s*单选题',
            r'^2\.\s*多选题',
        ]
        if any(re.search(p, q_text) for p in skip_patterns):
            continue

        # 判断题补充标准选项
        if not has_options and len(options) == 0:
            judge_keywords = ['党员要发扬', '我们党深刻认识到', '十九大报告指出', '社会主义核心价值观是']
            if any(kw in q_text for kw in judge_keywords) or \
               ('。' in q_text and len(q_text) > 10 and not re.search(r'[（(]', q_text)):
                options = extract_judge_options()
                has_options = True

        if not has_options and not answer:
            continue
        if len(options) <= 1 and not answer:
            continue
        if len(q_text) < 5:
            continue

        qtype = determine_type(q_text, options, answer)
        parsed_questions.append({
            "id": len(parsed_questions) + 1,
            "type": qtype,
            "text": q_text,
            "options": options,
            "answer": answer,
        })

    # ===== 后处理：去重 =====
    text_map = {}
    for q in parsed_questions:
        key = normalize_key(q["text"])
        if key in text_map:
            existing = text_map[key]
            if q["answer"] and not existing["answer"]:
                text_map[key] = q
            elif q["answer"] and existing["answer"] and len(q["options"]) > len(existing["options"]):
                text_map[key] = q
            elif not q["answer"] and not existing["answer"] and len(q["options"]) > len(existing["options"]):
                text_map[key] = q
        else:
            text_map[key] = q

    deduped = []
    for key, q in text_map.items():
        if len(q["options"]) <= 1 and not q["answer"]:
            continue
        q["id"] = len(deduped) + 1
        deduped.append(q)
    parsed_questions = deduped

    # 修复已知缺答案的题（人工核对）
    fixes = [
        ("1953年7月27日，由朝鲜人民军最高司令官", "B", "single"),
        ("1997年7月1日，香港回归祖国标志着邓小平", "B", "single"),
        ("是五四运动以来我国发生的三大历史性事件", "ABC", "multi"),
        ("被称为中国共产党历史上的两个伟大转折点是", "BC", "multi"),
        ("全会提出，加快发展()，推动经济体系优化升级。坚持把发展经济着力点放在()", "AD", "multi"),
        ("参观《复兴之路》展览时指出", "C", "single"),
    ]
    for q in parsed_questions:
        for pattern, ans, qtype in fixes:
            if pattern in q["text"] and not q["answer"]:
                q["answer"] = ans
                q["type"] = qtype
                break

    for q in parsed_questions:
        if not q["answer"]:
            if "正确" in str(list(q["options"].values())) and "错误" in str(list(q["options"].values())):
                q["type"] = "judge"

    return parsed_questions


# ========================
# CLI 入口
# ========================

def main():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(SCRIPT_DIR, "data")

    # 解析命令行参数
    if len(sys.argv) >= 2:
        raw_file = sys.argv[1]
    else:
        raw_file = os.path.join(DATA_DIR, "raw_party.txt")

    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        output_file = os.path.join(DATA_DIR, "party_bank.json")

    if not os.path.exists(raw_file):
        print(f"❌ 未找到输入文件: {raw_file}")
        sys.exit(1)

    print(f"📖 读取: {raw_file}")
    with open(raw_file, "r", encoding="utf-8") as f:
        text = f.read()

    questions = parse_raw_text(text)
    print(f"📊 解析出 {len(questions)} 道题目")

    types_count = {"single": 0, "multi": 0, "judge": 0, "fill": 0}
    for q in questions:
        t = q.get("type", "unknown")
        types_count[t] = types_count.get(t, 0) + 1
    for t, c in types_count.items():
        if c > 0:
            print(f"   {t}: {c}")

    bank_data = {
        "id": "party_bank",
        "original_filename": "2026年上半年入党积极分子培训班(题库导出)",
        "upload_time": "2026-05-27 19:00:00",
        "questions": questions,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(bank_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已保存: {output_file}")
    print(f"   文件大小: {os.path.getsize(output_file)} 字节")

    # 打印样本
    print("\n=== 样题 ===")
    for q in questions[:3]:
        print(f"  [{q['type']}] {q['text'][:60]}")
        opts_preview = {k: v[:25] for k, v in q['options'].items()}
        print(f"     选项: {opts_preview}")
        print(f"     答案: {q['answer']}")

    # 打印有问题的
    issues_found = False
    for q in questions:
        problems = []
        if len(q['options']) < 2:
            problems.append("选项不足")
        if not q['answer']:
            problems.append("缺答案")
        if problems:
            if not issues_found:
                print("\n⚠️  有问题的题目:")
                issues_found = True
            print(f"  Q{q['id']} [{q['type']}]: {'; '.join(problems)}")
            print(f"    文本: {q['text'][:60]}")
    if not issues_found:
        print("\n✅ 所有题目完整无缺！")


if __name__ == "__main__":
    main()
