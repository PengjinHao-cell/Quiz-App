"""
刷题通 Web 应用
- 支持上传 PDF / DOCX 题库文件
- 持久化存储：原始文件 + 解析后的 JSON 数据
- 考试模式 / 练习模式
- 题库列表管理
- 用户系统（注册/登录）
"""

import os
import re
import uuid
import json
import random
import datetime
import time as _time
import urllib.request
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, current_user, login_required
from werkzeug.utils import secure_filename
from parser import parse_file, create_sample_questions
from version import VERSION, VERSION_NAME
from models import db, User, WrongAnswer, Favorite, StudyHistory, QuestionBank
from auth import auth_bp

app = Flask(__name__)
DEFAULT_SECRET = "quiz-app-secret-key-change-in-production"
app.secret_key = os.environ.get("SECRET_KEY", DEFAULT_SECRET)
if app.secret_key == DEFAULT_SECRET:
    import sys as _sys
    _sys.stderr.write("❌ 错误: 使用默认 SECRET_KEY 启动不安全。请设置环境变量 SECRET_KEY。\n")
    _sys.stderr.write("   开发环境可用: export SECRET_KEY=\"dev-$(openssl rand -hex 16)\"\n")
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError("生产环境禁止使用默认 SECRET_KEY")
    print("⚠️  警告: 开发环境使用默认 SECRET_KEY，请勿用于生产")



login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.session_protection = "strong"  # 防止会话伪造
login_manager.remember_cookie_duration = datetime.timedelta(days=14)  # "记住我"有效期
login_manager.init_app(app)


@app.before_request
def session_timeout_check():
    """会话超时检查：非活动超过 24 小时（未勾选记住我）自动登出"""
    # 交给 Flask-Login 的 session_protection 处理
    pass


@app.before_request
def _sync_csrf_check():
    """轻量 CSRF 防护：所有 /api/sync/ POST/DELETE 需带 X-Requested-By: QuizApp"""
    if request.path.startswith("/api/sync/") and request.method in ("POST", "DELETE", "PUT", "PATCH"):
        if request.headers.get("X-Requested-By") != "QuizApp":
            return jsonify({"error": "CSRF 校验失败，缺少 X-Requested-By 头部"}), 403


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_globals():
    """向所有模板注入全局变量"""
    return {"lang": session.get("lang", "zh"), "VERSION": VERSION, "VERSION_NAME": VERSION_NAME}


app.register_blueprint(auth_bp)




# ---------- 配置 ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_FOLDER = os.path.join(BASE_DIR, "data")

# =========================== 默认管理员 ===========================

def _init_default_admin():
    """从环境变量读取管理员账号密码并创建（如已存在则跳过）
    
    环境变量未设置时使用硬编码默认值（PuertoJupiter / REDACTED）。
    """
    username = os.environ.get("ADMIN_USERNAME", "PuertoJupiter").strip()
    password = os.environ.get("ADMIN_PASSWORD", "REDACTED").strip()
    try:
        existing = User.query.filter_by(username=username).first()
        if existing:
            if not existing.is_admin:
                existing.is_admin = True
                db.session.commit()
                print(f"✅ 用户「{username}」已升级为管理员")
            return
        user = User(username=username, email=f"{username}@quizmaster.app", is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"✅ 管理员用户「{username}」已自动创建")
    except Exception as e:
        print(f"⚠️  管理员创建失败（可忽略）: {e}")


# ---------- 数据库配置 ----------
# Railway PostgreSQL 自动注入 DATABASE_URL
# 强制使用 pg8000 驱动（纯 Python，无系统依赖，SSL 可控）
import ssl as _ssl

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'quiz_app.db')}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql://"):
    # 强制使用 pg8000 驱动，在 URL 中声明
    if "+pg8000" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
    # Railway PostgreSQL 要求 TLSv1.2+，配置 SSL 上下文
    _ssl_ctx = _ssl.create_default_context()
    _ssl_ctx.minimum_version = _ssl.TLSVersion.TLSv1_2
    # 不验证服务器证书（Railway 内部网络，自签名证书）
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = _ssl.CERT_NONE
    print("🗄️  使用数据库驱动: pg8000 (SSL: TLSv1.2+, verify=no)")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"ssl_context": _ssl_ctx},
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

# 打印数据库连接信息（隐藏密码）
if "@" in DATABASE_URL:
    _user_part = DATABASE_URL.split("@")[0]
    _host_part = DATABASE_URL.split("@")[1]
    _pw_masked = _user_part.split(":")[0] + ":****"
    _db_url_display = _pw_masked + "@" + _host_part
else:
    _db_url_display = DATABASE_URL
print(f"🗄️  数据库: {_db_url_display}")

# 裸连测试
if DATABASE_URL.startswith("postgresql"):
    try:
        import socket as _sock
        _host = DATABASE_URL.split("@")[1].split(":")[0]
        _port = int(DATABASE_URL.split("@")[1].split(":")[1].split("/")[0].split("?")[0])
        _s = _sock.create_connection((_host, _port), timeout=5)
        print(f"🌐  TCP 连接到 {_host}:{_port} ✅")
        _s.close()
    except Exception as _e:
        print(f"🌐  TCP 连接到数据库失败: {_e}")

def _run_migration():
    """自动迁移：添加新字段 + 导入 JSON 题库到数据库"""
    try:
        with app.app_context():
            engine = db.engine
            # 检查 users 表是否有 is_admin 列
            if DATABASE_URL.startswith("sqlite"):
                import sqlite3
                db_path = DATABASE_URL.replace("sqlite:///", "")
                if not os.path.isabs(db_path):
                    db_path = os.path.join(BASE_DIR, db_path)
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("PRAGMA table_info(users)")
                cols = [row[1] for row in c.fetchall()]
                if "is_admin" not in cols:
                    c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
                    conn.commit()
                    print("📦 迁移: 已添加 is_admin 列 (SQLite)")
                conn.close()
            elif DATABASE_URL.startswith("postgresql"):
                from sqlalchemy import text
                with engine.connect() as conn:
                    result = conn.execute(text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='users' AND column_name='is_admin'"
                    ))
                    if result.fetchone() is None:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                        conn.commit()
                        print("📦 迁移: 已添加 is_admin 列 (PostgreSQL)")

            # 导入已有 JSON 题库到数据库
            if os.path.isdir(DATA_FOLDER):
                imported = 0
                for fname in os.listdir(DATA_FOLDER):
                    if not fname.endswith(".json"):
                        continue
                    bank_id = fname[:-5]
                    if QuestionBank.query.get(bank_id):
                        continue
                    filepath = os.path.join(DATA_FOLDER, fname)
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    bank_type = data.get("type", "quiz")
                    language = data.get("language", "zh") if bank_type == "reading" else "zh"
                    qb = QuestionBank(
                        id=bank_id,
                        original_filename=data.get("original_filename", ""),
                        upload_time=data.get("upload_time", ""),
                        type=bank_type,
                        language=language,
                        data_json=json.dumps(data, ensure_ascii=False),
                    )
                    db.session.add(qb)
                    db.session.commit()
                    imported += 1
                if imported:
                    print(f"📦 迁移: 已导入 {imported} 个题库到数据库")
    except Exception as e:
        print(f"⚠️  迁移失败（可忽略）: {e}")

try:
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _run_migration()
        _init_default_admin()
    print("✅ 数据库连接成功")
    try:
        _ = User.query.first()
    except Exception:
        pass
except Exception as e:
    import traceback as _tb
    _tb.print_exc()
    print(f"⚠️  数据库初始化失败: {e}")
    print(f"   应用将以无数据库模式运行（注册/登录功能不可用）")
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB 上传限制


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否在白名单内"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def check_name_duplicate(name: str, exclude_id: str = ""):
    """
    检查题库名称是否已存在（数据库版）。
    返回：{"id", "original_filename", "upload_time"} 或 None
    """
    if not name:
        return None
    qb = QuestionBank.query.filter(
        QuestionBank.original_filename == name,
        QuestionBank.id != exclude_id
    ).first()
    if qb:
        data = json.loads(qb.data_json)
        return {
            "id": qb.id,
            "original_filename": qb.original_filename,
            "upload_time": data.get("upload_time", ""),
        }
    return None


# 题库列表缓存（内存级，3秒 TTL）
_bank_list_cache = {"data": None, "time": 0.0, "lock": threading.Lock()}
_BANK_CACHE_TTL = 3.0

def _invalidate_bank_cache():
    with _bank_list_cache["lock"]:
        _bank_list_cache["time"] = 0.0

def load_bank_list() -> list:
    """从数据库加载题库列表（带内存缓存）"""
    now = _time.time()
    with _bank_list_cache["lock"]:
        if _bank_list_cache["data"] is not None and now - _bank_list_cache["time"] < _BANK_CACHE_TTL:
            return _bank_list_cache["data"]

    records = QuestionBank.query.order_by(QuestionBank.original_filename.asc()).all()
    banks = []
    for qb in records:
        try:
            data = json.loads(qb.data_json)
        except Exception:
            continue
        bank_type = qb.type

        if bank_type == "reading":
            passages = data.get("passages", [])
            total_q = sum(len(p.get("questions", [])) for p in passages)
            banks.append({
                "id": qb.id,
                "type": "reading",
                "language": qb.language,
                "original_filename": qb.original_filename,
                "upload_time": data.get("upload_time", ""),
                "question_count": total_q,
                "passage_count": len(passages),
            })
            continue

        questions = data.get("questions", [])
        if not questions:
            continue
        single_count = multi_count = judge_count = fill_count = 0
        for q in questions:
            t = detect_question_type(q)
            if t == "single": single_count += 1
            elif t == "multi": multi_count += 1
            elif t == "judge": judge_count += 1
            elif t == "fill": fill_count += 1
        banks.append({
            "id": qb.id,
            "type": "quiz",
            "original_filename": qb.original_filename,
            "upload_time": data.get("upload_time", ""),
            "question_count": len(questions),
            "single_count": single_count,
            "multi_count": multi_count,
            "judge_count": judge_count,
            "fill_count": fill_count,
        })

    banks.sort(key=lambda b: b.get("original_filename", "").lower())
    with _bank_list_cache["lock"]:
        _bank_list_cache["data"] = banks
        _bank_list_cache["time"] = _time.time()
    return banks


def load_bank(bank_id: str) -> dict:
    """从数据库加载题库"""
    qb = QuestionBank.query.get(bank_id)
    if not qb:
        raise FileNotFoundError(f"题库 {bank_id} 不存在")
    data = json.loads(qb.data_json)
    data["id"] = qb.id
    data["original_filename"] = qb.original_filename
    data["type"] = qb.type
    if qb.type == "reading":
        data["language"] = qb.language
    return data


def detect_question_type(question: dict) -> str:
    """根据已有字段或题目内容推测题型：single / multi / judge"""
    # 优先使用存储的 type 字段
    stored_type = question.get("type", "")
    if stored_type in ("single", "multi", "judge", "fill"):
        return stored_type

    text = question.get("text", "")
    options = question.get("options", {})
    num_opts = len(options)
    answer = question.get("answer", "").upper().strip()
    text_upper = text.upper()

    # 填空题特征：无选项，且题干含下划线/括号/「填空」等特征
    if num_opts == 0:
        if any(kw in text for kw in ["____", "＿＿", "()", "（）", "填空", "___"]):
            return "fill"

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
    fills = [q for q in questions if detect_question_type(q) == "fill"]

    pools = []
    if singles:
        pools.append(("single", singles))
    if multis:
        pools.append(("multi", multis))
    if judges:
        pools.append(("judge", judges))
    if fills:
        pools.append(("fill", fills))

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
    """保存题库到数据库"""
    bank_type = data.get("type", "quiz")
    language = data.get("language", "zh") if bank_type == "reading" else "zh"
    qb = QuestionBank.query.get(bank_id)
    if qb:
        qb.original_filename = data.get("original_filename", qb.original_filename)
        qb.type = bank_type
        qb.language = language
        qb.data_json = json.dumps(data, ensure_ascii=False)
    else:
        qb = QuestionBank(
            id=bank_id,
            original_filename=data.get("original_filename", ""),
            upload_time=data.get("upload_time", ""),
            type=bank_type,
            language=language,
            data_json=json.dumps(data, ensure_ascii=False),
        )
        db.session.add(qb)
    db.session.commit()


def delete_bank_files(bank_id: str):
    """从数据库删除题库"""
    qb = QuestionBank.query.get(bank_id)
    if qb:
        # 尝试删除对应的上传文件
        try:
            data = json.loads(qb.data_json)
            orig_name = data.get("original_filename", "")
            if orig_name:
                upload_path = os.path.join(UPLOAD_FOLDER, f"{bank_id}_{orig_name}")
                if os.path.exists(upload_path):
                    os.remove(upload_path)
        except Exception:
            pass
        db.session.delete(qb)
        db.session.commit()


# =========================== 页面路由 ===========================

@app.route("/")
def welcome():
    """欢迎页"""
    return render_template("welcome.html")


@app.route("/set-lang/<lang>")
def set_lang(lang):
    """切换语言并回到上一页"""
    if lang in ("zh", "en"):
        session["lang"] = lang
    referer = request.headers.get("Referer", url_for("welcome"))
    return redirect(referer)


@app.route("/agreement")
def agreement():
    """用户协议"""
    return render_template("agreement.html")


@app.route("/user")
def user_page():
    """用户中心页（所有用户均可访问，数据来自 localStorage）"""
    lang = request.args.get("lang", session.get("lang", "zh"))
    if lang not in ("zh", "en"):
        lang = "zh"
    session["lang"] = lang
    return render_template("user.html", lang=lang)


@app.route("/app")
def app_main():
    """主应用页 - 题库列表"""
    is_guest = request.args.get("guest", "0") == "1"
    if not current_user.is_authenticated and not is_guest:
        return redirect(url_for("welcome"))

    banks = load_bank_list()
    return render_template("index.html", banks=banks, is_guest=is_guest)


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

    # 解析文件（parse_file 返回 dict，含 type 字段区分 reading/quiz）
    try:
        parsed = parse_file(upload_path, original_filename)
    except Exception as e:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({"error": f"题目解析失败：{str(e)}"}), 400

    if not parsed:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({"error": "文件中未检测到题目，请检查文件格式"}), 400

    # 根据解析类型保存为不同格式
    if parsed.get("type") == "reading":
        # 阅读理解格式
        bank_data = {
            "id": bank_id,
            "type": "reading",
            "language": parsed.get("language", "zh"),
            "original_filename": original_filename,
            "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "passages": parsed.get("passages", []),
        }
        save_bank(bank_id, bank_data)
        _invalidate_bank_cache()
        total_q = sum(len(p.get("questions", [])) for p in bank_data["passages"])
        dup = check_name_duplicate(original_filename, exclude_id=bank_id)
        resp = {
            "success": True,
            "bank_id": bank_id,
            "question_count": total_q,
            "redirect": url_for("reading_page", bank_id=bank_id),
        }
    else:
        # 普通题库格式
        questions = parsed.get("questions", [])
        bank_data = {
            "id": bank_id,
            "original_filename": original_filename,
            "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "questions": questions,
        }
        save_bank(bank_id, bank_data)
        _invalidate_bank_cache()
        dup = check_name_duplicate(original_filename, exclude_id=bank_id)
        resp = {
            "success": True,
            "bank_id": bank_id,
            "question_count": len(questions),
            "mode": mode,
            "redirect": url_for("quiz_page", bank_id=bank_id, mode=mode),
        }

    if dup:
        resp["duplicate_warning"] = f'题库名称「{original_filename}」已存在 (上传于 {dup["upload_time"]})'
    return jsonify(resp)


@app.route("/quiz/<bank_id>")
def quiz_page(bank_id):
    """刷题页面"""
    mode = request.args.get("mode", "practice")
    if mode not in ("practice", "exam"):
        mode = "practice"

    count = request.args.get("count", "0")  # 0 = 全部
    duration = request.args.get("duration", "auto")  # auto / 分钟数 / 0
    qids = request.args.get("qids", "")  # 指定题目ID列表

    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return render_template("error.html", message="题库不存在或已被删除"), 404

    total_in_bank = len(bank["questions"])
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
        duration=duration,
        qids=qids,
    )


@app.route("/api/bank/<bank_id>/questions")
def api_get_questions(bank_id):
    """API: 获取某个题库的题目（支持 count/q/qids 参数）"""
    mode = request.args.get("mode", "practice")
    count = request.args.get("count", "0")  # 0 = 全部
    q = request.args.get("q", "").strip()  # 搜索关键词
    qids = request.args.get("qids", "").strip()  # 指定题目ID列表（逗号分隔）

    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return jsonify({"error": "题库不存在"}), 404

    questions = bank.get("questions", [])

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

    # 指定题目ID列表（错题重练、收藏复习等）
    if qids:
        id_set = set()
        for part in qids.split(","):
            part = part.strip()
            if part.isdigit():
                id_set.add(int(part))
        if id_set:
            questions = [q for q in questions if q["id"] in id_set]

    # 搜索模式：按题号排序
    is_search = bool(q)
    # 按比例抽选题目
    count_int = int(count) if count.isdigit() else 0
    if qids:
        # 指定题目列表时保持顺序
        shuffled = questions[:]
    elif count_int > 0 and count_int < len(questions):
        shuffled = sample_questions_proportional(questions, count_int)
    elif is_search:
        shuffled = sorted(questions, key=lambda x: x["id"])  # 搜索结果按题号排序
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
            "type": qtype,  # single / multi / judge / fill
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
        user_ans_raw = user_answers.get(qid, "").strip()
        correct_ans_raw = q.get("answer", "").strip()
        # 多选题：排序后比较
        if detect_question_type(q) == "multi":
            user_sorted = "".join(sorted(user_ans_raw.upper().replace(" ", "")))
            correct_sorted = "".join(sorted(correct_ans_raw.upper().replace(" ", "")))
            is_correct = user_sorted == correct_sorted
        elif detect_question_type(q) == "fill":
            # 填空题：去空格后比较，大小写敏感
            is_correct = user_ans_raw.replace(" ", "") == correct_ans_raw.replace(" ", "")
        else:
            is_correct = user_ans_raw.upper() == correct_ans_raw.upper() if correct_ans_raw else False

        if is_correct:
            correct_count += 1

        details.append({
            "id": q["id"],
            "text": q["text"],
            "options": q["options"],
            "user_answer": user_ans_raw,
            "correct_answer": correct_ans_raw,
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


# =========================== 阅读理解 ===========================

@app.route("/reading/<bank_id>")
def reading_page(bank_id):
    """阅读理解页面"""
    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return render_template("error.html", message="题库不存在或已被删除"), 404
    if bank.get("type") != "reading":
        return render_template("error.html", message="该题库不是阅读理解类型"), 400
    passages = bank.get("passages", [])
    return render_template(
        "reading.html",
        bank_id=bank_id,
        bank_name=bank.get("original_filename", ""),
        passage_count=len(passages),
    )


@app.route("/api/reading/<bank_id>")
def api_reading(bank_id):
    """API: 获取阅读理解数据（passage + questions）"""
    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return jsonify({"error": "题库不存在"}), 404
    if bank.get("type") != "reading":
        return jsonify({"error": "该题库不是阅读理解类型"}), 400
    return jsonify({
        "bank_id": bank_id,
        "bank_name": bank.get("original_filename", ""),
        "passages": bank.get("passages", []),
    })


@app.route("/api/bank/<bank_id>/rename", methods=["POST"])
def api_rename_bank(bank_id):
    """重命名题库"""
    data = request.get_json()
    new_name = data.get("name", "").strip()
    if not new_name:
        return jsonify({"error": "名称不能为空"}), 400
    if len(new_name) > 100:
        return jsonify({"error": "名称过长"}), 400

    # 检查新名称是否与其他题库重名
    dup = check_name_duplicate(new_name, exclude_id=bank_id)
    if dup:
        return jsonify({"error": f'该名称已被使用（题库「{dup["original_filename"]}」上传于 {dup["upload_time"]}）'}), 409

    try:
        bank = load_bank(bank_id)
    except FileNotFoundError:
        return jsonify({"error": "题库不存在"}), 404

    bank["original_filename"] = new_name
    save_bank(bank_id, bank)
    _invalidate_bank_cache()
    return jsonify({"success": True})


@app.route("/api/bank/<bank_id>/delete", methods=["POST"])
def api_delete_bank(bank_id):
    """删除题库（需密码验证）"""
    data = request.get_json() or {}
    pwd = data.get("password", "")
    expected = os.environ.get("DELETE_PASSWORD", "")
    if not expected:
        # 未设置 DELETE_PASSWORD 时，仅管理员可删除
        if current_user.is_authenticated and getattr(current_user, "is_admin", False):
            expected = current_user.password_hash  # 用管理员密码哈希鉴权
            if not current_user.check_password(pwd):
                return jsonify({"error": "删除密码错误"}), 403
        else:
            return jsonify({"error": "删除密码错误"}), 403
    elif pwd != expected:
        return jsonify({"error": "删除密码错误"}), 403
    delete_bank_files(bank_id)
    _invalidate_bank_cache()
    return jsonify({"success": True})


# =========================== AI 文本解析 ===========================

def parse_with_llm(raw_text: str):
    """
    调用 DeepSeek API 将纯文本解析为结构化题库。
    
    返回格式（普通题库）：
        [{"id": 1, "type": "single", "text": "题目", "options": {"A":".."}, "answer": "A"}, ...]
    
    返回格式（阅读理解）：
        {"type": "reading", "passages": [{"id": 1, "title": "...", "text": "...", "questions": [...]}]}
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

    prompt = f"""你是一个专业的题库解析助手。请将以下考试题目文本解析为JSON。

## 输入类型识别

**类型A：普通题目**（单选题、多选题、判断题、填空题）
如果文本是分散的独立题目，返回JSON数组：
[{{"id": 1, "type": "single", "text": "题目", "options": {{"A": "选项A", "B": "选项B"}}, "answer": "A"}}]

**类型B：阅读理解**（一篇文章 + 多道选择题）
如果文本包含一篇完整文章，后面跟着若干基于该文章的选择题，返回JSON对象：
{{"type": "reading", "language": "语言代码（zh=中文，en=英文，根据文章内容自动判断）", "passages": [{{"id": 1, "title": "文章标题（若无则留空）", "text": "完整文章内容", "questions": [{{"id": 1, "type": "single", "text": "问题", "options": {{"A":"..","B":".."}}, "answer": "A"}}]}}]}}

## 字段说明（通用）

- type: single(单选) / multi(多选) / judge(判断) / fill(填空)
- text: 题目或问题文本
- options: 选项字典，填空题可为 {{}}（空对象）
- answer: 用字母表示（单选"A"，多选"ABC"，判断"A/B"）

## 规则

1. 过滤掉非题目的内容（注意事项、试卷标题、题型说明、分值标记等）
2. 阅读理解的文章和它后面的题目必须放在同一个 passage 内
3. 如果多个选项挤在一行（如"A、xxx B、xxx"），拆分为独立选项
4. 纯数字答案不是多选题，按单选处理
5. 直接返回JSON，不要包含其他说明文字

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
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise RuntimeError(f"AI 返回格式异常，无法解析为JSON")

    # 判断是阅读理解（dict）还是普通题库（list）
    if isinstance(parsed, dict) and parsed.get("type") == "reading":
        # 阅读理解：验证并规范化
        passages = parsed.get("passages", [])
        if not passages:
            raise RuntimeError("AI 返回了阅读类型但没有文章内容")
        for pi, p in enumerate(passages):
            p["id"] = pi + 1
            for qi, q in enumerate(p.get("questions", [])):
                q["id"] = qi + 1
                q["type"] = q.get("type", "single")
                if q.get("options") and len(q["options"]) < 2:
                    q["options"] = {}
        return parsed  # dict with type: "reading"
    elif isinstance(parsed, list):
        # 普通题库：规范化
        result = []
        for i, q in enumerate(parsed):
            text = q.get("text", "").strip()
            if len(text) < 3:
                continue
            opts = q.get("options", {})
            if len(opts) < 2 and q.get("type") != "fill":
                continue
            answer = q.get("answer", "").strip()
            if not answer:
                continue
            qtype = q.get("type", "single")
            if qtype not in ("single", "multi", "judge", "fill"):
                qtype = "single"
            result.append({
                "id": i + 1,
                "type": qtype,
                "text": text,
                "options": opts,
                "answer": answer,
            })
        return result
    else:
        raise RuntimeError(f"AI 返回格式异常：期望数组或阅读对象，得到 {type(parsed).__name__}")


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
        parsed = parse_with_llm(raw_text)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"解析失败：{str(e)}"}), 500

    if not parsed:
        return jsonify({"error": "未能从文本中识别出有效题目，请检查内容格式"}), 400

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bank_id = uuid.uuid4().hex[:12]

    if isinstance(parsed, dict) and parsed.get("type") == "reading":
        # 保存为阅读理解题库
        lang = parsed.get("language", "zh") if isinstance(parsed, dict) else "zh"
        bank_data = {
            "id": bank_id,
            "type": "reading",
            "language": lang,
            "original_filename": f"AI阅读理解_{timestamp}",
            "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "passages": parsed.get("passages", []),
        }
        save_bank(bank_id, bank_data)
        total_q = sum(len(p.get("questions", [])) for p in bank_data["passages"])
        return jsonify({
            "success": True,
            "bank_id": bank_id,
            "question_count": total_q,
            "redirect": url_for("reading_page", bank_id=bank_id),
        })
    else:
        # 保存为普通题库
        questions = parsed if isinstance(parsed, list) else []
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


# =========================== 背单词 ===========================

VOCAB_PATH = os.path.join(DATA_FOLDER, "vocab_cet6.json")

def load_vocab() -> dict:
    """加载词汇数据"""
    if not os.path.exists(VOCAB_PATH):
        return {"words": []}
    with open(VOCAB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_vocab_question(word_item: dict, all_words: list, count: int = 3) -> dict:
    """基于一个单词生成选择题：给出英文，4选1中文释义"""
    correct = word_item["meaning"]
    # 从其他词中随机取 count 个不同释义作为干扰项
    others = [w for w in all_words if w["word"] != word_item["word"]]
    random.shuffle(others)
    distractors = [w["meaning"] for w in others[:count]]

    # 合并并打乱选项
    choices = [correct] + distractors
    random.shuffle(choices)

    # 找到正确答案对应的字母
    letters = "ABCD"
    opt_map = {}
    for i, c in enumerate(choices):
        opt_map[letters[i]] = c

    answer_letter = ""
    for k, v in opt_map.items():
        if v == correct:
            answer_letter = k
            break

    return {
        "word": word_item["word"],
        "phonetic": word_item.get("phonetic", ""),
        "example": word_item.get("example", ""),
        "translation": word_item.get("translation", ""),
        "options": opt_map,
        "answer": answer_letter,
    }


@app.route("/vocab")
def vocab_page():
    """词汇学习页面"""
    vocab = load_vocab()
    total = len(vocab.get("words", []))
    return render_template("vocab.html", total_words=total)


@app.route("/api/vocab/words")
def api_vocab_words():
    """获取 N 个随机词汇题（参数: count）"""
    count = int(request.args.get("count", "10"))
    count = max(1, min(count, 50))

    vocab = load_vocab()
    all_words = vocab.get("words", [])
    if not all_words:
        return jsonify({"error": "词汇数据为空", "questions": []}), 200

    selected = random.sample(all_words, min(count, len(all_words)))
    questions = []
    for w in selected:
        q = generate_vocab_question(w, all_words)
        if q:
            questions.append(q)

    return jsonify({
        "total": len(questions),
        "questions": questions,
    })


@app.route("/api/vocab/batch", methods=["POST"])
def api_vocab_batch():
    """批量生成更多词汇（用 AI 扩展词库）"""
    # 功能待实现：需先用 DeepSeek API 生成词汇并写入 vocab_cet6.json
    # 当前返回提示信息
    return jsonify({"error": "词汇扩展功能开发中，请先使用内置 CET-6 词库"}), 501


# =========================== 用户数据云端同步 API ===========================
# 登录用户可将错题本/收藏/学习记录同步到服务器，跨设备可用
# CSRF 防护：所有 POST/DELETE 端点需携带 X-Requested-By: QuizApp 头部

def _check_sync_csrf():
    """轻量 CSRF 防护：要求请求头 X-Requested-By: QuizApp"""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return True
    return request.headers.get("X-Requested-By") == "QuizApp"

@app.route("/api/sync/all", methods=["GET"])
@login_required
def api_sync_all():
    """拉取用户全部云端数据"""
    user_id = current_user.id

    wrong_answers = WrongAnswer.query.filter_by(user_id=user_id).all()
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    histories = StudyHistory.query.filter_by(user_id=user_id)\
        .order_by(StudyHistory.created_at.desc()).limit(50).all()

    wrong_book = {}
    for wa in wrong_answers:
        wrong_book[wa.question_key] = wa.to_dict()

    fav_book = {}
    for f in favorites:
        fav_book[f.question_key] = f.to_dict()

    history_list = [h.to_dict() for h in histories]

    return jsonify({
        "wrong_book": wrong_book,
        "favorites": fav_book,
        "history": history_list,
    })


@app.route("/api/sync/wrong-book", methods=["POST"])
@login_required
def api_sync_wrong_book():
    """批量同步错题本"""
    user_id = current_user.id
    data = request.get_json()
    if not data or "items" not in data:
        return jsonify({"error": "缺少 items"}), 400

    for item in data["items"]:
        question_key = item.get("question_key", "")
        if not question_key:
            continue

        existing = WrongAnswer.query.filter_by(
            user_id=user_id, question_key=question_key
        ).first()

        if existing:
            existing.wrong_count = item.get("wrong_count", existing.wrong_count)
            existing.user_wrong_answer = item.get("user_wrong_answer", existing.user_wrong_answer)
            existing.last_wrong_time = item.get("last_wrong_time", existing.last_wrong_time)
        else:
            wa = WrongAnswer(
                user_id=user_id,
                question_key=question_key,
                bank_id=item.get("bank_id", ""),
                bank_name=item.get("bank_name", ""),
                question_id=item.get("question_id", ""),
                question_text=item.get("question_text", ""),
                question_options=item.get("question_options", "{}"),
                correct_answer=item.get("correct_answer", ""),
                user_wrong_answer=item.get("user_wrong_answer", ""),
                question_type=item.get("type", "single"),
                wrong_count=item.get("wrong_count", 1),
                last_wrong_time=item.get("last_wrong_time", ""),
            )
            db.session.add(wa)

    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/sync/wrong-book", methods=["DELETE"])
@login_required
def api_delete_wrong_book():
    """删除指定错题"""
    user_id = current_user.id
    data = request.get_json()
    question_key = data.get("question_key", "") if data else ""

    if not question_key:
        return jsonify({"error": "缺少 question_key"}), 400

    WrongAnswer.query.filter_by(
        user_id=user_id, question_key=question_key
    ).delete()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/sync/wrong-book/clear", methods=["POST"])
@login_required
def api_clear_wrong_book():
    """清空所有错题"""
    WrongAnswer.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/sync/favorites", methods=["POST"])
@login_required
def api_sync_favorites():
    """批量同步收藏"""
    user_id = current_user.id
    data = request.get_json()
    if not data or "items" not in data:
        return jsonify({"error": "缺少 items"}), 400

    for item in data["items"]:
        question_key = item.get("question_key", "")
        if not question_key:
            continue

        existing = Favorite.query.filter_by(
            user_id=user_id, question_key=question_key
        ).first()

        if not existing:
            fav = Favorite(
                user_id=user_id,
                question_key=question_key,
                bank_id=item.get("bank_id", ""),
                bank_name=item.get("bank_name", ""),
                question_id=item.get("question_id", ""),
                question_text=item.get("question_text", ""),
                question_options=item.get("question_options", "{}"),
                answer=item.get("answer", ""),
                question_type=item.get("type", "single"),
                added_time=item.get("added_time", ""),
            )
            db.session.add(fav)

    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/sync/favorites", methods=["DELETE"])
@login_required
def api_delete_favorite():
    """取消收藏"""
    user_id = current_user.id
    data = request.get_json()
    question_key = data.get("question_key", "") if data else ""

    if not question_key:
        return jsonify({"error": "缺少 question_key"}), 400

    Favorite.query.filter_by(
        user_id=user_id, question_key=question_key
    ).delete()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/sync/favorites/clear", methods=["POST"])
@login_required
def api_clear_favorites():
    """清空所有收藏"""
    Favorite.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/sync/history", methods=["POST"])
@login_required
def api_sync_history():
    """同步学习记录"""
    user_id = current_user.id
    data = request.get_json()
    if not data or "items" not in data:
        return jsonify({"error": "缺少 items"}), 400

    for item in data["items"]:
        record_id = item.get("id", "")
        if not record_id:
            continue

        existing = StudyHistory.query.filter_by(
            user_id=user_id, record_id=record_id
        ).first()

        if not existing:
            sh = StudyHistory(
                user_id=user_id,
                record_id=record_id,
                bank_id=item.get("bank_id", ""),
                bank_name=item.get("bank_name", ""),
                mode=item.get("mode", "practice"),
                score=item.get("score", 0),
                correct=item.get("correct", 0),
                total=item.get("total", 0),
                answers_json=item.get("answers_json", "{}"),
                time_label=item.get("time", ""),
            )
            db.session.add(sh)

    # 保持最多 200 条
    count = StudyHistory.query.filter_by(user_id=user_id).count()
    if count > 200:
        excess = StudyHistory.query.filter_by(user_id=user_id)\
            .order_by(StudyHistory.created_at.asc())\
            .limit(count - 200).all()
        for e in excess:
            db.session.delete(e)

    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/sync/history", methods=["DELETE"])
@login_required
def api_delete_history():
    """删除单条学习记录"""
    user_id = current_user.id
    data = request.get_json()
    record_id = data.get("id", "") if data else ""

    if not record_id:
        return jsonify({"error": "缺少 id"}), 400

    StudyHistory.query.filter_by(
        user_id=user_id, record_id=record_id
    ).delete()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/sync/history/clear", methods=["POST"])
@login_required
def api_clear_history():
    """清空所有学习记录"""
    StudyHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})


# =========================== 管理后台 API ===========================

def admin_required(f):
    """装饰器：仅管理员可访问"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            if request.path.startswith("/api/"):
                return jsonify({"error": "需要管理员权限"}), 403
            return redirect(url_for("app_main"))
        return f(*args, **kwargs)
    return decorated


@app.route("/admin")
@login_required
@admin_required
def admin_page():
    """管理后台页面"""
    return render_template("admin.html")


@app.route("/api/admin/stats")
@login_required
@admin_required
def api_admin_stats():
    """数据概览"""
    user_count = User.query.count()

    # 题库统计（从数据库查询）
    bank_count = QuestionBank.query.count()
    total_questions = 0
    for qb in QuestionBank.query.all():
        try:
            data = json.loads(qb.data_json)
            if qb.type == "reading":
                total_questions += sum(len(p.get("questions", [])) for p in data.get("passages", []))
            else:
                total_questions += len(data.get("questions", []))
        except Exception:
            pass

    # 答题记录统计
    history_count = StudyHistory.query.count()
    wrong_count = WrongAnswer.query.count()

    return jsonify({
        "user_count": user_count,
        "bank_count": bank_count,
        "total_questions": total_questions,
        "history_count": history_count,
        "wrong_count": wrong_count,
    })


@app.route("/api/admin/users")
@login_required
@admin_required
def api_admin_users():
    """用户列表"""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        "users": [{
            "id": u.id,
            "username": u.username,
            "email": u.email or "",
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "",
            "is_admin": bool(u.is_admin),
            "wrong_count": WrongAnswer.query.filter_by(user_id=u.id).count(),
            "history_count": StudyHistory.query.filter_by(user_id=u.id).count(),
        } for u in users]
    })


@app.route("/api/admin/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def api_admin_reset_password(user_id):
    """重置用户密码"""
    data = request.get_json()
    new_password = (data or {}).get("new_password", "").strip()

    err = User.validate_password(new_password)
    if err:
        return jsonify({"error": err}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": f"用户「{user.username}」密码已重置"})


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@login_required
@admin_required
def api_admin_delete_user(user_id):
    """删除用户"""
    if user_id == current_user.id:
        return jsonify({"error": "不能删除自己的账号"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    # 检查是不是最后一个管理员
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            return jsonify({"error": "不能删除最后一个管理员"}), 400

    username = user.username

    # 级联删除关联数据
    WrongAnswer.query.filter_by(user_id=user_id).delete()
    Favorite.query.filter_by(user_id=user_id).delete()
    StudyHistory.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()

    return jsonify({"success": True, "message": f"用户「{username}」已删除"})


# =========================== 启动 ===========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
