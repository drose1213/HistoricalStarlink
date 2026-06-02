"""快速验证后端 8000 端口可访问关键端点"""
import urllib.request
import urllib.parse
import json
import time


def call(method: str, url: str, body: dict | None = None, params: dict | None = None) -> tuple:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if body else {})
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.status, (time.time() - t0) * 1000, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, (time.time() - t0) * 1000, {"error": e.read().decode()[:200]}
    except Exception as e:
        return -1, (time.time() - t0) * 1000, {"error": str(e)}


print("=" * 70)
cases = [
    ("GET", "http://127.0.0.1:8000/api/events/home", None, {"session_id": "session_1780410194445_kg8bs5rb"}),
    ("GET", "http://127.0.0.1:8000/api/events/home", None, None),
    ("GET", "http://127.0.0.1:8000/api/events", None, {"page_size": 3}),
    ("POST", "http://127.0.0.1:8000/api/rag/search-hybrid", {"query": "长城", "top_k": 3}, None),
    ("POST", "http://127.0.0.1:8000/api/rag/search", {"query": "长城", "top_k": 3}, None),
]

for m, u, b, p in cases:
    sc, ms, body = call(m, u, b, p)
    extra = ""
    if isinstance(body, dict) and "data" in body and isinstance(body["data"], dict):
        d = body["data"]
        if "recommended_total" in d:
            extra = f"recommended={d.get('recommended_total')} explored={d.get('explored_total')}"
        elif "list" in d:
            extra = f"total={d.get('total')}"
        elif isinstance(d, list):
            sources = [i.get("source") for i in d[:5] if isinstance(i, dict)]
            extra = f"items={len(d)} sources={sources}"
    print(f"{m:6s} {u.split('//')[1]:50s} {sc:>4d}  {ms:6.1f}ms  {extra}")
