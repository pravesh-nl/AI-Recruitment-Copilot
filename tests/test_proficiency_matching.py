"""
Regression tests for proficiency comparison logic.

Tests the centralized meets_proficiency() helper and
calculate_level_score() to ensure the ordered-rank rule is
applied consistently and correctly everywhere.

Business Rule:
  candidate_rank >= required_rank  ->  fulfilled (True / score 1.0)
  candidate_rank <  required_rank  ->  gap      (False / score < 1.0)
  unknown / None on either side    ->  False / score 0.0
"""

import sys
import os

# Allow import from the project root without installing the package.
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

import pytest

from app.services.matching import (
    PROFICIENCY_RANK,
    meets_proficiency,
    calculate_level_score,
)


# ============================================================
# PROFICIENCY_RANK sanity checks
# ============================================================

class TestProficiencyRank:
    def test_basic_rank(self):
        assert PROFICIENCY_RANK["basic"] == 1

    def test_beginner_rank(self):
        assert PROFICIENCY_RANK["beginner"] == 1

    def test_intermediate_rank(self):
        assert PROFICIENCY_RANK["intermediate"] == 2

    def test_advanced_rank(self):
        assert PROFICIENCY_RANK["advanced"] == 3

    def test_expert_rank(self):
        # Expert is treated the same as Advanced.
        assert PROFICIENCY_RANK["expert"] == 3

    def test_ordering(self):
        assert (
            PROFICIENCY_RANK["basic"]
            < PROFICIENCY_RANK["intermediate"]
            < PROFICIENCY_RANK["advanced"]
        )


# ============================================================
# meets_proficiency -- all 9 core combinations
# ============================================================

class TestMeetsProficiencyCoreCombinations:

    # ---- Required: Basic ----

    def test_basic_required_basic_candidate(self):
        assert meets_proficiency("Basic", "Basic") is True

    def test_basic_required_intermediate_candidate(self):
        assert meets_proficiency("Intermediate", "Basic") is True

    def test_basic_required_advanced_candidate(self):
        assert meets_proficiency("Advanced", "Basic") is True

    # ---- Required: Intermediate ----

    def test_intermediate_required_basic_candidate(self):
        assert meets_proficiency("Basic", "Intermediate") is False

    def test_intermediate_required_intermediate_candidate(self):
        assert meets_proficiency("Intermediate", "Intermediate") is True

    def test_intermediate_required_advanced_candidate(self):
        assert meets_proficiency("Advanced", "Intermediate") is True

    # ---- Required: Advanced ----

    def test_advanced_required_basic_candidate(self):
        assert meets_proficiency("Basic", "Advanced") is False

    def test_advanced_required_intermediate_candidate(self):
        assert meets_proficiency("Intermediate", "Advanced") is False

    def test_advanced_required_advanced_candidate(self):
        assert meets_proficiency("Advanced", "Advanced") is True


# ============================================================
# meets_proficiency -- Expert level
# ============================================================

class TestMeetsProficiencyExpert:

    def test_expert_satisfies_advanced(self):
        assert meets_proficiency("Expert", "Advanced") is True

    def test_expert_satisfies_intermediate(self):
        assert meets_proficiency("Expert", "Intermediate") is True

    def test_expert_satisfies_basic(self):
        assert meets_proficiency("Expert", "Basic") is True

    def test_advanced_satisfies_expert_requirement(self):
        assert meets_proficiency("Advanced", "Expert") is True

    def test_intermediate_does_not_satisfy_expert(self):
        assert meets_proficiency("Intermediate", "Expert") is False

    def test_basic_does_not_satisfy_expert(self):
        assert meets_proficiency("Basic", "Expert") is False


# ============================================================
# meets_proficiency -- missing / null / unknown
# ============================================================

class TestMeetsProficiencyEdgeCases:

    def test_none_candidate_level_returns_false(self):
        assert meets_proficiency(None, "Basic") is False

    def test_none_candidate_level_intermediate_required(self):
        assert meets_proficiency(None, "Intermediate") is False

    def test_empty_string_candidate_level_returns_false(self):
        assert meets_proficiency("", "Basic") is False

    def test_unknown_candidate_level_returns_false(self):
        assert meets_proficiency("novice", "Basic") is False

    def test_unknown_required_level_returns_false(self):
        assert meets_proficiency("Advanced", "mastery") is False

    def test_both_none_returns_false(self):
        assert meets_proficiency(None, None) is False

    def test_both_unknown_returns_false(self):
        assert meets_proficiency("guru", "mastery") is False


# ============================================================
# meets_proficiency -- case-insensitivity & whitespace
# ============================================================

class TestMeetsProficiencyCaseAndWhitespace:

    def test_uppercase_basic(self):
        assert meets_proficiency("BASIC", "BASIC") is True

    def test_mixed_case_basic(self):
        assert meets_proficiency("Basic", "basic") is True

    def test_padded_basic(self):
        assert meets_proficiency(" BASIC ", "basic") is True

    def test_uppercase_intermediate(self):
        assert meets_proficiency("INTERMEDIATE", "intermediate") is True

    def test_padded_intermediate_candidate(self):
        assert meets_proficiency("  intermediate  ", "Basic") is True

    def test_uppercase_advanced(self):
        assert meets_proficiency("ADVANCED", "Advanced") is True

    def test_padded_advanced(self):
        assert meets_proficiency("  Advanced  ", "  basic  ") is True

    def test_advanced_candidate_basic_requirement_padded(self):
        assert meets_proficiency(" Advanced ", " Basic ") is True

    def test_intermediate_candidate_basic_requirement_padded(self):
        assert meets_proficiency("  Intermediate  ", "  Basic  ") is True


# ============================================================
# meets_proficiency -- Beginner alias
# ============================================================

class TestMeetsProficiencyBeginner:

    def test_beginner_satisfies_basic(self):
        assert meets_proficiency("beginner", "basic") is True

    def test_beginner_does_not_satisfy_intermediate(self):
        assert meets_proficiency("beginner", "intermediate") is False

    def test_beginner_does_not_satisfy_advanced(self):
        assert meets_proficiency("beginner", "advanced") is False


# ============================================================
# calculate_level_score -- numeric scores
# ============================================================

class TestCalculateLevelScore:

    def test_basic_equals_basic(self):
        assert calculate_level_score("Basic", "Basic") == pytest.approx(1.0)

    def test_intermediate_equals_intermediate(self):
        assert calculate_level_score("Intermediate", "Intermediate") == pytest.approx(1.0)

    def test_advanced_equals_advanced(self):
        assert calculate_level_score("Advanced", "Advanced") == pytest.approx(1.0)

    def test_intermediate_exceeds_basic(self):
        assert calculate_level_score("Intermediate", "Basic") == pytest.approx(1.0)

    def test_advanced_exceeds_basic(self):
        assert calculate_level_score("Advanced", "Basic") == pytest.approx(1.0)

    def test_advanced_exceeds_intermediate(self):
        assert calculate_level_score("Advanced", "Intermediate") == pytest.approx(1.0)

    def test_expert_exceeds_advanced(self):
        assert calculate_level_score("Expert", "Advanced") == pytest.approx(1.0)

    def test_basic_below_intermediate_is_partial(self):
        score = calculate_level_score("Basic", "Intermediate")
        assert 0.0 < score < 1.0, f"Expected partial credit, got {score}"

    def test_basic_below_advanced_is_partial(self):
        score = calculate_level_score("Basic", "Advanced")
        assert 0.0 < score < 1.0

    def test_intermediate_below_advanced_is_partial(self):
        score = calculate_level_score("Intermediate", "Advanced")
        assert 0.0 < score < 1.0

    def test_unknown_candidate_level_returns_zero(self):
        assert calculate_level_score("novice", "Basic") == pytest.approx(0.0)

    def test_none_candidate_level_returns_zero(self):
        assert calculate_level_score(None, "Basic") == pytest.approx(0.0)

    def test_empty_candidate_level_returns_zero(self):
        assert calculate_level_score("", "Basic") == pytest.approx(0.0)

    def test_case_insensitive_scoring(self):
        s1 = calculate_level_score("advanced", "basic")
        s2 = calculate_level_score("ADVANCED", "BASIC")
        assert s1 == pytest.approx(s2) == pytest.approx(1.0)

    def test_whitespace_normalised_scoring(self):
        assert calculate_level_score(" Advanced ", " Basic ") == pytest.approx(1.0)


# ============================================================
# Integration: original bug regression
# ============================================================

class TestReportedBug:
    """Regression for: Advanced candidate + Basic requirement -> must be FULFILLED."""

    def test_advanced_candidate_basic_requirement_is_fulfilled(self):
        assert meets_proficiency("Advanced", "Basic") is True, (
            "BUG REGRESSION: Advanced candidate with Basic requirement "
            "must be fulfilled, not a gap."
        )

    def test_intermediate_candidate_basic_requirement_is_fulfilled(self):
        assert meets_proficiency("Intermediate", "Basic") is True, (
            "BUG REGRESSION: Intermediate candidate with Basic requirement "
            "must be fulfilled."
        )

    def test_basic_candidate_intermediate_requirement_is_gap(self):
        assert meets_proficiency("Basic", "Intermediate") is False

    def test_basic_candidate_advanced_requirement_is_gap(self):
        assert meets_proficiency("Basic", "Advanced") is False

    def test_intermediate_candidate_advanced_requirement_is_gap(self):
        assert meets_proficiency("Intermediate", "Advanced") is False
