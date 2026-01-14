"""
Tests for the aligned memory type system:
- Working Memory (short-term)
- Episodic Memory (long-term actions)
- Semantic Memory (long-term preferences)
- Procedural Memory (long-term rules)
- Shared Memory (handoffs)
"""

import pytest
from datetime import datetime
from memory.manager import MemoryManager


class TestSemanticMemory:
    """Tests for Semantic Memory (preferences)."""

    def setup_method(self):
        """Setup test fixtures."""
        from shared.db import MongoDB
        mongodb = MongoDB()
        self.db = mongodb.get_database()
        self.memory = MemoryManager(self.db)
        self.user_id = "test-user-semantic"

        # Clean up
        self.db.memory_semantic.delete_many({"user_id": self.user_id})

    def test_record_preference_new(self):
        """Test recording a new preference."""
        pref_id = self.memory.record_preference(
            user_id=self.user_id,
            key="focus_project",
            value="Voice Agent",
            source="explicit",
            confidence=0.9
        )

        assert pref_id is not None

        # Verify stored
        pref = self.memory.get_preference(self.user_id, "focus_project")
        assert pref is not None
        assert pref["value"] == "Voice Agent"
        assert pref["source"] == "explicit"
        assert pref["confidence"] == 0.9
        assert pref["times_used"] == 1

    def test_record_preference_update(self):
        """Test updating an existing preference."""
        # Create initial
        self.memory.record_preference(
            user_id=self.user_id,
            key="focus_project",
            value="AgentOps",
            source="inferred",
            confidence=0.7
        )

        # Update
        self.memory.record_preference(
            user_id=self.user_id,
            key="focus_project",
            value="Voice Agent",
            source="explicit",
            confidence=0.9
        )

        # Verify updated
        pref = self.memory.get_preference(self.user_id, "focus_project")
        assert pref["value"] == "Voice Agent"
        assert pref["confidence"] == 0.9  # Should take higher
        assert pref["times_used"] == 2  # Incremented

    def test_get_preferences_sorted(self):
        """Test preferences are sorted by confidence."""
        self.memory.record_preference(self.user_id, "low_pref", "low", confidence=0.5)
        self.memory.record_preference(self.user_id, "high_pref", "high", confidence=0.95)
        self.memory.record_preference(self.user_id, "mid_pref", "mid", confidence=0.75)

        prefs = self.memory.get_preferences(self.user_id)

        assert len(prefs) == 3
        assert prefs[0]["key"] == "high_pref"
        assert prefs[1]["key"] == "mid_pref"
        assert prefs[2]["key"] == "low_pref"

    def test_get_preferences_min_confidence(self):
        """Test filtering by minimum confidence."""
        self.memory.record_preference(self.user_id, "low_pref", "low", confidence=0.3)
        self.memory.record_preference(self.user_id, "high_pref", "high", confidence=0.9)

        prefs = self.memory.get_preferences(self.user_id, min_confidence=0.5)

        assert len(prefs) == 1
        assert prefs[0]["key"] == "high_pref"

    def test_delete_preference(self):
        """Test deleting a preference."""
        self.memory.record_preference(self.user_id, "to_delete", "value")

        result = self.memory.delete_preference(self.user_id, "to_delete")
        assert result is True

        pref = self.memory.get_preference(self.user_id, "to_delete")
        assert pref is None


class TestProceduralMemory:
    """Tests for Procedural Memory (rules)."""

    def setup_method(self):
        """Setup test fixtures."""
        from shared.db import MongoDB
        mongodb = MongoDB()
        self.db = mongodb.get_database()
        self.memory = MemoryManager(self.db)
        self.user_id = "test-user-procedural"

        # Clean up
        self.db.memory_procedural.delete_many({"user_id": self.user_id})

    def test_record_rule_new(self):
        """Test recording a new rule."""
        rule_id = self.memory.record_rule(
            user_id=self.user_id,
            trigger="done",
            action="complete_current_task",
            source="explicit",
            confidence=0.85
        )

        assert rule_id is not None

        # Verify stored
        rules = self.memory.get_rules(self.user_id)
        assert len(rules) == 1
        assert rules[0]["trigger_pattern"] == "done"
        assert rules[0]["action_type"] == "complete_current_task"

    def test_record_rule_normalizes_trigger(self):
        """Test that triggers are normalized."""
        self.memory.record_rule(self.user_id, "  DONE  ", "complete_current_task")

        rule = self.memory.get_rule_for_trigger(self.user_id, "done")
        assert rule is not None

    def test_record_rule_update(self):
        """Test updating an existing rule."""
        self.memory.record_rule(self.user_id, "done", "stop_current_task")
        self.memory.record_rule(self.user_id, "done", "complete_current_task")

        rules = self.memory.get_rules(self.user_id)
        assert len(rules) == 1  # Should update, not create new
        assert rules[0]["action_type"] == "complete_current_task"
        assert rules[0]["times_used"] == 2

    def test_get_rule_for_trigger(self):
        """Test getting rule by trigger."""
        self.memory.record_rule(self.user_id, "done", "complete_current_task")
        self.memory.record_rule(self.user_id, "next", "start_next_task")

        rule = self.memory.get_rule_for_trigger(self.user_id, "done")
        assert rule is not None
        assert rule["action_type"] == "complete_current_task"

        rule = self.memory.get_rule_for_trigger(self.user_id, "nonexistent")
        assert rule is None

    def test_get_rules_sorted_by_usage(self):
        """Test rules are sorted by times_used."""
        self.memory.record_rule(self.user_id, "rarely", "action1")
        self.memory.record_rule(self.user_id, "often", "action2")

        # Use "often" multiple times
        for _ in range(5):
            self.memory.get_rule_for_trigger(self.user_id, "often")

        rules = self.memory.get_rules(self.user_id)
        assert rules[0]["trigger_pattern"] == "often"
        assert rules[0]["times_used"] > rules[1]["times_used"]

    def test_delete_rule(self):
        """Test deleting a rule."""
        self.memory.record_rule(self.user_id, "to_delete", "action")

        result = self.memory.delete_rule(self.user_id, "to_delete")
        assert result is True

        rule = self.memory.get_rule_for_trigger(self.user_id, "to_delete")
        assert rule is None


class TestMemoryStats:
    """Tests for memory statistics."""

    def setup_method(self):
        """Setup test fixtures."""
        from shared.db import MongoDB
        mongodb = MongoDB()
        self.db = mongodb.get_database()
        self.memory = MemoryManager(self.db)
        self.user_id = "test-user-stats"
        self.session_id = "test-session-stats"

        # Clean up
        self.db.memory_episodic.delete_many({"user_id": self.user_id})
        self.db.memory_semantic.delete_many({"user_id": self.user_id})
        self.db.memory_procedural.delete_many({"user_id": self.user_id})
        self.memory.clear_session(self.session_id)  # Clears in-memory working memory

    def test_memory_stats_by_type(self):
        """Test stats include all memory types."""
        # Add various memory types
        self.memory.update_session_context(self.session_id, {"current_project": "Test"})
        self.memory.record_preference(self.user_id, "pref1", "value1")
        self.memory.record_preference(self.user_id, "pref2", "value2")
        self.memory.record_rule(self.user_id, "trigger1", "action1")
        self.memory.record_action(
            user_id=self.user_id,
            session_id=self.session_id,
            action_type="complete",
            entity_type="task",
            entity={"task_title": "Test task"},
            generate_embedding=False
        )

        stats = self.memory.get_memory_stats(self.session_id, self.user_id)

        assert "by_type" in stats
        by_type = stats["by_type"]

        assert by_type["working_memory"] >= 1
        assert by_type["semantic_memory"] == 2
        assert by_type["procedural_memory"] == 1
        assert by_type["episodic_memory"] >= 1


class TestUserMemoryProfile:
    """Tests for user memory profile."""

    def setup_method(self):
        """Setup test fixtures."""
        from shared.db import MongoDB
        mongodb = MongoDB()
        self.db = mongodb.get_database()
        self.memory = MemoryManager(self.db)
        self.user_id = "test-user-profile"

        # Clean up
        self.db.memory_episodic.delete_many({"user_id": self.user_id})
        self.db.memory_semantic.delete_many({"user_id": self.user_id})
        self.db.memory_procedural.delete_many({"user_id": self.user_id})

    def test_get_user_memory_profile(self):
        """Test getting complete user profile."""
        # Add memory
        self.memory.record_preference(self.user_id, "focus", "Project A")
        self.memory.record_rule(self.user_id, "done", "complete")

        profile = self.memory.get_user_memory_profile(self.user_id)

        assert "preferences" in profile
        assert "rules" in profile
        assert "action_summary" in profile

        assert len(profile["preferences"]) == 1
        assert len(profile["rules"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
