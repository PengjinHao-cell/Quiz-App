"""
管理员账号初始化脚本。
用法：python init_admin.py
效果：创建管理员用户 PuertoJupiter（如已存在则跳过）
"""
import os
import sys

# 确保能导入项目模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from app import app, db
from models import User

ADMIN_USERNAME = "PuertoJupiter"
ADMIN_PASSWORD = "REDACTED"

def main():
    with app.app_context():
        existing = User.query.filter_by(username=ADMIN_USERNAME).first()
        if existing:
            print(f"✅ 管理员用户「{ADMIN_USERNAME}」已存在，跳过")
            return

        user = User(username=ADMIN_USERNAME, email="admin@quizmaster.app")
        user.set_password(ADMIN_PASSWORD)
        db.session.add(user)
        db.session.commit()
        print(f"✅ 管理员用户「{ADMIN_USERNAME}」创建成功")

if __name__ == "__main__":
    main()
