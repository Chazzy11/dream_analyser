from datetime import datetime

from dream_interpreter.database import DreamDatabase
from dream_interpreter.models import DreamAnalysis, DreamRecord


def _make_record(
    user_id: str = "user1",
    upper_downer: float = 0.5,
    static_dynamic: float = 0.5,
    confidence: float = 0.8,
) -> DreamRecord:
    """Create a DreamRecord with sensible defaults for testing."""
    return DreamRecord(
        id="placeholder",
        dream_text="I was flying through golden clouds",
        user_id=user_id,
        analysis=DreamAnalysis(
            upper_downer_score=upper_downer,
            static_dynamic_score=static_dynamic,
            confidence=confidence,
            keywords=["flying"],
        ),
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
    )


class TestDreamDatabase:
    """Test cases for the DreamDatabase class."""

    def setup_method(self):
        """Set up a fresh database for each test."""
        self.db = DreamDatabase()

    # ------------------------------------------------------------------
    # store_dream
    # ------------------------------------------------------------------

    def test_store_dream_returns_string_id(self):
        """store_dream should return a non-empty string ID."""
        dream_id = self.db.store_dream(_make_record())
        assert isinstance(dream_id, str)
        assert len(dream_id) > 0

    def test_store_dream_assigns_id_to_record(self):
        """store_dream should write the generated ID back onto the record."""
        record = _make_record()
        dream_id = self.db.store_dream(record)
        assert record.id == dream_id

    def test_store_dream_returns_unique_ids(self):
        """Each stored dream should receive a distinct UUID."""
        ids = {self.db.store_dream(_make_record()) for _ in range(5)}
        assert len(ids) == 5

    def test_store_dream_indexes_by_user(self):
        """After storing, the dream ID should appear under the correct user."""
        record = _make_record(user_id="alice")
        dream_id = self.db.store_dream(record)
        assert dream_id in self.db.user_dreams["alice"]

    def test_store_dream_accumulates_multiple_dreams_for_same_user(self):
        """Storing two dreams for the same user should produce two entries."""
        self.db.store_dream(_make_record(user_id="bob"))
        self.db.store_dream(_make_record(user_id="bob"))
        assert len(self.db.user_dreams["bob"]) == 2

    def test_store_dream_keeps_users_separate(self):
        """Dreams stored under different user IDs must not bleed into each other."""
        self.db.store_dream(_make_record(user_id="alice"))
        self.db.store_dream(_make_record(user_id="bob"))
        assert len(self.db.user_dreams["alice"]) == 1
        assert len(self.db.user_dreams["bob"]) == 1

    # ------------------------------------------------------------------
    # get_dream
    # ------------------------------------------------------------------

    def test_get_dream_returns_stored_record(self):
        """get_dream should return the exact record that was stored."""
        record = _make_record(user_id="alice")
        dream_id = self.db.store_dream(record)
        fetched = self.db.get_dream(dream_id)
        assert fetched is record

    def test_get_dream_returns_none_for_unknown_id(self):
        """get_dream should return None when the ID does not exist."""
        assert self.db.get_dream("nonexistent-id") is None

    # ------------------------------------------------------------------
    # get_user_dreams
    # ------------------------------------------------------------------

    def test_get_user_dreams_returns_empty_list_for_unknown_user(self):
        """get_user_dreams should return [] when the user has no dreams stored."""
        assert self.db.get_user_dreams("ghost") == []

    def test_get_user_dreams_returns_all_dreams_for_user(self):
        """get_user_dreams should return every dream stored under that user ID."""
        r1 = _make_record(user_id="carol")
        r2 = _make_record(user_id="carol")
        self.db.store_dream(r1)
        self.db.store_dream(r2)
        dreams = self.db.get_user_dreams("carol")
        assert len(dreams) == 2
        assert r1 in dreams
        assert r2 in dreams

    def test_get_user_dreams_excludes_other_users(self):
        """get_user_dreams must not return dreams belonging to a different user."""
        self.db.store_dream(_make_record(user_id="dave"))
        self.db.store_dream(_make_record(user_id="eve"))
        assert len(self.db.get_user_dreams("dave")) == 1

    # ------------------------------------------------------------------
    # get_user_stats — empty / no dreams
    # ------------------------------------------------------------------

    def test_get_user_stats_no_dreams_returns_zero_total(self):
        """get_user_stats should return {total_dreams: 0} for a user with no dreams."""
        stats = self.db.get_user_stats("nobody")
        assert stats == {"total_dreams": 0}

    # ------------------------------------------------------------------
    # get_user_stats — with dreams
    # ------------------------------------------------------------------

    def test_get_user_stats_total_dreams_count(self):
        """total_dreams should equal the number of stored dreams."""
        for _ in range(3):
            self.db.store_dream(_make_record(user_id="frank"))
        assert self.db.get_user_stats("frank")["total_dreams"] == 3

    def test_get_user_stats_average_scores_are_rounded(self):
        """Averages should be rounded to two decimal places."""
        self.db.store_dream(
            _make_record(
                user_id="grace", upper_downer=0.1, static_dynamic=0.2, confidence=0.9
            )
        )
        self.db.store_dream(
            _make_record(
                user_id="grace", upper_downer=0.2, static_dynamic=0.3, confidence=0.7
            )
        )
        stats = self.db.get_user_stats("grace")
        assert stats["average_emotional_score"] == round((0.1 + 0.2) / 2, 2)
        assert stats["average_dynamic_score"] == round((0.2 + 0.3) / 2, 2)
        assert stats["average_confidence"] == round((0.9 + 0.7) / 2, 2)

    def test_get_user_stats_single_dream_averages_equal_that_dream(self):
        """With one dream, each average should equal that dream's score."""
        self.db.store_dream(
            _make_record(
                user_id="henry", upper_downer=0.6, static_dynamic=-0.4, confidence=0.75
            )
        )
        stats = self.db.get_user_stats("henry")
        assert stats["average_emotional_score"] == 0.6
        assert stats["average_dynamic_score"] == -0.4
        assert stats["average_confidence"] == 0.75

    def test_get_user_stats_contains_dominant_quadrant_key(self):
        """get_user_stats result should always include a dominant_quadrant key."""
        self.db.store_dream(_make_record(user_id="ida"))
        stats = self.db.get_user_stats("ida")
        assert "dominant_quadrant" in stats

    # ------------------------------------------------------------------
    # _get_dominant_quadrant (tested indirectly via get_user_stats)
    # ------------------------------------------------------------------

    def test_dominant_quadrant_dynamic_upper(self):
        """Positive upper_downer and positive static_dynamic → Dynamic Upper."""
        self.db.store_dream(
            _make_record(user_id="q1", upper_downer=0.5, static_dynamic=0.5)
        )
        stats = self.db.get_user_stats("q1")
        assert stats["dominant_quadrant"] == "Dynamic Upper (Energetic Positive)"

    def test_dominant_quadrant_static_upper(self):
        """Positive upper_downer and non-positive static_dynamic → Static Upper."""
        self.db.store_dream(
            _make_record(user_id="q2", upper_downer=0.5, static_dynamic=0.0)
        )
        stats = self.db.get_user_stats("q2")
        assert stats["dominant_quadrant"] == "Static Upper (Peaceful Positive)"

    def test_dominant_quadrant_dynamic_downer(self):
        """Non-positive upper_downer and positive static_dynamic → Dynamic Downer."""
        self.db.store_dream(
            _make_record(user_id="q3", upper_downer=-0.5, static_dynamic=0.5)
        )
        stats = self.db.get_user_stats("q3")
        assert stats["dominant_quadrant"] == "Dynamic Downer (Chaotic Negative)"

    def test_dominant_quadrant_static_downer(self):
        """Non-positive upper_downer and non-positive static_dynamic → Static Downer."""
        self.db.store_dream(
            _make_record(user_id="q4", upper_downer=0.0, static_dynamic=0.0)
        )
        stats = self.db.get_user_stats("q4")
        assert stats["dominant_quadrant"] == "Static Downer (Stagnant Negative)"
