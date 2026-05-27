"""
刷题通 Web 应用
- 支持上传 PDF / DOCX 题库文件
- 持久化存储：原始文件 + 解析后的 JSON 数据
- 考试模式 / 练习模式
- 题库列表管理
"""

import os
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

    # 随机打乱并截取指定数量
    count_int = int(count) if count.isdigit() else 0
    shuffled = random.sample(questions, min(count_int if count_int > 0 else len(questions), len(questions)))

    result = {
        "bank_id": bank_id,
        "bank_name": bank["original_filename"],
        "total": len(shuffled),
        "mode": mode,
        "questions": [],
    }

    for q in shuffled:
        item = {
            "id": q["id"],
            "text": q["text"],
            "options": q["options"],
        }
        if mode == "practice":
            item["answer"] = q.get("answer", "")
        result["questions"].append(item)

    return jsonify(result)


@app.route("/api/bank/<bank_id>/submit", methods=["POST"])
def api_submit(bank_id):
    """提交答题结果，返回评分"""
    data = request.get_json()
    user_answers = data.get("answers", {})

    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return jsonify({"error": "题库不存在"}), 404

    questions = bank["questions"]
    total = len(questions)
    correct_count = 0
    details = []

    for q in questions:
        qid = str(q["id"])
        user_ans = user_answers.get(qid, "").strip().upper()
        correct_ans = q.get("answer", "").strip().upper()
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)