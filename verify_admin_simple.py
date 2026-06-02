"""直接打印 register 详细错误"""
import json
import time
import urllib.request
import urllib.error

ts = int(time.time())
body = {
    "username": f"test_{ts}",
    "email": f"test_{ts}@example.com",
    "email_code": "000000",
    "password": "TestPass123!",
    "nickname": "test"
}
data = json.dumps(body).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/auth/register",
    data=data, method="POST",
    headers={"Content-Type": "application/json"},
)
try:
    r = urllib.request.urlopen(req, timeout=10)
    print("HTTP", r.status)
    print(r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:500])
