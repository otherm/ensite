"""
ENSITE Application Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHAPEFILE_PATH = os.path.join(BASE_DIR, "data", "shapefiles")
#POLICY_DOCS_PATH = os.path.join(BASE_DIR, "data", "policy_docs")
#CACHE_PATH = os.path.join(BASE_DIR, "data", "cache")
#OUTPUTS_PATH = os.path.join(BASE_DIR, "outputs")

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