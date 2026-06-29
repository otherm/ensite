"""
ENSITE Agent 2: Policy Research Agent
=============================================
LangGraph Version — Consistent with Agent 1

Flow:
  START
    │
    ▼
  Node 1: Gather sources and stable facts
  (config/state_data.py — no LLM needed)
    │
    ▼
  Node 2: LLM researches current policies
  (searches authoritative sources live)
    │
    ▼
  Node 3: Format final report
  (structures output consistently)
    │
    ▼
  END

Key design decisions:
  - LangGraph nodes match Agent 1 pattern
  - Node 1 pulls stable facts without LLM
  - Node 2 uses LLM for live policy research
  - source_hierarchy.py flags data quality
  - state_data.py provides sources not answers

Imports from:
  config/settings.py          paths and constants
  config/source_hierarchy.py  trust scoring
  config/state_data.py        sources and stable facts
  agents/llm_factory.py       LLM connection

Author: ENSITE Project, UNH
Date: June 2026
"""

# ============================================
# SECTION 1: IMPORTS
# ============================================
import json
import logging
from datetime import datetime
from typing import TypedDict, Optional

# LangGraph
from langgraph.graph import StateGraph, END

# LangChain
from langchain_core.messages import HumanMessage

# Project files
from config.settings import (
    NEW_ENGLAND_STATES,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    MAX_SOURCE_AGE_DAYS
)
from config.source_hierarchy import (
    get_source_tier,
    get_trust_score,
    SOURCE_TIERS
)
from config.state_data import (
    STATE_REGULATORY_INFO,
    get_authoritative_sources,
    get_stable_facts,
    get_search_queries,
    get_naics_context
)
from agents.llm_factory import get_llm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================
# SECTION 2: SOURCE METADATA
# ============================================
# Tracks WHERE data comes from and HOW FRESH
# it is. Used by get_source_freshness_flag()
# to apply source_hierarchy.py rules.

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
    }
}


def get_source_freshness_flag(source_key: str) -> dict:
    """
    Uses source_hierarchy.py rules to assess
    whether a data source is fresh enough to trust.

    Args:
        source_key: Key from POLICY_SOURCES dict

    Returns:
        dict with confidence level and flag color
    """
    source = POLICY_SOURCES.get(source_key, {})
    tier = source.get("tier", "tier3")
    last_updated_str = source.get(
        "last_updated", "2024-01-01"
    )

    try:
        last_updated = datetime.strptime(
            last_updated_str, "%Y-%m-%d"
        )
        age_days = (datetime.now() - last_updated).days
    except ValueError:
        age_days = 999

    max_age = MAX_SOURCE_AGE_DAYS.get(tier, 90)
    trust_score = get_trust_score(
        source.get("url", "")
    )

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
# SECTION 3: DEFINE STATE
# ============================================
# Defines what data flows between nodes.
# Same pattern as AgentState in Agent 1.
# Parameter name uses agent_state throughout
# to avoid conflict with state["state"] key.

class PolicyAgentState(TypedDict):

    # INPUT (set at start by run_agent2)
    facility_state: str          # Two-letter state code
    technology: str              # e.g. Solar PV
    system_size_kw: float        # System size in kW
    naics_code: str              # NAICS code
    utility: str                 # From Agent 1
    facility_type: str           # Private/Municipal/etc

    # SET BY NODE 1 (source gathering)
    authoritative_sources: Optional[dict]
    stable_facts: Optional[dict]
    search_queries: Optional[list]
    naics_context: Optional[dict]
    source_freshness: Optional[dict]

    # SET BY NODE 2 (LLM research)
    rps_findings: Optional[str]
    net_metering_findings: Optional[str]
    interconnection_findings: Optional[str]
    incentive_findings: Optional[str]
    raw_llm_research: Optional[str]

    # SET BY NODE 3 (report formatting)
    final_report: Optional[str]

    # ERROR HANDLING
    error: Optional[str]
    error_node: Optional[str]


# ============================================
# SECTION 4: DEFINE NODES
# ============================================

def node_gather_sources(
    agent_state: PolicyAgentState
) -> PolicyAgentState:
    """
    NODE 1: Gather sources and stable facts.

    No LLM needed here — just dictionary lookups
    from config/state_data.py.

    This node tells the LLM in Node 2:
    - WHERE to look for current information
    - WHAT stable facts it can rely on
    - WHAT search queries to use
    - WHAT sector context is relevant

    Reads:  agent_state["facility_state"]
            agent_state["technology"]
            agent_state["system_size_kw"]
            agent_state["naics_code"]
    Writes: agent_state["authoritative_sources"]
            agent_state["stable_facts"]
            agent_state["search_queries"]
            agent_state["naics_context"]
            agent_state["source_freshness"]
    """
    state_code = agent_state["facility_state"]
    logger.info(
        f"Node 1 - Gathering sources for: {state_code}"
    )

    try:
        # Get WHERE to look for current info
        # From STATE_AUTHORITATIVE_SOURCES
        # in config/state_data.py
        agent_state["authoritative_sources"] = (
            get_authoritative_sources(state_code)
        )

        # Get stable facts we can rely on
        # without live verification
        # From STATE_STABLE_FACTS in config/state_data.py
        agent_state["stable_facts"] = (
            get_stable_facts(state_code)
        )

        # Get pre-built search queries
        # for finding current policy info
        agent_state["search_queries"] = (
            get_search_queries(
                state_code,
                agent_state["technology"],
                agent_state["system_size_kw"]
            )
        )

        # Get NAICS sector context
        # helps LLM identify relevant programs
        agent_state["naics_context"] = (
            get_naics_context(agent_state["naics_code"])
        )

        # Check freshness of our policy document
        # using source_hierarchy.py rules
        agent_state["source_freshness"] = (
            get_source_freshness_flag("policy_document")
        )

        logger.info(
            f"  Sources gathered for {state_code}. "
            f"Freshness: "
            f"{agent_state['source_freshness']['confidence']}"
        )

    except Exception as e:
        logger.error(f"  Node 1 failed: {e}")
        agent_state["error"] = str(e)
        agent_state["error_node"] = "gather_sources"

    return agent_state


def node_llm_research(
    agent_state: PolicyAgentState
) -> PolicyAgentState:
    """
    NODE 2: LLM researches current policies.

    This is where the LLM does live research
    using the authoritative sources identified
    in Node 1.

    The LLM is given:
    - Exactly WHERE to look (source URLs)
    - Exactly WHAT to search for (queries)
    - Stable facts to anchor its research
    - NAICS context for relevance

    Because the LLM is just doing research
    and writing prose (not calling tools in
    strict format), this works reliably with
    Ollama/Mistral.

    Reads:  All fields set by Node 1
    Writes: agent_state["raw_llm_research"]
            agent_state["rps_findings"]
            agent_state["net_metering_findings"]
            agent_state["interconnection_findings"]
            agent_state["incentive_findings"]
    """
    state_code = agent_state["facility_state"]
    logger.info(
        f"Node 2 - LLM researching policies for: "
        f"{state_code}"
    )

    try:
        llm = get_llm()

        # Get source freshness warning
        freshness = agent_state.get(
            "source_freshness", {}
        )
        freshness_warning = ""
        if freshness.get("flag_color") == "red":
            freshness_warning = (
                f"⚠️  WARNING: Policy document is "
                f"{freshness.get('age_days')} days old. "
                f"Verify all information with current "
                f"authoritative sources."
            )
        elif freshness.get("flag_color") == "yellow":
            freshness_warning = (
                f"⚠️  NOTE: Policy document is "
                f"{freshness.get('age_days')} days old. "
                f"Some details may have changed."
            )

        # Build the research prompt
        # LLM receives structured context from Node 1
        # and is asked to research specific topics
        prompt = f"""You are ENSITE Agent 2 researching 
current energy policies for the University of New Hampshire.

{freshness_warning}

FACILITY DETAILS:
- State: {state_code} ({NEW_ENGLAND_STATES.get(state_code, '')})
- Technology: {agent_state['technology']}
- System Size: {agent_state['system_size_kw']} kW
- NAICS Code: {agent_state['naics_code']}
- Utility: {agent_state.get('utility', 'Unknown')}
- Facility Type: {agent_state.get('facility_type', 'Unknown')}

STABLE FACTS YOU CAN RELY ON:
{json.dumps(agent_state.get('stable_facts', {}), indent=2)}

AUTHORITATIVE SOURCES TO CHECK FOR CURRENT INFO:
{json.dumps(agent_state.get('authoritative_sources', {}), indent=2)}

NAICS SECTOR CONTEXT:
{json.dumps(agent_state.get('naics_context', {}), indent=2)}

SEARCH QUERIES TO USE:
{json.dumps(agent_state.get('search_queries', []), indent=2)}

Please research and provide current policy information
for each of the following topics. For each topic cite
your source URL and note when it was last updated.
Flag any information you cannot verify as current.

TOPIC 1 - RENEWABLE PORTFOLIO STANDARD:
- Is {agent_state['technology']} eligible under the 
  {state_code} RPS?
- Are there technology-specific carveouts that apply?
- What is the current RPS requirement percentage?

TOPIC 2 - NET METERING:
- What is the current net metering credit rate?
- What is the system size limit for this facility?
- Is {agent_state['technology']} eligible?

TOPIC 3 - INTERCONNECTION:
- What process tier applies to a 
  {agent_state['system_size_kw']} kW system?
- What are the application fees?
- What technical studies are required?
- What is the typical timeline?

TOPIC 4 - INCENTIVE PROGRAMS:
- What state incentive programs are currently open?
- What utility rebates are available from 
  {agent_state.get('utility', 'the serving utility')}?
- What federal programs apply to this facility type?

For each finding state:
1. What you found
2. Source URL
3. How current the information is
4. Confidence level (HIGH/MEDIUM/LOW)
"""

        response = llm.invoke(
            [HumanMessage(content=prompt)]
        )
        agent_state["raw_llm_research"] = (
            response.content
        )

        logger.info(
            "  LLM research completed successfully"
        )

    except Exception as e:
        logger.error(f"  Node 2 LLM research failed: {e}")
        agent_state["error"] = str(e)
        agent_state["error_node"] = "llm_research"
        # Set fallback so Node 3 can still run
        agent_state["raw_llm_research"] = (
            f"LLM research unavailable: {str(e)}"
        )

    return agent_state


def node_format_report(
    agent_state: PolicyAgentState
) -> PolicyAgentState:
    """
    NODE 3: Format the final policy report.

    Takes raw LLM research from Node 2 and
    formats it into a consistent structured
    report with source quality metadata.

    This uses a second LLM call to ensure
    consistent formatting regardless of how
    Node 2 structured its output.

    Reads:  agent_state["raw_llm_research"]
            agent_state["source_freshness"]
    Writes: agent_state["final_report"]
    """
    logger.info("Node 3 - Formatting policy report")

    try:
        freshness = agent_state.get(
            "source_freshness", {}
        )

        llm = get_llm()

        prompt = f"""You are formatting a policy research 
report for the ENSITE system at the 
University of New Hampshire.

Here is the raw research from our policy agent:

{agent_state.get('raw_llm_research', 'No research available')}

Please format this into a clean structured report
using exactly this format:

================================================
ENSITE POLICY RESEARCH REPORT
================================================
Facility State:  {agent_state['facility_state']}
Technology:      {agent_state['technology']}
System Size:     {agent_state['system_size_kw']} kW
NAICS Code:      {agent_state['naics_code']}
Generated:       {datetime.now().strftime('%B %d, %Y')}
Data Confidence: {freshness.get('confidence', 'Unknown')}
================================================

1. EXECUTIVE SUMMARY
[2-3 sentence summary of key findings]

2. RENEWABLE PORTFOLIO STANDARD
[RPS eligibility and requirements]

3. NET METERING POLICY
[Current credit rates and limits]

4. INTERCONNECTION REQUIREMENTS
[Process tier and requirements for this system size]

5. AVAILABLE INCENTIVE PROGRAMS
[Currently open programs with amounts if known]

6. REGULATORY CONTACTS
[Key contacts for next steps]

7. DATA QUALITY NOTES
[Flag any LOW or MEDIUM confidence findings]
[Note any information that needs verification]
[List sources used with dates]

================================================
⚠️  VERIFICATION NOTICE
Policy data sourced from:
{freshness.get('source_name', 'Unknown')}
Last updated: {freshness.get('last_updated', 'Unknown')}
Data age: {freshness.get('age_days', 'Unknown')} days

Always verify current program status with:
- State PUC website
- DSIRE: dsireusa.org
- Serving utility directly
================================================
"""

        response = llm.invoke(
            [HumanMessage(content=prompt)]
        )
        agent_state["final_report"] = response.content
        logger.info(
            "  Report formatted successfully"
        )

    except Exception as e:
        logger.error(f"  Node 3 formatting failed: {e}")
        # Fall back to raw research if formatting fails
        agent_state["final_report"] = (
            agent_state.get(
                "raw_llm_research",
                "Report generation failed"
            )
        )

    return agent_state


def node_handle_error(
    agent_state: PolicyAgentState
) -> PolicyAgentState:
    """
    ERROR NODE: Handles failures gracefully.
    """
    error = agent_state.get("error", "Unknown error")
    error_node = agent_state.get("error_node", "Unknown")

    logger.error(
        f"Error handler: Failed at {error_node}: {error}"
    )

    agent_state["final_report"] = f"""
ENSITE AGENT 2 — POLICY RESEARCH INCOMPLETE
=============================================
State:      {agent_state.get('facility_state')}
Technology: {agent_state.get('technology')}
Failed at:  {error_node}
Error:      {error}

Please try again or contact:
Matt Davis, Matt.Davis@unh.edu

Manual research resources:
- DSIRE: dsireusa.org
- State PUC websites listed in state_data.py
"""

    return agent_state


# ============================================
# SECTION 5: ROUTING FUNCTIONS
# ============================================

def route_after_gather(
    agent_state: PolicyAgentState
) -> str:
    """Route after Node 1."""
    if agent_state.get("error"):
        return "handle_error"
    return "llm_research"


def route_after_research(
    agent_state: PolicyAgentState
) -> str:
    """
    Route after Node 2.
    Note: Even if LLM research had issues
    we still go to format_report because
    node_llm_research sets a fallback value.
    """
    if agent_state.get("error_node") == "gather_sources":
        return "handle_error"
    return "format_report"


# ============================================
# SECTION 6: BUILD THE GRAPH
# ============================================

def create_agent2_graph():
    """
    Builds and compiles the Agent 2 LangGraph.

    Graph structure:
    gather_sources → llm_research → format_report → END
    (errors route to handle_error → END)
    """
    logger.info("Building Agent 2 LangGraph")

    graph = StateGraph(PolicyAgentState)

    # Add nodes
    graph.add_node("gather_sources", node_gather_sources)
    graph.add_node("llm_research", node_llm_research)
    graph.add_node("format_report", node_format_report)
    graph.add_node("handle_error", node_handle_error)

    # Set entry point
    graph.set_entry_point("gather_sources")

    # Add edges
    graph.add_conditional_edges(
        "gather_sources",
        route_after_gather,
        {
            "llm_research": "llm_research",
            "handle_error": "handle_error"
        }
    )

    graph.add_conditional_edges(
        "llm_research",
        route_after_research,
        {
            "format_report": "format_report",
            "handle_error": "handle_error"
        }
    )

    graph.add_edge("format_report", END)
    graph.add_edge("handle_error", END)

    compiled = graph.compile()
    logger.info("Agent 2 graph compiled successfully")
    return compiled


# ============================================
# SECTION 7: RUN THE AGENT
# ============================================

def run_agent2(
    facility_state: str,
    technology: str,
    system_size_kw: float,
    naics_code: str,
    utility: str = "Unknown",
    facility_type: str = "Private Commercial"
) -> dict:
    """
    Main entry point for Agent 2.

    Args:
        facility_state: Two-letter state code
                        (from Agent 1 result)
        technology:     Energy technology type
        system_size_kw: System size in kW
        naics_code:     NAICS code
        utility:        Utility name (from Agent 1)
        facility_type:  Private/Municipal/Nonprofit

    Returns:
        dict with:
        - success: True/False
        - final_report: Formatted policy report
        - source_quality: Data freshness info
        - timestamp: When query ran
        - error: Error message if failed
    """
    logger.info(
        f"Agent 2 starting: {facility_state}, "
        f"{technology}, {system_size_kw} kW"
    )

    try:
        # Build initial state
        initial_state: PolicyAgentState = {
            "facility_state": facility_state.upper().strip(),
            "technology": technology,
            "system_size_kw": system_size_kw,
            "naics_code": naics_code,
            "utility": utility,
            "facility_type": facility_type,
            "authoritative_sources": None,
            "stable_facts": None,
            "search_queries": None,
            "naics_context": None,
            "source_freshness": None,
            "rps_findings": None,
            "net_metering_findings": None,
            "interconnection_findings": None,
            "incentive_findings": None,
            "raw_llm_research": None,
            "final_report": None,
            "error": None,
            "error_node": None
        }

        graph = create_agent2_graph()
        final_state = graph.invoke(initial_state)

        success = final_state.get("error") is None

        logger.info(
            f"Agent 2 complete. Success: {success}"
        )

        return {
            "success": success,
            "agent": "agent2_policy",
            "facility_state": facility_state,
            "technology": technology,
            "system_size_kw": system_size_kw,
            "naics_code": naics_code,
            "utility": utility,
            "final_report": final_state.get(
                "final_report", ""
            ),
            "source_quality": final_state.get(
                "source_freshness", {}
            ),
            "timestamp": datetime.now().isoformat(),
            "error": final_state.get("error")
        }

    except Exception as e:
        logger.error(f"Agent 2 exception: {e}")
        return {
            "success": False,
            "agent": "agent2_policy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================
# SECTION 8: DISPLAY HELPER
# ============================================

def print_agent2_result(result: dict):
    """Prints Agent 2 result to terminal."""

    print("\n" + "=" * 60)
    print("  ENSITE AGENT 2: POLICY RESEARCH RESULT")
    print("  University of New Hampshire")
    print("=" * 60)

    status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
    print(f"\nStatus:     {status}")
    print(f"State:      {result.get('facility_state')}")
    print(f"Technology: {result.get('technology')}")
    print(f"Size:       {result.get('system_size_kw')} kW")
    print(f"Timestamp:  {result.get('timestamp')}")

    quality = result.get("source_quality", {})
    if quality:
        print(
            f"Data Age:   {quality.get('age_days')} days"
        )
        print(
            f"Confidence: {quality.get('confidence')}"
        )

    print("\n" + "-" * 60)
    print("POLICY REPORT:")
    print("-" * 60)
    print(result.get("final_report", "No report generated"))

    if result.get("error"):
        print(f"\n⚠️  Error: {result['error']}")

    print("=" * 60 + "\n")


# ============================================
# SECTION 9: MAIN
# ============================================

def main():
    """Tests Agent 2 with example queries."""

    print("\n" + "=" * 60)
    print("  ENSITE Agent 2: Policy Research Agent")
    print("  LangGraph Version + Ollama")
    print("  University of New Hampshire")
    print("=" * 60)

    # Test case
    result = run_agent2(
        facility_state="NH",
        technology="Solar PV",
        system_size_kw=250.0,
        naics_code="332",
        utility="Eversource Energy",
        facility_type="Private Industrial"
    )

    print_agent2_result(result)


if __name__ == "__main__":
    main()
    