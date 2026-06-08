# -*- coding: utf-8 -*-
"""对话引擎单元测试"""
import pytest
from backend.dialogue_engine import (
    generate_opening,
    process_choice,
    process_free_text,
    process_post_ending,
    calculate_timeline_branches,
    get_available_events,
    get_script,
    DIALOGUE_SCRIPTS,
    build_dynamic_event_id,
    start_dynamic_dialogue,
    process_dynamic_choice,
    process_dynamic_free_text,
    _build_dynamic_ending,
    _keyword_fallback_text,
)


@pytest.mark.unit
class TestDialogueEngine:

    def test_dialogue_scripts_not_empty(self):
        assert len(DIALOGUE_SCRIPTS) > 0

    def test_each_script_has_required_fields(self):
        for sid, script in DIALOGUE_SCRIPTS.items():
            assert "title" in script or "npc_name" in script, f"剧本 {sid} 缺必要字段"
            assert "rounds" in script or "opening" in script, f"剧本 {sid} 缺 rounds/opening"

    def test_generate_opening_known_event(self):
        result = generate_opening("qin_unification")
        assert result is not None
        assert "narrative" in result
        assert "choices" in result
        assert len(result["choices"]) > 0

    def test_generate_opening_unknown_event(self):
        result = generate_opening("nonexistent_event_xyz")
        assert result is None

    def test_get_script_returns_dict(self):
        script = get_script("qin_unification")
        assert script is not None
        assert "npc_name" in script

    def test_get_script_unknown_returns_none(self):
        assert get_script("xxx") is None

    def test_get_available_events_list(self):
        events = get_available_events()
        assert isinstance(events, list)
        assert len(events) > 0
        for ev in events:
            assert "event_id" in ev
            assert "npc_name" in ev

    def test_process_choice_valid(self):
        result = process_choice("qin_unification", "a", current_round=1, choices_made=[])
        assert result is not None
        assert "narrative" in result

    def test_process_choice_invalid_event(self):
        result = process_choice("nonexistent_xyz", "a", current_round=1, choices_made=[])
        assert result is None or "narrative" not in result

    def test_process_free_text_returns_response(self):
        result = process_free_text(
            "qin_unification",
            "我来自未来",
            current_round=1,
            choices_made=[]
        )
        assert "narrative" in result

    def test_process_post_ending_returns_response(self):
        result = process_post_ending("qin_unification", "感谢陛下的教诲")
        assert "narrative" in result

    def test_calculate_timeline_branches_empty(self):
        result = calculate_timeline_branches([])
        assert isinstance(result, list)

    def test_calculate_timeline_branches_with_data(self):
        choices = [
            {"round": 1, "choice_id": "a", "timeline_change": True, "consequence": "分支A"},
            {"round": 2, "choice_id": "b", "mood": "thoughtful", "consequence": "分支B"},
            {"round": 3, "choice_id": "c"},  # 不触发分支
        ]
        result = calculate_timeline_branches(choices)
        assert isinstance(result, list)
        assert len(result) == 2
        # 两个分支应包含 consequence
        for branch in result:
            assert "branch_point" in branch
            assert "altered" in branch

    # ===== 分支结局 + 4 维画像 增强测试 (Task 5) =====

    def test_compute_path_signature_empty(self):
        from backend.dialogue_engine import compute_path_signature
        assert compute_path_signature([]) == ""
        assert compute_path_signature(None) == ""

    def test_compute_path_signature_stable(self):
        from backend.dialogue_engine import compute_path_signature
        choices = [
            {"mood": "agree"},
            {"mood": "thoughtful"},
            {"mood": "disagree"},
        ]
        sig1 = compute_path_signature(choices)
        sig2 = compute_path_signature(choices)
        assert sig1 == sig2 == "A-T-D"

    def test_compute_dimension_scores_cumulative(self):
        from backend.dialogue_engine import compute_dimension_scores
        # 两次 thoughtful → reform=20
        scores = compute_dimension_scores([{"mood": "thoughtful"}, {"mood": "thoughtful"}])
        assert scores["reform"] == 20
        assert scores["conservative"] == 0
        assert scores["empathy"] == 0
        assert scores["radicalism"] == 0

        # 加入含"百姓"的 free_text → empathy +8
        scores2 = compute_dimension_scores(
            [{"mood": "agree"}],
            free_texts=["陛下应以百姓为重"]
        )
        assert scores2["empathy"] == 8
        assert scores2["conservative"] == 10

    def test_build_ending_matches_preset(self):
        """_build_ending 命中预设 ending key 时 outcome_summary 等于该 key."""
        from backend.dialogue_engine import _build_ending
        script = get_script("qin_unification")
        choices = [
            {"round": 1, "mood": "agree", "choice_id": "a", "choice_text": "x", "consequence": "y"},
            {"round": 2, "mood": "thoughtful", "choice_id": "a", "choice_text": "x", "consequence": "y"},
        ]
        ending = _build_ending(script, choices)
        assert ending["ending_type"] == "A-T"
        assert ending["is_ending"] is True
        assert "path_signature" in ending
        assert ending["path_signature"] == "A-T"
        assert ending["partial_match"] is False

    def test_build_ending_rag_fallback(self, monkeypatch):
        """_build_ending 未命中预设时走 RAG 兜底 (mock)."""
        from backend.dialogue_engine import _build_ending
        # 构造一个只有 historical 的剧本, 强制走 RAG
        fake_script = {
            "npc_name": "测试NPC",
            "endings": {"historical": "历史定论文本"},
        }
        # monkeypatch rag_engine.full_rag_query
        from backend import dialogue_engine as de

        def fake_full(query, top_k=5, **kwargs):
            return {"answer": "RAG 生成的兜底结局, 长度可控", "sources": []}

        # 直接 stub _rag_fallback_ending_sync
        monkeypatch.setattr(de, "_rag_fallback_ending_sync", lambda *a, **kw: "RAG 生成的兜底结局, 长度可控")
        choices = [{"mood": "thoughtful"}]
        ending = _build_ending(fake_script, choices)
        assert ending["ending_type"] == "rag_fallback"
        assert "RAG" in ending["narrative"]

    def test_build_ending_historical_fallback(self):
        """_build_ending 无预设 + RAG 失败时回退 historical."""
        from backend.dialogue_engine import _build_ending
        fake_script = {
            "npc_name": "测试NPC",
            "endings": {"historical": "最终历史定论"},
        }
        # choices 产生 'D-D' 签名, 但剧本里没有
        choices = [{"mood": "disagree"}, {"mood": "disagree"}]
        ending = _build_ending(fake_script, choices)
        # RAG 在无 API key 时返回 None, 应回退到 historical
        assert ending["ending_type"] in ("historical", "rag_fallback")
        if ending["ending_type"] == "historical":
            assert "最终历史定论" in ending["narrative"]

    def test_predict_endings_returns_known_keys(self):
        from backend.dialogue_engine import predict_endings
        script = get_script("qin_unification")
        # path_sig="A-T" 在 qin 剧本中, 应返回 ["A-T"]
        result = predict_endings(script, "A-T", top_n=2)
        assert "A-T" in result
        # 不存在签名 → 返回空 (因为前缀匹配不到)
        result2 = predict_endings(script, "X-X", top_n=2)
        assert result2 == []


# === ���⻰�� dynamic ģʽ ��Ԫ���� ===
class TestDynamicDialogue:
    """���⻰�� dynamic �Ի�������� (������ DB, RAG ʧ��ʱ�߹ؼ��� fallback)."""

    def test_build_dynamic_event_id_handles_chinese(self):
        eid = build_dynamic_event_id("AI development")
        assert eid.startswith("dynamic_")
        assert "ai" in eid.lower()  # ascii part preserved

    def test_build_dynamic_event_id_empty_fallback(self):
        eid = build_dynamic_event_id("")
        assert eid == "dynamic_unknown"

    @pytest.mark.asyncio
    async def test_start_dynamic_dialogue_returns_opening(self, monkeypatch):
        """mock RAG ʧ��, �߹ؼ��� fallback, ���ܷ������� opening."""
        # ǿ�� RAG ʧ��
        async def _fake_rag(*a, **kw):
            return {"answer": ""}
        monkeypatch.setattr("backend.rag_engine.full_rag_query", _fake_rag, raising=False)
        result = await start_dynamic_dialogue("test topic")
        assert result["is_dynamic"] is True
        assert result["event_id"].startswith("dynamic_")
        # npc_name should be present (any value, just check key)
        assert result.get("npc_name")
        assert result["narrative"]  # 必有内容 (RAG 失败时由关键词 fallback 拼装)
        assert len(result["choices"]) >= 1

    @pytest.mark.asyncio
    async def test_start_dynamic_dialogue_rag_failure_falls_back(self, monkeypatch):
        """RAG ���쳣ʱ��Ӧ��, �߹ؼ��� fallback."""
        async def _boom(*a, **kw):
            raise RuntimeError("RAG broken")
        monkeypatch.setattr("backend.rag_engine.full_rag_query", _boom, raising=False)
        result = await start_dynamic_dialogue("̫��̽��")
        assert result["is_dynamic"] is True
        assert result["narrative"]  # �����ı��ǿ�

    @pytest.mark.asyncio
    async def test_start_dynamic_dialogue_empty_topic_raises(self):
        with pytest.raises(ValueError):
            await start_dynamic_dialogue("")

    @pytest.mark.asyncio
    async def test_process_dynamic_choice_accumulates_path(self, monkeypatch):
        """����ѡ��Ӧ�ۼ� path_signature / cumulative_impact."""
        async def _fake_rag(*a, **kw):
            return {"answer": "ʱ�նԻ����Ļ�Ӧ��"}
        monkeypatch.setattr("backend.rag_engine.full_rag_query", _fake_rag, raising=False)
        r1 = await process_dynamic_choice("�����䷨", "explore_origin", choices_made=[])
        assert r1["is_ending"] is False
        assert r1["path_signature"] == "T"  # explore_origin �� thoughtful
        r2 = await process_dynamic_choice("�����䷨", "ask_impact", choices_made=[{
            "round": 1, "choice_id": "explore_origin", "mood": "thoughtful", "choice_text": "��Դ"
        }])
        assert r2["path_signature"] == "T-T"
        assert r2["cumulative_impact"]["reform"] >= 20  # ���� thoughtful

    @pytest.mark.asyncio
    async def test_process_dynamic_choice_invalid_id_safe(self, monkeypatch):
        async def _fake_rag(*a, **kw):
            return {"answer": "ok"}
        monkeypatch.setattr("backend.rag_engine.full_rag_query", _fake_rag, raising=False)
        r = await process_dynamic_choice("����", "nonexistent_choice", choices_made=[])
        assert r["narrative"]  # ����, ��Ĭ�ϻ�Ӧ
        assert r["is_ending"] is False

    @pytest.mark.asyncio
    async def test_process_dynamic_free_text_returns_response(self, monkeypatch):
        async def _fake_rag(*a, **kw):
            return {"answer": "���ڡ�...���Ļ�Ӧ"}
        monkeypatch.setattr("backend.rag_engine.full_rag_query", _fake_rag, raising=False)
        r = await process_dynamic_free_text("����", "����ʲô���ף�", choices_made=[])
        assert r["narrative"]
        assert r["is_ending"] is False
        assert "cumulative_impact" in r

    @pytest.mark.asyncio
    async def test_build_dynamic_ending_truncates_to_280(self, monkeypatch):
        """���Ӧ���ضϵ� 280 ������."""
        async def _fake_rag(*a, **kw):
            return {"answer": "x" * 1000}  # ��������
        monkeypatch.setattr("backend.rag_engine.full_rag_query", _fake_rag, raising=False)
        r = await _build_dynamic_ending("���⻰��", choices_made=[{
            "round": 1, "mood": "thoughtful"
        }])
        assert r["is_ending"] is True
        assert r["ending_type"] == "rag_dynamic"
        assert len(r["narrative"]) <= 280

    @pytest.mark.asyncio
    async def test_build_dynamic_ending_rag_failure_safe(self, monkeypatch):
        """RAG ��ȫʧ��ʱӦ���ܸ������׽��, ���� 500."""
        async def _boom(*a, **kw):
            raise RuntimeError("RAG down")
        monkeypatch.setattr("backend.rag_engine.full_rag_query", _boom, raising=False)
        r = await _build_dynamic_ending("̫��", choices_made=[])
        assert r["narrative"]
        assert r["is_ending"] is True

    def test_keyword_fallback_text_returns_nonempty(self):
        """_keyword_fallback_text ���� query ����ʱҲ���طǿ��ı�."""
        text = _keyword_fallback_text("����", top_k=3, max_chars=500)
        assert text
        assert len(text) <= 500
