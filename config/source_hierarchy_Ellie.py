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
            "portal.ct.gov/pura",
            "portal.ct.gov/deep",
            "energy.ri.gov",
            "dsireusa.org",
            "eversource.com",
            "masscec.com",
            "efficiencymaine.com",
            "pacenation.org",
            "energysaver.vermont.gov",
            "openei.org/wiki/Vermont/EZ_Policies",
            "greenmountainpower.com",
            "nationalgridus.com",
        ]
    },
    "tier2": {
        "name": "Specialized Industry Sources",
        "trust_score_range": (75, 94),
        "max_age_days": 60,
        "sources": [
            "maine.gov/mpuc",
            "maine.gov/energy",
            "puc.vermont.gov",
            "mass.gov/dpu",
            "ripuc.ri.gov",
            "afdc.energy.gov",
            "irs.gov/credits-deductions/clean-vehicle-and-energy-credits",
            "iso-ne.com",
            "energysage.com",
        ]
    },
    "tier3": {
        "name": "General Consumer Sources",
        "trust_score_range": (50, 74),
        "max_age_days": 90,
        "sources": [
            "veic.org",
            "forbes.com",
            "cnet.com",
            "pv-magazine.com",
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
