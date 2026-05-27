"""
题库文件解析模块
支持 PDF 和 DOCX 格式的文件，提取题目（文本、选项、正确答案）
"""

import re
import docx
import io
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None


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

    # 优先使用 pymupdf（效果更好）
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

    # 备用：PyPDF2
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
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _parse_questions(text: str) -> list:
    """
    从纯文本中解析出题目
    支持多种常见格式：
    
    格式1（编号+换行）：
        1. 题目内容
        A. 选项A
        B. 选项B
        C. 选项C  
        D. 选项D
        答案：A

    格式2（紧凑型）：
        1. 题目内容
        A. 选项A  B. 选项B  C. 选项C  D. 选项D
        正确答案: A

    格式3（分隔区）：
        单选题
        1. 题目内容
        A、选项A
        B、选项B
        答案:A
    """
    if not text or not text.strip():
        return []

    questions = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]

        # 检测题目起始行（匹配 "1." "1、" "1)" 等编号）
        question_match = re.match(
            r'^(?:（?\d+）?|[（(]\s*\d+\s*[）)]|第[一二三四五六七八九十\d]+题|[一二三四五六七八九十]+[、.]|\d+[\.\、\)）])\s*(.+)',
            line
        )

        if not question_match and i > 0:
            # 可能存在编号后直接跟文本或被分割的情况
            question_match = re.match(
                r'^(?:（?\d+）?|[（(]\s*\d+\s*[）)]|第[一二三四五六七八九十\d]+题|[一二三四五六七八九十]+[、.]|\d+[\.\、\)）])\s*(.+)',
                line
            )

        if question_match:
            question_text = question_match.group(1).strip() if question_match.lastindex else line
            options = {}
            answer = None

            # 向后扫描选项和答案
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                j += 1

                # 检测是否是下一题（结束条件）
                if re.match(
                    r'^(?:（?\d+）?|[（(]\s*\d+\s*[）)]|第[一二三四五六七八九十\d]+题|[一二三四五六七八九十]+[、.]|\d+[\.\、\)）])',
                    next_line
                ):
                    j -= 1  # 回退，让外层循环处理
                    break

                # 检测选项 (A. B. C. D. 或 A) B) 或 A、B、)
                option_match = re.match(
                    r'^([A-Ha-h])\s*[\.\、\）\))\s]\s*(.+)',
                    next_line
                )
                if option_match:
                    label = option_match.group(1).upper()
                    value = option_match.group(2).strip()
                    options[label] = value
                    continue

                # 检测答案行
                answer_match = re.match(
                    r'^(?:答案|正确答案|参考答案|Answer)\s*[：:是为\s]*\s*([A-Ha-h])',
                    next_line,
                    re.IGNORECASE
                )
                if answer_match:
                    answer = answer_match.group(1).upper()
                    continue

                # 如果同一行有多个选项（紧凑格式）
                multi_option = re.findall(
                    r'([A-Ha-h])\s*[\.\、\）\)]\s*([^A-H]+?)(?=\s*[A-Ha-h]\s*[\.\、\）\)]|$)',
                    next_line
                )
                if multi_option:
                    for label, value in multi_option:
                        options[label.upper()] = value.strip()
                    # 不再继续往后扫描选项（防止混淆）
                    continue

                # 非以上格式的行作为题目文本补充
                # 但优先检查是否是答案
                if not answer and not options:
                    ans2 = re.match(
                        r'^(?:答案|正确答案|参考答案|Answer)\s*[：:是为\s]*\s*([A-Ha-h])',
                        next_line,
                        re.IGNORECASE
                    )
                    if ans2:
                        answer = ans2.group(1).upper()
                        continue

            # 仅当有题目文本且有选项时保存
            if question_text and options:
                questions.append({
                    "id": len(questions) + 1,
                    "text": question_text,
                    "options": options,
                    "answer": answer or "",
                })

            i = j
        else:
            i += 1

    return questions


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