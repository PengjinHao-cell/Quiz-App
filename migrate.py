"""
数据库迁移脚本：为已有数据库添加缺失的列
Railway 部署前运行一次即可。
"""
import os
import sys

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ 需要设置 DATABASE_URL 环境变量")
    sys.exit(1)

# ── 需迁移的列定义 ──
MIGRATIONS = {
    "users": {
        "is_admin": {"sqlite": "INTEGER DEFAULT 0", "pg": "BOOLEAN DEFAULT FALSE"},
    },
    "question_banks": {
        "question_count": {"sqlite": "INTEGER DEFAULT 0", "pg": "INTEGER DEFAULT 0"},
        "single_count":   {"sqlite": "INTEGER DEFAULT 0", "pg": "INTEGER DEFAULT 0"},
        "multi_count":    {"sqlite": "INTEGER DEFAULT 0", "pg": "INTEGER DEFAULT 0"},
        "judge_count":    {"sqlite": "INTEGER DEFAULT 0", "pg": "INTEGER DEFAULT 0"},
        "fill_count":     {"sqlite": "INTEGER DEFAULT 0", "pg": "INTEGER DEFAULT 0"},
        "passage_count":  {"sqlite": "INTEGER DEFAULT 0", "pg": "INTEGER DEFAULT 0"},
    },
}

if DATABASE_URL.startswith("sqlite"):
    import sqlite3
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        base = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base, db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for table, cols in MIGRATIONS.items():
        c.execute(f"PRAGMA table_info({table})")
        existing = [row[1] for row in c.fetchall()]
        for col_name, sql_def in cols.items():
            if col_name not in existing:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {sql_def['sqlite']}")
                conn.commit()
                print(f"✅ SQLite: {table}.{col_name} 已添加")
            else:
                print(f"⏭️  SQLite: {table}.{col_name} 已存在，跳过")
    conn.close()

elif DATABASE_URL.startswith("postgresql"):
    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        for table, cols in MIGRATIONS.items():
            for col_name, sql_def in cols.items():
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name=:tname AND column_name=:cname"
                ), {"tname": table, "cname": col_name})
                if result.fetchone() is None:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {col_name} {sql_def['pg']}"
                    ))
                    conn.commit()
                    print(f"✅ PostgreSQL: {table}.{col_name} 已添加")
                else:
                    print(f"⏭️  PostgreSQL: {table}.{col_name} 已存在，跳过")
    engine.dispose()
else:
    print(f"❌ 不支持的数据库类型: {DATABASE_URL.split(':')[0]}")
    sys.exit(1)
