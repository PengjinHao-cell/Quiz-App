"""
数据库模型定义
- User: 用户表
"""
import re
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

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


# ========== 用户云端同步模型 ==========

class WrongAnswer(db.Model):
    """错题本（云端同步）"""
    __tablename__ = "wrong_answers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    question_key = db.Column(db.String(256), nullable=False)  # "{bank_id}_{question_id}"
    bank_id = db.Column(db.String(64), nullable=False)
    bank_name = db.Column(db.String(256), default="")
    question_id = db.Column(db.String(64), nullable=False)
    question_text = db.Column(db.Text, default="")
    question_options = db.Column(db.Text, default="{}")  # JSON
    correct_answer = db.Column(db.String(64), default="")
    user_wrong_answer = db.Column(db.String(64), default="")
    question_type = db.Column(db.String(16), default="single")
    wrong_count = db.Column(db.Integer, default=1)
    last_wrong_time = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "question_key", name="uq_user_wrong"),
    )

    def to_dict(self):
        return {
            "bank_id": self.bank_id,
            "bank_name": self.bank_name,
            "question_id": self.question_id,
            "question_text": self.question_text,
            "question_options": self.question_options,
            "correct_answer": self.correct_answer,
            "user_wrong_answer": self.user_wrong_answer,
            "type": self.question_type,
            "wrong_count": self.wrong_count,
            "last_wrong_time": self.last_wrong_time,
        }


class Favorite(db.Model):
    """收藏（云端同步）"""
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    question_key = db.Column(db.String(256), nullable=False)
    bank_id = db.Column(db.String(64), nullable=False)
    bank_name = db.Column(db.String(256), default="")
    question_id = db.Column(db.String(64), nullable=False)
    question_text = db.Column(db.Text, default="")
    question_options = db.Column(db.Text, default="{}")
    answer = db.Column(db.String(64), default="")
    question_type = db.Column(db.String(16), default="single")
    added_time = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "question_key", name="uq_user_fav"),
    )

    def to_dict(self):
        return {
            "bank_id": self.bank_id,
            "bank_name": self.bank_name,
            "question_id": self.question_id,
            "question_text": self.question_text,
            "question_options": self.question_options,
            "answer": self.answer,
            "type": self.question_type,
            "added_time": self.added_time,
        }


class StudyHistory(db.Model):
    """学习记录（云端同步）"""
    __tablename__ = "study_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    record_id = db.Column(db.String(32), nullable=False)  # 客户端生成的唯一 ID
    bank_id = db.Column(db.String(64), nullable=False)
    bank_name = db.Column(db.String(256), default="")
    mode = db.Column(db.String(16), default="practice")  # practice / exam
    score = db.Column(db.Float, default=0)
    correct = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    answers_json = db.Column(db.Text, default="{}")  # 详细答题 JSON
    time_label = db.Column(db.String(64), default="")  # 客户端时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.record_id,
            "bank_id": self.bank_id,
            "bank_name": self.bank_name,
            "mode": self.mode,
            "score": self.score,
            "correct": self.correct,
            "total": self.total,
            "time": self.time_label,
        }


class QuestionBank(db.Model):
    """题库（存储在数据库，解决 Railway 部署丢数据问题）"""
    __tablename__ = "question_banks"

    id = db.Column(db.String(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    original_filename = db.Column(db.String(256), default="")
    upload_time = db.Column(db.String(64), default="")
    type = db.Column(db.String(16), default="quiz")  # "quiz" or "reading"
    language = db.Column(db.String(8), default="zh")
    data_json = db.Column(db.Text, default="{}")  # 完整题库 JSON
    is_official = db.Column(db.Boolean, default=False)  # 管理员标记的官方题库
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SystemLog(db.Model):
    """系统运行日志"""
    __tablename__ = "system_logs"

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(16), default="info")  # info / warning / error
    source = db.Column(db.String(64), default="")      # 来源（如"上传""登录""解析"）
    message = db.Column(db.String(512), default="")
    detail = db.Column(db.Text, default="")            # 详细错误信息
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    username = db.Column(db.String(64), default="")
    ip_address = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
