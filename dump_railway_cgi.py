"""在 Railway 容器内运行，dump PG 到 JSON 并通过 HTTP 返回"""
import json, os, psycopg2

DB = os.environ.get("DATABASE_URL", "")
if not DB:
    print("Content-Type: text/plain\n")
    print("DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(DB, connect_timeout=5)
cur = conn.cursor()

dump = {}
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [r[0] for r in cur.fetchall()]

for table in tables:
    cur.execute(f'SELECT * FROM "{table}"')
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    dump[table] = [
        dict(zip(cols, [str(v) if v is not None else None for v in row]))
        for row in rows
    ]

conn.close()

print("Content-Type: application/json\n")
print(json.dumps(dump, ensure_ascii=False))
