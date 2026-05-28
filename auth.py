"""
认证蓝图：注册 / 登录 / 登出
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """注册"""
    if request.method == "GET":
        return render_template("register.html")

    # POST: AJAX 注册
    data = request.get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip()

    # 校验用户名
    err = User.validate_username(username)
    if err:
        return jsonify({"error": err}), 400

    # 校验密码
    err = User.validate_password(password)
    if err:
        return jsonify({"error": err}), 400

    # 用户名唯一
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "用户名已被注册"}), 409

    # 邮箱唯一（如果填写了）
    if email:
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "邮箱已被绑定"}), 409

    # 创建用户
    user = User(username=username, email=email or None)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return jsonify({"success": True, "username": user.username})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """登录"""
    if request.method == "GET":
        return render_template("login.html")

    # POST: AJAX 登录
    data = request.get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "用户名或密码错误"}), 401

    login_user(user, remember=True)
    return jsonify({"success": True, "username": user.username})


@auth_bp.route("/logout")
def logout():
    """登出"""
    logout_user()
    return redirect(url_for("app_main"))
