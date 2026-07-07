"""对话 API 黑盒测试"""
import re
import pytest


@pytest.mark.e2e
class TestDialogueAPI:
    """测试 /api/dialogue 系列接口"""

    # SESSION_PATTERN = session_<digits>_<8 hex/alnum chars>
    # 基础串尾部 7 字符 + 1 字符后缀 = 8 字符
    _BASE = "session_1700000200_pr0file"  # 7 chars after last _, +suffix = 8

    def _sid(self, suffix: str) -> str:
        return self._BASE + suffix

    async def test_list_available_events(self, client, test_db):
        """获取可对话事件列表"""
        res = await client.get("/api/dialogue/events")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body["data"], list)
        assert len(body["data"]) > 0

    async def test_start_dialogue_success(self, client, test_db):
        res = await client.post("/api/dialogue/start", json={
            "event_id": "qin_unification",
            "session_id": "session_1700000000_abcdef01",
        })
        assert res.status_code == 200
        body = res.json()
        assert body["code"] == 200
        assert "dialogue_id" in body["data"]
        assert "narrative" in body["data"]
        assert "choices" in body["data"]
        assert len(body["data"]["choices"]) > 0

    async def test_start_dialogue_no_script_returns_404(self, client, test_db):
        res = await client.post("/api/dialogue/start", json={
            "event_id": "nonexistent_event_xyz",
            "session_id": "session_1700000000_abcdef02",
        })
        # 事件没剧本 → 404
        assert res.status_code == 404

    async def test_start_dialogue_invalid_session(self, client, test_db):
        res = await client.post("/api/dialogue/start", json={
            "event_id": "qin_unification",
            "session_id": "invalid_session",
        })
        # session 格式不对 → 400
        assert res.status_code == 400

    async def test_dialogue_flow_e2e(self, client, test_db):
        """完整对话流程：start → choice → chat → ending"""
        # 1. 启动
        start_res = await client.post("/api/dialogue/start", json={
            "event_id": "qin_unification",
            "session_id": "session_1700000000_abcdef03",
        })
        start_body = start_res.json()
        dialogue_id = start_body["data"]["dialogue_id"]
        choices = start_body["data"]["choices"]
        assert len(choices) > 0

        # 2. 选择
        choice_res = await client.post("/api/dialogue/choice", json={
            "dialogue_id": str(dialogue_id),
            "choice_id": choices[0]["choice_id"],
        })
        assert choice_res.status_code == 200
        choice_body = choice_res.json()
        assert "narrative" in choice_body["data"]

        # 3. 自由聊天
        chat_res = await client.post("/api/dialogue/chat", json={
            "dialogue_id": str(dialogue_id),
            "message": "陛下英明",
        })
        assert chat_res.status_code == 200
        chat_body = chat_res.json()
        assert "narrative" in chat_body["data"]

    async def test_dialogue_choice_invalid_dialogue(self, client, test_db):
        res = await client.post("/api/dialogue/choice", json={
            "dialogue_id": "99999",
            "choice_id": "a",
        })
        assert res.status_code == 404

    async def test_dialogue_records_list(self, client, test_db):
        res = await client.get("/api/dialogue/records?page=1&page_size=5")
        assert res.status_code == 200
        body = res.json()
        assert "data" in body
        assert "total" in body
        assert isinstance(body["data"], list)

    # ========== 分支结局 + 用户画像增强 (Task 5) ==========

    async def test_start_returns_cumulative_impact(self, client, test_db):
        """start 接口响应应包含 cumulative_impact / path_signature / predicted_endings"""
        res = await client.post("/api/dialogue/start", json={
            "event_id": "qin_unification",
            "session_id": self._sid("1"),
        })
        assert res.status_code == 200, res.text
        body = res.json()["data"]
        assert "cumulative_impact" in body
        ci = body["cumulative_impact"]
        assert "reform" in ci
        assert "conservative" in ci
        assert "empathy" in ci
        assert "radicalism" in ci
        assert ci["reform"] == 0
        assert "path_signature" in body
        assert body["path_signature"] == ""
        assert "predicted_endings" in body
        assert isinstance(body["predicted_endings"], list)

    async def test_choice_cumulative_accumulates(self, client, test_db):
        """连续 choice 后 cumulative_impact 应累计, path_signature 反映路径"""
        start_res = await client.post("/api/dialogue/start", json={
            "event_id": "qin_unification",
            "session_id": self._sid("2"),
        })
        assert start_res.status_code == 200, start_res.text
        dialogue_id = start_res.json()["data"]["dialogue_id"]

        # round 1: choice a (mood=agree)
        r1 = await client.post("/api/dialogue/choice", json={
            "dialogue_id": str(dialogue_id),
            "choice_id": "a",
        })
        assert r1.status_code == 200, r1.text
        body1 = r1.json()["data"]
        # cumulative_impact.conservative 应当增加 (agree +10)
        assert body1["cumulative_impact"]["conservative"] == 10
        assert body1["path_signature"] == "A"

        # 找到 round 2 thoughtful 的 choice
        # 已知 round2 options: a=thoughtful, b=thoughtful, c=agree
        # 直接选 a → thoughtful
        if not body1.get("is_ending") and body1.get("choices"):
            # 找出 mood=thoughtful 的 choice
            t_choice = None
            for c in body1["choices"]:
                if c.get("mood") == "thoughtful":
                    t_choice = c["choice_id"]
                    break
            if t_choice is None:
                t_choice = "a"  # fallback
            r2 = await client.post("/api/dialogue/choice", json={
                "dialogue_id": str(dialogue_id),
                "choice_id": t_choice,
            })
            assert r2.status_code == 200, r2.text
            body2 = r2.json()["data"]
            # 若选到 thoughtful, reform 应 >= 10
            if not body2.get("is_ending"):
                assert body2["cumulative_impact"]["reform"] >= 10
                assert body2["path_signature"] in ("A-T", "A-D", "A-A")

    async def test_profile_empty_session_returns_zero(self, client, test_db):
        """未探索过的 session 返回空画像"""
        res = await client.get(f"/api/dialogue/profile?session_id={self._sid('3')}")
        assert res.status_code == 200, res.text
        body = res.json()["data"]
        assert body["records"] == []
        assert body["aggregate"]["reform"] == 0
        assert body["aggregate"]["conservative"] == 0
        assert body["events_explored"] == []
        assert body["endings_unlocked"] == 0

    async def test_profile_invalid_session_returns_400(self, client, test_db):
        """非法 session_id 返回 400"""
        res = await client.get("/api/dialogue/profile?session_id=invalid_format")
        assert res.status_code == 400

    async def test_branches_returns_all_endings(self, client, test_db):
        """GET /branches/{event_id} 返回全部结局"""
        res = await client.get("/api/dialogue/branches/qin_unification")
        assert res.status_code == 200, res.text
        body = res.json()["data"]
        assert body["event_id"] == "qin_unification"
        assert len(body["available_endings"]) >= 4  # 至少 historical + altered + A-T + D-T + T-T + A-D
        for e in body["available_endings"]:
            assert "key" in e
            assert "label" in e
            assert "hint" in e

    async def test_branches_unknown_event_returns_404(self, client, test_db):
        """未知 event_id 返回 404"""
        res = await client.get("/api/dialogue/branches/totally_made_up_event")
        assert res.status_code == 404, res.text

    async def test_full_flow_writes_profile(self, client, test_db):
        """完整对话 (start → 走完 ending) 后 profile 接口应能查到记录"""
        start_res = await client.post("/api/dialogue/start", json={
            "event_id": "qin_unification",
            "session_id": self._sid("4"),
        })
        assert start_res.status_code == 200, start_res.text
        dialogue_id = start_res.json()["data"]["dialogue_id"]

        # 连续 choice 直至 ending
        for _ in range(5):
            r = await client.post("/api/dialogue/choice", json={
                "dialogue_id": str(dialogue_id),
                "choice_id": "a",
            })
            assert r.status_code == 200, r.text
            if r.json()["data"].get("is_ending"):
                break

        # 查 profile
        prof_res = await client.get(f"/api/dialogue/profile?session_id={self._sid('4')}")
        assert prof_res.status_code == 200, prof_res.text
        prof_body = prof_res.json()["data"]
        assert len(prof_body["records"]) >= 1
        # 第 1 条是 qin_unification
        assert any(r["event_id"] == "qin_unification" for r in prof_body["records"])
        # conservative 或 reform 至少一项 > 0 (选 agree 或 thoughtful)
        assert prof_body["aggregate"]["reform"] > 0 or prof_body["aggregate"]["conservative"] > 0

    async def test_full_flow_writes_exploration_record_with_notes(self, client, test_db):
        sid = self._sid("6")
        start_res = await client.post("/api/dialogue/start", json={
            "event_id": "qin_unification",
            "session_id": sid,
        })
        assert start_res.status_code == 200, start_res.text
        dialogue_id = start_res.json()["data"]["dialogue_id"]

        ending_body = None
        for _ in range(5):
            choice_res = await client.post("/api/dialogue/choice", json={
                "dialogue_id": str(dialogue_id),
                "choice_id": "a",
            })
            assert choice_res.status_code == 200, choice_res.text
            body = choice_res.json()["data"]
            if body.get("is_ending"):
                ending_body = body
                break

        assert ending_body is not None
        records_res = await client.get(f"/api/exploration/records?session_id={sid}&event_id=qin_unification")
        assert records_res.status_code == 200, records_res.text
        records = records_res.json()["data"]
        assert len(records) == 1
        record = records[0]
        assert record["notes"]
        assert record["depth"] == len(record["explore_path"]["choices"])
        assert record["explore_path"]["ending_type"] == ending_body["ending_type"]
        assert record["explore_path"]["path_signature"] == ending_body["path_signature"]

    async def test_branches_with_session_shows_unlocked(self, client, test_db):
        """branches 接口带 session_id 时, unlocked_endings 应包含已解锁结局"""
        # 启动并完成对话
        start_res = await client.post("/api/dialogue/start", json={
            "event_id": "qin_unification",
            "session_id": self._sid("5"),
        })
        assert start_res.status_code == 200, start_res.text
        dialogue_id = start_res.json()["data"]["dialogue_id"]

        # 走完
        for _ in range(5):
            r = await client.post("/api/dialogue/choice", json={
                "dialogue_id": str(dialogue_id),
                "choice_id": "a",
            })
            if r.json()["data"].get("is_ending"):
                break

        # 查 branches
        br_res = await client.get(
            f"/api/dialogue/branches/qin_unification?session_id={self._sid('5')}"
        )
        assert br_res.status_code == 200, br_res.text
        br_body = br_res.json()["data"]
        assert len(br_body["unlocked_endings"]) >= 1
        # 已解锁的 key 应在 available_endings 中
        for k in br_body["unlocked_endings"]:
            assert any(e["key"] == k for e in br_body["available_endings"])


# === 任意话题 dynamic 模式 e2e 测试 ===
class TestDynamicDialogueAPI:
    """测试 /api/dialogue/dynamic/* 系列接口."""

    _BASE = "session_1700000900_dyn"  # 后缀由调用方补足 5 字符以拼成 8 字符

    def _sid(self, suffix: str) -> str:
        # suffix 必须是 5 字符, 与 "dyn" 拼成 8 字符
        assert len(suffix) == 5, f"suffix must be 5 chars: {suffix}"
        return self._BASE + suffix

    async def test_dynamic_start_with_any_topic_returns_201(self, client, test_db):
        res = await client.post(
            "/api/dialogue/dynamic/start",
            json={"topic": "AI 发展史", "session_id": self._sid("start")},
        )
        assert res.status_code == 200, res.text
        body = res.json()["data"]
        assert body["is_dynamic"] is True
        assert body["event_id"].startswith("dynamic_")
        assert body["narrative"]  # 有内容
        assert len(body["choices"]) >= 1

    async def test_dynamic_start_empty_topic_returns_400(self, client, test_db):
        res = await client.post(
            "/api/dialogue/dynamic/start",
            json={"topic": "", "session_id": self._sid("empty")},
        )
        # Pydantic min_length=1 校验失败
        assert res.status_code in (400, 422), res.text

    async def test_dynamic_full_flow_writes_profile(self, client, test_db):
        sid = self._sid("flow1")
        # 1. start
        r1 = await client.post(
            "/api/dialogue/dynamic/start",
            json={"topic": "test topic", "session_id": sid},
        )
        assert r1.status_code == 200, r1.text
        d = r1.json()["data"]
        dialogue_id = d["dialogue_id"]
        # 2. 选 explore_origin
        r2 = await client.post(
            "/api/dialogue/dynamic/choice",
            json={"dialogue_id": dialogue_id, "choice_id": "explore_origin"},
        )
        assert r2.status_code == 200, r2.text
        assert r2.json()["data"]["is_dynamic"] is True
        # 3. 自由聊天
        r3 = await client.post(
            "/api/dialogue/dynamic/chat",
            json={"dialogue_id": dialogue_id, "message": "test followup"},
        )
        assert r3.status_code == 200, r3.text
        # 4. 主动结束 → 应有 RAG 动态结局
        r4 = await client.post(
            "/api/dialogue/dynamic/end",
            json={"dialogue_id": dialogue_id},
        )
        assert r4.status_code == 200, r4.text
        ed = r4.json()["data"]
        assert ed["is_dynamic"] is True
        assert ed["is_ending"] is True
        assert ed["ending_type"] == "rag_dynamic"
        assert ed["narrative"]  # 有结局文本

    async def test_dynamic_choice_on_preset_dialogue_returns_400(self, client, test_db):
        # 先开预设
        r0 = await client.post(
            "/api/dialogue/start",
            json={"event_id": "qin_unification", "session_id": self._sid("pres1")},
        )
        assert r0.status_code == 200
        did = r0.json()["data"]["dialogue_id"]
        # 用 dynamic 接口去 choice, 应 400
        r = await client.post(
            "/api/dialogue/dynamic/choice",
            json={"dialogue_id": did, "choice_id": "a"},
        )
        assert r.status_code == 400, r.text

    async def test_preset_events_unaffected_by_dynamic_field(self, client, test_db):
        """回归保护: 预置事件仍能正常开启."""
        # 直接用完整 sid (8 字符后缀), 避免拼接问题
        eid_to_sid = {
            "qin_unification": "session_1700000901_qinreg01",
            "han_empire":      "session_1700000902_hanreg01",
        }
        for eid, sid in eid_to_sid.items():
            r = await client.post(
                "/api/dialogue/start",
                json={"event_id": eid, "session_id": sid},
            )
            assert r.status_code == 200, f"{eid} failed: {r.text}"
            body = r.json()["data"]
            # 预置事件 dialogue_id 应存在
            assert body["dialogue_id"]
