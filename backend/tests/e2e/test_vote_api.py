"""Vote API behavior tests."""
import pytest


@pytest.mark.e2e
class TestVoteAPI:
    async def test_star_vote_counts_as_favorite_and_returns_current_vote(self, client, test_db):
        payload = {
            "event_id": "qin_unification",
            "event_name": "Qin unification",
            "session_id": "session_vote_001",
            "vote_type": 2,
        }
        create_res = await client.post("/api/vote", json=payload)
        assert create_res.status_code == 200, create_res.text
        created = create_res.json()["data"]
        assert created["favorite_count"] == 1
        assert created["my_vote"] == 2

        stats_res = await client.get(
            "/api/vote/stats/qin_unification?session_id=session_vote_001"
        )
        assert stats_res.status_code == 200, stats_res.text
        stats = stats_res.json()["data"]
        assert stats["favorite_count"] == 1
        assert stats["star_count"] == 1
        assert stats["my_vote"] == 2
