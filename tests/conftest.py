"""
pytest 配置 — 使用 SQLite 内存数据库进行测试
必须在导入 app 前设置 DATABASE_URL 才能覆盖 module-level 的初始化
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest"
os.environ["FLASK_ENV"] = "test"

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from app import app as _app, db as _db
from models import User, WrongAnswer, Favorite, StudyHistory


@pytest.fixture
def app():
    """提供测试用的 Flask 应用实例，每个测试函数结束后回滚数据库"""
    _app.config["TESTING"] = True
    _app.config["WTF_CSRF_ENABLED"] = False
    _app.config["SERVER_NAME"] = "test.local"

    with _app.app_context():
        _db.create_all()
        yield _app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """测试客户端"""
    return app.test_client()


@pytest.fixture
def db(app):
    """数据库实例"""
    return _db


# ---------- 用户相关 fixture ----------

def _create_user(username="testuser", password="Test@123", email="test@example.com", is_admin=False):
    """创建测试用户（不提交事务，由调用方管理 session）"""
    user = User(
        username=username,
        email=email,
        is_admin=is_admin,
        created_at=None,  # 使用默认值
    )
    user.set_password(password)
    _db.session.add(user)
    _db.session.flush()
    return user


@pytest.fixture
def normal_user(db):
    """创建并返回一个普通用户（已持久化）"""
    user = _create_user()
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db):
    """创建并返回一个管理员用户"""
    user = _create_user(username="admin", email="admin@example.com", is_admin=True)
    db.session.commit()
    return user


@pytest.fixture
def logged_in_client(client, normal_user):
    """已登录普通用户的测试客户端"""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(normal_user.id)
        sess["_fresh"] = True
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """已登录管理员的测试客户端"""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_user.id)
        sess["_fresh"] = True
    return client


# ---------- 同步数据 fixture ----------

@pytest.fixture
def sample_wrong_book_data():
    """示例错题数据"""
    return {
        "items": [
            {
                "question_key": "bank1_q1",
                "bank_id": "bank1",
                "bank_name": "测试题库",
                "question_id": "q1",
                "question_text": "1+1=?",
                "question_options": json.dumps({"A": "1", "B": "2", "C": "3", "D": "4"}),
                "correct_answer": "B",
                "user_wrong_answer": "A",
                "question_type": "single",
                "wrong_count": 2,
                "last_wrong_time": "2026-01-01 10:00",
            },
            {
                "question_key": "bank1_q2",
                "bank_id": "bank1",
                "bank_name": "测试题库",
                "question_id": "q2",
                "question_text": "2+2=?",
                "question_options": json.dumps({"A": "1", "B": "2", "C": "3", "D": "4"}),
                "correct_answer": "D",
                "user_wrong_answer": "A",
                "question_type": "single",
                "wrong_count": 1,
                "last_wrong_time": "2026-01-01 11:00",
            },
        ]
    }


@pytest.fixture
def sample_favorites_data():
    """示例收藏数据"""
    return {
        "items": [
            {
                "question_key": "bank1_fav1",
                "bank_id": "bank1",
                "bank_name": "测试题库",
                "question_id": "fav1",
                "question_text": "什么是 Python？",
                "question_options": json.dumps({"A": "语言", "B": "蛇"}),
                "answer": "A",
                "question_type": "single",
                "added_time": "2026-01-01 12:00",
            },
        ]
    }


@pytest.fixture
def sample_history_data():
    """示例学习记录数据"""
    return {
        "items": [
            {
                "id": "test_hist_001",
                "bank_id": "bank1",
                "bank_name": "测试题库",
                "mode": "practice",
                "score": 80,
                "correct": 8,
                "total": 10,
                "answers_json": json.dumps({"q1": "B", "q2": "D"}),
                "time": "2026-01-01 14:00",
            },
        ]
    }
