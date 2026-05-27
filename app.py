"""
刷题通 Web 应用
- 支持上传 PDF / DOCX 题库文件
- 持久化存储：原始文件 + 解析后的 JSON 数据
- 考试模式 / 练习模式
- 题库列表管理
"""

import os
import re
import uuid
import json
import random
import datetime
import urllib.request
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
from parser import parse_file, create_sample_questions

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "quiz-app-secret-key-change-in-production")

# ---------- 配置 ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
ALLOWED_EXTENSIONS = {"pdf", "docx"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB 上传限制


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否在白名单内"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_bank_list() -> list:
    """加载所有题库的元数据（不加载完整题目）"""
    banks = []
    if not os.path.isdir(DATA_FOLDER):
        return banks

    for fname in os.listdir(DATA_FOLDER):
        if fname.endswith(".json"):
            filepath = os.path.join(DATA_FOLDER, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                banks.append({
                    "id": data.get("id", ""),
                    "original_filename": data.get("original_filename", ""),
                    "upload_time": data.get("upload_time", ""),
                    "question_count": len(data.get("questions", [])),
                })
            except Exception:
                continue

    # 按上传时间倒序排列
    banks.sort(key=lambda b: b["upload_time"], reverse=True)
    return banks


def load_bank(bank_id: str) -> dict:
    """根据题库 ID 加载完整数据"""
    filepath = os.path.join(DATA_FOLDER, f"{bank_id}.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"题库 {bank_id} 不存在")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_question_type(question: dict) -> str:
    """根据已有字段或题目内容推测题型：single / multi / judge"""
    # 优先使用存储的 type 字段
    stored_type = question.get("type", "")
    if stored_type in ("single", "multi", "judge"):
        return stored_type

    text = question.get("text", "")
    options = question.get("options", {})
    num_opts = len(options)
    answer = question.get("answer", "").upper().strip()
    text_upper = text.upper()

    # 判断题特征：2 个选项，或题干含 "判断题"、"正确/错误"
    if num_opts == 2 and set(options.keys()) <= {"A", "B"}:
        return "judge"
    if any(kw in text for kw in ["判断题", "判断对错", "正确错误", "对错题"]):
        return "judge"
    if any(kw in text_upper for kw in ["判断题", "判断对错", "×", "√", "TRUE", "FALSE"]):
        return "judge"

    # 多选题特征：题干含"多选题"、"多项选择"、"多选"，或答案长度 > 1
    if any(kw in text for kw in ["多选题", "多项选择", "多选", "多选题", "多项选择题"]):
        return "multi"
    if any(kw in text_upper for kw in ["MULTI", "多选", "多选题"]):
        return "multi"
    if len(answer) > 2 and all(c in "ABCDEFGH" for c in answer):
        return "multi"
    if number_match := re.search(r"(\d+)", answer):
        pass  # 纯数字答案不是多选题

    # 默认单选题
    return "single"


def sample_questions_proportional(questions: list, count: int) -> list:
    """按题型按比例抽选题目"""
    if count >= len(questions):
        return random.sample(questions, len(questions))

    # 按题型分组
    singles = [q for q in questions if detect_question_type(q) == "single"]
    multis = [q for q in questions if detect_question_type(q) == "multi"]
    judges = [q for q in questions if detect_question_type(q) == "judge"]

    pools = []
    if singles:
        pools.append(("single", singles))
    if multis:
        pools.append(("multi", multis))
    if judges:
        pools.append(("judge", judges))

    total = len(questions)
    result = []
    remaining = count

    for i, (ptype, pool) in enumerate(pools):
        if i == len(pools) - 1:
            # 最后一个池子用完剩余配额
            n = remaining
        else:
            n = max(1, int(count * len(pool) / total))
        n = min(n, len(pool), remaining)
        if n > 0:
            result.extend(random.sample(pool, n))
            remaining -= n

    # 如果还有配额，从所有题目中补齐
    if remaining > 0:
        already_ids = {q["id"] for q in result}
        remaining_pool = [q for q in questions if q["id"] not in already_ids]
        extra = random.sample(remaining_pool, min(remaining, len(remaining_pool)))
        result.extend(extra)

    random.shuffle(result)
    return result


def save_bank(bank_id: str, data: dict):
    """保存题库数据到 JSON 文件"""
    filepath = os.path.join(DATA_FOLDER, f"{bank_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def delete_bank_files(bank_id: str):
    """删除原始文件和 JSON 数据文件"""
    data_path = os.path.join(DATA_FOLDER, f"{bank_id}.json")
    if os.path.exists(data_path):
        # 尝试获取原始文件名
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            orig_name = data.get("original_filename", "")
            if orig_name:
                upload_path = os.path.join(UPLOAD_FOLDER, f"{bank_id}_{orig_name}")
                if os.path.exists(upload_path):
                    os.remove(upload_path)
        except Exception:
            pass
        os.remove(data_path)


# =========================== 页面路由 ===========================

@app.route("/")
def index():
    """欢迎页 - 题库列表"""
    banks = load_bank_list()
    return render_template("index.html", banks=banks)


@app.route("/upload", methods=["POST"])
def upload():
    """上传题库文件，解析并保存"""
    if "file" not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "未选择文件"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"不支持的文件格式，仅支持：{', '.join(ALLOWED_EXTENSIONS)}"}), 400

    mode = request.form.get("mode", "practice")  # 默认练习模式
    if mode not in ("practice", "exam"):
        mode = "practice"

    # 生成唯一题库 ID
    bank_id = uuid.uuid4().hex[:12]
    original_filename = secure_filename(file.filename)

    # 保存原始文件
    saved_filename = f"{bank_id}_{original_filename}"
    upload_path = os.path.join(UPLOAD_FOLDER, saved_filename)
    file.save(upload_path)

    # 解析文件
    try:
        questions = parse_file(upload_path, original_filename)
    except Exception as e:
        # 解析失败时删除上传的文件
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({"error": f"题目解析失败：{str(e)}"}), 400

    if not questions:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({"error": "文件中未检测到题目，请检查文件格式"}), 400

    # 保存解析后的数据
    bank_data = {
        "id": bank_id,
        "original_filename": original_filename,
        "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "questions": questions,
    }
    save_bank(bank_id, bank_data)

    # 返回成功，前端重定向到刷题页
    return jsonify({
        "success": True,
        "bank_id": bank_id,
        "question_count": len(questions),
        "mode": mode,
        "redirect": url_for("quiz_page", bank_id=bank_id, mode=mode),
    })


@app.route("/quiz/<bank_id>")
def quiz_page(bank_id):
    """刷题页面"""
    mode = request.args.get("mode", "practice")
    if mode not in ("practice", "exam"):
        mode = "practice"

    count = request.args.get("count", "0")  # 0 = 全部

    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return render_template("error.html", message="题库不存在或已被删除"), 404

    total_in_bank = len(bank["questions"])
    # 计算实际题目数
    count_int = int(count) if count.isdigit() else 0
    actual_total = count_int if count_int > 0 else total_in_bank
    actual_total = min(actual_total, total_in_bank)

    return render_template(
        "quiz.html",
        bank_id=bank_id,
        bank_name=bank["original_filename"],
        total=actual_total,
        mode=mode,
        count=count,
    )


@app.route("/api/bank/<bank_id>/questions")
def api_get_questions(bank_id):
    """API: 获取某个题库的题目（支持 count/q 参数）"""
    mode = request.args.get("mode", "practice")
    count = request.args.get("count", "0")  # 0 = 全部
    q = request.args.get("q", "").strip()  # 搜索关键词

    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return jsonify({"error": "题库不存在"}), 404

    questions = bank["questions"]

    # 搜索过滤
    if q:
        q_lower = q.lower()
        filtered = []
        for question in questions:
            if q_lower in question["text"].lower():
                filtered.append(question)
                continue
            for opt_text in question["options"].values():
                if q_lower in opt_text.lower():
                    filtered.append(question)
                    break
        questions = filtered

    # 按比例抽选题目
    count_int = int(count) if count.isdigit() else 0
    if count_int > 0 and count_int < len(questions):
        shuffled = sample_questions_proportional(questions, count_int)
    else:
        shuffled = random.sample(questions, len(questions))

    result = {
        "bank_id": bank_id,
        "bank_name": bank["original_filename"],
        "total": len(shuffled),
        "mode": mode,
        "questions": [],
    }

    for q in shuffled:
        qtype = detect_question_type(q)
        item = {
            "id": q["id"],
            "text": q["text"],
            "options": q["options"],
            "type": qtype,  # single / multi / judge
        }
        if mode == "practice":
            item["answer"] = q.get("answer", "")
        result["questions"].append(item)

    return jsonify(result)


@app.route("/api/bank/<bank_id>/submit", methods=["POST"])
def api_submit(bank_id):
    """提交答题结果，返回评分（仅评分实际抽选的题目）"""
    data = request.get_json()
    user_answers = data.get("answers", {})
    question_ids = data.get("question_ids", [])  # 实际展示的题目 ID 列表

    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return jsonify({"error": "题库不存在"}), 404

    all_questions = bank["questions"]
    # 构建 ID -> 题目的映射
    qmap = {str(q["id"]): q for q in all_questions}

    # 如果传了 question_ids，只评分这些题目；否则评分所有有答案的题目
    if question_ids:
        target_ids = [str(qid) for qid in question_ids]
    else:
        target_ids = [qid for qid in user_answers.keys() if user_answers[qid]]

    total = len(target_ids)
    correct_count = 0
    details = []

    for qid in target_ids:
        q = qmap.get(qid)
        if q is None:
            continue
        user_ans = user_answers.get(qid, "").strip().upper()
        correct_ans = q.get("answer", "").strip().upper()
        # 多选题：排序后比较
        if detect_question_type(q) == "multi":
            user_sorted = "".join(sorted(user_ans.replace(" ", "")))
            correct_sorted = "".join(sorted(correct_ans.replace(" ", "")))
            is_correct = user_sorted == correct_sorted
        else:
            is_correct = user_ans == correct_ans if correct_ans else False

        if is_correct:
            correct_count += 1

        details.append({
            "id": q["id"],
            "text": q["text"],
            "options": q["options"],
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
        })

    score = round(correct_count / total * 100, 1) if total > 0 else 0

    return jsonify({
        "total": total,
        "correct": correct_count,
        "score": score,
        "details": details,
    })


@app.route("/result/<bank_id>")
def result_page(bank_id):
    """结果页面"""
    return render_template("result.html", bank_id=bank_id)


@app.route("/api/bank/<bank_id>/delete", methods=["POST"])
def api_delete_bank(bank_id):
    """删除题库"""
    delete_bank_files(bank_id)
    return jsonify({"success": True})


# =========================== AI 文本解析 ===========================

def parse_with_llm(raw_text: str) -> list:
    """
    调用 DeepSeek API 将纯文本解析为结构化题目列表。
    返回格式同 parse_file：[{id, text, options, answer}, ...]
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        # 尝试从 .env 文件读取
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip("\"'")
                        break
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未设置（可放 ~/.zshrc 或项目 .env 文件）")

    prompt = f"""你是一个专业的题库解析助手。请将以下考试题目文本解析为JSON格式。

要求：
1. 识别每一道题目及其题型（single=单选题, multi=多选题, judge=判断题）
2. 提取题目标题（text）
3. 提取选项（options，用字典 {{'A':'内容','B':'内容',...}}）
4. 提取正确答案（answer，单选题填单个字母如"A"，多选题填字母组合如"ABC"，判断题填"A"或"B"）
5. 过滤掉非题目的内容（如"注意事项"、"试卷标题"、"题型说明"等）
6. 如果某个选项包含多个子选项（如"A、xxx B、xxx"），请拆分为独立选项
7. 忽略"分值"、"试题类型"等元数据标记
8. 如果某题缺少选项或答案，尽量根据上下文推断，无法推断则跳过

请直接返回JSON数组，不要包含其他说明文字。
格式：[{{"id": 1, "type": "single", "text": "题目内容", "options": {{"A": "选项A", "B": "选项B"}}, "answer": "A"}}]

---
{raw_text}
---"""

    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个JSON输出机器人，只输出合法JSON。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 16384,
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

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            content = body["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"AI API 调用失败: {e}")

    # 提取 JSON（AI 有时会在 ```json ... ``` 中返回）
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if json_match:
        content = json_match.group(1)

    try:
        questions = json.loads(content)
    except json.JSONDecodeError:
        raise RuntimeError(f"AI 返回格式异常，无法解析为JSON")

    if not isinstance(questions, list):
        raise RuntimeError(f"AI 返回格式异常：期望数组，得到 {type(questions).__name__}")

    # 规范化
    result = []
    for i, q in enumerate(questions):
        text = q.get("text", "").strip()
        if len(text) < 3:
            continue
        opts = q.get("options", {})
        if len(opts) < 2:
            continue
        answer = q.get("answer", "").strip().upper()
        if not answer:
            continue
        qtype = q.get("type", "single")
        if qtype not in ("single", "multi", "judge"):
            qtype = "single"
        result.append({
            "id": i + 1,
            "type": qtype,
            "text": text,
            "options": opts,
            "answer": answer,
        })

    return result


@app.route("/api/parse-text", methods=["POST"])
def api_parse_text():
    """接收纯文本，用 AI 解析为结构化的题库"""
    data = request.get_json()
    raw_text = data.get("text", "").strip()

    if not raw_text:
        return jsonify({"error": "请输入题目文本"}), 400
    if len(raw_text) < 20:
        return jsonify({"error": "文本太短，请粘贴更多内容"}), 400

    try:
        questions = parse_with_llm(raw_text)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"解析失败：{str(e)}"}), 500

    if not questions:
        return jsonify({"error": "未能从文本中识别出有效题目，请检查内容格式"}), 400

    # 保存题库
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bank_id = uuid.uuid4().hex[:12]
    bank_data = {
        "id": bank_id,
        "original_filename": f"AI解析题库_{timestamp}",
        "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "questions": questions,
    }
    save_bank(bank_id, bank_data)

    return jsonify({
        "success": True,
        "bank_id": bank_id,
        "question_count": len(questions),
        "redirect": url_for("quiz_page", bank_id=bank_id, mode="practice"),
    })


# =========================== 示例题库初始化 ===========================

@app.route("/api/init-sample", methods=["POST"])
def init_sample():
    """生成示例题库（内置 Python 题）"""
    sample_data = {
        "id": "__sample__",
        "original_filename": "Python基础示例题库（内置）",
        "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "questions": create_sample_questions(),
    }
    save_bank("__sample__", sample_data)
    return jsonify({"success": True, "bank_id": "__sample__"})


# =========================== 启动 ===========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
