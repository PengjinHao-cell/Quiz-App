"""
数据库迁移脚本：为已有数据库添加 is_admin 列
Railway 部署前运行一次即可。
"""
import os
import sys

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ 需要设置 DATABASE_URL 环境变量")
    sys.exit(1)

if DATABASE_URL.startswith("sqlite"):
    # SQLite
    import sqlite3
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        base = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base, db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in c.fetchall()]
    if "is_admin" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        conn.commit()
        print("✅ SQLite: 已添加 is_admin 列")
    else:
        print("✅ SQLite: is_admin 列已存在")
    conn.close()

elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL
    import urllib.parse
    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # 检查列是否存在
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='is_admin'"
        ))
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("✅ PostgreSQL: 已添加 is_admin 列")
        else:
            print("✅ PostgreSQL: is_admin 列已存在")

    engine.dispose()
else:
    print(f"❌ 不支持的数据库类型: {DATABASE_URL.split(':')[0]}")
    sys.exit(1)
