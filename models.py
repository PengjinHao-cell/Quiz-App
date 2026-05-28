"""
数据库模型定义
- User: 用户表
"""
import re
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_username(username: str):
        """校验用户名，返回 None 表示合法，否则返回错误信息"""
        if not username or len(username) < 2:
            return "用户名至少 2 个字符"
        if len(username) > 32:
            return "用户名不能超过 32 个字符"
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            return "用户名只能包含字母和数字"
        return None

    @staticmethod
    def validate_password(password: str):
        """校验密码，返回 None 表示合法"""
        if not password or len(password) < 6:
            return "密码至少 6 个字符"
        if not re.search(r'[a-zA-Z]', password):
            return "密码必须包含字母"
        if not re.search(r'[0-9]', password):
            return "密码必须包含数字"
        if not re.search(r'[^a-zA-Z0-9]', password):
            return "密码必须包含特殊字符"
        return None

    def __repr__(self):
        return f"<User {self.username}>"
