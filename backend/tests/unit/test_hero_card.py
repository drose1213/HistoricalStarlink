# -*- coding: utf-8 -*-
"""英雄卡牌系统单元测试"""
import pytest
import asyncio

from backend.dialogue_engine import (
    resolve_hero_for_topic,
    _fallback_heroes_from_events,
    _call_llm_for_hero_recommendation,
    _build_persona_prompt,
    _get_persona_by_hero_id,
    cache_hero_persona,
    clear_hero_persona_cache,
    start_dynamic_dialogue,
    process_dynamic_choice,
    _slugify_topic,
)


@pytest.mark.unit
class TestFallbackHeroes:
    """测试关键词兜底算法."""

    def test_empty_topic_returns_empty(self):
        result = _fallback_heroes_from_events("")
        assert result == []

    def test_nonexistent_topic_returns_empty(self):
        result = _fallback_heroes_from_events("完全不存在的瞎编xyzabc")
        assert result == []

    def test_known_topic_returns_candidates(self):
        """'秦' 应该匹配到秦统一六国等事件."""
        result = _fallback_heroes_from_events("秦")
        assert len(result) > 0
        all_names = " ".join(r.get("name", "") for r in result)
        assert "秦" in all_names or "嬴政" in all_names or "始" in all_names

    def test_max_count_respected(self):
        result = _fallback_heroes_from_events("改革", max_count=2)
        assert len(result) <= 2


@pytest.mark.unit
class TestLLMRecommender:
    """测试 LLM 推荐 (无 API Key 场景)."""

    def test_no_api_key_returns_empty(self):
        """无 MINIMAX_API_KEY 时应返回空列表."""
        import os
        old_key = os.environ.pop("MINIMAX_API_KEY", None)
        try:
            result = asyncio.run(_call_llm_for_hero_recommendation("赤壁之战"))
            assert result == []
        finally:
            if old_key:
                os.environ["MINIMAX_API_KEY"] = old_key

    def test_resolve_hero_falls_back_to_events(self):
        """无 API Key 时, resolve_hero_for_topic 应回退到 events_data."""
        import os
        old_key = os.environ.pop("MINIMAX_API_KEY", None)
        try:
            result = asyncio.run(resolve_hero_for_topic("秦"))
            assert result["source"] == "fallback"
            assert len(result["heroes"]) > 0
            for h in result["heroes"]:
                assert "hero_id" in h
                assert "name" in h
                assert "role" in h
                assert "era" in h
        finally:
            if old_key:
                os.environ["MINIMAX_API_KEY"] = old_key

    def test_resolve_hero_empty_topic(self):
        result = asyncio.run(resolve_hero_for_topic(""))
        assert result == {"heroes": [], "source": "empty"}


@pytest.mark.unit
class TestPersonaPrompt:
    """测试 persona prompt 构造."""

    def test_none_persona_returns_generic(self):
        """None persona 应使用通用 prompt (向后兼容)."""
        prompt = _build_persona_prompt(None)
        assert "历史知识助手" in prompt

    def test_valid_persona_includes_name(self):
        persona = {
            "name": "诸葛亮",
            "role": "蜀汉丞相",
            "era": "三国 (181-234)",
            "speaking_pattern": "亮",
            "style_hint": "古朴典雅",
            "description": "三顾茅庐",
        }
        prompt = _build_persona_prompt(persona, "测试上下文")
        assert "诸葛亮" in prompt
        assert "亮" in prompt
        assert "蜀汉丞相" in prompt
        assert "测试上下文" in prompt

    def test_empty_context_fallback(self):
        persona = {"name": "李白", "role": "诗人", "speaking_pattern": "某"}
        prompt = _build_persona_prompt(persona, "")
        assert "李白" in prompt
        assert "暂无参考资料" in prompt


@pytest.mark.unit
class TestPersonaCache:
    """测试 persona 缓存."""

    def setup_method(self):
        clear_hero_persona_cache()

    def teardown_method(self):
        clear_hero_persona_cache()

    def test_cache_and_get(self):
        persona = {"hero_id": "test_hero", "name": "测试人物", "role": "测试"}
        cache_hero_persona(persona)
        cached = _get_persona_by_hero_id("test_hero")
        assert cached == persona

    def test_get_nonexistent_returns_none(self):
        result = _get_persona_by_hero_id("nonexistent")
        assert result is None

    def test_get_empty_hero_id(self):
        result = _get_persona_by_hero_id("")
        assert result is None


@pytest.mark.unit
class TestStartDynamicWithHero:
    """测试 start_dynamic_dialogue 接受 hero_id."""

    def setup_method(self):
        clear_hero_persona_cache()

    def teardown_method(self):
        clear_hero_persona_cache()

    def test_start_without_hero_id_uses_default_npc(self):
        """无 hero_id 时, 使用默认'时空对话机'."""
        result = asyncio.run(start_dynamic_dialogue("丝绸之路"))
        assert result["npc_name"] == "时空对话机"
        assert "hero" not in result

    def test_start_with_hero_id_uses_persona(self):
        """有 hero_id 时, 使用 persona 的 NPC 信息."""
        persona = {
            "hero_id": "hero_zhugeliang",
            "name": "诸葛亮",
            "role": "蜀汉丞相",
            "era": "三国 (181-234)",
            "greeting": "在下亮, 阁下有何指教?",
            "speaking_pattern": "亮",
            "style_hint": "古朴典雅",
            "description": "三顾茅庐",
        }
        cache_hero_persona(persona)
        result = asyncio.run(start_dynamic_dialogue("赤壁之战", hero_id="hero_zhugeliang"))
        assert result["npc_name"] == "诸葛亮"
        assert result["npc_role"] == "蜀汉丞相"
        assert "hero" in result
        assert result["hero"]["hero_id"] == "hero_zhugeliang"

    def test_start_with_invalid_hero_id_falls_back(self):
        """无效的 hero_id 应回退到默认 NPC (不抛异常)."""
        result = asyncio.run(start_dynamic_dialogue("丝绸之路", hero_id="invalid_hero"))
        assert result["npc_name"] == "时空对话机"


@pytest.mark.unit
class TestProcessDynamicWithPersona:
    """测试 process_dynamic_* 透传 npc_persona."""

    def test_process_choice_accepts_persona_param(self):
        """process_dynamic_choice 应接受 npc_persona 参数 (不报错)."""
        persona = {"name": "测试", "role": "r", "speaking_pattern": "某"}
        result = asyncio.run(
            process_dynamic_choice("topic", "explore_origin", [], npc_persona=persona)
        )
        assert "mood" in result

    def test_process_choice_backward_compatible(self):
        """不传 persona 时行为不变."""
        result = asyncio.run(
            process_dynamic_choice("topic", "explore_origin", [])
        )
        assert "mood" in result


@pytest.mark.unit
class TestSlugifyTopic:
    """测试 _slugify_topic 仍正常工作."""

    def test_chinese_topic(self):
        result = _slugify_topic("赤壁之战")
        assert len(result) > 0

    def test_empty_topic(self):
        result = _slugify_topic("")
        assert result == "unknown"
