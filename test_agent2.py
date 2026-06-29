"""
tests/test_agent2.py
=============================================
Tests each Agent 2 LangGraph node individually.

Run this to verify each piece works before
running the full agent or connecting to
the orchestrator.

Follows same pattern as test_nodes.py for Agent 1.

Usage:
    python tests/test_agent2.py

Author: ENSITE Project, UNH
Date: June 2026
"""

# ============================================
# SECTION 1: PATH SETUP
# ============================================
# Add project root to Python path so imports
# work correctly when running from tests/ folder

import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# ============================================
# SECTION 2: IMPORTS
# ============================================
import json
import logging
from datetime import datetime

from agents.agent2_policy import (
    node_gather_sources,
    node_llm_research,
    node_format_report,
    node_handle_error,
    run_agent2,
    get_source_freshness_flag,
    POLICY_SOURCES
)
from config.state_data import (
    get_authoritative_sources,
    get_stable_facts,
    get_search_queries,
    get_naics_context,
    STATE_REGULATORY_INFO
)
from config.settings import NEW_ENGLAND_STATES

# Suppress verbose logging for cleaner test output
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ============================================
# SECTION 3: BLANK STATE TEMPLATE
# ============================================

def blank_state(
    facility_state: str = "NH",
    technology: str = "Solar PV",
    system_size_kw: float = 250.0,
    naics_code: str = "332",
    utility: str = "Eversource Energy",
    facility_type: str = "Private Industrial"
) -> dict:
    """
    Returns a fresh PolicyAgentState for testing.

    Args:
        facility_state: Two-letter state code
        technology:     Energy technology
        system_size_kw: System size in kW
        naics_code:     NAICS code
        utility:        Utility name
        facility_type:  Facility ownership type

    Returns:
        dict matching PolicyAgentState TypedDict
    """
    return {
        # Inputs
        "facility_state": facility_state,
        "technology": technology,
        "system_size_kw": system_size_kw,
        "naics_code": naics_code,
        "utility": utility,
        "facility_type": facility_type,

        # Node 1 outputs
        "authoritative_sources": None,
        "stable_facts": None,
        "search_queries": None,
        "naics_context": None,
        "source_freshness": None,

        # Node 2 outputs
        "rps_findings": None,
        "net_metering_findings": None,
        "interconnection_findings": None,
        "incentive_findings": None,
        "raw_llm_research": None,

        # Node 3 outputs
        "final_report": None,

        # Error handling
        "error": None,
        "error_node": None
    }


# ============================================
# SECTION 4: DISPLAY HELPERS
# ============================================

def print_test_header(test_name: str):
    """Prints a test section header."""
    print(f"\n{'─' * 60}")
    print(f"TEST: {test_name}")
    print(f"{'─' * 60}")


def print_field(
    label: str,
    value,
    expected_present: bool = False
):
    """
    Prints a result field with pass/fail icon.

    Args:
        label:            Field name to display
        value:            Value to display
        expected_present: If True show pass/fail icon
    """
    if expected_present:
        is_present = (
            value is not None and
            value != {} and
            value != [] and
            value != ""
        )
        icon = "✅" if is_present else "❌"
    else:
        icon = "📋"

    # Truncate long values for display
    display_value = str(value)
    if len(display_value) > 80:
        display_value = display_value[:80] + "..."

    print(f"  {icon} {label}: {display_value}")


def print_json_summary(label: str, data: dict):
    """Prints a summary of a dict result."""
    if not data:
        print(f"  📋 {label}: Empty")
        return

    print(f"  📋 {label}:")
    for key, value in data.items():
        display = str(value)
        if len(display) > 60:
            display = display[:60] + "..."
        print(f"       {key}: {display}")


# ============================================
# SECTION 5: PRE-FLIGHT CHECKS
# ============================================

def test_preflight_state_data():
    """
    Pre-flight check 1: Verify state_data.py
    has the required functions and data.
    """
    print_test_header(
        "Pre-flight 1: state_data.py Check"
    )

    all_passed = True

    # Check STATE_REGULATORY_INFO has all 6 states
    print("\n  Checking STATE_REGULATORY_INFO...")
    for state_code in NEW_ENGLAND_STATES.keys():
        if state_code in STATE_REGULATORY_INFO:
            info = STATE_REGULATORY_INFO[state_code]
            puc = info.get("puc_name", "Missing!")
            print(f"  ✅ {state_code}: {puc}")
        else:
            print(
                f"  ❌ {state_code}: MISSING from "
                f"STATE_REGULATORY_INFO"
            )
            all_passed = False

    # Check helper functions exist and work
    print("\n  Checking helper functions...")
    try:
        sources = get_authoritative_sources("NH")
        if sources:
            print("  ✅ get_authoritative_sources() works")
        else:
            print(
                "  ⚠️  get_authoritative_sources() "
                "returned empty for NH"
            )
    except Exception as e:
        print(f"  ❌ get_authoritative_sources() failed: {e}")
        all_passed = False

    try:
        facts = get_stable_facts("NH")
        if facts:
            print("  ✅ get_stable_facts() works")
        else:
            print(
                "  ⚠️  get_stable_facts() "
                "returned empty for NH"
            )
    except Exception as e:
        print(f"  ❌ get_stable_facts() failed: {e}")
        all_passed = False

    try:
        queries = get_search_queries(
            "NH", "Solar PV", 250.0
        )
        if queries:
            print(
                f"  ✅ get_search_queries() works "
                f"({len(queries)} queries)"
            )
        else:
            print(
                "  ⚠️  get_search_queries() "
                "returned empty"
            )
    except Exception as e:
        print(f"  ❌ get_search_queries() failed: {e}")
        all_passed = False

    try:
        context = get_naics_context("332")
        if context:
            print(
                f"  ✅ get_naics_context() works: "
                f"{context.get('name', 'No name')}"
            )
        else:
            print(
                "  ⚠️  get_naics_context() "
                "returned empty for NAICS 332"
            )
    except Exception as e:
        print(f"  ❌ get_naics_context() failed: {e}")
        all_passed = False

    status = "✅ PASSED" if all_passed else "❌ FAILED"
    print(f"\n  Result: {status}")
    return all_passed


def test_preflight_source_hierarchy():
    """
    Pre-flight check 2: Verify source_hierarchy.py
    and freshness checking work correctly.
    """
    print_test_header(
        "Pre-flight 2: Source Hierarchy Check"
    )

    all_passed = True

    print("\n  Checking POLICY_SOURCES...")
    for source_key, source_data in POLICY_SOURCES.items():
        print(f"\n  Source: {source_key}")
        print_field("  Name", source_data.get("name"))
        print_field("  Tier", source_data.get("tier"))
        print_field(
            "  Last updated",
            source_data.get("last_updated")
        )

    print("\n  Checking get_source_freshness_flag()...")
    try:
        freshness = get_source_freshness_flag(
            "policy_document"
        )
        print_field(
            "  Source name",
            freshness.get("source_name"),
            expected_present=True
        )
        print_field(
            "  Age (days)",
            freshness.get("age_days"),
            expected_present=True
        )
        print_field(
            "  Confidence",
            freshness.get("confidence"),
            expected_present=True
        )
        print_field(
            "  Flag color",
            freshness.get("flag_color"),
            expected_present=True
        )
        print_field(
            "  Verification needed",
            freshness.get("verification_needed")
        )

        # Policy document from Dec 2024 should
        # be LOW confidence by June 2026
        if freshness.get("flag_color") == "red":
            print(
                "\n  ⚠️  Policy document is LOW confidence"
                "\n     This is expected for Dec 2024 data"
                "\n     LLM will be instructed to verify"
            )
        elif freshness.get("flag_color") == "yellow":
            print(
                "\n  ⚠️  Policy document is MEDIUM confidence"
                "\n     LLM will flag items for verification"
            )
        else:
            print(
                "\n  ✅ Policy document is HIGH confidence"
            )

        print("\n  ✅ Source hierarchy check passed")

    except Exception as e:
        print(
            f"\n  ❌ Source hierarchy check failed: {e}"
        )
        all_passed = False

    status = "✅ PASSED" if all_passed else "❌ FAILED"
    print(f"\n  Result: {status}")
    return all_passed


def test_preflight_ollama():
    """
    Pre-flight check 3: Verify Ollama is running.
    """
    print_test_header(
        "Pre-flight 3: Ollama Connection Check"
    )

    try:
        import requests
        from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL

        response = requests.get(
            OLLAMA_BASE_URL,
            timeout=5
        )

        if "Ollama is running" in response.text:
            print(
                f"  ✅ Ollama running at {OLLAMA_BASE_URL}"
            )
            print(f"  ✅ Model configured: {OLLAMA_MODEL}")
            return True
        else:
            print(
                f"  ⚠️  Unexpected response from Ollama"
            )
            return False

    except Exception as e:
        print(f"  ❌ Cannot connect to Ollama: {e}")
        print(
            f"  Check: http://localhost:11434 in browser"
        )
        return False


# ============================================
# SECTION 6: NODE TESTS
# ============================================

def test_node1_gather_sources(
    facility_state: str = "NH",
    technology: str = "Solar PV",
    system_size_kw: float = 250.0,
    naics_code: str = "332"
) -> dict:
    """
    Tests Node 1: Gather sources and stable facts.

    This node does NOT use the LLM so it should
    always work if state_data.py is correct.

    Args:
        facility_state: State to test
        technology:     Technology to test
        system_size_kw: System size to test
        naics_code:     NAICS code to test

    Returns:
        Updated state dict or None if failed
    """
    print_test_header(
        f"Node 1: Gather Sources "
        f"({facility_state}, {technology})"
    )

    state = blank_state(
        facility_state=facility_state,
        technology=technology,
        system_size_kw=system_size_kw,
        naics_code=naics_code
    )

    print(f"\n  Input state: {facility_state}")
    print(f"  Technology:  {technology}")
    print(f"  Size:        {system_size_kw} kW")
    print(f"  NAICS:       {naics_code}")
    print("\n  Running node_gather_sources()...")

    result = node_gather_sources(state)

    print("\n  Results:")
    print_field(
        "Authoritative sources",
        "Present" if result.get("authoritative_sources")
        else "Missing",
        expected_present=True
    )
    print_field(
        "Stable facts",
        "Present" if result.get("stable_facts")
        else "Missing",
        expected_present=True
    )
    print_field(
        "Search queries",
        f"{len(result.get('search_queries', []))} queries"
        if result.get("search_queries") else "Missing",
        expected_present=True
    )
    print_field(
        "NAICS context",
        result.get("naics_context", {}).get(
            "name", "Missing"
        ),
        expected_present=True
    )
    print_field(
        "Source freshness",
        result.get("source_freshness", {}).get(
            "confidence", "Missing"
        ),
        expected_present=True
    )
    print_field(
        "Error",
        result.get("error", "None")
    )

    # Show detail of what was gathered
    if result.get("authoritative_sources"):
        sources = result["authoritative_sources"]
        tier1 = sources.get("tier1_sources", [])
        print(
            f"\n  Tier 1 sources found: {len(tier1)}"
        )
        for s in tier1[:3]:  # Show first 3
            print(f"    - {s.get('name', 'Unknown')}")
        if len(tier1) > 3:
            print(f"    ... and {len(tier1)-3} more")

    if result.get("stable_facts"):
        facts = result["stable_facts"]
        utilities = facts.get("electric_utilities", [])
        print(
            f"\n  Utilities in stable facts: "
            f"{len(utilities)}"
        )
        for u in utilities:
            print(
                f"    - {u.get('name', 'Unknown')}"
            )

    if result.get("search_queries"):
        queries = result["search_queries"]
        print(f"\n  Sample search queries:")
        for q in queries[:2]:  # Show first 2
            print(
                f"    Topic: {q.get('topic', 'Unknown')}"
            )
            query_text = q.get("query", "")[:60]
            print(f"    Query: {query_text}...")

    if result.get("error"):
        print(f"\n  ❌ Node 1 FAILED: {result['error']}")
        return None

    print(f"\n  ✅ Node 1 PASSED")
    return result


def test_node2_llm_research(
    node1_result: dict = None
) -> dict:
    """
    Tests Node 2: LLM policy research.

    Requires Ollama to be running.
    Uses output from Node 1 if available,
    otherwise uses hardcoded test data.

    Args:
        node1_result: State dict from Node 1 test
                      or None to use test data

    Returns:
        Updated state dict or None if failed
    """
    print_test_header("Node 2: LLM Policy Research")
    print("  Note: Requires Ollama to be running")
    print(
        "  This may take 30-90 seconds with Ollama"
    )

    if node1_result is None:
        print(
            "\n  Node 1 result not provided. "
            "Building test state manually..."
        )
        state = blank_state()

        # Manually populate what Node 1 would have set
        state["authoritative_sources"] = (
            get_authoritative_sources("NH")
        )
        state["stable_facts"] = get_stable_facts("NH")
        state["search_queries"] = get_search_queries(
            "NH", "Solar PV", 250.0
        )
        state["naics_context"] = get_naics_context("332")
        state["source_freshness"] = (
            get_source_freshness_flag("policy_document")
        )
    else:
        state = node1_result

    print(
        f"\n  Researching: "
        f"{state['facility_state']} | "
        f"{state['technology']} | "
        f"{state['system_size_kw']} kW"
    )
    print("\n  Running node_llm_research()...")
    print("  (LLM is researching policies...)")

    start_time = datetime.now()
    result = node_llm_research(state)
    elapsed = (datetime.now() - start_time).seconds

    print(f"\n  Completed in {elapsed} seconds")
    print("\n  Results:")

    print_field(
        "Raw LLM research",
        "Present" if result.get("raw_llm_research")
        else "Missing",
        expected_present=True
    )
    print_field(
        "Error",
        result.get("error", "None")
    )

    if result.get("raw_llm_research"):
        research = result["raw_llm_research"]
        char_count = len(research)
        line_count = len(research.split("\n"))
        print(f"\n  Research length: {char_count} chars")
        print(f"  Research lines:  {line_count}")

        # Check key topics were covered
        print("\n  Topic coverage check:")
        topics = {
            "RPS": [
                "rps", "renewable portfolio",
                "eligible"
            ],
            "Net Metering": [
                "net meter", "credit rate", "nem"
            ],
            "Interconnection": [
                "interconnect", "process tier",
                "application"
            ],
            "Incentives": [
                "incentive", "rebate", "program"
            ]
        }

        research_lower = research.lower()
        for topic, keywords in topics.items():
            found = any(
                kw in research_lower
                for kw in keywords
            )
            icon = "✅" if found else "⚠️ "
            print(f"    {icon} {topic}: {'Found' if found else 'Not found'}")

        # Show preview of research
        print("\n  Research preview (first 300 chars):")
        print("  " + "─" * 50)
        preview = research[:300].replace("\n", "\n  ")
        print(f"  {preview}...")
        print("  " + "─" * 50)

    if result.get("error"):
        print(
            f"\n  ❌ Node 2 FAILED: {result['error']}"
        )
        return None

    print(f"\n  ✅ Node 2 PASSED")
    return result


def test_node3_format_report(
    node2_result: dict = None
) -> dict:
    """
    Tests Node 3: Format final policy report.

    Uses output from Node 2 if available,
    otherwise uses hardcoded test data.

    Args:
        node2_result: State dict from Node 2 test
                      or None to use test data

    Returns:
        Updated state dict or None if failed
    """
    print_test_header("Node 3: Format Policy Report")

    if node2_result is None:
        print(
            "\n  Node 2 result not provided. "
            "Using sample research text..."
        )
        state = blank_state()
        state["source_freshness"] = (
            get_source_freshness_flag("policy_document")
        )
        # Provide sample research text
        state["raw_llm_research"] = """
TOPIC 1 - RENEWABLE PORTFOLIO STANDARD:
Solar PV is eligible under the NH RPS.
The current RPS requirement is approximately 25.2%
by 2025 with solar carveout requirements.
Source: puc.nh.gov (verified June 2026)
Confidence: HIGH

TOPIC 2 - NET METERING:
NH NEM 2.0 is active through 2041.
Credit rate is approximately 85% of retail rate
(~\$0.23/kWh based on current Eversource rates).
System size limit: 1 MW for standard, 5 MW for
group net metering with municipal host.
Source: puc.nh.gov/electric/net-metering
Confidence: HIGH

TOPIC 3 - INTERCONNECTION:
A 250 kW system falls under the Expedited Process
(between 10 kW simplified limit and 1 MW standard limit).
Application fee: \$100 plus \$2 per kW = ~\$600.
Timeline: typically 45-90 days for expedited review.
Source: puc.nh.gov/electric/interconnection
Confidence: HIGH

TOPIC 4 - INCENTIVE PROGRAMS:
Note: HB 2 (2025) closed NH state rebate programs.
Eversource Connected Solutions: Battery storage rebate
available at \$230/kWh for demand response participation.
Federal ITC: 30% investment tax credit available for
commercial solar under IRA Section 48E.
Source: dsireusa.org/state/NH (verified June 2026)
Confidence: MEDIUM - verify current program status
"""
    else:
        state = node2_result

    print(
        f"\n  Formatting report for: "
        f"{state['facility_state']} | "
        f"{state['technology']}"
    )
    print("\n  Running node_format_report()...")

    start_time = datetime.now()
    result = node_format_report(state)
    elapsed = (datetime.now() - start_time).seconds

    print(f"\n  Completed in {elapsed} seconds")
    print("\n  Results:")

    print_field(
        "Final report",
        "Present" if result.get("final_report")
        else "Missing",
        expected_present=True
    )
    print_field(
        "Error",
        result.get("error", "None")
    )

    if result.get("final_report"):
        report = result["final_report"]
        char_count = len(report)
        line_count = len(report.split("\n"))
        print(f"\n  Report length: {char_count} chars")
        print(f"  Report lines:  {line_count}")

        # Check report has required sections
        print("\n  Section check:")
        sections = [
            "EXECUTIVE SUMMARY",
            "RENEWABLE PORTFOLIO",
            "NET METERING",
            "INTERCONNECTION",
            "INCENTIVE",
            "REGULATORY CONTACTS",
            "VERIFICATION"
        ]

        report_upper = report.upper()
        for section in sections:
            found = section in report_upper
            icon = "✅" if found else "⚠️ "
            print(
                f"    {icon} {section}: "
                f"{'Found' if found else 'Missing'}"
            )

        # Print full report
        print("\n" + "─" * 60)
        print("FULL FORMATTED REPORT:")
        print("─" * 60)
        print(report)
        print("─" * 60)

    if result.get("error"):
        print(
            f"\n  ❌ Node 3 FAILED: {result['error']}"
        )
        return None

    print(f"\n  ✅ Node 3 PASSED")
    return result


# ============================================
# SECTION 7: FULL AGENT TEST
# ============================================

def test_full_agent2(
    facility_state: str = "NH",
    technology: str = "Solar PV",
    system_size_kw: float = 250.0,
    naics_code: str = "332",
    utility: str = "Eversource Energy"
) -> dict:
    """
    Tests the complete Agent 2 pipeline
    using run_agent2() end to end.

    Args:
        facility_state: State to test
        technology:     Technology to test
        system_size_kw: System size to test
        naics_code:     NAICS code to test
        utility:        Utility name to test

    Returns:
        Agent 2 result dict
    """
    print_test_header(
        f"Full Agent 2 Pipeline Test: "
        f"{facility_state} | {technology}"
    )
    print(
        "\n  This runs all nodes end to end."
        "\n  May take 60-180 seconds with Ollama."
    )

    start_time = datetime.now()

    result = run_agent2(
        facility_state=facility_state,
        technology=technology,
        system_size_kw=system_size_kw,
        naics_code=naics_code,
        utility=utility,
        facility_type="Private Industrial"
    )

    elapsed = (datetime.now() - start_time).seconds

    print(f"\n  Completed in {elapsed} seconds")
    print("\n  Results:")

    print_field(
        "Success",
        result.get("success"),
        expected_present=True
    )
    print_field(
        "State",
        result.get("facility_state"),
        expected_present=True
    )
    print_field(
        "Technology",
        result.get("technology"),
        expected_present=True
    )
    print_field(
        "Final report",
        "Present" if result.get("final_report")
        else "Missing",
        expected_present=True
    )

    quality = result.get("source_quality", {})
    print_field(
        "Data confidence",
        quality.get("confidence", "Unknown")
    )
    print_field(
        "Data age (days)",
        quality.get("age_days", "Unknown")
    )
    print_field(
        "Error",
        result.get("error", "None")
    )

    if result.get("final_report"):
        print("\n" + "─" * 60)
        print("FULL REPORT:")
        print("─" * 60)
        print(result["final_report"])
        print("─" * 60)

    status = (
        "✅ PASSED" if result.get("success")
        else "❌ FAILED"
    )
    print(f"\n  Result: {status}")
    return result


# ============================================
# SECTION 8: MAIN TEST RUNNER
# ============================================

def main():
    """
    Runs all Agent 2 tests in sequence.
    Asks user before running LLM-dependent tests
    since those take significant time.
    """

    print("\n" + "=" * 60)
    print("  ENSITE Agent 2 Node Tests")
    print("  University of New Hampshire")
    print("=" * 60)

    results = {
        "preflight_state_data": False,
        "preflight_source_hierarchy": False,
        "preflight_ollama": False,
        "node1": False,
        "node2": False,
        "node3": False,
        "full_agent": False
    }

    # ----------------------------------------
    # PRE-FLIGHT CHECKS
    # These do not require LLM
    # ----------------------------------------
    print("\n" + "═" * 60)
    print("PRE-FLIGHT CHECKS (no LLM required)")
    print("═" * 60)

    results["preflight_state_data"] = (
        test_preflight_state_data()
    )
    results["preflight_source_hierarchy"] = (
        test_preflight_source_hierarchy()
    )
    results["preflight_ollama"] = (
        test_preflight_ollama()
    )

    # ----------------------------------------
    # NODE 1 TEST
    # Does not require LLM
    # ----------------------------------------
    print("\n" + "═" * 60)
    print("NODE TESTS")
    print("═" * 60)

    node1_result = test_node1_gather_sources(
        facility_state="NH",
        technology="Solar PV",
        system_size_kw=250.0,
        naics_code="332"
    )
    results["node1"] = node1_result is not None

    # ----------------------------------------
    # NODE 2 TEST
    # Requires LLM — ask user first
    # ----------------------------------------
    print("\n" + "─" * 60)
    if not results["preflight_ollama"]:
        print(
            "\n⏭️  Skipping Node 2 — Ollama not available"
        )
        node2_result = None
    else:
        run_node2 = input(
            "\nRun Node 2 LLM research test? "
            "(30-90 seconds) (yes/no): "
        ).strip().lower()

        if run_node2 == "yes":
            node2_result = test_node2_llm_research(
                node1_result
            )
            results["node2"] = node2_result is not None
        else:
            print("  ⏭️  Skipping Node 2 LLM test")
            node2_result = None

    # ----------------------------------------
    # NODE 3 TEST
    # Requires LLM — ask user first
    # ----------------------------------------
    print("\n" + "─" * 60)
    if not results["preflight_ollama"]:
        print(
            "\n⏭️  Skipping Node 3 — Ollama not available"
        )
    else:
        run_node3 = input(
            "\nRun Node 3 report formatting test? "
            "(30-60 seconds) (yes/no): "
        ).strip().lower()

        if run_node3 == "yes":
            node3_result = test_node3_format_report(
                node2_result
            )
            results["node3"] = node3_result is not None
        else:
            print("  ⏭️  Skipping Node 3 test")

    # ----------------------------------------
    # FULL AGENT TEST
    # Runs all nodes end to end
    # ----------------------------------------
    print("\n" + "─" * 60)
    if not results["preflight_ollama"]:
        print(
            "\n⏭️  Skipping full agent test — "
            "Ollama not available"
        )
    else:
        run_full = input(
            "\nRun full Agent 2 pipeline test? "
            "(60-180 seconds) (yes/no): "
        ).strip().lower()

        if run_full == "yes":

            # Let user choose test case
            print("\n  Available test cases:")
            test_cases = [
                {
                    "label": "NH Solar PV 250 kW",
                    "state": "NH",
                    "tech": "Solar PV",
                    "size": 250.0,
                    "naics": "332",
                    "utility": "Eversource Energy"
                },
                {
                    "label": "ME Biomass 500 kW (Paper Mill)",
                    "state": "ME",
                    "tech": "Biomass",
                    "size": 500.0,
                    "naics": "322",
                    "utility": "Central Maine Power"
                },
                {
                    "label": "VT Battery Storage 100 kW",
                    "state": "VT",
                    "tech": "Battery Storage",
                    "size": 100.0,
                    "naics": "311",
                    "utility": "Green Mountain Power"
                }
            ]

            for i, tc in enumerate(test_cases, 1):
                print(f"    {i}. {tc['label']}")

            try:
                choice = int(
                    input(
                        "\n  Choose test case (1-3): "
                    ).strip()
                ) - 1
                if 0 <= choice < len(test_cases):
                    tc = test_cases[choice]
                else:
                    tc = test_cases[0]
            except ValueError:
                tc = test_cases[0]

            full_result = test_full_agent2(
                facility_state=tc["state"],
                technology=tc["tech"],
                system_size_kw=tc["size"],
                naics_code=tc["naics"],
                utility=tc["utility"]
            )
            results["full_agent"] = (
                full_result.get("success", False)
            )

        else:
            print("  ⏭️  Skipping full agent test")

    # ----------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    labels = {
        "preflight_state_data":
            "Pre-flight: state_data.py",
        "preflight_source_hierarchy":
            "Pre-flight: source_hierarchy.py",
        "preflight_ollama":
            "Pre-flight: Ollama connection",
        "node1":
            "Node 1: Gather sources (no LLM)",
        "node2":
            "Node 2: LLM policy research",
        "node3":
            "Node 3: Format report",
        "full_agent":
            "Full Agent 2 pipeline"
    }

    passed = 0
    skipped = 0

    for key, label in labels.items():
        if results[key] is True:
            print(f"  ✅ PASS    {label}")
            passed += 1
        elif results[key] is False and key in [
            "node2", "node3", "full_agent"
        ]:
            # These may have been skipped
            print(f"  ⏭️  SKIP    {label}")
            skipped += 1
        else:
            print(f"  ❌ FAIL    {label}")

    total = len(results) - skipped
    print(
        f"\n  {passed}/{total} tests passed "
        f"({skipped} skipped)"
    )

    # Key advice based on results
    if not results["preflight_state_data"]:
        print(
            "\n⚠️  state_data.py is incomplete."
            "\n   Add missing states or helper functions."
        )

    if not results["node1"]:
        print(
            "\n⚠️  Node 1 failed."
            "\n   Check get_authoritative_sources(),"
            "\n   get_stable_facts(), get_search_queries()"
            "\n   in config/state_data.py"
        )

    if results["node1"] and not results["node2"]:
        print(
            "\n⚠️  Node 1 passed but Node 2 failed."
            "\n   Check Ollama is running and"
            "\n   llm_factory.py get_llm() works."
        )

    print("=" * 60 + "\n")


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    main()
