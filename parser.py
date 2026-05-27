"""
题库文件解析模块
支持 PDF 和 DOCX 格式的文件，提取题目（文本、选项、正确答案）
使用状态机处理多行题目和跨页分割
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


def parse_file(file_path: str, filename: str) -> list:
    """
    根据文件扩展名选择解析方法
    返回题目列表，每道题格式：
    {
        "id": int,
        "text": str,
        "options": {"A": str, "B": str, ...},
        "answer": str
    }
    """
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        text = _extract_pdf(file_path)
    elif ext == "docx":
        text = _extract_docx(file_path)
    else:
        raise ValueError(f"不支持的文件格式：.{ext}（仅支持 PDF 和 DOCX）")

    return _parse_questions(text)


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


def _parse_questions(text: str) -> list:
    """
    从纯文本中解析出题目，使用状态机方法处理多行题目。
    
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

            # 检查选项行
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

            # 尝试同一行多选项（紧凑格式）
            multi_opts = re.findall(
                r'([A-H])\s*[、\.\)）]\s*([^A-H]+?)(?=\s*[A-H]\s*[、\.\)）]|$)',
                line
            )
            if len(multi_opts) >= 2:
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

        # 跳过纯解析的假题目（题目文本太短的）
        if len(question_text) < 6:
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