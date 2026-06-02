"""对话 API 黑盒测试"""
import pytest


@pytest.mark.e2e
class TestDialogueAPI:
    """测试 /api/dialogue 系列接口"""

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
