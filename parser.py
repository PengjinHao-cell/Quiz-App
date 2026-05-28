"""
题库文件解析模块
支持 PDF / DOCX / TXT 格式的文件，提取题目（文本、选项、正确答案）
使用状态机处理多行题目和跨页分割

支持双引擎解析：
1. 标准引擎（_parse_questions）— 处理 "1、题目\nA、选项\n答案：A" 格式
2. 专用引擎（parse_party.parse_raw_text）— 处理入党格式（试题类型XXX分值2）
   当标准引擎找不到题或检测到入党格式标记时，自动 fallback
"""
import re
import hashlib

try:
    import docx
except ImportError:
    docx = None

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


# 专用解析器：处理入党积极分子培训班等异形格式
# 懒加载——parse_party 较大，只在检测到需要时才 import
def _try_party_parser(text: str):  # -> list | None  (Python 3.10+)
    """
    尝试用专用解析器（parse_party.parse_raw_text）解析文本。
    该解析器专门处理 "试题类型X选题题目XXXX分值2" 等异形格式。
    返回题目列表，若不适配则返回 None。
    """
    try:
        from parse_party import parse_raw_text
        questions = parse_raw_text(text)
        if questions and len(questions) >= 3:
            return questions
        return None
    except Exception:
        return None


# ========================
#  阅读格式检测与解析
# ========================

_READING_KEYWORDS_EN = [
    'according to the', 'according to the passage', 'passage', 'the author',
    'implies', 'suggests that', 'paragraph', 'infer from', 'in the context',
    'refers to', 'based on the', 'the main idea', 'the best title',
    'the purpose of', 'can be learned', 'can be inferred',
    'we can conclude', 'the underlined', 'the word',
    'which of the following', 'the passage', 'the text', 'the article',
    'what is', 'what does', 'why does', 'how does',
    'in paragraph', 'mentioned in', 'described as',
]

_READING_KEYWORDS_ZH = [
    '根据文章', '根据本文', '根据上文', '根据原文',
    '本文主要', '文章主要', '文章主旨', '最佳标题',
    '作者认为', '作者提到', '作者意在',
    '从文中', '从文章', '从这段', '从划线',
    '下列哪项', '以下哪项', '以下哪个',
    '文中划线', '上文提到', '这段话',
    '可以推断', '可以看出', '可以得出',
    '文章指出', '文章提到', '文章认为',
    '文中提到', '文中指出',
    '阅读下列', '阅读下面',
]


def _detect_is_reading(text: str) -> bool:
    """
    检测文本是否为阅读理解格式（长篇正文 + 选择题）。
    同时支持中文和英文。
    判断依据：
    1. 包含一个 ≥300 字符的连续段落（文章正文）
    2. 段落后紧跟 3+ 道选择题
    3. 题目文本含阅读理解关键词
    """
    if not text or len(text) < 500:
        return False

    lines = text.splitlines()
    # 找所有连续段落（连续非空行），再合并彼此相邻的段落形成"正文块"
    raw_paragraphs = []
    current_para = []
    for line in lines:
        s = line.strip()
        if s:
            current_para.append(s)
        else:
            if current_para:
                raw_paragraphs.append(' '.join(current_para))
                current_para = []
    if current_para:
        raw_paragraphs.append(' '.join(current_para))

    # 将相邻段落合为正文块（中间无题号分隔的段落视为同一篇文章）
    # 题号模式：用于判断段落是否含题号（题号后的内容不是正文）
    q_start_pattern = re.compile(r'^\d+\s*[、,，.\u3001]\s*.{10,}')
    passage_blocks = []
    current_block = []
    for para in raw_paragraphs:
        if q_start_pattern.match(para):
            # 遇到题号行，当前正文块结束
            if current_block:
                passage_blocks.append(' '.join(current_block))
                current_block = []
            break  # 题号之后的都不是正文
        current_block.append(para)
    if current_block:
        passage_blocks.append(' '.join(current_block))

    # 找长正文块
    threshold = 150 if _is_chinese_heavy(text) else 300
    long_para_indices = [i for i, p in enumerate(passage_blocks) if len(p) >= threshold]
    if not long_para_indices:
        return False

    # 在长段落后的内容找题目
    for pi in long_para_indices:
        # 长段落之后的文本
        after_text = '\n'.join(lines)
        # 在长段落位置之后的题号
        question_pattern = re.compile(r'^\d+\s*[、,，.\u3001]\s*', re.MULTILINE)
        all_matches = list(question_pattern.finditer(after_text))
        if len(all_matches) >= 2:
            # 检查题目文本是否含阅读关键词
            question_texts_after = []
            for m in all_matches:
                start = m.end()
                end_line = after_text.find('\n', start)
                q_line = after_text[start:end_line].strip() if end_line > 0 else after_text[start:start+100].strip()
                if q_line:
                    question_texts_after.append(q_line)

            reading_hits = sum(
                1 for qt in question_texts_after[:5]  # 只看前5题
                if any(kw in qt.lower() for kw in _READING_KEYWORDS_EN)
                or any(kw in qt for kw in _READING_KEYWORDS_ZH)
            )
            # 至少1题含阅读关键词即视为阅读（2题以上更可靠，但短阅读也支持）
            if reading_hits >= 1:
                return True

    return False


def _parse_reading(text: str) -> dict:
    """
    解析阅读理解文本，分离文章正文和题目。
    返回：
    {"type": "reading", "language": "zh/en", "passages": [{"id": 1, "title": "", "text": "...", "questions": [...]}]}
    """
    # 判断语言
    lang = 'zh' if _is_chinese_heavy(text) else 'en'

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # 找第一个题号的位置
    question_start = None
    for i, line in enumerate(lines):
        if re.match(r'^\d+\s*[、,，.\u3001]\s*', line):
            # 检查这行是不是真的问题（不是文章段落里的数字）
            rest = re.sub(r'^\d+\s*[、,，.\u3001]\s*', '', line)
            if len(rest) > 10:
                question_start = i
                break

    if question_start is None:
        return {"type": "reading", "language": lang, "passages": []}

    # 文章正文：第一个题号之前的所有内容
    passage_lines = lines[:question_start]
    passage_text = '\n\n'.join(passage_lines) if lang == 'zh' else ' '.join(passage_lines)

    # 题目部分：第一个题号之后的所有内容
    question_text = '\n'.join(lines[question_start:])

    # 用标准解析器解析题目
    questions = _parse_questions('\n'.join(lines[question_start:]))

    if not questions:
        return {"type": "reading", "language": lang, "passages": []}

    passage = {
        "id": 1,
        "title": "",
        "text": passage_text.strip(),
        "questions": questions
    }

    return {
        "type": "reading",
        "language": lang,
        "passages": [passage]
    }


def _detect_party_format(text: str) -> bool:
    """
    检测文本是否包含入党/异形格式的特征标记。
    "试题类型单选题题目"、"试题类型多选题题目"、"分值2" 等是典型特征。
    """
    markers = [
        '试题类型单选题',
        '试题类型多选题',
        '试题类型判断题',
        '分值2',
        '试题类型 单选题',
        '试题类型 多选题',
    ]
    return any(m in text for m in markers)


def parse_file(file_path: str, filename: str) -> dict:
    """
    根据文件扩展名选择解析方法。
    支持 PDF / DOCX / TXT，三引擎自动识别。

    返回 dict，两种格式：
    - 普通题库：{"type": "quiz", "questions": [{...}, ...]}
    - 阅读理解：{"type": "reading", "language": "zh/en", "passages": [{...}, ...]}
    """
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        text = _extract_pdf(file_path)
    elif ext == "docx":
        text = _extract_docx(file_path)
    elif ext == "txt":
        text = _extract_txt(file_path)
    else:
        raise ValueError(f"不支持的文件格式：.{ext}（仅支持 PDF、DOCX、TXT）")

    return _parse_with_fallback(text)


def _extract_pdf(file_path: str) -> str:
    """从 PDF 提取纯文本"""
    text = ""

    if fitz is not None:
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            if text.strip():
                return text
        except Exception:
            pass

    if PyPDF2 is not None:
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                return text
        except Exception:
            pass

    if not text.strip():
        raise RuntimeError("无法从 PDF 文件中提取文字（文件可能是扫描版图片PDF）")

    return text


def _extract_docx(file_path: str) -> str:
    """从 DOCX 提取纯文本"""
    if docx is None:
        raise RuntimeError("python-docx 未安装")
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _extract_txt(file_path: str) -> str:
    """从纯文本文件读取内容"""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _normalize_text(text: str) -> str:
    """统一处理文本中的各种空白和特殊字符"""
    # 替换全角空格为半角
    text = text.replace('\u3000', ' ')
    # 规范化换行
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text


def _hash_question_text(text: str) -> str:
    """计算题目文本的哈希，用于去重"""
    # 去除空白后计算 MD5
    cleaned = re.sub(r'\s+', '', text)
    return hashlib.md5(cleaned.encode('utf-8')).hexdigest()


def _parse_with_fallback(text: str) -> dict:
    """
    三引擎解析，返回统一 dict 格式：
    - 阅读模式:  {"type": "reading", "language": "zh/en", "passages": [...]}
    - 题库模式:  {"type": "quiz", "questions": [...]}

    引擎优先级：
    1. 阅读检测（_detect_is_reading）— 识别长篇正文+选择题，中英文均支持
    2. 入党格式检测（_detect_party_format）— 识别 "试题类型X选题"
    3. 标准状态机（_parse_questions）— 处理常规题目
    """
    # 第一轮：阅读格式检测（中英文均支持）
    if _detect_is_reading(text):
        reading_result = _parse_reading(text)
        if reading_result.get('passages'):
            return reading_result

    # 第二轮：入党格式检测
    if _detect_party_format(text):
        party_result = _try_party_parser(text)
        if party_result is not None:
            return {"type": "quiz", "questions": party_result}

    # 第三轮：标准状态机解析
    questions = _parse_questions(text)
    return {"type": "quiz", "questions": questions}


def _parse_questions(text: str) -> list:
    """
    【标准引擎】从纯文本中解析出题目，使用状态机处理多行题目。
    
    适合 "1、题目\nA、选项 B、选项\n答案：A" 这种标准格式。

    PDF 格式特点：
    - 题目以 "N、" 开头（数字+中文顿号）
    - 选项以 "A、" "B、" "C、" "D、" "E、" 开头
    - 答案单独一行："答案：A"
    - 题目可能跨越多行（选项行之间插入的普通文本行也属于题目文本）
    - 页分割可能出现在任何位置
    """
    if not text or not text.strip():
        return []

    text = _normalize_text(text)

    # 将文本按行分割，但保留有效的非空行
    raw_lines = text.splitlines()

    # 第一步：预处理——移除页分割标记和纯空白行，合并被截断的行
    lines = []
    for line in raw_lines:
        line = line.strip()
        if not line or line == '---PAGE---':
            continue
        lines.append(line)

    # 第二步：找到所有题目起始位置（以 "数字、" 开头的行）
    # 注意：标题行如 "1、" 也可能是选项列表中的序号，需要排除
    question_start_pattern = re.compile(
        r'^(\d+)\s*[、,，.]\s*(.+)'
    )

    # 选项行模式
    option_pattern = re.compile(
        r'^([A-H])\s*[、\.\)）\s]\s*(.+)'
    )

    # 答案行模式
    answer_pattern = re.compile(
        r'^(?:答案|正确答案|参考答案|Answer)\s*[：:是为\s]*\s*([A-H])',
        re.IGNORECASE
    )

    # 分类/标题过滤模式
    filter_pattern = re.compile(
        r'^(试题类型|题型|第[一二三四五六七八九十\d]+章|第[一二三四五六七八九十\d]+节|'
        r'[一二三四五六七八九十]+[、.]\s*(单选题|多选题|判断题|简答题|填空题))'
    )

    # 识别题号开头，收集所有可能的题目起始行
    question_starts = []
    for i, line in enumerate(lines):
        m = question_start_pattern.match(line)
        if m:
            qnum = int(m.group(1))
            # 过滤掉可能的假阳性（如选项内的数字列表）
            # 如果行太长或包含括号选项标记，可能是假起始
            rest = m.group(2)
            # 跳过分类标题
            if filter_pattern.match(rest):
                continue
            # 如果"题目编号"很大（>500），可能是误解
            if qnum > 500:
                continue
            question_starts.append((i, qnum, rest))

    # 如果没有找到题目，返回空
    if not question_starts:
        return []

    # 第三步：处理每道题（从起始行到下一题起始行之间）
    # 使用从后往前的序号重新分配，确保去重后序号连续
    raw_questions = []

    for idx, (start_idx, qnum, first_line_text) in enumerate(question_starts):
        # 确定本题结束位置
        if idx + 1 < len(question_starts):
            end_idx = question_starts[idx + 1][0]
        else:
            end_idx = len(lines)

        # 收集本题所有行
        question_lines = [first_line_text]  # 第一行文本（不含编号）
        current_options = {}
        current_answer = None
        current_text_lines = [first_line_text]

        # 遍历中间行
        accumulating_text = True  # 初始阶段在积累题目文本
        for j in range(start_idx + 1, end_idx):
            line = lines[j]

            # 检查答案行
            ans_m = answer_pattern.match(line)
            if ans_m:
                current_answer = ans_m.group(1).upper()
                accumulating_text = False
                continue

            # 先检查同一行多选项（紧凑格式如 "A、xx B、xx C、xx"）
            # 注意：不能用 [^A-H] 排除字母，因为中文文本可能包含字母（如"选项A"）
            # 改用分隔符分词：以 "A、/B、/C、" 模式分割
            multi_opts = re.findall(
                r'([A-H])\s*[、\.\)）]\s*([^、\.\)）]+?)(?=\s*[A-H]\s*[、\.\)）]|$)',
                line
            )
            if len(multi_opts) >= 2:
                for label, value in multi_opts:
                    lbl = label.upper()
                    if lbl not in current_options:
                        current_options[lbl] = value.strip()
                accumulating_text = False
                continue

            # 检查单选项行
            opt_m = option_pattern.match(line)
            if opt_m:
                label = opt_m.group(1).upper()
                value = opt_m.group(2).strip()
                if label not in current_options:
                    current_options[label] = value
                else:
                    # 重复选项标签，可能是多行题目文本的延续（误识别）
                    # 保守处理：视为题目文本
                    current_text_lines.append(line)
                accumulating_text = False
                continue
                for label, value in multi_opts:
                    lbl = label.upper()
                    if lbl not in current_options:
                        current_options[lbl] = value.strip()
                accumulating_text = False
                continue

            # 普通文本行：如果还在积累文本阶段或没有选项，则追加到题目文本
            if accumulating_text or not current_options:
                current_text_lines.append(line)
            else:
                # 已有选项了，非选项非答案的文本行可能是题目文本的延续（PDF 换行）
                # 检查是否像答案行或下一个题号
                if not answer_pattern.match(line) and not question_start_pattern.match(line):
                    # 如果它看起来不像新题也不像选项，加入题目文本
                    if not re.match(r'^[A-H]\s*[、\.\)）]', line):
                        current_text_lines.append(line)

        # 合并题目文本
        question_text = ''.join(current_text_lines).strip()
        # 清理多余空格
        question_text = re.sub(r'\s+', '', question_text) if _is_chinese_heavy(question_text) else re.sub(r'\s+', ' ', question_text)
        # 去除开头的顿号/逗号
        question_text = re.sub(r'^[、,，]\s*', '', question_text)
        # 去除尾部的 "解析：XXX" 或 "解析:XXX" 注释
        question_text = re.sub(r'\s*解析[：:].*$', '', question_text)
        # 去除尾部的 "D多选题:" 等标记
        question_text = re.sub(r'\s*[A-H]\s*[多单选]选题[：:].*$', '', question_text)
        question_text = question_text.strip()

        # 跳过过短的文本（防止把标题/标记当题目）
        if len(question_text) < 3:
            continue

        # 过滤掉分类标题
        if filter_pattern.match(question_text):
            continue

        # 仅当有题目文本且有至少 2 个选项时保存
        if question_text and len(current_options) >= 2:
            raw_questions.append({
                "text": question_text,
                "options": current_options,
                "answer": current_answer or "",
            })

    # 第四步：去重（基于题目文本的 MD5）
    seen_hashes = set()
    deduped = []
    for q in raw_questions:
        h = _hash_question_text(q["text"])
        if h not in seen_hashes:
            seen_hashes.add(h)
            deduped.append(q)

    # 第五步：如果去重后数量合理（< 1000），使用去重结果
    final_questions = deduped if len(deduped) > 0 else raw_questions

    # 第六步：规范化——给每道题重新分配 ID
    result = []
    for i, q in enumerate(final_questions):
        result.append({
            "id": i + 1,
            "text": q["text"],
            "options": q["options"],
            "answer": q["answer"],
        })

    return result


def _is_chinese_heavy(text: str) -> bool:
    """判断文本是否以中文为主"""
    if not text:
        return False
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return chinese_chars > len(text) * 0.3


def create_sample_questions() -> list:
    """生成示例题库，供测试用"""
    return [
        {
            "id": 1,
            "text": "Python 中，以下哪个不是可变数据类型？",
            "options": {
                "A": "列表 (list)",
                "B": "字典 (dict)",
                "C": "元组 (tuple)",
                "D": "集合 (set)",
            },
            "answer": "C",
        },
        {
            "id": 2,
            "text": "以下哪个关键字用于在 Python 中定义函数？",
            "options": {
                "A": "func",
                "B": "def",
                "C": "function",
                "D": "define",
            },
            "answer": "B",
        },
        {
            "id": 3,
            "text": "list('hello') 的结果是什么？",
            "options": {
                "A": "['hello']",
                "B": "['h', 'e', 'l', 'l', 'o']",
                "C": "'hello'",
                "D": "报错 TypeError",
            },
            "answer": "B",
        },
        {
            "id": 4,
            "text": "Python 中如何打开文件并读取所有内容？",
            "options": {
                "A": "open('f.txt').readlines()",
                "B": "with open('f.txt') as f: data = f.read()",
                "C": "file.open('f.txt')",
                "D": "读取文件在 Python 中只能用 os 模块",
            },
            "answer": "B",
        },
        {
            "id": 5,
            "text": "以下哪个是 Python 合法的变量名？",
            "options": {
                "A": "2things",
                "B": "my-var",
                "C": "_my_var",
                "D": "class",
            },
            "answer": "C",
        },
        {
            "id": 6,
            "text": "Python 中，以下哪个语句用于异常处理？",
            "options": {
                "A": "if ... else",
                "B": "try ... except",
                "C": "for ... in",
                "D": "switch ... case",
            },
            "answer": "B",
        },
        {
            "id": 7,
            "text": "以下哪个是 Python 的列表推导式？",
            "options": {
                "A": "[x for x in range(10)]",
                "B": "for x in range(10): list(x)",
                "C": "list(range(10))",
                "D": "range(10).to_list()",
            },
            "answer": "A",
        },
        {
            "id": 8,
            "text": "Python 中，lambda 函数的主要用途是？",
            "options": {
                "A": "创建匿名小函数",
                "B": "定义类的方法",
                "C": "导入模块",
                "D": "替代 print 语句",
            },
            "answer": "A",
        },
        {
            "id": 9,
            "text": "以下哪个方法可以将列表元素拼接成字符串？",
            "options": {
                "A": "list.join(sep)",
                "B": "sep.join(list)",
                "C": "str.concat(list)",
                "D": "list.concat(sep)",
            },
            "answer": "B",
        },
        {
            "id": 10,
            "text": "Python 中，装饰器（decorator）的语法符号是？",
            "options": {
                "A": "#",
                "B": "$",
                "C": "@",
                "D": "&",
            },
            "answer": "C",
        },
    ]