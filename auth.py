"""
认证蓝图：注册 / 登录 / 登出 / 邮箱验证
"""
import time
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from email_utils import (
    generate_code, send_verify_email,
    can_send_code, store_code, verify_code
)

auth_bp = Blueprint("auth", __name__)

# ---------- 登录限流（内存计数，进程级） ----------
_LOGIN_ATTEMPTS = {}  # {ip: [timestamp, ...]}

def _check_login_rate_limit(ip: str) -> tuple:
    """
    检查 IP 登录频率。
    返回 (allowed: bool, wait_seconds: int)
    规则：同一 IP 5 分钟内失败 5 次后，限流 5 分钟。
    """
    now = time.time()
    if ip not in _LOGIN_ATTEMPTS:
        return True, 0
    # 清理超过 5 分钟的旧记录
    _LOGIN_ATTEMPTS[ip] = [t for t in _LOGIN_ATTEMPTS[ip] if now - t < 300]
    attempts = len(_LOGIN_ATTEMPTS[ip])
    if attempts >= 5:
        oldest = _LOGIN_ATTEMPTS[ip][0]
        wait = int(300 - (now - oldest))
        return False, max(wait, 1)
    return True, 0

def _record_login_attempt(ip: str, success: bool):
    """记录登录尝试"""
    now = time.time()
    if success:
        # 成功后清空该 IP 记录
        _LOGIN_ATTEMPTS.pop(ip, None)
    else:
        if ip not in _LOGIN_ATTEMPTS:
            _LOGIN_ATTEMPTS[ip] = []
        _LOGIN_ATTEMPTS[ip].append(now)

# ---------- 验证码限流（每邮箱 3 次） ----------
_VERIFY_CODE_ATTEMPTS = {}  # {email: [timestamp, ...]}

def _check_code_rate_limit(email: str) -> tuple:
    """
    检查邮箱验证码重试频率。
    返回 (allowed: bool, wait_seconds: int)
    规则：同一邮箱 10 分钟内错误 3 次后锁定 10 分钟。
    """
    now = time.time()
    if email not in _VERIFY_CODE_ATTEMPTS:
        return True, 0
    _VERIFY_CODE_ATTEMPTS[email] = [t for t in _VERIFY_CODE_ATTEMPTS[email] if now - t < 600]
    if len(_VERIFY_CODE_ATTEMPTS[email]) >= 3:
        oldest = _VERIFY_CODE_ATTEMPTS[email][0]
        wait = int(600 - (now - oldest))
        return False, max(wait, 1)
    return True, 0

def _record_code_attempt(email: str, success: bool):
    """记录验证码验证尝试"""
    now = time.time()
    if success:
        _VERIFY_CODE_ATTEMPTS.pop(email, None)
    else:
        if email not in _VERIFY_CODE_ATTEMPTS:
            _VERIFY_CODE_ATTEMPTS[email] = []
        _VERIFY_CODE_ATTEMPTS[email].append(now)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """注册"""
    if request.method == "GET" and current_user.is_authenticated:
        return redirect(url_for("app_main"))
    if request.method == "GET":
        return render_template("register.html")

    # POST: AJAX 注册（含验证码校验）
    data = request.get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()

    # 校验用户名
    err = User.validate_username(username)
    if err:
        return jsonify({"error": err}), 400

    # 校验密码
    err = User.validate_password(password)
    if err:
        return jsonify({"error": err}), 400

    # 校验邮箱
    if not email:
        return jsonify({"error": "请填写邮箱"}), 400
    if "@" not in email or "." not in email:
        return jsonify({"error": "邮箱格式不正确"}), 400

    # 验证码不能为空
    if not code:
        return jsonify({"error": "请填写验证码"}), 400

    # 验证码重试限流
    allowed, wait = _check_code_rate_limit(email)
    if not allowed:
        return jsonify({"error": f"验证码错误次数过多，请 {wait} 秒后再试"}), 429

    # 校验验证码
    if not verify_code(email, code):
        _record_code_attempt(email, False)
        return jsonify({"error": "验证码错误或已过期"}), 400
    _record_code_attempt(email, True)

    # 用户名唯一
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "用户名已被注册"}), 409

    # 邮箱唯一
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "邮箱已被绑定"}), 409

    # 创建用户
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return jsonify({"success": True, "username": user.username})


@auth_bp.route("/api/send-code", methods=["POST"])
def api_send_code():
    """发送邮箱验证码（90 秒限流）"""
    data = request.get_json()
    email = (data.get("email") or "").strip()

    if not email or "@" not in email or "." not in email:
        return jsonify({"error": "邮箱格式不正确"}), 400

    # 检查全局限流（所有用户共享冷却期）
    allowed, wait = can_send_code()
    if not allowed:
        return jsonify({"error": f"抱歉，邮箱请求已满，请 {wait} 秒后再试"}), 429

    # 生成验证码
    code = generate_code()

    # 先存储（保证验证码可用）
    store_code(email, code)

    # 发送邮件（3 秒超时，不阻塞太久）
    ok = send_verify_email(email, code, email.split("@")[0])

    if ok:
        return jsonify({"success": True, "message": "✅ 验证码已发送到邮箱，5 分钟内有效"})
    else:
        return jsonify({"error": "邮件发送失败，请检查邮箱地址或稍后重试"}), 500


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """登录"""
    # 已登录用户访问登录页 → 自动跳转主页
    if request.method == "GET" and current_user.is_authenticated:
        return redirect(url_for("app_main"))
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    remember = data.get("remember", False)

    # 登录限流检查（内存操作，<1ms）
    client_ip = request.remote_addr or "unknown"
    allowed, wait = _check_login_rate_limit(client_ip)
    if not allowed:
        return jsonify({"error": f"登录尝试过于频繁，请 {wait} 秒后再试"}), 429

    # 数据库查询 + 密码验证（慢点在这）
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        _record_login_attempt(client_ip, False)
        return jsonify({"error": "用户名或密码错误"}), 401

    _record_login_attempt(client_ip, True)
    login_user(user, remember=bool(remember))
    return jsonify({"success": True, "username": user.username})


@auth_bp.route("/api/reset-password", methods=["POST"])
def api_reset_password():
    """忘记密码：通过邮箱验证码重置密码"""
    data = request.get_json()
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()
    new_password = data.get("password") or ""

    if not email:
        return jsonify({"error": "请填写邮箱"}), 400
    if not code:
        return jsonify({"error": "请填写验证码"}), 400
    if not new_password:
        return jsonify({"error": "请填写新密码"}), 400

    err = User.validate_password(new_password)
    if err:
        return jsonify({"error": err}), 400

    allowed, wait = _check_code_rate_limit(email)
    if not allowed:
        return jsonify({"error": f"验证码错误次数过多，请 {wait} 秒后再试"}), 429

    if not verify_code(email, code):
        _record_code_attempt(email, False)
        return jsonify({"error": "验证码错误或已过期"}), 400
    _record_code_attempt(email, True)

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "该邮箱未注册"}), 404

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": "密码已重置，请重新登录"})


@auth_bp.route("/api/update-profile", methods=["POST"])
@login_required
def api_update_profile():
    """修改用户名或密码"""
    data = request.get_json()
    action = data.get("action", "")  # "username" or "password"
    user = current_user

    if action == "username":
        new_username = (data.get("username") or "").strip()
        err = User.validate_username(new_username)
        if err:
            return jsonify({"error": err}), 400
        if User.query.filter_by(username=new_username).first():
            return jsonify({"error": "用户名已被使用"}), 409
        user.username = new_username
        db.session.commit()
        return jsonify({"success": True, "username": new_username})

    if action == "password":
        new_password = data.get("password") or ""
        code = (data.get("code") or "").strip()
        email = user.email or ""

        if not email:
            return jsonify({"error": "请先绑定邮箱"}), 400
        if not code:
            return jsonify({"error": "请填写验证码"}), 400
        allowed, wait = _check_code_rate_limit(email)
        if not allowed:
            return jsonify({"error": f"验证码错误次数过多，请 {wait} 秒后再试"}), 429
        if not verify_code(email, code):
            _record_code_attempt(email, False)
            return jsonify({"error": "验证码错误或已过期"}), 400
        _record_code_attempt(email, True)
        err = User.validate_password(new_password)
        if err:
            return jsonify({"error": err}), 400
        user.set_password(new_password)
        db.session.commit()
        return jsonify({"success": True})

    return jsonify({"error": "未知操作"}), 400


@auth_bp.route("/logout")
def logout():
    """登出"""
    logout_user()
    return redirect(url_for("welcome"))
