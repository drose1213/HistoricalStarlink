"""HTTP 端到端验证: 直接调用 FastAPI TestClient 避免 curl 兼容性问题"""
import json
import time
import sys
import logging
import os
os.environ.setdefault("SQLALCHEMY_WARN_20", "0")
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("sqlalchemy").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
logging.getLogger("historical_starlink").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

import backend.config as _cfg
_cfg.settings.DEBUG = False

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import engine
engine.echo = False

client = TestClient(app)

def call(method: str, path: str, **kw) -> tuple:
    t0 = time.time()
    if method == "GET":
        r = client.get(path, **kw)
    else:
        r = client.post(path, **kw)
    dt = (time.time() - t0) * 1000
    return r.status_code, dt, r


cases = [
    ("GET",  "/api/events/home",                      {"params": {"session_id": "test-session-1"}}),
    ("GET",  "/api/events/home",                      {}),
    ("GET",  "/api/events",                           {"params": {"page_size": 5}}),
    ("POST", "/api/rag/search-hybrid",                {"json": {"query": "长城", "top_k": 3}}),
    ("POST", "/api/rag/search",                       {"json": {"query": "长城", "top_k": 3}}),
    ("GET",  "/api/health",                           {}),
    # 空 event_name 过滤的端到端: 通过 import/manual 路径
    ("POST", "/api/rag/import/manual",                {"json": {"title": "空事件名测试", "content": "正文", "event_name": "", "source_type": "test"}}),
]

print("=" * 70)
print(f"{'METHOD':6s} {'PATH':35s} {'STATUS':7s} {'TIME(ms)':9s} NOTES")
print("=" * 70)

for method, path, kw in cases:
    try:
        sc, ms, r = call(method, path, **kw)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else None
        note = ""
        if method == "GET" and path == "/api/events/home":
            if body and "data" in body:
                d = body["data"]
                note = f"recommended={d.get('recommended_total',0)} explored={d.get('explored_total',0)}"
        if method == "POST" and path == "/api/rag/import/manual":
            note = f"body={str(body)[:120]}"
        if method == "POST" and "/api/rag/search" in path:
            items = body.get("data", []) if body else []
            sources = [i.get("source") for i in items[:5]] if isinstance(items, list) else []
            note = f"items={len(items) if isinstance(items, list) else 'N/A'} sources={sources}"
        print(f"{method:6s} {path:35s} {sc:<7d} {ms:7.1f}   {note}")
    except Exception as e:
        print(f"{method:6s} {path:35s} EXCEPTION  -          {e}")

print("=" * 70)
print("DONE")
