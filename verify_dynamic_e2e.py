"""直接用后端 API 跑完 10 轮 choice 让 dynamic 对话结束, 然后用 Playwright 观察前端是否埋点."""
import asyncio
import json
import sys
import urllib.request
import urllib.error


def post(url: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:200]}")
        return {}


def main() -> int:
    # 1. 启动 dynamic 对话
    import time, uuid
    session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    print(f"[1] start dynamic dialogue for 商鞅变法 session={session_id}")
    res = post("http://127.0.0.1:8000/api/dialogue/dynamic/start", {
        "topic": "商鞅变法",
        "session_id": session_id,
    })
    print(f"   -> {json.dumps(res, ensure_ascii=False)[:300]}")
    if not res.get("data"):
        print("FAIL: no dialogue started")
        return 1
    dialogue_id = res["data"]["dialogue_id"]
    print(f"   dialogue_id = {dialogue_id}")

    # 2. 走 10 轮 choice
    for i in range(10):
        choice_id = "explore_origin" if i % 2 == 0 else "ask_impact"
        res = post("http://127.0.0.1:8000/api/dialogue/dynamic/choice", {
            "dialogue_id": dialogue_id,
            "choice_id": choice_id,
        })
        if not res.get("data"):
            print(f"   round {i}: FAIL - {res}")
            return 1
        d = res["data"]
        is_ending = d.get("is_ending", False)
        print(f"   round {i+1} choice={choice_id} is_ending={is_ending}")
        if is_ending:
            print(f"   narrative head: {(d.get('narrative') or '')[:80]}")
            break

    print(f"\n[OK] dialogue {dialogue_id} ended via API")
    return 0


if __name__ == "__main__":
    sys.exit(main())
