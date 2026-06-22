"""
tests/test_nodes.py
=============================================
Tests each Agent 1 LangGraph node individually.
Run this to verify each piece works before
running the full agent.

Usage:
    python tests/test_nodes.py

Author: ENSITE Project, UNH
Date: June 2026
"""

import sys
import os

# Add project root to Python path
# This ensures imports work correctly
# when running from the tests/ folder
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from agents.agent1_location import (
    node_geocode,
    node_find_utility,
    node_get_regulatory_info,
    node_llm_summary
)
from tools.spatial_query import get_shapefile_info

# ============================================
# BLANK STATE TEMPLATE
# Copy this for each test
# ============================================
def blank_state():
    """Returns a fresh empty AgentState."""
    return {
        "address": "",
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


def print_test_header(test_name: str):
    print(f"\n{'─' * 55}")
    print(f"TEST: {test_name}")
    print(f"{'─' * 55}")


def print_result(label: str, value, expected=None):
    if expected is not None:
        passed = str(value).lower() != "none" and value is not None
        icon = "✅" if passed else "❌"
    else:
        icon = "📋"
    print(f"  {icon} {label}: {value}")


# ============================================
# PRE-FLIGHT CHECK
# ============================================
def test_shapefile_diagnostic():
    """Check shapefile before running node tests."""
    print_test_header("Pre-flight: Shapefile Diagnostic")

    info = get_shapefile_info()

    print(f"  📁 Path:    {info['path']}")
    print(f"  📄 Exists:  {info['exists']}")

    if not info["exists"]:
        print(
            f"\n  ❌ SHAPEFILE NOT FOUND!"
            f"\n  Expected: {info['path']}"
            f"\n  Fix: Copy your shapefile to that location"
            f"\n  Skipping spatial tests."
        )
        return False

    if info["loaded"]:
        print(f"  📊 Rows:    {info['row_count']}")
        print(f"  🗂️  Columns: {info['columns']}")
        print(f"  🌐 CRS:     {info['crs']}")
        print(f"  ✅ Shapefile loaded successfully")
        return True

    return False


# ============================================
# NODE 1 TEST
# ============================================
def test_node_geocode():
    """Tests Node 1: Geocoding."""
    print_test_header("Node 1: Geocode Address")

    state = blank_state()
    state["address"] = "105 Main Street, Durham, NH 03824"

    print(f"  Input address: {state['address']}")
    print("  Running node_geocode()...")

    result = node_geocode(state)

    print_result("Latitude", result["latitude"], expected=True)
    print_result("Longitude", result["longitude"], expected=True)
    print_result("Formatted address", result["formatted_address"])
    print_result("Confidence", result["geocode_confidence"])
    print_result("Error", result["error"])

    if result["latitude"] and result["longitude"]:
        print(f"\n  ✅ Node 1 PASSED")
        # Sanity check coordinates
        # Durham NH should be around 43.1N, 70.9W
        lat_ok = 43.0 <= result["latitude"] <= 43.3
        lon_ok = -71.1 <= result["longitude"] <= -70.8
        if lat_ok and lon_ok:
            print(f"  ✅ Coordinates look correct for Durham NH")
        else:
            print(
                f"  ⚠️  Coordinates may be wrong for Durham NH"
                f"\n     Expected: ~43.13N, ~70.93W"
                f"\n     Got: {result['latitude']}N, "
                f"{abs(result['longitude'])}W"
            )
        return result
    else:
        print(f"\n  ❌ Node 1 FAILED")
        print(f"  Error: {result['error']}")
        return None


# ============================================
# NODE 2 TEST
# ============================================
def test_node_find_utility(geocoded_state=None):
    """Tests Node 2: Utility identification."""
    print_test_header("Node 2: Find Utility")

    if geocoded_state is None:
        # Use known coordinates for Durham NH
        # if geocoding was not run first
        print("  Using hardcoded Durham NH coordinates")
        state = blank_state()
        state["address"] = "105 Main Street, Durham, NH 03824"
        state["latitude"] = 43.1348
        state["longitude"] = -70.9234
    else:
        state = geocoded_state

    print(
        f"  Input coordinates: "
        f"{state['latitude']}, {state['longitude']}"
    )
    print("  Running node_find_utility()...")

    result = node_find_utility(state)

    print_result("Utility name", result["utility_name"], expected=True)
    print_result("Utility type", result["utility_type"])
    print_result("State", result["state"], expected=True)
    print_result("ISO region", result["iso_region"])
    print_result("Error", result["error"])

    if result["utility_name"] and result["state"]:
        print(f"\n  ✅ Node 2 PASSED")
        # Sanity check for Durham NH
        if "eversource" in str(result["utility_name"]).lower():
            print(f"  ✅ Correct utility for Durham NH (Eversource)")
        else:
            print(
                f"  ⚠️  Unexpected utility: {result['utility_name']}"
                f"\n     Expected Eversource for Durham NH"
            )
        return result
    else:
        print(f"\n  ❌ Node 2 FAILED")
        print(f"  Error: {result.get('error')}")
        print(
            f"\n  Common causes:"
            f"\n  1. Shapefile not found"
            f"\n  2. Missing 'global _utility_gdf' in spatial_query.py"
            f"\n  3. Column names in shapefile do not match expected"
            f"\n  4. Coordinates outside shapefile coverage"
        )
        return None


# ============================================
# NODE 3 TEST
# ============================================
def test_node_regulatory_info(utility_state=None):
    """Tests Node 3: Regulatory info lookup."""
    print_test_header("Node 3: Get Regulatory Info")

    if utility_state is None:
        print("  Using hardcoded NH state")
        state = blank_state()
        state["state"] = "NH"
    else:
        state = utility_state

    print(f"  Input state: {state['state']}")
    print("  Running node_get_regulatory_info()...")

    result = node_get_regulatory_info(state)

    print_result("PUC name", result["puc_name"], expected=True)
    print_result("PUC website", result["puc_website"])
    print_result("Energy office", result["energy_office"])
    print_result(
        "Regulatory info keys",
        list(result["regulatory_info"].keys())
        if result["regulatory_info"] else "None"
    )

    if result["puc_name"]:
        print(f"\n  ✅ Node 3 PASSED")
        return result
    else:
        print(f"\n  ❌ Node 3 FAILED")
        print(
            f"  Check config/state_data.py has "
            f"STATE_REGULATORY_INFO['NH']"
        )
        return None


# ============================================
# NODE 4 TEST
# ============================================
def test_node_llm_summary(reg_state=None):
    """Tests Node 4: LLM summary generation."""
    print_test_header("Node 4: LLM Summary")
    print("  Note: This requires Ollama to be running")
    print("  Check: http://localhost:11434 in browser")

    if reg_state is None:
        print("  Using hardcoded test data")
        state = blank_state()
        state["address"] = "105 Main Street, Durham, NH 03824"
        state["latitude"] = 43.1348
        state["longitude"] = -70.9234
        state["formatted_address"] = "105 Main St, Durham, NH 03824"
        state["utility_name"] = "Eversource Energy"
        state["utility_type"] = "Unknown"
        state["state"] = "NH"
        state["iso_region"] = "ISO New England (ISO-NE)"
        state["puc_name"] = "NH Public Utilities Commission"
        state["puc_website"] = "puc.nh.gov"
        state["energy_office"] = "NH Department of Energy"
        state["regulatory_info"] = {
            "puc_name": "NH Public Utilities Commission",
            "puc_website": "puc.nh.gov"
        }
    else:
        state = reg_state

    print("  Running node_llm_summary()...")
    print("  (This may take 20-60 seconds with Ollama)")

    result = node_llm_summary(state)

    if result["final_summary"]:
        preview = result["final_summary"][:150].replace("\n", " ")
        print(f"\n  Summary preview: {preview}...")
        print(f"\n  ✅ Node 4 PASSED")
        return result
    else:
        print(f"\n  ❌ Node 4 FAILED")
        print(
            f"  Check Ollama is running at "
            f"http://localhost:11434"
        )
        return None


# ============================================
# MAIN TEST RUNNER
# ============================================
def main():
    print("\n" + "=" * 55)
    print("  ENSITE Agent 1 Node Tests")
    print("  University of New Hampshire")
    print("=" * 55)

    results = {
        "preflight": False,
        "node1": False,
        "node2": False,
        "node3": False,
        "node4": False
    }

    # Pre-flight check
    shapefile_ok = test_shapefile_diagnostic()
    results["preflight"] = shapefile_ok

    # Node 1: Geocoding
    geocoded = test_node_geocode()
    results["node1"] = geocoded is not None

    # Node 2: Utility lookup
    # Only run if shapefile is available
    if shapefile_ok:
        utility = test_node_find_utility(geocoded)
        results["node2"] = utility is not None
    else:
        print("\n⏭️  Skipping Node 2 — shapefile not found")
        utility = None

    # Node 3: Regulatory info
    # Runs regardless of shapefile

    reg_info = test_node_regulatory_info(utility)
    results["node3"] = reg_info is not None

    # Node 4: LLM summary
    # Ask user before running (takes time)

    print("\n" + "─" * 55)
    run_llm = input(
        "Run Node 4 LLM test? "
        "Requires Ollama (yes/no): "
    ).strip().lower()

    if run_llm == "yes":
        llm_result = test_node_llm_summary(reg_info)
        print('llm result')
        print(llm_result)
        results["node4"] = llm_result is not None
    else:
        print("  ⏭️  Skipping Node 4 LLM test")

    # Summary
    print("\n" + "=" * 55)
    print("TEST SUMMARY")
    print("=" * 55)

    labels = {
        "preflight": "Shapefile diagnostic",
        "node1": "Node 1: Geocoding",
        "node2": "Node 2: Utility lookup",
        "node3": "Node 3: Regulatory info",
        "node4": "Node 4: LLM summary"
    }

    passed = 0
    for key, label in labels.items():
        status = "✅ PASS" if results[key] else "❌ FAIL"
        print(f"  {status}  {label}")
        if results[key]:
            passed += 1

    print(f"\n  {passed}/{len(results)} tests passed")

    if not results["node2"] and shapefile_ok:
        print(
            f"\n⚠️  Node 2 failed with shapefile present."
            f"\n   Most likely cause: missing 'global _utility_gdf'"
            f"\n   in tools/spatial_query.py _load_shapefile() function"
            f"\n   Check the fix in the corrected spatial_query.py"
        )

    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()