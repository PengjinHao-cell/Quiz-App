"""通过代理 dump Railway PG"""
import socket, ssl, json, os, threading, time, sys

T_HOST, T_PORT = 'zephyr.proxy.rlwy.net', 16667
PROXY_HOST, PROXY_PORT = '127.0.0.1', 20122
LOCAL_PORT = 15433

done = threading.Event()

def tunnel():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', LOCAL_PORT))
    srv.listen(1)
    srv.settimeout(30)
    print("[tunnel] listening", file=sys.stderr)

    try:
        client, addr = srv.accept()
        print(f"[tunnel] accepted {addr}", file=sys.stderr)

        # 连代理
        proxy = socket.create_connection((PROXY_HOST, PROXY_PORT), timeout=10)
        req = f"CONNECT {T_HOST}:{T_PORT} HTTP/1.1\r\nHost: {T_HOST}:{T_PORT}\r\n\r\n"
        proxy.sendall(req.encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += proxy.recv(4096)
        print(f"[tunnel] proxy: {resp.split(b'\r\n')[0].decode()}", file=sys.stderr)

        # SSL
        ctx = ssl.create_default_context()
        ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        remote = ctx.wrap_socket(proxy, server_hostname=T_HOST)
        print("[tunnel] SSL established", file=sys.stderr)

        def fwd(a, b):
            try:
                while not done.is_set():
                    data = a.recv(8192)
                    if not data: break
                    b.sendall(data)
            except: pass

        t1 = threading.Thread(target=fwd, args=(client, remote)); t1.daemon = True; t1.start()
        t2 = threading.Thread(target=fwd, args=(remote, client)); t2.daemon = True; t2.start()
        t1.join(); t2.join()
    except Exception as e:
        print(f"[tunnel] error: {e}", file=sys.stderr)
    finally:
        srv.close()

# 启动隧道（先 accept，等客户端连）
t = threading.Thread(target=tunnel)
t.start()
time.sleep(0.3)

print("[main] connecting pg...", file=sys.stderr)
import psycopg2
conn = psycopg2.connect(
    host='127.0.0.1', port=LOCAL_PORT,
    dbname='railway', user='postgres',
    password='WDgsGGrlFVvKKimWevYGgdNtyHIqSNjc',
    connect_timeout=15, sslmode='disable'
)
print("[main] pg connected", file=sys.stderr)

cur = conn.cursor()
dump = {}
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [r[0] for r in cur.fetchall()]
print(f"Tables: {tables}")

for table in tables:
    cur.execute(f'SELECT * FROM "{table}"')
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    dump[table] = [dict(zip(cols, [str(v) if v is not None else None for v in row])) for row in rows]
    print(f"  {table}: {len(rows)} rows")

conn.close()
done.set()

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "railway_backup.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(dump, f, ensure_ascii=False, indent=2)
print(f"\n✅ Backup: {path} ({os.path.getsize(path)} bytes)")
