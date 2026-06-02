"""端到端验证 is_admin 字段在登录与 /me 响应中存在"""
import json
import time
import urllib.request
import urllib.error


def call(method: str, url: str, body=None, token=None) -> tuple:
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.status, (time.time() - t0) * 1000, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, (time.time() - t0) * 1000, {"error": e.read().decode()[:300]}
    except Exception as e:
        return -1, (time.time() - t0) * 1000, {"error": str(e)}


print("=" * 70)
print(f"{'METHOD':6s} {'PATH':35s} {'STATUS':>5s} {'TIME':>7s}  KEY FIELDS")
print("=" * 70)

# 1. 注册一个新测试用户
test_user = {
    "username": f"tester_admin_{int(time.time())}",
    "email": f"tester_admin_{int(time.time())}@example.com",
    "email_code": "000000",  # 测试环境验证码可能是任何值, 看后端
    "password": "TestPass123!",
    "nickname": "管理员测试"
}

sc, ms, body = call("POST", "http://127.0.0.1:8000/api/auth/register", test_user)
is_admin_register = body.get("data", {}).get("user", {}).get("is_admin")
print(f"{'POST':6s} {'/api/auth/register':35s} {sc:>5d} {ms:>5.1f}ms  is_admin={is_admin_register}")

# 2. 用新用户登录
sc, ms, body = call("POST", "http://127.0.0.1:8000/api/auth/login",
                     {"username": test_user["username"], "password": test_user["password"]})
token = body.get("data", {}).get("token")
is_admin_login = body.get("data", {}).get("user", {}).get("is_admin")
print(f"{'POST':6s} {'/api/auth/login':35s} {sc:>5d} {ms:>5.1f}ms  is_admin={is_admin_login}")

# 3. /api/auth/me
if token:
    sc, ms, body = call("GET", "http://127.0.0.1:8000/api/auth/me", token=token)
    is_admin_me = body.get("data", {}).get("is_admin")
    print(f"{'GET':6s} {'/api/auth/me':35s} {sc:>5d} {ms:>5.1f}ms  is_admin={is_admin_me}")
else:
    print(f"{'GET':6s} {'/api/auth/me':35s} {'SKIP':>5s} (no token)")
    is_admin_me = None

print()
print("=" * 70)
verdict = "PASS" if is_admin_register is False and is_admin_login is False and is_admin_me is False else "WARN"
print(f"[{verdict}] 新用户三处 is_admin 均应为 False (默认非管理员)")
print("=" * 70)
