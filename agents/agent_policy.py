"""
ENSITE Agent 2: Policy Research Agent
======================================
CORRECTED VERSION - properly integrates with:
- config/source_hierarchy.py  (trust scoring)
- config/state_data.py        (state policy data)
- config/settings.py          (app configuration)
- agents/llm_factory.py       (LLM connection)

Author: ENSITE Project, UNH
Date: June 2026
"""

# ============================================
# SECTION 1: IMPORTS
# ============================================
import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# LangChain imports
from langchain.tools import tool
from deepagents import create_deep_agent

# ============================================
# IMPORT FROM OUR OWN PROJECT FILES
# This is what was missing from the first version!
# ============================================
from config.settings import (
    NEW_ENGLAND_STATES,
    MAX_SOURCE_AGE_DAYS,
    POLICY_DOCS_PATH
)
from config.source_hierarchy import (
    get_source_tier,
    get_trust_score,
    SOURCE_TIERS
)
from config.state_data import (
    STATE_REGULATORY_INFO,
    STATE_POLICY_DATA
)
from agents.llm_factory import get_llm

load_dotenv()
logger = logging.getLogger(__name__)


# ============================================
# SECTION 2: SOURCE METADATA
# ============================================
# This is where source_hierarchy.py gets used!
# Every tool now tracks WHERE its data came from
# and HOW FRESH it is.

POLICY_SOURCES = {
    "policy_document": {
        "name": "Policy_Landscape_updated_12.13.24.pptx",
        "url": "internal://policy_docs/Policy_Landscape",
        "tier": "tier1",
        "last_updated": "2024-12-13",
        "update_frequency": "As updated by Matt Davis/UNH"
    },
    "dsire": {
        "name": "DSIRE Database",
        "url": "dsireusa.org",
        "tier": "tier1",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "update_frequency": "Weekly via API"
    },
    "nh_doe": {
        "name": "NH Department of Energy",
        "url": "energy.nh.gov",
        "tier": "tier1",
        "last_updated": "2026-06-01",
        "update_frequency": "Monthly scrape"
    },
    "me_puc": {
        "name": "Maine Public Utilities Commission",
        "url": "maine.gov/mpuc",
        "tier": "tier1",
        "last_updated": "2026-06-01",
        "update_frequency": "Monthly scrape"
    }
}


def get_source_freshness_flag(source_key: str) -> dict:
    """
    Uses source_hierarchy.py rules to determine
    if a data source is fresh enough to trust.

    Returns a confidence flag based on source
    tier and age.
    """
    source = POLICY_SOURCES.get(source_key, {})
    tier = source.get("tier", "tier3")
    last_updated_str = source.get("last_updated", "2024-01-01")

    # Calculate source age in days
    try:
        last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d")
        age_days = (datetime.now() - last_updated).days
    except ValueError:
        age_days = 999  # Unknown age - treat as very old

    # Get max allowed age for this tier
    # from source_hierarchy.py settings
    max_age = MAX_SOURCE_AGE_DAYS.get(tier, 90)
    trust_score = get_trust_score(source.get("url", ""))

    # Determine confidence level
    if age_days <= max_age * 0.5:
        confidence = "HIGH ✅"
        flag_color = "green"
    elif age_days <= max_age:
        confidence = "MEDIUM ⚠️"
        flag_color = "yellow"
    else:
        confidence = "LOW 🚨"
        flag_color = "red"

    return {
        "source_name": source.get("name", "Unknown"),
        "source_tier": tier,
        "tier_description": SOURCE_TIERS[tier]["name"],
        "trust_score": trust_score,
        "last_updated": last_updated_str,
        "age_days": age_days,
        "max_age_days": max_age,
        "confidence": confidence,
        "flag_color": flag_color,
        "verification_needed": age_days > max_age
    }


# ============================================
# SECTION 3: POLICY LOOKUP TOOLS
# ============================================
# Now properly pulling from config/state_data.py
# instead of duplicating data here.
# Each tool also uses source_hierarchy.py to
# flag data quality.

@tool
def get_state_rps_policy(state: str) -> str:
    """
    Returns Renewable Portfolio Standard (RPS)
    policy details for a given New England state.

    Args:
        state: Two-letter state abbreviation

    Returns:
        JSON string with RPS details AND
        source quality metadata
    """
    state = state.upper().strip()

    # Validate state
    if state not in NEW_ENGLAND_STATES:
        return json.dumps({
            "error": f"State '{state}' not found",
            "available_states": list(NEW_ENGLAND_STATES.keys())
        })

    # Pull from config/state_data.py
    # NOT from hardcoded data in this file!
    policy = STATE_POLICY_DATA.get(state, {})

    if not policy:
        return json.dumps({
            "error": f"No policy data for state '{state}'",
            "suggestion": "Check config/state_data.py"
        })

    # Get source quality from source_hierarchy.py
    freshness = get_source_freshness_flag("policy_document")

    result = {
        "state": state,
        "state_name": NEW_ENGLAND_STATES[state],
        "rps": policy.get("rps", {}),
        "source_quality": freshness
    }

    logger.info(
        f"RPS lookup: {state} | "
        f"Confidence: {freshness['confidence']}"
    )
    return json.dumps(result, indent=2)


@tool
def get_net_metering_policy(state: str) -> str:
    """
    Returns net metering rules and credit rates
    for a given New England state.

    Args:
        state: Two-letter state abbreviation

    Returns:
        JSON string with net metering details
        AND source quality metadata
    """
    state = state.upper().strip()

    if state not in NEW_ENGLAND_STATES:
        return json.dumps({
            "error": f"State '{state}' not found"
        })

    # Pull from config/state_data.py
    policy = STATE_POLICY_DATA.get(state, {})
    freshness = get_source_freshness_flag("policy_document")

    result = {
        "state": state,
        "state_name": NEW_ENGLAND_STATES[state],
        "net_metering": policy.get("net_metering", {}),
        "source_quality": freshness
    }

    logger.info(f"Net metering lookup: {state}")
    return json.dumps(result, indent=2)


@tool
def get_interconnection_requirements(
    state: str,
    system_size_kw: float
) -> str:
    """
    Returns interconnection process tier and
    requirements for a given state and system size.

    Args:
        state: Two-letter state abbreviation
        system_size_kw: System size in kilowatts

    Returns:
        JSON string with interconnection details
        including applicable process tier
    """
    state = state.upper().strip()

    if state not in NEW_ENGLAND_STATES:
        return json.dumps({
            "error": f"State '{state}' not found"
        })

    policy = STATE_POLICY_DATA.get(state, {})
    interconnect = policy.get("interconnection", {})
    freshness = get_source_freshness_flag("policy_document")

    # Determine process tier from thresholds
    # stored in config/state_data.py
    thresholds = interconnect.get("process_thresholds", {})
    process_tier = "Standard Process"
    process_notes = "Full engineering study required"

    simplified_limit = thresholds.get("simplified_kw", 0)
    expedited_limit = thresholds.get("expedited_kw", 0)

    if simplified_limit and system_size_kw <= simplified_limit:
        process_tier = "Simplified Process"
        process_notes = (
            f"System under {simplified_limit} kW threshold - "
            f"minimal grid impact expected"
        )
    elif expedited_limit and system_size_kw <= expedited_limit:
        process_tier = "Expedited Process"
        process_notes = (
            f"System between {simplified_limit} kW and "
            f"{expedited_limit} kW - pre-screening criteria apply"
        )
    else:
        process_tier = "Standard Process"
        process_notes = (
            f"System exceeds {expedited_limit} kW threshold - "
            f"detailed engineering study required"
        )

    result = {
        "state": state,
        "system_size_kw": system_size_kw,
        "process_tier": process_tier,
        "process_notes": process_notes,
        "interconnection_details": interconnect,
        "source_quality": freshness
    }

    logger.info(
        f"Interconnection lookup: {state}, "
        f"{system_size_kw} kW → {process_tier}"
    )
    return json.dumps(result, indent=2)


@tool
def get_technology_policy(
    state: str,
    technology: str
) -> str:
    """
    Returns technology-specific policy notes
    for a given state and energy technology.

    Args:
        state: Two-letter state abbreviation
        technology: Energy technology type

    Returns:
        JSON string with technology-specific
        policy details
    """
    state = state.upper().strip()

    if state not in NEW_ENGLAND_STATES:
        return json.dumps({
            "error": f"State '{state}' not found"
        })

    policy = STATE_POLICY_DATA.get(state, {})
    tech_policies = policy.get("technology_specific", {})
    freshness = get_source_freshness_flag("policy_document")

    # Try exact match then partial match
    tech_note = tech_policies.get(technology)
    matched_key = technology

    if not tech_note:
        for key in tech_policies:
            if (technology.lower() in key.lower() or
                    key.lower() in technology.lower()):
                tech_note = tech_policies[key]
                matched_key = key
                break

    rps_data = policy.get("rps", {})
    eligible_techs = rps_data.get("eligible_technologies", [])
    rps_eligible = any(
        technology.lower() in t.lower()
        for t in eligible_techs
    )

    result = {
        "state": state,
        "technology_queried": technology,
        "technology_matched": matched_key,
        "policy_notes": tech_note or "No specific notes found",
        "rps_eligible": rps_eligible,
        "rps_eligible_technologies": eligible_techs,
        "source_quality": freshness
    }

    logger.info(
        f"Technology policy: {state}, {technology} | "
        f"RPS eligible: {rps_eligible}"
    )
    return json.dumps(result, indent=2)


@tool
def get_state_context(state: str) -> str:
    """
    Returns regulatory contacts, challenges,
    and opportunities for a given state.
    Pulls from config/state_data.py which
    consolidates all static state information.

    Args:
        state: Two-letter state abbreviation

    Returns:
        JSON string with state context
    """
    state = state.upper().strip()

    if state not in NEW_ENGLAND_STATES:
        return json.dumps({
            "error": f"State '{state}' not found"
        })

    # Pull regulatory info from state_data.py
    # This is the SINGLE SOURCE OF TRUTH
    # for regulatory contacts
    reg_info = STATE_REGULATORY_INFO.get(state, {})
    policy = STATE_POLICY_DATA.get(state, {})
    freshness = get_source_freshness_flag("policy_document")

    result = {
        "state": state,
        "state_name": NEW_ENGLAND_STATES[state],
        "regulatory_contacts": reg_info,
        "challenges": policy.get("challenges", []),
        "opportunities": policy.get("opportunities", []),
        "source_quality": freshness
    }

    logger.info(f"State context lookup: {state}")
    return json.dumps(result, indent=2)


@tool
def check_source_reliability(source_key: str) -> str:
    """
    Checks the reliability and freshness of a
    specific data source using the ENSITE
    source hierarchy framework.

    This tool implements the data quality
    requirements from the ENSITE requirements
    document (Section 6.4).

    Args:
        source_key: Source identifier
                    (policy_document, dsire,
                    nh_doe, me_puc)

    Returns:
        JSON string with source quality assessment
    """
    if source_key not in POLICY_SOURCES:
        return json.dumps({
            "error": f"Source '{source_key}' not found",
            "available_sources": list(POLICY_SOURCES.keys())
        })

    freshness = get_source_freshness_flag(source_key)
    source = POLICY_SOURCES[source_key]

    result = {
        "source_key": source_key,
        "source_details": source,
        "quality_assessment": freshness,
        "recommendation": (
            "Use with confidence"
            if freshness["flag_color"] == "green"
            else "Verify with primary source"
            if freshness["flag_color"] == "yellow"
            else "Do not use without verification"
        )
    }

    logger.info(
        f"Source check: {source_key} | "
        f"Confidence: {freshness['confidence']}"
    )
    return json.dumps(result, indent=2)


# ============================================
# SECTION 4: CREATE THE POLICY AGENT
# ============================================

def create_policy_agent(llm_provider: str = "ollama"):
    """
    Creates ENSITE Policy Research Agent.
    Now properly uses:
    - llm_factory.py for LLM connection
    - source_hierarchy.py for data quality
    - state_data.py for policy data

    Args:
        llm_provider: "ollama", "deepthought", "azure"

    Returns:
        Configured Deep Agent
    """

    # Get LLM from llm_factory.py
    # NOT defined inline here!
    llm = get_llm(llm_provider)

    system_prompt = """You are ENSITE Agent 2: Policy Research Agent.

You work for the University of New Hampshire ENSITE system.
Your job is to research energy policies for industrial facilities
across New England.

TOOLS AVAILABLE:
- get_state_rps_policy: RPS details for a state
- get_net_metering_policy: Net metering rules
- get_interconnection_requirements: Process tier for system size
- get_technology_policy: Technology-specific policy notes
- get_state_context: Regulatory contacts, challenges, opportunities
- check_source_reliability: Verify data quality before reporting

INSTRUCTIONS:
1. ALWAYS call check_source_reliability first to assess
   data quality before reporting any policy information
2. Use ALL relevant tools to gather complete information
3. Include source quality confidence scores in your response
4. Flag any LOW confidence data prominently
5. Structure your response in clearly labeled sections
6. Include regulatory contacts for next steps

DATA QUALITY RULES (from ENSITE requirements Section 6.4):
- HIGH confidence (green): Use and report with confidence
- MEDIUM confidence (yellow): Use but flag for verification
- LOW confidence (red): Flag prominently, recommend verification

FORMAT YOUR RESPONSE AS:
1. Data Quality Assessment
2. Executive Summary
3. Renewable Portfolio Standard
4. Net Metering Policy
5. Interconnection Requirements
6. Technology-Specific Notes
7. State Context (Challenges & Opportunities)
8. Regulatory Contacts & Next Steps
9. Verification Recommendations"""

    tools = [
        get_state_rps_policy,
        get_net_metering_policy,
        get_interconnection_requirements,
        get_technology_policy,
        get_state_context,
        check_source_reliability
    ]

    agent = create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )

    logger.info(
        f"Policy agent created "
        f"(provider: {llm_provider})"
    )
    return agent


# ============================================
# SECTION 5: RUN THE AGENT
# ============================================

def run_policy_agent(
    state: str,
    technology: str,
    system_size_kw: float,
    naics_code: str,
    utility: str = "Unknown",
    facility_type: str = "Private Commercial",
    llm_provider: str = "ollama"
) -> dict:
    """
    Main entry point for Agent 2.

    Args:
        state: Two-letter state abbreviation
        technology: Energy technology type
        system_size_kw: System size in kW
        naics_code: NAICS code
        utility: Electric utility (from Agent 1)
        facility_type: Facility ownership type
        llm_provider: LLM to use

    Returns:
        dict with policy research results
        including source quality metadata
    """
    logger.info(
        f"Policy research: {state}, "
        f"{technology}, {system_size_kw} kW"
    )

    agent = create_policy_agent(llm_provider)

    query = f"""
Please research applicable energy policies for this facility:

FACILITY DETAILS:
- State: {state}
- Electric Utility: {utility}
- Proposed Technology: {technology}
- System Size: {system_size_kw} kW
- NAICS Code: {naics_code}
- Facility Type: {facility_type}

REQUIRED STEPS:
1. First check source reliability using
   check_source_reliability("policy_document")
2. Then research all applicable policies
3. Flag any data quality concerns clearly
4. Provide regulatory contacts for next steps
"""

    try:
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": query
            }]
        })

        messages = result.get("messages", [])
        final_response = ""

        for message in reversed(messages):
            if hasattr(message, "content") and message.content:
                final_response = message.content
                break

        # Get overall source quality for metadata
        doc_freshness = get_source_freshness_flag(
            "policy_document"
        )

        logger.info("Policy research completed")

        return {
            "success": True,
            "agent": "agent2_policy",
            "state": state,
            "technology": technology,
            "system_size_kw": system_size_kw,
            "naics_code": naics_code,
            "utility": utility,
            "policy_report": final_response,
            "timestamp": datetime.now().isoformat(),
            "llm_provider": llm_provider,
            "source_quality": doc_freshness,
            "data_sources_used": list(POLICY_SOURCES.keys())
        }

    except Exception as e:
        logger.error(f"Policy agent failed: {e}")
        return {
            "success": False,
            "agent": "agent2_policy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================
# SECTION 6: MAIN
# ============================================

def main():
    """Run Agent 2 with example queries."""

    print("\n" + "=" * 65)
    print("  ENSITE Agent 2: Policy Research Agent")
    print("  University of New Hampshire")
    print("=" * 65)

    # Change this to switch LLM providers
    LLM_PROVIDER = "ollama"

    # Run example query
    result = run_policy_agent(
        state="NH",
        technology="Solar PV",
        system_size_kw=250.0,
        naics_code="332",
        utility="Eversource Energy",
        facility_type="Private Industrial",
        llm_provider=LLM_PROVIDER
    )

    if result["success"]:
        print(f"\n📊 Source Confidence: "
              f"{result['source_quality']['confidence']}")
        print(f"📅 Data Age: "
              f"{result['source_quality']['age_days']} days")
        print("\n" + "-" * 65)
        print(result["policy_report"])
    else:
        print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    main()