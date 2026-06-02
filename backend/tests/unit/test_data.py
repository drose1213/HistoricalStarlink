"""事件种子数据单元测试"""
import pytest
from backend.data.events_data import events_data


@pytest.mark.unit
class TestEventsSeedData:
    """验证事件种子数据完整性"""

    def test_events_list_not_empty(self):
        assert len(events_data) > 0, "事件种子数据不能为空"

    def test_events_count_above_threshold(self):
        """至少有 30+ 个事件，保证产品体验"""
        assert len(events_data) >= 30, f"事件数量过少：{len(events_data)}"

    def test_each_event_has_required_fields(self):
        required = {"id", "name", "year", "region", "importance", "description"}
        for ev in events_data:
            for field in required:
                assert field in ev, f"事件 {ev.get('id', '?')} 缺少字段 {field}"

    def test_event_id_unique(self):
        ids = [ev["id"] for ev in events_data]
        assert len(ids) == len(set(ids)), f"事件 id 有重复: {ids}"

    def test_event_region_valid(self):
        for ev in events_data:
            assert ev["region"] in ("china", "foreign"), \
                f"事件 {ev['id']} region 必须是 china/foreign，得到 {ev['region']}"

    def test_event_importance_range(self):
        for ev in events_data:
            assert 1 <= ev["importance"] <= 10, \
                f"事件 {ev['id']} importance 越界: {ev['importance']}"

    def test_event_description_length(self):
        """描述至少 50 字，保证内容质量"""
        for ev in events_data:
            assert len(ev.get("description", "")) >= 50, \
                f"事件 {ev['id']} 描述过短: {len(ev['description'])}"

    def test_china_and_foreign_both_present(self):
        regions = {ev["region"] for ev in events_data}
        assert "china" in regions, "缺少东方事件"
        assert "foreign" in regions, "缺少西方事件"

    def test_causes_and_consequences_list_format(self):
        for ev in events_data:
            assert isinstance(ev.get("causes", []), list), \
                f"事件 {ev['id']} causes 应为列表"
            assert isinstance(ev.get("consequences", []), list), \
                f"事件 {ev['id']} consequences 应为列表"
            assert len(ev.get("causes", [])) >= 2, \
                f"事件 {ev['id']} 至少 2 个原因"
            assert len(ev.get("consequences", [])) >= 2, \
                f"事件 {ev['id']} 至少 2 个影响"

    def test_tags_and_figures_format(self):
        for ev in events_data:
            assert isinstance(ev.get("tags", []), list)
            assert isinstance(ev.get("figures", []), list)

    def test_year_range_reasonable(self):
        """历史事件年份合理范围：-3000 ~ 2100"""
        for ev in events_data:
            assert -3000 <= ev["year"] <= 2100, \
                f"事件 {ev['id']} 年份越界: {ev['year']}"
