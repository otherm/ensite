"""
ENSITE Source Trust Hierarchy
Implements the data quality framework from requirements document
"""

SOURCE_TIERS = {
    "tier1": {
        "name": "Primary Sources",
        "trust_score_range": (95, 100),
        "max_age_days": 30,
        "sources": [
            "energy.nh.gov",
            "puc.nh.gov",
            "maine.gov/mpuc",
            "maine.gov/energy",
            "puc.vermont.gov",
            "mass.gov/dpu",
            "portal.ct.gov/pura",
            "portal.ct.gov/deep",
            "ripuc.ri.gov",
            "energy.ri.gov",
            "dsireusa.org",
            "afdc.energy.gov",
            "irs.gov",
            "eversource.com",
            "greenmountainpower.com",
            "nationalgridus.com",
        ]
    },
    "tier2": {
        "name": "Specialized Industry Sources",
        "trust_score_range": (75, 94),
        "max_age_days": 60,
        "sources": [
            "nrel.gov",
            "masscec.com",
            "efficiencymaine.com",
            "veic.org",
            "iso-ne.com",
            "energysage.com",
        ]
    },
    "tier3": {
        "name": "General Consumer Sources",
        "trust_score_range": (50, 74),
        "max_age_days": 90,
        "sources": [
            "thisoldhouse.com",
            "forbes.com",
            "cnet.com",
        ]
    }
}

def get_source_tier(url: str) -> str:
    """Returns the tier for a given URL."""
    for tier, data in SOURCE_TIERS.items():
        for source in data["sources"]:
            if source in url:
                return tier
    return "tier3"  # Default to lowest tier if unknown

def get_trust_score(url: str) -> int:
    """Returns a trust score for a given URL."""
    tier = get_source_tier(url)
    score_range = SOURCE_TIERS[tier]["trust_score_range"]
    return score_range[0]  # Return minimum score for tier