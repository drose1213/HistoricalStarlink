"""直接验证: 1) users 表已有 is_admin 列; 2) 手动插入测试用户, 验证 login/me 响应含 is_admin"""
import json
import time
import urllib.request
import urllib.error
import sqlite3
from pathlib import Path


def call(method, url, body=None, token=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:200]}


# 1) 直接查 SQLite 表结构
sqlite_path = Path("data/local.db")
if not sqlite_path.exists():
    sqlite_path = Path("backend/data/local.db")
if not sqlite_path.exists():
    sqlite_path = Path("historical_starlink.db")
print(f"DB path: {sqlite_path.resolve()}")
print("=" * 70)
print("【1. SQLite 表结构验证】")
print("=" * 70)
conn = sqlite3.connect(str(sqlite_path))
cur = conn.execute("PRAGMA table_info(users)")
cols = cur.fetchall()
print(f"{'cid':>4s} {'name':20s} {'type':12s} {'notnull':>8s} {'default'}")
for c in cols:
    print(f"{c[0]:>4d} {c[1]:20s} {c[2]:12s} {c[3]:>8d} {c[4]}")
has_is_admin = any(c[1] == "is_admin" for c in cols)
print(f"\n[{'OK' if has_is_admin else 'FAIL'}] is_admin 列已存在: {has_is_admin}")
conn.close()

# 2) 手动 hash 密码 + 插入 admin user
print()
print("=" * 70)
print("【2. 手动插入 admin=true 测试用户】")
print("=" * 70)
import hashlib
import secrets

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200000)
    return f"{salt}${h.hex()}"

ts = int(time.time())
username = f"adm_{ts}"
email = f"adm_{ts}@example.com"
password = "AdminTest123!"
hashed = _hash_password(password)
nickname = "Admin Test"

conn = sqlite3.connect(str(sqlite_path))
conn.execute(
    "INSERT INTO users (username, email, hashed_password, nickname, avatar_url, is_active, is_admin, created_at, updated_at) "
    "VALUES (?, ?, ?, ?, '', 1, 1, datetime('now'), datetime('now'))",
    (username, email, hashed, nickname),
)
conn.commit()
print(f"  插入用户: {username}, is_admin=1")

# 读取回填确认
cur = conn.execute("SELECT id, username, is_admin FROM users WHERE username = ?", (username,))
row = cur.fetchone()
print(f"  回读: id={row[0]}, username={row[1]}, is_admin={row[2]}")
conn.close()

# 3) 用此用户登录, 验证 is_admin=true 在响应中
print()
print("=" * 70)
print("【3. 登录响应含 is_admin=true】")
print("=" * 70)
sc, body = call("POST", "http://127.0.0.1:8000/api/auth/login",
                 {"username": username, "password": password})
print(f"  HTTP {sc}")
print(f"  响应 user: {body.get('data', {}).get('user', {})}")
is_admin_login = body.get("data", {}).get("user", {}).get("is_admin")
token = body.get("data", {}).get("token")

# 4) /me 验证
print()
print("=" * 70)
print("【4. /api/auth/me 响应含 is_admin=true】")
print("=" * 70)
if token:
    sc, body = call("GET", "http://127.0.0.1:8000/api/auth/me", token=token)
    print(f"  HTTP {sc}")
    print(f"  响应: {body}")
    is_admin_me = body.get("data", {}).get("is_admin")
else:
    is_admin_me = None
    print("  无 token, 跳过")

# 5) 验证
print()
print("=" * 70)
verdict = "PASS" if (has_is_admin and is_admin_login is True and is_admin_me is True) else "WARN"
print(f"[{verdict}] is_admin 字段已正确流转: 列存在={has_is_admin}, login={is_admin_login}, me={is_admin_me}")
print("=" * 70)
