# ============================================
# tests/test_state_data.py
#
# Validation tests for config/state_data.py
# Run with: pytest test/test_state_data.py -v
# ============================================

import sys
import os

# Add project root to path so we can import config
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
))

from config.state_data import (
    get_authoritative_sources,
    get_stable_facts,
    get_search_queries,
    get_naics_context,
    STATE_AUTHORITATIVE_SOURCES,
    STATE_STABLE_FACTS,
    NAICS_SECTOR_CONTEXT,
    POLICY_TOPICS
)

# ============================================
# CONSTANTS
# ============================================

ALL_STATES = ["CT", "ME", "MA", "NH", "RI", "VT"]

REQUIRED_STABLE_FIELDS = [
    "state_name",
    "iso_region",
    "market_type",
    "electric_utilities",
    "primary_regulator",
    "energy_office",
    "dominant_industrial_sectors",
    "unique_policy_characteristics"
]

REQUIRED_TOPIC_FIELDS = [
    "topic_id",
    "topic_name",
    "questions",
    "primary_source_key",
    "agent"
]

# ============================================
# TEST 1: Authoritative Sources
# ============================================

def test_all_states_have_authoritative_sources():
    """Every state must have authoritative sources"""
    for state in ALL_STATES:
        sources = get_authoritative_sources(state)
        assert sources, (
            f"No authoritative sources found for {state}"
        )

def test_all_states_have_tier1_sources():
    """Every state must have at least 1 tier1 source"""
    for state in ALL_STATES:
        sources = get_authoritative_sources(state)
        tier1 = sources.get("tier1_sources", [])
        assert len(tier1) > 0, (
            f"No tier1 sources found for {state}"
        )

def test_all_states_have_tier2_sources():
    """Every state must have at least 1 tier2 source"""
    for state in ALL_STATES:
        sources = get_authoritative_sources(state)
        tier2 = sources.get("tier2_sources", [])
        assert len(tier2) > 0, (
            f"No tier2 sources found for {state}"
        )

def test_all_sources_have_required_fields():
    """Every source must have name, url, what_to_find"""
    required = ["name", "url", "what_to_find"]
    for state in ALL_STATES:
        sources = get_authoritative_sources(state)
        all_sources = (
            sources.get("tier1_sources", []) +
            sources.get("tier2_sources", [])
        )
        for source in all_sources:
            for field in required:
                assert field in source, (
                    f"{state} source missing {field}: "
                    f"{source.get('name', 'unknown')}"
                )

def test_unknown_state_returns_empty_sources():
    """Unknown state should return empty dict"""
    result = get_authoritative_sources("XX")
    assert result == {}

# ============================================
# TEST 2: Stable Facts
# ============================================

def test_all_states_have_stable_facts():
    """Every state must have stable facts"""
    for state in ALL_STATES:
        facts = get_stable_facts(state)
        assert facts, (
            f"No stable facts found for {state}"
        )

def test_all_states_have_required_fields():
    """Every state must have all required fields"""
    for state in ALL_STATES:
        facts = get_stable_facts(state)
        for field in REQUIRED_STABLE_FIELDS:
            assert field in facts, (
                f"{state}: Missing field {field}"
            )

def test_all_states_are_iso_ne():
    """All 6 states must be ISO-NE members"""
    for state in ALL_STATES:
        facts = get_stable_facts(state)
        assert facts["iso_region"] == (
            "ISO New England (ISO-NE)"
        ), f"{state}: Wrong ISO region"

def test_all_states_are_rggi_members():
    """All 6 states must be RGGI members"""
    for state in ALL_STATES:
        facts = get_stable_facts(state)
        assert facts["rggi_member"] == True, (
            f"{state}: Should be RGGI member"
        )

def test_vermont_is_regulated_market():
    """Vermont is the only regulated market"""
    vt = get_stable_facts("VT")
    assert vt["market_type"] == "Regulated"

def test_all_others_are_restructured():
    """CT, ME, MA, NH, RI must be restructured"""
    restructured = ["CT", "ME", "MA", "NH", "RI"]
    for state in restructured:
        facts = get_stable_facts(state)
        assert facts["market_type"] == "Restructured", (
            f"{state}: Should be Restructured"
        )

def test_all_states_have_utilities():
    """Every state must have at least 1 utility"""
    for state in ALL_STATES:
        facts = get_stable_facts(state)
        utilities = facts.get("electric_utilities", [])
        assert len(utilities) > 0, (
            f"{state}: No utilities found"
        )

def test_ri_has_single_utility():
    """RI should have exactly 1 utility"""
    facts = get_stable_facts("RI")
    utilities = facts["electric_utilities"]
    assert len(utilities) == 1, (
        "RI should have exactly 1 utility"
    )

def test_ri_utility_correct_name():
    """RI utility should be Rhode Island Energy"""
    facts = get_stable_facts("RI")
    name = facts["electric_utilities"][0]["name"]
    assert name == "Rhode Island Energy", (
        f"RI utility wrong: {name}"
    )

def test_nh_has_efficiency_program():
    """NH must have an efficiency program (NHSaves)"""
    facts = get_stable_facts("NH")
    assert "efficiency_program" in facts, (
        "NH: Missing efficiency_program field"
    )
    assert facts["efficiency_program"]["name"] == (
        "NHSaves"
    ), "NH: Wrong efficiency program name"

def test_ma_energy_office_is_doer():
    """MA energy office must be DOER not MassCEC"""
    facts = get_stable_facts("MA")
    abbreviation = facts["energy_office"]["abbreviation"]
    assert abbreviation == "DOER", (
        f"MA energy office wrong: {abbreviation}"
    )

def test_ma_has_clean_energy_center():
    """MA must also have MassCEC as clean_energy_center"""
    facts = get_stable_facts("MA")
    assert "clean_energy_center" in facts, (
        "MA: Missing clean_energy_center field"
    )
    assert facts["clean_energy_center"][
        "abbreviation"
    ] == "MassCEC"

def test_unknown_state_returns_empty_facts():
    """Unknown state should return empty dict"""
    result = get_stable_facts("XX")
    assert result == {}

def test_case_insensitive_lookup():
    """Lookups should work regardless of case"""
    assert get_stable_facts("nh") == (
        get_stable_facts("NH")
    )
    assert get_stable_facts("ct") == (
        get_stable_facts("CT")
    )

# ============================================
# TEST 3: Search Queries
# ============================================

def test_search_queries_build_for_all_states():
    """Search queries must build for every state"""
    for state in ALL_STATES:
        queries = get_search_queries(
            state, "solar", 100
        )
        assert len(queries) > 0, (
            f"{state}: No search queries returned"
        )

def test_search_queries_have_topic_and_query():
    """Every query must have topic and query fields"""
    for state in ALL_STATES:
        queries = get_search_queries(
            state, "solar", 100
        )
        for q in queries:
            assert "topic" in q, (
                f"{state}: Query missing topic"
            )
            assert "query" in q, (
                f"{state}: Query missing query"
            )

def test_search_queries_contain_state_name():
    """Queries must contain the state name (except federal programs)"""
    for state in ALL_STATES:
        facts = get_stable_facts(state)
        state_name = facts["state_name"]
        queries = get_search_queries(
            state, "solar", 100
        )
        for q in queries:
            if q["topic"] == "federal_programs":
                continue  # federal queries don't need state name
            assert state_name in q["query"], (
                f"{state}: State name missing "
                f"from query: {q['topic']}"
            )

# ============================================
# TEST 4: NAICS Coverage
# ============================================

def test_all_referenced_naics_codes_exist():
    """
    Every NAICS code referenced by a state
    must exist in NAICS_SECTOR_CONTEXT
    """
    for state in ALL_STATES:
        facts = get_stable_facts(state)
        for sector in facts.get(
            "dominant_industrial_sectors", []
        ):
            code = sector["naics"]
            context = get_naics_context(code)
            assert context, (
                f"NAICS {code} referenced by "
                f"{state} but not in "
                f"NAICS_SECTOR_CONTEXT"
            )

def test_naics_entries_have_required_fields():
    """Every NAICS entry must have name and technologies"""
    required = ["name", "relevant_technologies"]
    for code, data in NAICS_SECTOR_CONTEXT.items():
        for field in required:
            assert field in data, (
                f"NAICS {code}: Missing {field}"
            )

def test_naics_unknown_code_returns_empty():
    """Unknown NAICS code should return empty dict"""
    result = get_naics_context("999")
    assert result == {}

# ============================================
# TEST 5: Policy Topics
# ============================================

def test_policy_topics_have_required_fields():
    """Every policy topic must have required fields"""
    for topic in POLICY_TOPICS:
        for field in REQUIRED_TOPIC_FIELDS:
            assert field in topic, (
                f"Topic missing {field}: "
                f"{topic.get('topic_id', 'unknown')}"
            )

def test_policy_topics_have_questions():
    """Every policy topic must have at least 1 question"""
    for topic in POLICY_TOPICS:
        assert len(topic["questions"]) > 0, (
            f"Topic has no questions: "
            f"{topic['topic_id']}"
        )

def test_expected_policy_topics_exist():
    """These 4 core topics must exist"""
    topic_ids = [t["topic_id"] for t in POLICY_TOPICS]
    for expected in [
        "rps",
        "net_metering",
        "interconnection",
        "incentives"
    ]:
        assert expected in topic_ids, (
            f"Missing policy topic: {expected}"
        )