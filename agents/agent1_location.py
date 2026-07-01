"""
ENSITE Agent 1: Location & Utility Identifier
=============================================
LangGraph Version — Reliable with Ollama/Mistral

Flow:
  START
    │
    ▼
  Node 1: Geocode address → lat/long
    │
    ▼ (or error handler)
  Node 2: Find utility from coordinates
    │
    ▼ (or error handler)
  Node 3: Get regulatory info from state_data.py
    │
    ▼
  Node 4: LLM writes summary
    │
    ▼
  END

Key difference from ReAct version:
  - YOUR code calls the tools at each node
  - LLM only writes the final summary
  - No parsing errors from bad LLM formatting
  - Works reliably with Ollama + Mistral/Llama

Imports from:
  config/settings.py       paths and constants
  config/state_data.py     regulatory info
  tools/geocoding.py       address to lat/long
  tools/spatial_query.py   GIS point in polygon

Author: ENSITE Project, UNH
Date: June 2026
"""

# ============================================
# SECTION 1: IMPORTS
# ============================================
import json
import logging
import requests
from datetime import datetime
from typing import TypedDict, Optional

# LangGraph imports
from langgraph.graph import StateGraph, END

# LangChain LLM
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

# Import from our project files
from config.settings import (
    NEW_ENGLAND_STATES,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL
)
from config.state_data import STATE_REGULATORY_INFO
from tools.geocoding import geocode_address
from tools.spatial_query import find_utility
from tools.spatial_query import find_dacsts
from tools.spatial_query import find_iwg

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================
# SECTION 2: DEFINE STATE
# ============================================
# AgentState is a TypedDict that defines
# exactly what data flows through the graph.
#
# Think of it as a data container that gets
# passed from node to node. Each node reads
# from it and writes back to it.
#
# Every field must be Optional because at the
# START of the graph most fields are empty.
# They get filled in as nodes run.

class AgentState(TypedDict):
    # INPUT (set at start)
    address: str                        # Facility address from user

    # SET BY NODE 1 (geocoding)
    latitude: Optional[float]      # Lat from geocoding
    longitude: Optional[float]     # Lon from geocoding
    formatted_address: Optional[str]    # Cleaned address string
    geocode_confidence: Optional[str]   # high/medium/low

    # SET BY NODE 2 (utility lookup)
    utility_name: Optional[str]         # e.g. Eversource Energy
    utility_type: Optional[str]         # e.g. municipal, investor owned, etc
    state: Optional[str]                # Two letter state code
    iso_region: Optional[str]           # ISO New England

    # SET BY NODE 3 (dac status lookup)
    DACSTS: Optional[str]               # e.g. False
    city: Optional[str]                 # e.g. Durham
    county: Optional[str]               # e.g. Strafford County
    stateabb: Optional[str]             # Two letter state code

    # SET BY NODE 4 (iwg status lookup)
    name: Optional[str]                 # Name of company/industry
    facility_a: Optional[str]           # Facility address
    naics_ni_c: Optional[str]           # NAICS Code

    # SET BY NODE 5 (regulatory info)
    regulatory_info: Optional[dict]     # From state_data.py
    puc_name: Optional[str]             # Regulator name
    puc_website: Optional[str]          # Regulator website
    energy_office: Optional[str]        # State energy office

    # SET BY NODE 6 (LLM summary)
    final_summary: Optional[str]        # LLM written summary

    # ERROR HANDLING
    error: Optional[str]                # Error message if failed
    error_node: Optional[str]           # Which node failed
    error_suggestion: Optional[str]     # How to fix it


# ============================================
# SECTION 3: DEFINE NODES
# ============================================
# Each node is a plain Python function that:
# 1. Receives the current state
# 2. Does its specific job
# 3. Returns the updated state
#
# No LLM involved until Node 6!

def node_geocode(agent_state: AgentState) -> AgentState:
    """
    NODE 1: Geocode the facility address.

    Converts street address to lat/long coordinates
    using OpenStreetMap Nominatim geocoder.

    Reads:  state["address"]
    Writes: state["latitude"]
            state["longitude"]
            state["formatted_address"]
            state["geocode_confidence"]
    """
    logger.info(f"Node 1 - Geocoding: {agent_state['address']}")

    try:
        # Call geocoding tool from tools/geocoding.py
        result = geocode_address(agent_state["address"])

        if result["success"]:
            agent_state["latitude"] = result["latitude"]
            agent_state["longitude"] = result["longitude"]
            agent_state["formatted_address"] = result.get(
                "formatted_address",
                agent_state["address"]
            )
            agent_state["geocode_confidence"] = result.get(
                "confidence", "medium"
            )
            logger.info(
                f"  Geocoded: {agent_state['latitude']}, "
                f"{agent_state['longitude']} "
                f"(confidence: {agent_state['geocode_confidence']})"
            )

        else:
            agent_state["error"] = result.get(
                "error",
                "Geocoding failed"
            )
            agent_state["error_node"] = "geocode"
            agent_state["error_suggestion"] = (
                "Try adding zip code or being more specific. "
                "Example: 105 Main Street, Durham, NH 03824"
            )
            logger.error(f"  Geocoding failed: {agent_state['error']}")

    except Exception as e:
        agent_state["error"] = f"Geocoding exception: {str(e)}"
        agent_state["error_node"] = "geocode"
        agent_state["error_suggestion"] = (
            "Check internet connection. "
            "Geocoding uses OpenStreetMap."
        )
        logger.error(f"  Geocoding exception: {e}")

    return agent_state


def node_find_utility(agent_state: AgentState) -> AgentState:
    """
    NODE 2: Find the electric utility serving
    the geocoded location.

    Performs a spatial point-in-polygon query
    against New England utility territory shapefiles.

    Reads:  state["latitude"]
            state["longitude"]
    Writes: state["utility_name"]
            state["utility_type"]
            state["state"]
            state["iso_region"]
    """
    logger.info(
        f"Node 2 - Finding utility at: "
        f"{agent_state['latitude']}, {agent_state['longitude']}"
    )

    try:
        # Call spatial query tool from tools/spatial_query.py
        result = find_utility(
            agent_state["latitude"],
            agent_state["longitude"]
        )

        if result["success"]:
            agent_state["utility_name"] = result.get(
                "utility_name", "Unknown"
            )
            agent_state["utility_type"] = result.get(
                "utility_type", "Unknown"
            )
            agent_state["state"] = result.get(
                "state", "Unknown"
            )
            agent_state["iso_region"] = result.get(
                "iso_region",
                "ISO New England (ISO-NE)"
            )
            logger.info(
                f"  Found utility: {agent_state['utility_name']} "
                f"({agent_state['state']})"
            )

        else:
            agent_state["error"] = result.get(
                "error",
                "Utility not found for these coordinates"
            )
            agent_state["error_node"] = "find_utility"
            agent_state["error_suggestion"] = (
                "Location may be on a utility boundary. "
                "Try a nearby address or contact the "
                "state PUC directly."
            )
            logger.error(
                f"  Utility not found: {agent_state['error']}"
            )

    except Exception as e:
        agent_state["error"] = f"Utility lookup exception: {str(e)}"
        agent_state["error_node"] = "find_utility"
        agent_state["error_suggestion"] = (
            "Check that shapefile is loaded correctly. "
            "Verify SHAPEFILE_DIR in config/settings.py"
        )
        logger.error(f"  Utility lookup exception: {e}")

    return agent_state

def node_find_dacsts(agent_state: AgentState) -> AgentState:
    """
    NODE 3: Find the DAC Status
    the geocoded location.

    Performs a spatial point-in-polygon query
    against DOE DAC shapefiles.

    Reads:  state["latitude"]
            state["longitude"]
    Writes: state["DACSTS"]
            state["city"]
            state["stateabb"]
    """
    logger.info(
        f"Node 3 - Finding DAC Status at: "
        f"{agent_state['latitude']}, {agent_state['longitude']}"
    )

    try:
        # Call spatial query tool from tools/spatial_query.py
        result = find_dacsts(agent_state["latitude"], agent_state["longitude"])

        if result["success"]:
            agent_state["DACSTS"] = result.get(
                "DACSTS", "Unknown"
            )
            agent_state["city"] = result.get(
                "city", "Unknown"
            )
            agent_state["stateabb"] = result.get(
                "stateabb", "Unknown"
            )
            logger.info(
                f"  Found DAC Status: {agent_state['DACSTS']} "
                f"({agent_state['state']})"
            )

        else:
            agent_state["error"] = result.get(
                "error",
                "DAC Status not found for these coordinates"
            )
            agent_state["error_node"] = "find_dacsts"
            agent_state["error_suggestion"] = (
                "Location may be on a shapefile boundary. "
                "Try a nearby address or contact the "
                "state DOE DAC Database directly."
            )
            logger.error(
                f"  Utility not found: {agent_state['error']}"
            )

    except Exception as e:
        agent_state["error"] = f"DAC lookup exception: {str(e)}"
        agent_state["error_node"] = "find_dacsts"
        agent_state["error_suggestion"] = (
            "Check that shapefile is loaded correctly. "
            "Verify SHAPEFILE_DIR in config/settings.py"
        )
        logger.error(f"  DAC Status lookup exception: {e}")

    return agent_state

def node_find_iwg(agent_state: AgentState) -> AgentState:
    """
    NODE 4: Find the IWG Status using
    formatted address.

    Performs a spatial point-in-polygon query
    to generate an address which is then
    compared against IWG database

    Reads:  state["latitude"]
            state["longitude"]
    Writes: state["name"]
            state["facility_a"]
            state["naics_ni_c"]
    """
    logger.info(
        f"Node 4 - Finding IWG Status at: "
        f"{agent_state['latitude']}, {agent_state['longitude']}"
    )

    try:
        # Call spatial query tool from tools/spatial_query.py
        result = find_iwg(
            agent_state["latitude"],
            agent_state["longitude"]
        )

        if result["success"]:
            agent_state["name"] = result.get(
                "name", "Unknown"
            )
            agent_state["facility_a"] = result.get(
                "facility_a", "Unknown"
            )
            agent_state["naics_ni_c"] = result.get(
                "naics_ni_c", "Unknown"
            )
            logger.info(
                f"  Found IWG Status: {agent_state['name']} "
            )

        else:
            agent_state["error"] = result.get(
                "error",
                "IWG Status not found for these coordinates"
            )
            agent_state["error_node"] = "find_iwg"
            agent_state["error_suggestion"] = (
                "Location may be on a shapefile boundary. "
                "Try a nearby address or search the "
                "IWG Database directly."
            )
            logger.error(
                f"  IWG Status not found: {agent_state['error']}"
            )

    except Exception as e:
        agent_state["error"] = f"IWG lookup exception: {str(e)}"
        agent_state["error_node"] = "find_iwg"
        agent_state["error_suggestion"] = (
            "Check that shapefile is loaded correctly. "
            "Verify SHAPEFILE_DIR in config/settings.py"
        )
        logger.error(f"  IWG Status lookup exception: {e}")

    return agent_state

def node_get_regulatory_info(agent_state: AgentState) -> AgentState:
    """
    NODE 5: Get regulatory agency contacts and
    policy context for the identified state.

    Reads directly from config/state_data.py.
    No API call or LLM needed!

    Reads:  state["state"]
    Writes: state["regulatory_info"]
            state["puc_name"]
            state["puc_website"]
            state["energy_office"]
    """
    state_code = agent_state.get("state", "")
    logger.info(
        f"Node 5 - Getting regulatory info for: {state_code}"
    )

    try:
        # Pull directly from config/state_data.py
        # No LLM needed — just a dictionary lookup!
        reg_info = STATE_REGULATORY_INFO.get(state_code, {})

        if reg_info:
            agent_state["regulatory_info"] = reg_info
            agent_state["puc_name"] = reg_info.get(
                "puc_name", "Unknown"
            )
            agent_state["puc_website"] = reg_info.get(
                "puc_website", "Unknown"
            )
            agent_state["energy_office"] = reg_info.get(
                "energy_office", "Unknown"
            )
            logger.info(
                f"  Regulator: {agent_state['puc_name']}"
            )

        else:
            # Not a critical error — we can still
            # produce a partial result without reg info
            logger.warning(
                f"  No regulatory info for state: {state_code}"
            )
            agent_state["regulatory_info"] = {}
            agent_state["puc_name"] = (
                f"See state PUC website for {state_code}"
            )
            agent_state["puc_website"] = "dsireusa.org"
            agent_state["energy_office"] = (
                f"See state energy office for {state_code}"
            )

    except Exception as e:
        # Non-critical — log but do not set error state
        # We can still produce output without reg info
        logger.warning(
            f"  Regulatory info exception: {e}"
        )
        agent_state["regulatory_info"] = {}

    return agent_state


def node_llm_summary(agent_state: AgentState) -> AgentState:
    """
    NODE 6: Use LLM to write a clear, professional
    summary of the utility identification results.

    This is the ONLY node that uses the LLM.
    All data has already been collected by nodes 1-3.
    The LLM just formats it into readable text.

    Because we are NOT asking the LLM to call tools
    or follow a strict format, even smaller models
    like Llama 3.2 work reliably here.

    Reads:  All state fields set by nodes 1-3
    Writes: state["final_summary"]
    """
    logger.info("Node 6 - Generating LLM summary")

    try:
        # Connect to Ollama
        llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0,
            timeout=120
        )

        # Build prompt with all collected data
        # The LLM receives everything it needs —
        # no tool calling required!
        prompt = f"""You are writing a utility identification
report for the ENSITE system at the University of New Hampshire.

Here is the data that has been collected:

FACILITY INFORMATION:
- Input Address: {agent_state.get('address', 'Unknown')}
- Formatted Address: {agent_state.get('formatted_address', 'Unknown')}
- Coordinates: {agent_state.get('latitude')}, {agent_state.get('longitude')}
- Geocode Confidence: {agent_state.get('geocode_confidence', 'Unknown')}

UTILITY IDENTIFICATION:
- Electric Utility: {agent_state.get('utility_name', 'Unknown')}
- Utility Type: {agent_state.get('utility_type', 'Unknown')}
- State: {agent_state.get('state', 'Unknown')} \
({agent_state.get('state', '')})
- ISO/RTO Region: {agent_state.get('iso_region', 'ISO New England')}

REGULATORY CONTACTS:
- Primary Regulator: {agent_state.get('puc_name', 'Unknown')}
- Regulator Website: {agent_state.get('puc_website', 'Unknown')}
- State Energy Office: {agent_state.get('energy_office', 'Unknown')}

ADDITIONAL REGULATORY DETAILS:
{json.dumps(agent_state.get('regulatory_info', {}), indent=2)}

Please write a clear professional summary of these results
formatted as an ENSITE utility identification report.

Include these sections:
1. Facility Location Summary (2-3 sentences)
2. Electric Utility Details
3. Regulatory Framework
4. Key Policy Notes for this State
5. Recommended Next Steps

Keep the tone professional and factual.
Flag any unknown or missing data clearly.
"""

        response = llm.invoke([HumanMessage(content=prompt)])
        agent_state["final_summary"] = response.content
        logger.info("  LLM summary generated successfully")

    except Exception as e:
        # If LLM fails, build a plain text summary
        # from the collected data instead
        logger.error(f"  LLM summary failed: {e}")
        logger.info("  Building plain text summary instead")

        agent_state["final_summary"] = f"""
ENSITE AGENT 1 RESULT
=====================
Address:    {agent_state.get('formatted_address', agent_state.get('address'))}
Utility:    {agent_state.get('utility_name', 'Unknown')}
State:      {agent_state.get('state', 'Unknown')}
ISO Region: {agent_state.get('iso_region', 'ISO New England')}
Regulator:  {agent_state.get('puc_name', 'Unknown')}
Website:    {agent_state.get('puc_website', 'Unknown')}

Note: LLM summary unavailable ({str(e)})
Data above was collected directly from
geocoding and shapefile sources.
"""

    return agent_state


def node_handle_error(agent_state: AgentState) -> AgentState:
    """
    ERROR NODE: Handles failures gracefully.

    Called when any node sets state["error"].
    Builds a helpful error message with
    suggestions for the user.

    Reads:  state["error"]
            state["error_node"]
            state["error_suggestion"]
    Writes: state["final_summary"]
    """
    error = agent_state.get("error", "Unknown error")
    error_node = agent_state.get("error_node", "Unknown step")
    suggestion = agent_state.get(
        "error_suggestion",
        "Please check your input and try again"
    )

    logger.error(
        f"Error handler called. "
        f"Failed at: {error_node}. "
        f"Error: {error}"
    )

    agent_state["final_summary"] = f"""
ENSITE AGENT 1 — ANALYSIS INCOMPLETE
======================================
Address:      {agent_state.get('address', 'Unknown')}
Failed at:    {error_node}
Error:        {error}

Suggestion:   {suggestion}

PARTIAL RESULTS COLLECTED:
- Coordinates:  {agent_state.get('latitude')}, {agent_state.get('longitude')}
- Utility:      {agent_state.get('utility_name', 'Not identified')}
- State:        {agent_state.get('state', 'Not identified')}

Please verify your input and try again, or contact
Matt Davis at Matt.Davis@unh.edu for assistance.
"""

    return agent_state


# ============================================
# SECTION 4: ROUTING FUNCTIONS
# ============================================
# These functions decide which node to go to
# next based on the current state.
# This is where branching logic lives.

def route_after_geocode(agent_state: AgentState) -> str:
    """
    After geocoding, decide what to do next.
    If geocoding failed → go to error handler
    If geocoding succeeded → find the utility
    """
    if agent_state.get("error"):
        logger.info("Routing: geocode → handle_error")
        return "handle_error"
    logger.info("Routing: geocode → find_utility")
    return "find_utility"


def route_after_find_utility(agent_state: AgentState) -> str:
    """
    After utility lookup, decide what to do next.
    If lookup failed → go to error handler
    If lookup succeeded → get regulatory info
    """
    if agent_state.get("error"):
        logger.info("Routing: find_utility → handle_error")
        return "handle_error"
    logger.info("Routing: find_utility → get_regulatory_info")
    return "get_regulatory_info"


# ============================================
# SECTION 5: BUILD THE GRAPH
# ============================================

def create_agent1_graph():
    """
    Builds and compiles the Agent 1 LangGraph.

    Graph structure:
    geocode → find_utility → get_regulatory_info
                                      → llm_summary → END
    (errors route to handle_error → END)

    Returns:
        Compiled LangGraph ready to invoke
    """
    logger.info("Building Agent 1 LangGraph")

    # Create the graph with our state definition
    graph = StateGraph(AgentState)

    # ----------------------------------------
    # Add nodes
    # Each node is a Python function defined above
    # ----------------------------------------
    graph.add_node("geocode", node_geocode)
    graph.add_node("find_utility", node_find_utility)
    graph.add_node("get_regulatory_info", node_get_regulatory_info)
    graph.add_node("llm_summary", node_llm_summary)
    graph.add_node("handle_error", node_handle_error)

    # ----------------------------------------
    # Set entry point
    # This is where the graph starts
    # ----------------------------------------
    graph.set_entry_point("geocode")

    # ----------------------------------------
    # Add edges
    # These define how nodes connect to each other
    # ----------------------------------------

    # After geocoding: check for errors
    graph.add_conditional_edges(
        "geocode",              # From this node
        route_after_geocode,    # Call this function
        {                       # Map return values to nodes
            "find_utility": "find_utility",
            "handle_error": "handle_error"
        }
    )

    # After finding utility: check for errors
    graph.add_conditional_edges(
        "find_utility",
        route_after_find_utility,
        {
            "get_regulatory_info": "get_regulatory_info",
            "handle_error": "handle_error"
        }
    )

    # After regulatory info: always go to LLM summary
    # No error check here — reg info failure is non-critical
    graph.add_edge("get_regulatory_info", "llm_summary")

    # Both success and error paths end at END
    graph.add_edge("llm_summary", END)
    graph.add_edge("handle_error", END)

    # Compile and return
    compiled = graph.compile()
    logger.info("Agent 1 graph compiled successfully")
    return compiled


# ============================================
# SECTION 6: RUN THE AGENT
# ============================================

def run_agent1(address: str) -> dict:
    """
    Main entry point for Agent 1.

    Args:
        address: Facility street address
                 Include city, state, and zip
                 for best results

    Returns:
        dict with:
        - success: True/False
        - address: Input address
        - utility_name: Identified utility
        - state: Two letter state code
        - iso_region: ISO New England
        - output: Full LLM written summary
        - raw_state: Complete graph state
        - timestamp: When query ran
        - error: Error message if failed
    """
    logger.info(f"Agent 1 starting: {address}")

    try:
        # Build initial state
        # Only address is set — everything else is None
        initial_state: AgentState = {
            "address": address,
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "geocode_confidence": None,
            "utility_name": None,
            "utility_type": None,
            "state": None,
            "iso_region": None,
            "regulatory_info": None,
            "puc_name": None,
            "puc_website": None,
            "energy_office": None,
            "final_summary": None,
            "error": None,
            "error_node": None,
            "error_suggestion": None
        }

        # Create and run the graph
        graph = create_agent1_graph()
        final_state = graph.invoke(initial_state)

        # Determine success
        success = (
            final_state.get("error") is None and
            final_state.get("utility_name") is not None
        )

        logger.info(
            f"Agent 1 complete. "
            f"Success: {success}. "
            f"Utility: {final_state.get('utility_name')}"
        )

        return {
            "success": success,
            "agent": "agent1_location",
            "address": address,
            "utility_name": final_state.get("utility_name"),
            "utility_type": final_state.get("utility_type"),
            "state": final_state.get("state"),
            "iso_region": final_state.get("iso_region"),
            "latitude": final_state.get("latitude"),
            "longitude": final_state.get("longitude"),
            "puc_name": final_state.get("puc_name"),
            "puc_website": final_state.get("puc_website"),
            "output": final_state.get("final_summary", ""),
            "raw_state": final_state,
            "timestamp": datetime.now().isoformat(),
            "llm_provider": f"ollama/{OLLAMA_MODEL}",
            "error": final_state.get("error")
        }

    except Exception as e:
        logger.error(f"Agent 1 exception: {e}")
        return {
            "success": False,
            "agent": "agent1_location",
            "address": address,
            "output": "",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "suggestion": (
                f"Check Ollama is running at {OLLAMA_BASE_URL}. "
                f"Verify {OLLAMA_MODEL} is pulled."
            )
        }


# ============================================
# SECTION 7: DISPLAY HELPER
# ============================================

def print_result(result: dict):
    """Prints Agent 1 result to terminal."""

    print("\n" + "=" * 60)
    print("  ENSITE AGENT 1: LOCATION & UTILITY RESULT")
    print("  University of New Hampshire")
    print("=" * 60)

    status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
    print(f"\nStatus:    {status}")
    print(f"Address:   {result['address']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"LLM:       {result.get('llm_provider', 'Unknown')}")

    if result["success"]:
        print(f"\nUtility:   {result.get('utility_name')}")
        print(f"State:     {result.get('state')}")
        print(f"ISO:       {result.get('iso_region')}")
        print(f"Regulator: {result.get('puc_name')}")

    print("\n" + "-" * 60)
    print("FULL REPORT:")
    print("-" * 60)
    print(result.get("output", "No output generated"))

    if result.get("error"):
        print(f"\n⚠️  Error: {result['error']}")

    print("=" * 60 + "\n")


# ============================================
# SECTION 8: VISUALIZE THE GRAPH (OPTIONAL)
# ============================================

def visualize_graph():
    """
    Prints a text representation of the graph.
    Useful for understanding and debugging.
    """
    print("\n" + "=" * 60)
    print("AGENT 1 GRAPH STRUCTURE")
    print("=" * 60)
    print("""
    START
      │
      ▼
  ┌─────────────────────────────────┐
  │  NODE 1: geocode                │
  │  tools/geocoding.py             │
  │  address → lat/long             │
  └──────────────┬──────────────────┘
                 │
         ┌───────┴───────┐
         │               │
      success           error
         │               │
         ▼               ▼
  ┌────────────┐  ┌──────────────────┐
  │  NODE 2:   │  │  ERROR NODE:     │
  │  find_     │  │  handle_error    │
  │  utility   │  │  Builds helpful  │
  │  GIS query │  │  error message   │
  └─────┬──────┘  └────────┬─────────┘
        │                  │
    ┌───┴───┐              │
    │       │              │
 success  error            │
    │       │              │
    ▼       └──────────────┤
  ┌─────────────────────┐  │
  │  NODE 3:            │  │
  │  get_regulatory_    │  │
  │  info               │  │
  │  config/state_data  │  │
  └──────────┬──────────┘  │
             │              │
             ▼              │
  ┌─────────────────────┐  │
  │  NODE 4:            │  │
  │  llm_summary        │  │
  │  Ollama/Mistral     │  │
  │  writes report      │  │
  └──────────┬──────────┘  │
             │              │
             └──────┬───────┘
                    │
                    ▼
                   END
    """)
    print("=" * 60)


# ============================================
# SECTION 9: MAIN
# ============================================

def main():
    """
    Tests Agent 1 LangGraph with example addresses.
    """

    print("\n" + "=" * 60)
    print("  ENSITE Agent 1: Location & Utility Identifier")
    print("  LangGraph Version + Ollama")
    print("  University of New Hampshire")
    print("=" * 60)

    # Show graph structure
    visualize_graph()

    # Verify Ollama is running
    print("\n🔍 Checking Ollama...")
    try:
        response = requests.get(OLLAMA_BASE_URL, timeout=5)
        if "Ollama is running" in response.text:
            print(f"✅ Ollama running at {OLLAMA_BASE_URL}")
            print(f"✅ Model: {OLLAMA_MODEL}")
        else:
            print("⚠️  Unexpected Ollama response")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama")
        print(f"   Check: {OLLAMA_BASE_URL} in browser")
        return

    # Test addresses
    test_addresses = [
        "105 Main Street, Durham, NH 03824",
        "100 Main Street, Berlin, NH 03570",
        "123 Congress Street, Portland, ME 04101"
    ]

    for i, address in enumerate(test_addresses, 1):
        print(f"\n{'─' * 60}")
        print(f"TEST {i}/{len(test_addresses)}: {address}")
        print("─" * 60)
        print("Running... (20-60 seconds with Ollama)")

        result = run_agent1(address)
        print_result(result)

        if i < len(test_addresses):
            input("Press Enter for next test...")

    # Interactive mode
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE — Type 'quit' to exit")
    print("=" * 60)

    while True:
        address = input(
            "\nEnter facility address: "
        ).strip()

        if address.lower() in ["quit", "exit", "q", ""]:
            print("\nGoodbye!")
            break

        print("\nRunning analysis...")
        result = run_agent1(address)
        print_result(result)


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    main()