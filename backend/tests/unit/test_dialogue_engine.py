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
