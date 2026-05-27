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
    """API: 获取某个题库的题目（支持 count 参数限制数量，随机选取）"""
    mode = request.args.get("mode", "practice")
    count = request.args.get("count", "0")  # 0 = 全部

    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return jsonify({"error": "题库不存在"}), 404

    questions = bank["questions"]

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
