"""
ENSITE Application Settings
"""

# ============================================
# SILENCE TENSORFLOW WARNINGS
# Must be set BEFORE any tensorflow imports
# ============================================
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from config.suppress_warnings import *

# Silence oneDNN floating point warning
# Safe for ENSITE - we do not need this precision
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Silence all TensorFlow info messages
# 0=all, 1=info, 2=warnings, 3=errors only
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Silence absl (Google's logging library)
# used internally by TensorFlow
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"

# ============================================
# API Configuration
# ============================================
# Use DeepThought (USNH approved) or Azure OpenAI
#LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure")  # "azure" or "deepthought"
#LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
#LLM_TEMPERATURE = 0  # 0 = deterministic, best for factual tasks

# DeepThought (USNH platform)
#DEEPTHOUGHT_API_KEY = os.getenv("DEEPTHOUGHT_API_KEY")
#DEEPTHOUGHT_BASE_URL = os.getenv("DEEPTHOUGHT_BASE_URL")

# DSIRE API
#DSIRE_API_KEY = os.getenv("DSIRE_API_KEY")
#DSIRE_BASE_URL = "https://api.dsireusa.org/v1"

# ============================================
# Data Paths
# ============================================

"""
ENSITE Application Settings
config/settings.py
=============================================
Single source of truth for all configuration.

All other ENSITE files should import from here.
No other file should call load_dotenv() or
use os.getenv() directly.

Current LLM Configuration:
  Provider:  Ollama (local development)
  Model:     Mistral or Llama 3.2
  Framework: LangChain + LangGraph

Planned Production Configuration:
  Provider:  DeepThought AI (USNH Platform)
  Details:   Pending confirmation from USNH IT

Usage in other files:
    from config.settings import SHAPEFILE_DIR
    from config.settings import OLLAMA_MODEL
    from config.settings import NEW_ENGLAND_STATES
    from config.settings import validate_settings

Author: ENSITE Project, UNH
Date: June 2026
"""

# ============================================
# STEP 1: LOAD .env FILE
# Must happen before any os.getenv() calls.
# Only called here — never in other files!
# ============================================
load_dotenv()

# ============================================
# STEP 2: SET UP LOGGING
# Configure once here so all modules use
# the same logging format automatically
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# ============================================
# STEP 3: BASE DIRECTORY
# Path(__file__) = this file (settings.py)
# .parent        = config/ folder
# .parent        = project root (ensite/)
#
# Using Path() instead of strings means this
# works correctly on Windows, Mac, and Linux
# regardless of where the project is located
# ============================================
#BASE_DIR = Path(__file__).parent.parent

# ============================================
# STEP 4: DIRECTORY PATHS
# These point to FOLDERS.
# Use these when you need to build a path
# to a specific file inside the folder.
#
# Example:
#   shapefile = SHAPEFILE_DIR / "myfile.shp"
#   doc = POLICY_DOCS_DIR / "policy.pptx"
# ============================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHAPEFILE_DIR = os.path.join(BASE_DIR, "data", "shapefiles")
POLICY_DOCS_DIR = os.path.join(BASE_DIR, "data", "policy_docs")
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
# ============================================
# STEP 5: SPECIFIC FILE PATHS
# These point to known FILES.
# Use these when you need a specific file
# that is always in the same location.
#
# NOTE: We do NOT define a single SHAPEFILE_PATH
# because you may have multiple shapefiles.
# Build shapefile paths in your code like this:
#   utility_shp = SHAPEFILE_DIR / "New_England_Electric_Utilitiesv2a.shp"
# ============================================
POLICY_DOCUMENT_PATH = os.path.join(POLICY_DOCS_DIR, "Policy_Landscape_updated_12.13.24.pptx")

# ============================================
# STEP 6: LLM CONFIGURATION
# ============================================

# ------------------------------------------
# CURRENT: Ollama (local development)
# Free, private, no API key needed.
# Runs entirely on your PC.
# Data never leaves your machine.
# USNH policy compliant for development.
# ------------------------------------------

# Which Ollama model to use.
# Options tested with LangChain ReAct/LangGraph:
#   "mistral"      Best balance - recommended
#   "mistral-nemo" Best ReAct format following
#   "llama3.1:8b"  Better than 3.2 for agents
#   "qwen2.5:7b"   Good instruction following
#   "llama3.2"     Baseline - inconsistent ReAct
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Ollama server URL.
# Default is localhost:11434.
# On Windows, Ollama starts automatically
# at login so this is always available.
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

# Ollama API endpoint for completions
# Used by LangChain ChatOllama internally
OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/api"

# ------------------------------------------
# PLANNED: DeepThought AI (USNH Production)
# Pending confirmation from USNH IT.
# Contact USNH IT to get actual values for:
#   DEEPTHOUGHT_API_KEY
#   DEEPTHOUGHT_BASE_URL
#   DEEPTHOUGHT_MODEL
# ------------------------------------------
DEEPTHOUGHT_API_KEY = os.getenv(
    "DEEPTHOUGHT_API_KEY", ""
)
DEEPTHOUGHT_BASE_URL = os.getenv(
    "DEEPTHOUGHT_BASE_URL", ""
)
DEEPTHOUGHT_MODEL = os.getenv(
    "DEEPTHOUGHT_MODEL", ""
)

# ------------------------------------------
# FALLBACK: Azure OpenAI (USNH Approved)
# Available if DeepThought API not ready.
# Requires USNH Microsoft Copilot Pro license.
# ------------------------------------------
AZURE_OPENAI_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY", ""
)
AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT", ""
)
AZURE_OPENAI_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT", "gpt-4o"
)

# ------------------------------------------
# ACTIVE PROVIDER SELECTION
# Controls which LLM llm_factory.py uses.
# Set in .env file.
# Options: "ollama", "deepthought", "azure"
# ------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# LLM behavior settings
# Temperature 0 = deterministic responses
# Best for factual policy lookups
LLM_TEMPERATURE = 0.1

# Timeout in seconds for LLM responses.
# Ollama on local PC can be slow (30-120 sec)
# depending on model size and hardware.
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))

# Maximum iterations for ReAct agent loop.
# Prevents infinite loops if LLM gets stuck.
LLM_MAX_ITERATIONS = int(
    os.getenv("LLM_MAX_ITERATIONS", "10")
)

# ============================================
# STEP 7: LANGCHAIN CONFIGURATION
# Settings that affect LangChain behavior
# ============================================

# Show agent reasoning in terminal.
# True = verbose output showing each step
# False = quiet, only show final answer
# Set True during development, False in production
LANGCHAIN_VERBOSE = os.getenv(
    "LANGCHAIN_VERBOSE", "True"
).lower() == "true"

# LangSmith tracing (optional but useful for debugging)
# Sign up free at smith.langchain.com
# Leave blank to disable tracing
LANGCHAIN_TRACING_V2 = os.getenv(
    "LANGCHAIN_TRACING_V2", "false"
)
LANGCHAIN_API_KEY = os.getenv(
    "LANGCHAIN_API_KEY", ""
)
LANGCHAIN_PROJECT = os.getenv(
    "LANGCHAIN_PROJECT", "ensite-unh"
)

# Set LangChain environment variables
# LangChain reads these from os.environ directly
if LANGCHAIN_TRACING_V2 == "true" and LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT

# ============================================
# STEP 8: LANGGRAPH CONFIGURATION
# Settings specific to LangGraph agents
# ============================================

# Maximum number of steps in a LangGraph run.
# Prevents infinite loops in complex graphs.
LANGGRAPH_MAX_STEPS = int(
    os.getenv("LANGGRAPH_MAX_STEPS", "25")
)

# Whether to return intermediate steps
# in agent results. Useful for debugging.
LANGGRAPH_RETURN_INTERMEDIATE = os.getenv(
    "LANGGRAPH_RETURN_INTERMEDIATE", "True"
).lower() == "true"

# ============================================
# STEP 9: GIS CONFIGURATION
# Settings for GeoPandas and shapefile handling
# ============================================

# Coordinate reference system for all GIS operations.
# EPSG:4326 = WGS84 = standard GPS coordinates
# All shapefiles are converted to this CRS on load.
GIS_CRS = "EPSG:4326"

# New England state codes for filtering shapefiles
# Filtering to NE only makes spatial queries faster
NEW_ENGLAND_STATES = {
    "CT": "Connecticut",
    "MA": "Massachusetts",
    "ME": "Maine",
    "NH": "New Hampshire",
    "RI": "Rhode Island",
    "VT": "Vermont"
}

# FIPS codes for New England states
# Used for filtering HIFLD and Census shapefiles
NEW_ENGLAND_STATE_FIPS = {
    "CT": "09",
    "MA": "25",
    "ME": "23",
    "NH": "33",
    "RI": "44",
    "VT": "50"
}

# ISO/RTO region for all New England states
ISO_REGION = "ISO New England (ISO-NE)"

# ============================================
# STEP 10: GEOCODING CONFIGURATION
# ============================================

# Geocoding service to use.
# "nominatim" = OpenStreetMap (free, no key needed)
# "google"    = Google Maps (more accurate, needs key)
GEOCODING_SERVICE = os.getenv(
    "GEOCODING_SERVICE", "nominatim"
)

# User agent string required by Nominatim terms of service
NOMINATIM_USER_AGENT = "ensite_unh_v1"

# Google Maps API key (optional, only if using Google)
GOOGLE_MAPS_API_KEY = os.getenv(
    "GOOGLE_MAPS_API_KEY", ""
)

# Geocoding timeout in seconds
GEOCODING_TIMEOUT = int(
    os.getenv("GEOCODING_TIMEOUT", "10")
)

# ============================================
# STEP 11: DATA SOURCE CONFIGURATION
# ============================================

# DSIRE API (free incentive database)
# Register at: dsireusa.org
DSIRE_API_KEY = os.getenv("DSIRE_API_KEY", "")
DSIRE_BASE_URL = "https://api.dsireusa.org/v1"

# Data freshness rules (days) by source tier
# Used by config/source_hierarchy.py
# Tier 1 = government/official sources
# Tier 2 = industry sources
# Tier 3 = consumer sources
MAX_SOURCE_AGE_DAYS = {
    "tier1": 30,
    "tier2": 60,
    "tier3": 90
}

# Cache settings for API responses
# Avoids hitting APIs repeatedly for same data
CACHE_TTL_HOURS = int(
    os.getenv("CACHE_TTL_HOURS", "24")
)

# ============================================
# STEP 12: APP SETTINGS
# ============================================

# Debug mode
# True = verbose output, extra logging
# False = quiet production mode
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Streamlit server settings
STREAMLIT_PORT = int(
    os.getenv("STREAMLIT_PORT", "8501")
)
STREAMLIT_HOST = os.getenv(
    "STREAMLIT_HOST", "localhost"
)

# Report settings
MAX_REPORT_AGE_DAYS = int(
    os.getenv("MAX_REPORT_AGE_DAYS", "90")
)

# ============================================
# STEP 13: VALIDATION FUNCTION
# ============================================

def validate_settings() -> dict:
    """
    Checks that all critical settings are
    configured correctly.

    Call this once at application startup
    to catch configuration problems early.

    Returns:
        dict with:
        - errors: List of blocking problems
        - warnings: List of non-blocking issues
        - info: List of informational messages
        - ready: True if safe to start app
    """
    errors = []
    warnings = []
    info = []

    # ------------------------------------------
    # Check directories exist
    # ------------------------------------------
    dirs_to_check = [
        (SHAPEFILE_DIR, "Shapefile directory"),
        (POLICY_DOCS_DIR, "Policy documents directory"),
        (CACHE_DIR, "Cache directory"),
        (OUTPUTS_DIR, "Outputs directory")
    ]

    for dir_path, dir_name in dirs_to_check:
        if not dir_path.exists():
            warnings.append(
                f"{dir_name} not found: {dir_path}. "
                f"Creating it now."
            )
            # Create missing directories automatically
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            info.append(f"✅ {dir_name}: {dir_path}")

    # ------------------------------------------
    # Check shapefiles exist
    # ------------------------------------------
    expected_shapefiles = [
        "New_England_Electric_Utilitiesv2a.shp"
    ]

    for shp in expected_shapefiles:
        shp_path = SHAPEFILE_DIR / shp
        if not shp_path.exists():
            warnings.append(
                f"Shapefile not found: {shp_path}. "
                f"Download from HIFLD or check filename."
            )
        else:
            info.append(f"✅ Shapefile found: {shp}")

    # ------------------------------------------
    # Check policy document exists
    # ------------------------------------------
    if not POLICY_DOCUMENT_PATH.exists():
        warnings.append(
            f"Policy document not found: "
            f"{POLICY_DOCUMENT_PATH}"
        )
    else:
        info.append(
            f"✅ Policy document found: "
            f"{POLICY_DOCUMENT_PATH.name}"
        )

    # ------------------------------------------
    # Check LLM configuration
    # ------------------------------------------
    if LLM_PROVIDER == "ollama":
        # Check Ollama is reachable
        try:
            import requests
            response = requests.get(
                OLLAMA_BASE_URL,
                timeout=3
            )
            if "Ollama is running" in response.text:
                info.append(
                    f"✅ Ollama running at {OLLAMA_BASE_URL}"
                )
                info.append(f"✅ Model: {OLLAMA_MODEL}")
            else:
                warnings.append(
                    f"Ollama responded but with unexpected "
                    f"content at {OLLAMA_BASE_URL}"
                )
        except Exception:
            errors.append(
                f"Cannot connect to Ollama at "
                f"{OLLAMA_BASE_URL}. "
                f"Make sure Ollama is installed and running."
            )

    elif LLM_PROVIDER == "deepthought":
        if not DEEPTHOUGHT_API_KEY:
            errors.append(
                "DEEPTHOUGHT_API_KEY not set in .env. "
                "Contact USNH IT for API credentials."
            )
        if not DEEPTHOUGHT_BASE_URL:
            errors.append(
                "DEEPTHOUGHT_BASE_URL not set in .env. "
                "Contact USNH IT for API endpoint."
            )
        if not DEEPTHOUGHT_MODEL:
            errors.append(
                "DEEPTHOUGHT_MODEL not set in .env. "
                "Contact USNH IT for model name."
            )

    elif LLM_PROVIDER == "azure":
        if not AZURE_OPENAI_API_KEY:
            errors.append(
                "AZURE_OPENAI_API_KEY not set in .env"
            )
        if not AZURE_OPENAI_ENDPOINT:
            errors.append(
                "AZURE_OPENAI_ENDPOINT not set in .env"
            )

    # ------------------------------------------
    # Check optional services
    # ------------------------------------------
    if not DSIRE_API_KEY:
        warnings.append(
            "DSIRE_API_KEY not set. "
            "Incentive lookups will use cached data only. "
            "Register free at dsireusa.org"
        )

    if not GOOGLE_MAPS_API_KEY:
        info.append(
            "Google Maps API key not set. "
            "Using OpenStreetMap for geocoding (free)."
        )

    # ------------------------------------------
    # Summary
    # ------------------------------------------
    ready = len(errors) == 0

    return {
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "ready": ready,
        "llm_provider": LLM_PROVIDER,
        "llm_model": (
            OLLAMA_MODEL if LLM_PROVIDER == "ollama"
            else DEEPTHOUGHT_MODEL if LLM_PROVIDER == "deepthought"
            else AZURE_OPENAI_DEPLOYMENT
        )
    }


# ============================================
# STEP 14: STARTUP OUTPUT
# Print configuration summary when settings
# is imported (DEBUG mode only)
# ============================================
if DEBUG:
    print("\n" + "=" * 55)
    print("  ENSITE Settings Loaded")
    print("=" * 55)
    print(f"  BASE_DIR:       {BASE_DIR}")
    print(f"  SHAPEFILE_DIR:  {SHAPEFILE_DIR}")
    print(f"  POLICY_DOCS:    {POLICY_DOCS_DIR}")
    print(f"  LLM_PROVIDER:   {LLM_PROVIDER}")

    if LLM_PROVIDER == "ollama":
        print(f"  OLLAMA_MODEL:   {OLLAMA_MODEL}")
        print(f"  OLLAMA_URL:     {OLLAMA_BASE_URL}")
    elif LLM_PROVIDER == "deepthought":
        print(f"  DT_MODEL:       {DEEPTHOUGHT_MODEL}")
        print(f"  DT_URL:         {DEEPTHOUGHT_BASE_URL}")
    elif LLM_PROVIDER == "azure":
        print(f"  AZURE_DEPLOY:   {AZURE_OPENAI_DEPLOYMENT}")

    print(f"  LANGCHAIN_VERBOSE: {LANGCHAIN_VERBOSE}")
    print(f"  DEBUG:          {DEBUG}")
    print("=" * 55 + "\n")
# ============================================
# New England States
# ============================================
NEW_ENGLAND_STATES = {
    "CT": "Connecticut",
    "MA": "Massachusetts",
    "ME": "Maine",
    "NH": "New Hampshire",
    "RI": "Rhode Island",
    "VT": "Vermont"
}

# ============================================
# Data Freshness Rules
# ============================================
#CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", 24))
#MAX_SOURCE_AGE_DAYS = {
#    "tier1": 30,    # Gov sources - flag if older than 30 days
#    "tier2": 60,    # Industry sources - flag if older than 60 days
#    "tier3": 90,    # Consumer sources - flag if older than 90 days
#}