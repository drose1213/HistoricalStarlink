"""端到端验证: 卡牌与排行榜真实化

1. 验证 /api/champion 返回分页结构
2. 验证 /api/leaderboard 返回 ranking + championEvents
3. 模拟 session 创建几张卡牌 (POST /api/champion), 再拉取验证可见
4. 验证空数据场景的处理
"""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"
import time
SID = f"verify_session_champion_lb_{int(time.time())}"


def get(path, params=None):
    url = BASE + path
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")
    except Exception as e:
        return 0, {"error": str(e)}


def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")
    except Exception as e:
        return 0, {"error": str(e)}


def main():
    print("=" * 60)
    print("[1] GET /api/champion (空 session)")
    code, body = get("/api/champion", {"session_id": SID, "page": 1, "page_size": 20})
    print(f"  status={code} items={len(body.get('data') or [])} total={body.get('total')}")
    assert code == 200, "champion 列表接口应返回 200"
    assert body.get("total") == 0, f"新 session 应无卡牌, 实际 total={body.get('total')}"
    print("  [OK] 空 session 拉取卡牌接口成功, 无数据")

    print()
    print("[2] POST /api/champion 模拟 3 张不同等级卡牌")
    cards = [
        {"session_id": SID, "event_id": "evt_qin", "event_name": "秦始皇统一六国",
         "event_year": -221, "event_region": "china", "event_description": "公元前221年秦灭六国, 书同文车同轨"},
        {"session_id": SID, "event_id": "evt_roman", "event_name": "罗马帝国建立",
         "event_year": -27, "event_region": "foreign", "event_description": "屋大维加冕, 罗马进入帝国时代"},
        {"session_id": SID, "event_id": "evt_tang", "event_name": "大唐盛世",
         "event_year": 712, "event_region": "china", "event_description": "贞观之治与开元盛世, 万邦来朝"},
    ]
    created_ids = []
    for c in cards:
        code, body = post("/api/champion", c)
        print(f"  POST {c['event_name']} -> status={code} card_level={body.get('data', {}).get('card_level') if body.get('data') else 'N/A'}")
        assert code == 200, f"创建卡牌失败: {body}"
        created_ids.append(body["data"]["id"])

    print()
    print("[3] 多次 POST 同一事件以触发 explore_count 累计")
    for _ in range(3):
        post("/api/champion", cards[0])
    code, body = get("/api/champion", {"session_id": SID, "event_id": "evt_qin"})
    items = body.get("data") or []
    if not items and "items" in (body.get("data") or {}):
        items = body["data"]["items"]
    qin_card = items[0] if items else None
    print(f"  秦卡牌 explore_count={qin_card['explore_count']} level={qin_card['card_level']}")
    assert qin_card["explore_count"] >= 4, f"累计探索次数应 >= 4, 实际 {qin_card['explore_count']}"

    print()
    print("[4] GET /api/champion 拉取所有卡牌")
    code, body = get("/api/champion", {"session_id": SID, "page": 1, "page_size": 20})
    items = body.get("data") or body.get("items") or []
    print(f"  status={code} total={body.get('total')} items_count={len(items)}")
    for c in items:
        print(f"  - id={c['id']} name={c['event_name']} level={c['card_level']} count={c['explore_count']}")
    assert body.get("total") == 3, f"应有 3 张卡牌, 实际 {body.get('total')}"
    print("  [OK] 真实数据接入验证通过")

    print()
    print("[5] GET /api/leaderboard")
    for period in ("daily", "weekly", "monthly", "yearly"):
        code, body = get("/api/leaderboard", {"period": period, "limit": 10})
        ranking = body.get("data", {}).get("ranking", []) or []
        events = body.get("data", {}).get("championEvents", []) or []
        print(f"  period={period} status={code} ranking={len(ranking)} events={len(events)}")
        assert code == 200, f"leaderboard 接口应 200, 实际 {code}"
    print("  [OK] 排行榜各周期接口可达")

    print()
    print("=" * 60)
    print("[ALL PASS] 卡牌与排行榜真实化后端验证全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
