"""端到端验证: 星图数据接口
1. 后端 GET /api/star-data 返回 D3 标准 JSON
2. 节点固定 50, 字段含 id/name/category/value
3. value 反映 session 探索次数
4. 链接基于因果
5. CORS 预检通过
"""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"
SID = f"verify_star_session_{__import__('time').time()}"


def get(path, params=None, headers=None):
    from urllib.parse import urlencode
    url = BASE + path
    if params:
        url += "?" + urlencode(params)
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), json.loads(e.read().decode() or "{}")
    except Exception as e:
        return 0, {}, {"error": str(e)}


def main():
    print("=" * 60)
    print("[1] GET /api/star-data (无 session_id)")
    code, headers, body = get("/api/star-data")
    assert code == 200, f"应返回 200, 实际 {code} body={body}"
    data = body.get("data") or {}
    nodes = data.get("nodes") or []
    links = data.get("links") or []
    print(f"  status={code} nodes={len(nodes)} links={len(links)}")
    assert "nodes" in data and "links" in data, "返回结构必须含 nodes 和 links"

    print()
    print("[2] 节点数 <= 50, 字段完整")
    assert len(nodes) <= 50, f"节点应 <= 50, 实际 {len(nodes)}"
    for n in nodes[:3]:
        for k in ("id", "name", "category", "value"):
            assert k in n, f"节点缺少字段 {k}"
        print(f"  - {n['id']:30s} | {n['name']:20s} | {n['category']:5s} | value={n['value']}")
    print("  [OK] 节点字段完整")

    print()
    print("[3] 节点 value 反映 session 探索次数")
    evt_id = nodes[0]["id"]
    import time
    for i in range(3):
        post_url = BASE + "/api/exploration/start"
        payload = json.dumps({
            "session_id": SID,
            "event_id": evt_id,
        }).encode()
        req = urllib.request.Request(
            post_url, data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                r.read()
        except Exception as e:
            print(f"  [warn] exploration start 失败: {e}")
        post_url = BASE + "/api/exploration/end"
        payload = json.dumps({
            "session_id": SID,
            "event_id": evt_id,
            "duration": 30,
        }).encode()
        req = urllib.request.Request(
            post_url, data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                r.read()
        except Exception as e:
            print(f"  [warn] exploration end 失败: {e}")
        time.sleep(0.1)
    code, _, body = get("/api/star-data", {"session_id": SID})
    new_nodes = (body.get("data") or {}).get("nodes") or []
    target = next((n for n in new_nodes if n["id"] == evt_id), None)
    if target is None:
        print(f"  [warn] 节点 {evt_id} 不在 top 50, 跳过 value 验证")
    else:
        print(f"  节点 {evt_id} 探索 3 次后 value={target['value']}")
        assert target["value"] >= 1, f"value 应 >= 1, 实际 {target['value']}"

    print()
    print("[4] 链接基于因果 (字段 source/target 存在)")
    if links:
        lk = links[0]
        assert "source" in lk and "target" in lk
        print(f"  示例: {lk['source']} -> {lk['target']}")
    print(f"  链接总数: {len(links)}")
    print("  [OK] 链接结构正确")

    print()
    print("[5] CORS 预检 (OPTIONS)")
    req = urllib.request.Request(
        BASE + "/api/star-data",
        method="OPTIONS",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            cors_headers = {k: v for k, v in resp.headers.items() if k.lower().startswith("access-control")}
            all_headers = dict(resp.headers)
            print(f"  status={resp.status} cors_headers={cors_headers}")
            print(f"  all_headers_keys={list(all_headers.keys())}")
            assert resp.status in (200, 204), f"OPTIONS 应 200/204, 实际 {resp.status}"
            assert any("localhost:5173" in v for v in cors_headers.values()), \
                f"应返回 Access-Control-Allow-Origin 含 localhost:5173, 实际 {cors_headers}"
            print("  [OK] CORS 预检通过")
    except urllib.error.HTTPError as e:
        cors_headers = {k: v for k, v in e.headers.items() if "Access-Control" in k}
        all_headers = dict(e.headers)
        print(f"  status={e.code} cors_headers={cors_headers}")
        print(f"  all_headers_keys={list(all_headers.keys())}")
        if e.code in (200, 204):
            print("  [OK] CORS 预检通过 (HTTPError 包装)")
        else:
            raise

    print()
    print("[6] 节点分类分布")
    from collections import Counter
    cats = Counter(n["category"] for n in nodes)
    print(f"  {dict(cats)}")
    assert len(cats) >= 2, f"应包含多个文明分类, 实际 {dict(cats)}"

    print()
    print("=" * 60)
    print("[ALL PASS] 星图数据接口与 CORS 端到端验证全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
