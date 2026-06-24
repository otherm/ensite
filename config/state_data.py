"""
config/state_data.py
=============================================
Stripped down version that supports LLM-driven
information retrieval rather than hardcoding
policy details that become outdated.

Philosophy:
    This file contains STRUCTURE and SOURCES
    not ANSWERS.

    The LLM agents use this file to know:
    1. WHERE to look for current information
    2. WHAT questions to ask
    3. WHO the authoritative sources are
    4. WHAT rarely-changes facts to rely on

    Everything that changes frequently
    (rates, amounts, program status, deadlines)
    is retrieved live by the LLM agents from
    the authoritative sources listed here.

Author: ENSITE Project, UNH
Date: June 2026
"""

# ============================================
# SECTION 1: AUTHORITATIVE SOURCE URLS
# ============================================
# These are the Tier 1 sources the LLM agents
# should query for current policy information.
#
# These URLs change rarely — a state PUC
# website URL is stable even when the content
# on that page changes frequently.
#
# The LLM uses these as starting points for
# web searches and document retrieval.

STATE_REGULATORY_INFO = {}

STATE_AUTHORITATIVE_SOURCES = {

    "ME": {
        "state_name": "Maine",

        # Primary regulatory sources
        # LLM should check these first
        "tier1_sources": [
            {
                "name": "Maine Public Utilities Commission",
                "url": "maine.gov/mpuc",
                "what_to_find": [
                    "Net metering rules and credit rates",
                    "Interconnection standards and fees",
                    "Current RPS requirements",
                    "Utility rate filings",
                    "Recent docket decisions"
                ]
            },
            {
                "name": "Governor's Energy Office",
                "url": "maine.gov/energy",
                "what_to_find": [
                    "State energy policy updates",
                    "Clean energy programs",
                    "Energy storage initiatives",
                    "Current incentive programs"
                ]
            },
            {
                "name": "Efficiency Maine Trust",
                "url": "efficiencymaine.com",
                "what_to_find": [
                    "Commercial and industrial rebates",
                    "Energy storage incentives",
                    "Solar rebate availability",
                    "Current program funding status",
                    "Application deadlines"
                ]
            },
            {
                "name": "DSIRE Maine Programs",
                "url": "programs.dsireusa.org/state/ME",
                "what_to_find": [
                    "All active incentive programs",
                    "Program eligibility requirements",
                    "Incentive amounts and caps",
                    "Program expiration dates"
                ]
            }
        ],

        # Secondary sources to cross-check
        "tier2_sources": [
            {
                "name": "Efficiency Maine - Commercial Programs",
                "url": "efficiencymaine.com/business",
                "what_to_find": [
                    "Current commercial rebate amounts",
                    "Eligible equipment and measures"
                ]
            },
            {
                "name": "ISO New England Maine",
                "url": "iso-ne.com",
                "what_to_find": [
                    "Grid interconnection queue",
                    "Capacity market participation",
                    "Transmission constraints"
                ]
            }
        ]
    },

    "NH": {
        "state_name": "New Hampshire",

        "tier1_sources": [
            {
                "name": "NH Public Utilities Commission",
                "url": "puc.nh.gov",
                "what_to_find": [
                    "Net metering rules (NEM 2.0 status)",
                    "Interconnection standards",
                    "Current RPS requirements",
                    "Utility rate filings",
                    "Recent docket decisions affecting renewables"
                ]
            },
            {
                "name": "NH Department of Energy",
                "url": "energy.nh.gov",
                "what_to_find": [
                    "Current rebate program status",
                    "HB 2 impacts on rebate programs",
                    "HEAR program launch status",
                    "State energy policy updates"
                ]
            },
            {
                "name": "NHSaves",
                "url": "nhsaves.com",
                "what_to_find": [
                    "Commercial and industrial rebates",
                    "Current rebate amounts by measure",
                    "Program availability"
                ]
            },
            {
                "name": "DSIRE New Hampshire Programs",
                "url": "programs.dsireusa.org/state/NH",
                "what_to_find": [
                    "All active incentive programs",
                    "Program status updates",
                    "Federal program availability in NH"
                ]
            }
        ],

        "tier2_sources": [
            {
                "name": "Eversource NH",
                "url": "eversource.com/content/nh",
                "what_to_find": [
                    "Connected Solutions battery rebate",
                    "Net metering enrollment",
                    "Interconnection application process"
                ]
            },
            {
                "name": "Community Power Coalition NH",
                "url": "cpcnh.org",
                "what_to_find": [
                    "Municipal aggregation participation",
                    "Current supply rates"
                ]
            }
        ]
    },

    "VT": {
        "state_name": "Vermont",

        "tier1_sources": [
            {
                "name": "Vermont Public Utility Commission",
                "url": "puc.vermont.gov",
                "what_to_find": [
                    "Renewable Energy Standard requirements",
                    "Net metering rules",
                    "Interconnection standards",
                    "Current IRP filings"
                ]
            },
            {
                "name": "Efficiency Vermont",
                "url": "efficiencyvermont.com",
                "what_to_find": [
                    "Commercial and industrial rebates",
                    "Current program funding",
                    "Demand Resources Plan status"
                ]
            },
            {
                "name": "DSIRE Vermont Programs",
                "url": "programs.dsireusa.org/state/VT",
                "what_to_find": [
                    "All active Vermont incentive programs",
                    "2024 renewable mandate details",
                    "Program eligibility"
                ]
            }
        ],

        "tier2_sources": [
            {
                "name": "Green Mountain Power",
                "url": "greenmountainpower.com",
                "what_to_find": [
                    "Net metering enrollment",
                    "Battery storage programs",
                    "Interconnection process"
                ]
            },
            {
                "name": "VELCO",
                "url": "velco.com",
                "what_to_find": [
                    "Transmission planning",
                    "Grid capacity information"
                ]
            }
        ]
    },

    "MA": {
        "state_name": "Massachusetts",

        "tier1_sources": [
            {
                "name": "Massachusetts Department of Public Utilities",
                "url": "mass.gov/dpu",
                "what_to_find": [
                    "Net metering rules (NEM 3.0 status)",
                    "Interconnection standards",
                    "Electric Sector Modernization Plans",
                    "RPS requirements"
                ]
            },
            {
                "name": "Massachusetts Clean Energy Center",
                "url": "masscec.com",
                "what_to_find": [
                    "Current clean energy incentive programs",
                    "Commercial and industrial programs",
                    "Offshore wind opportunities",
                    "Energy storage incentives"
                ]
            },
            {
                "name": "MA Department of Energy Resources",
                "url": "mass.gov/doer",
                "what_to_find": [
                    "RPS solar carveout details",
                    "SMART program status",
                    "Clean Peak Standard",
                    "State energy policy updates"
                ]
            },
            {
                "name": "DSIRE Massachusetts Programs",
                "url": "programs.dsireusa.org/state/MA",
                "what_to_find": [
                    "All active MA incentive programs",
                    "Program funding availability"
                ]
            }
        ],

        "tier2_sources": [
            {
                "name": "Eversource MA",
                "url": "eversource.com/content/ma",
                "what_to_find": [
                    "Net metering enrollment",
                    "Demand response programs",
                    "Interconnection applications"
                ]
            }
        ]
    },

    "CT": {
        "state_name": "Connecticut",

        "tier1_sources": [
            {
                "name": "CT Public Utilities Regulatory Authority",
                "url": "portal.ct.gov/pura",
                "what_to_find": [
                    "RPS requirements including fuel cells",
                    "Net metering rules",
                    "Interconnection standards",
                    "Recent docket decisions"
                ]
            },
            {
                "name": "CT Department of Energy and Environmental Protection",
                "url": "portal.ct.gov/deep",
                "what_to_find": [
                    "Integrated Resource Plan",
                    "Clean energy programs",
                    "Climate goals and compliance",
                    "Commercial energy efficiency programs"
                ]
            },
            {
                "name": "DSIRE Connecticut Programs",
                "url": "programs.dsireusa.org/state/CT",
                "what_to_find": [
                    "All active CT incentive programs",
                    "Fuel cell incentive details",
                    "Program eligibility"
                ]
            }
        ],

        "tier2_sources": [
            {
                "name": "Eversource CT",
                "url": "eversource.com/content/ct",
                "what_to_find": [
                    "Commercial energy efficiency rebates",
                    "Net metering enrollment",
                    "Interconnection process"
                ]
            }
        ]
    },

    "RI": {
        "state_name": "Rhode Island",

        "tier1_sources": [
            {
                "name": "Rhode Island Public Utilities Commission",
                "url": "ripuc.ri.gov",
                "what_to_find": [
                    "Renewable Energy Standard requirements",
                    "Net metering rules",
                    "Interconnection standards",
                    "National Grid rate filings"
                ]
            },
            {
                "name": "Rhode Island Office of Energy Resources",
                "url": "energy.ri.gov",
                "what_to_find": [
                    "State energy programs",
                    "Clean energy incentives",
                    "Offshore wind developments",
                    "Commercial programs"
                ]
            },
            {
                "name": "DSIRE Rhode Island Programs",
                "url": "programs.dsireusa.org/state/RI",
                "what_to_find": [
                    "All active RI incentive programs",
                    "Program eligibility and amounts"
                ]
            }
        ],

        "tier2_sources": [
            {
                "name": "National Grid RI",
                "url": "nationalgridus.com/ri",
                "what_to_find": [
                    "Commercial energy efficiency rebates",
                    "Net metering enrollment",
                    "Interconnection process"
                ]
            }
        ]
    }
}


# ============================================
# SECTION 2: STABLE REFERENCE DATA
# ============================================
# Facts that almost never change.
# Safe to hardcode because they are structural
# not programmatic.
#
# Examples of what IS stable:
#   - State PUC names
#   - ISO region membership
#   - Utility names and service areas
#   - NAICS sector names
#
# Examples of what IS NOT stable (do not hardcode):
#   - Incentive amounts
#   - Program status (open/closed)
#   - Credit rates
#   - Application deadlines

STATE_STABLE_FACTS = {

    "ME": {
        "state_name": "Maine",
        "iso_region": "ISO New England (ISO-NE)",
        "market_type": "Restructured",
        "rps_exists": True,
        "rps_created": 1997,
        "net_metering_exists": True,
        "rggi_member": True,

        # Utility names and service areas
        # These change rarely (major utility mergers aside)
        "electric_utilities": [
            {
                "name": "Central Maine Power (CMP)",
                "owner": "Avangrid",
                "service_area": "Southern and central Maine",
                "website": "cmpco.com",
                "eia_id": "3265"
            },
            {
                "name": "Versant Power",
                "formerly": "Emera Maine",
                "owner": "ENMAX",
                "service_area": "Northern and eastern Maine",
                "website": "versantpower.com",
                "eia_id": "19545"
            }
        ],

        # Regulators — names change rarely
        "primary_regulator": {
            "name": "Maine Public Utilities Commission (PUC)",
            "abbreviation": "Maine PUC",
            "website": "maine.gov/mpuc",
            "phone": "(207) 287-3831"
        },
        "energy_office": {
            "name": "Governor's Energy Office (GEO)",
            "website": "maine.gov/energy"
        },
        "efficiency_program": {
            "name": "Efficiency Maine Trust",
            "website": "efficiencymaine.com",
            "phone": "1-866-376-2463"
        },

        # Dominant industrial sectors from NREL 2018
        # NAICS codes and sector names are stable
        # Energy consumption values may shift over time
        "dominant_industrial_sectors": [
            {"naics": "322", "name": "Paper Manufacturing"},
            {"naics": "321", "name": "Wood Product Manufacturing"},
            {"naics": "311", "name": "Food Manufacturing"},
            {"naics": "332", "name": "Fabricated Metal Products"}
        ],

        # Unique policy characteristics
        # These are structural facts not amounts
        "unique_policy_characteristics": [
            "Black liquor classified as renewable under RPS",
            "Paper manufacturing represents >75% of industrial energy",
            "400 MW energy storage goal established by LD 528 (2021)",
            "Grid planning required on 5-year cycle starting 2022",
            "Interconnection standards last updated 2020"
        ]
    },

    "NH": {
        "state_name": "New Hampshire",
        "iso_region": "ISO New England (ISO-NE)",
        "market_type": "Restructured",
        "rps_exists": True,
        "net_metering_exists": True,
        "net_metering_program_name": "NEM 2.0",
        "rggi_member": True,

        "electric_utilities": [
            {
                "name": "Eversource Energy (NH)",
                "service_area": "Most of NH",
                "website": "eversource.com/content/nh",
                "eia_id": "3454"
            },
            {
                "name": "Unitil Energy Systems",
                "service_area": "Seacoast, Capital, and southern NH",
                "website": "unitil.com",
                "eia_id": "20155"
            },
            {
                "name": "Liberty Utilities",
                "service_area": "Western and southern NH",
                "website": "libertyutilities.com",
                "eia_id": "17166"
            }
        ],

        "primary_regulator": {
            "name": "NH Public Utilities Commission",
            "abbreviation": "NH PUC",
            "website": "puc.nh.gov",
            "phone": "(603) 271-2431"
        },
        "energy_office": {
            "name": "NH Department of Energy",
            "website": "energy.nh.gov",
            "phone": "(603) 271-3670"
        },
        "efficiency_program": {
            "name": "NHSaves",
            "website": "nhsaves.com"
        },

        "dominant_industrial_sectors": [
            {"naics": "334", "name": "Computer and Electronic Products"},
            {"naics": "332", "name": "Fabricated Metal Products"},
            {"naics": "333", "name": "Machinery Manufacturing"},
            {"naics": "311", "name": "Food Manufacturing"}
        ],

        "unique_policy_characteristics": [
            "NEM 2.0 locked through 2041 by NH PUC order",
            "No state sales tax on solar equipment",
            "HB 2 (2025) closed all state rebate programs",
            "Weak state-level support for renewable energy",
            "IRP requirement for utilities was repealed"
        ]
    },

    "VT": {
        "state_name": "Vermont",
        "iso_region": "ISO New England (ISO-NE)",
        "market_type": "Regulated",
        "rps_exists": True,
        "rps_created": 2015,
        "net_metering_exists": True,
        "rggi_member": True,

        "electric_utilities": [
            {
                "name": "Green Mountain Power",
                "service_area": "Most of Vermont",
                "website": "greenmountainpower.com"
            },
            {
                "name": "Vermont Electric Cooperative",
                "service_area": "Northeast Vermont",
                "website": "vermontelectric.coop"
            }
        ],
        "transmission_operator": {
            "name": "VELCO",
            "description": "Vermont's unified state grid operator",
            "website": "velco.com"
        },

        "primary_regulator": {
            "name": "Vermont Public Utility Commission",
            "abbreviation": "VT PUC",
            "website": "puc.vermont.gov"
        },
        "energy_office": {
            "name": "Vermont Department of Public Service",
            "website": "publicservice.vermont.gov"
        },
        "efficiency_program": {
            "name": "Efficiency Vermont (operated by VEIC)",
            "website": "efficiencyvermont.com"
        },

        "dominant_industrial_sectors": [
            {"naics": "322", "name": "Paper Manufacturing"},
            {"naics": "311", "name": "Food Manufacturing"},
            {"naics": "334", "name": "Computer and Electronic Products"},
            {"naics": "333", "name": "Machinery Manufacturing"}
        ],

        "unique_policy_characteristics": [
            "VELCO is unified state grid operator",
            "Efficiency Vermont is state energy efficiency utility",
            "Aggressive statewide renewable mandate approved summer 2024",
            "IRP required every 3 years for regulated utilities",
            "Demand Resources Plan filed every 3 years by Efficiency VT"
        ]
    },

    "MA": {
        "state_name": "Massachusetts",
        "iso_region": "ISO New England (ISO-NE)",
        "market_type": "Restructured",
        "rps_exists": True,
        "net_metering_exists": True,
        "net_metering_program_name": "NEM 3.0",
        "rggi_member": True,

        "electric_utilities": [
            {
                "name": "Eversource Energy Eastern MA (NSTAR)",
                "owner": "Eversource Energy",
                "service_area": "Eastern Massachusetts",
                "website": "eversource.com/content/ma",
                "eia_id": "13975"
            },
            {
                "name": "Eversource Energy Western MA (WMECO)",
                "owner": "Eversource Energy",
                "service_area": "Western Massachusetts",
                "website": "eversource.com/content/ma",
                "eia_id": "20542"
            },
            {
                "name": "Massachusetts Electric Company",
                "owner": "National Grid",
                "service_area": "Central and eastern Massachusetts",
                "website": "nationalgridus.com/ma",
                "eia_id": "12261"
            },
            {
                "name": "Nantucket Electric Company",
                "owner": "National Grid",
                "service_area": "Nantucket Island",
                "website": "nationalgridus.com/ma",
                "eia_id": "13206"
            },
            {
                "name": "Unitil Energy Systems MA",
                "owner": "Unitil Corp",
                "service_area": "Fitchburg area",
                "website": "unitil.com",
                "eia_id": "24590"
            }
        ],
        "primary_regulator": {
            "name": "Massachusetts Department of Public Utilities",
            "abbreviation": "MA DPU",
            "website": "mass.gov/dpu"
        },
        "energy_office": {
            "name": "Massachusetts Department of Energy Resources",
            "abbreviation": "DOER",
            "website": "mass.gov/doer"
        },
        "clean_energy_center": {
            "name": "Massachusetts Clean Energy Center",
            "abbreviation": "MassCEC",
            "website": "masscec.com"
        },

        "dominant_industrial_sectors": [
            {"naics": "325", "name": "Chemical Manufacturing"},
            {"naics": "334", "name": "Computer and Electronic Products"},
            {"naics": "332", "name": "Fabricated Metal Products"},
            {"naics": "311", "name": "Food Manufacturing"}
        ],

        "unique_policy_characteristics": [
            "Solar PV carveout in RPS",
            "SMART program for solar incentives",
            "Electric Sector Modernization Plan required every 5 years",
            "Largest industrial energy consumer in New England",
            "Strong offshore wind program"
        ]
    },

    "CT": {
        "state_name": "Connecticut",
        "iso_region": "ISO New England (ISO-NE)",
        "market_type": "Restructured",
        "rps_exists": True,
        "rps_created": 1998,
        "net_metering_exists": True,
        "rggi_member": True,

        "electric_utilities": [
            {
                "name": "Eversource Energy (CT)",
                "service_area": "Most of Connecticut",
                "website": "eversource.com/content/ct"
            },
            {
                "name": "United Illuminating (UI)",
                "service_area": "New Haven and Bridgeport areas",
                "website": "uinet.com"
            }
        ],

        "primary_regulator": {
            "name": "Public Utilities Regulatory Authority",
            "abbreviation": "PURA",
            "website": "portal.ct.gov/pura"
        },
        "energy_office": {
            "name": "CT Department of Energy and Environmental Protection",
            "abbreviation": "DEEP",
            "website": "portal.ct.gov/deep"
        },

        "dominant_industrial_sectors": [
            {"naics": "332", "name": "Fabricated Metal Products"},
            {"naics": "325", "name": "Chemical Manufacturing"},
            {"naics": "334", "name": "Computer and Electronic Products"},
            {"naics": "335", "name": "Electrical Equipment Manufacturing"}
        ],

        "unique_policy_characteristics": [
            "Fuel cells explicitly eligible under RPS",
            "IRP required every 2 years",
            "Global Warming Solutions Act compliance",
            "DEEP and PURA have complementary roles"
        ]
    },

    "RI": {
        "state_name": "Rhode Island",
        "iso_region": "ISO New England (ISO-NE)",
        "market_type": "Restructured",
        "rps_exists": True,
        "rps_created": 2004,
        "net_metering_exists": True,
        "rggi_member": True,

        "electric_utilities": [
            {
                "name": "Rhode Island Energy",
                "formerly": "National Grid RI",
                "service_area": "All of Rhode Island",
                "website": "rienergy.com",
                "notes": "Single utility simplifies decision making"
            }
        ],

        "primary_regulator": {
            "name": "Rhode Island Public Utilities Commission",
            "abbreviation": "RIPUC",
            "website": "ripuc.ri.gov"
        },
        "energy_office": {
            "name": "Rhode Island Office of Energy Resources",
            "abbreviation": "OER",
            "website": "energy.ri.gov"
        },

        "dominant_industrial_sectors": [
            {"naics": "313", "name": "Textile Mills"},
            {"naics": "332", "name": "Fabricated Metal Products"},
            {"naics": "326", "name": "Plastics and Rubber Products"},
            {"naics": "311", "name": "Food Manufacturing"}
        ],

        "unique_policy_characteristics": [
            "Single utility (National Grid) serves entire state",
            "83% of electricity from natural gas",
            "Abundant coastal wind resource",
            "Ocean energy largely untapped",
            "Dense population supports thermal district opportunities"
        ]
    }
}


# ============================================
# SECTION 3: SEARCH QUERY TEMPLATES
# ============================================
# Pre-built search queries the LLM agents
# use to find current policy information.
#
# Using templates ensures agents search for
# the RIGHT information in the RIGHT way
# rather than generating ad-hoc queries
# that may miss important details.

POLICY_SEARCH_QUERIES = {

    "net_metering": (
        "current net metering rules credit rate "
        "{state_name} {year} site:{puc_url}"
    ),

    "rps_requirements": (
        "renewable portfolio standard requirements "
        "percentage {state_name} {year} "
        "site:{puc_url} OR site:{dsire_url}"
    ),

    "interconnection": (
        "interconnection standards application fees "
        "process {state_name} {year} "
        "site:{puc_url}"
    ),

    "incentive_programs": (
        "commercial industrial energy incentive "
        "rebate program {state_name} {year} "
        "site:{dsire_url} OR site:{efficiency_url}"
    ),

    "program_status": (
        "{program_name} program status open closed "
        "{state_name} {year}"
    ),

    "storage_incentives": (
        "battery energy storage incentive rebate "
        "{state_name} commercial industrial {year}"
    ),

    "federal_programs": (
        "federal investment tax credit ITC section 48E "
        "status {year} commercial industrial "
        "site:irs.gov OR site:dsireusa.org"
    )
}


# ============================================
# SECTION 4: POLICY TOPIC STRUCTURE
# ============================================
# Defines what topics Agent 2 should research
# for each facility query.
#
# This ensures consistent report structure
# regardless of which LLM is used or which
# state is being researched.

POLICY_TOPICS = [
    {
        "topic_id": "rps",
        "topic_name": "Renewable Portfolio Standard",
        "questions": [
            "Is {technology} eligible under the {state} RPS?",
            "What is the current RPS requirement percentage?",
            "Are there technology-specific carveouts relevant to {technology}?",
            "What is the Alternative Compliance Payment rate?"
        ],
        "primary_source_key": "tier1_sources",
        "agent": "agent2_policy"
    },
    {
        "topic_id": "net_metering",
        "topic_name": "Net Metering",
        "questions": [
            "What is the current net metering credit rate in {state}?",
            "What is the system size limit for net metering?",
            "Is {technology} eligible for net metering?",
            "What utility administers net metering for this location?"
        ],
        "primary_source_key": "tier1_sources",
        "agent": "agent2_policy"
    },
    {
        "topic_id": "interconnection",
        "topic_name": "Interconnection Requirements",
        "questions": [
            "What interconnection process tier applies to a {size_kw} kW system?",
            "What is the application fee for this system size?",
            "What technical studies are required?",
            "What is the typical timeline for interconnection approval?"
        ],
        "primary_source_key": "tier1_sources",
        "agent": "agent4_interconnect"
    },
    {
        "topic_id": "incentives",
        "topic_name": "Financial Incentives",
        "questions": [
            "What state incentive programs are currently open for {technology}?",
            "What federal incentive programs apply to {facility_type}?",
            "What utility rebates are available from {utility}?",
            "What financing programs are available?"
        ],
        "primary_source_key": "tier1_sources",
        "agent": "agent3_incentives"
    }
]


# ============================================
# SECTION 5: NAICS SECTOR CONTEXT
# ============================================
# Provides sector-specific context that helps
# agents ask better questions and identify
# relevant programs.
#
# NAICS codes and sector names are stable.
# Technology recommendations are guidance only —
# agents should verify current program
# availability for each sector.

NAICS_SECTOR_CONTEXT = {
    "322": {
        "name": "Paper Manufacturing",
        "relevant_technologies": [
            "Biomass CHP",
            "Black liquor recovery",
            "Steam optimization",
            "Energy storage"
        ],
        "key_policy_note": (
            "Maine classifies black liquor as renewable. "
            "Verify current status with Maine PUC."
        ),
        "high_energy_intensity": True
    },
    "311": {
        "name": "Food Manufacturing",
        "relevant_technologies": [
            "Solar PV",
            "CHP",
            "Refrigeration efficiency",
            "Battery storage"
        ],
        "high_energy_intensity": True
    },
    "332": {
        "name": "Fabricated Metal Products",
        "relevant_technologies": [
            "Solar PV",
            "Compressed air optimization",
            "Motor efficiency",
            "Battery storage"
        ],
        "high_energy_intensity": False
    },
    "325": {
        "name": "Chemical Manufacturing",
        "relevant_technologies": [
            "CHP",
            "Process heat recovery",
            "Solar PV",
            "Fuel cells"
        ],
        "high_energy_intensity": True
    },
    "334": {
        "name": "Computer and Electronic Products",
        "relevant_technologies": [
            "Solar PV",
            "Battery storage",
            "Energy management systems"
        ],
        "high_energy_intensity": False
    },
    "321": {
        "name": "Wood Product Manufacturing",
        "relevant_technologies": [
            "Biomass CHP",
            "Solar PV",
            "Steam optimization",
            "Energy storage"
        ],
        "high_energy_intensity": True
    },
    "333": {
        "name": "Machinery Manufacturing",
        "relevant_technologies": [
            "Solar PV",
            "Compressed air optimization",
            "Motor efficiency",
            "Battery storage"
        ],
        "high_energy_intensity": False
    },
    "335": {
        "name": "Electrical Equipment Manufacturing",
        "relevant_technologies": [
            "Solar PV",
            "Energy management systems",
            "Motor efficiency",
            "Battery storage"
        ],
        "high_energy_intensity": False
    },
    "313": {
        "name": "Textile Mills",
        "relevant_technologies": [
            "Solar PV",
            "Steam optimization",
            "Motor efficiency",
            "CHP"
        ],
        "high_energy_intensity": True
    },
    "326": {
        "name": "Plastics and Rubber Products",
        "relevant_technologies": [
            "Solar PV",
            "Process heat recovery",
            "Energy management systems",
            "Battery storage"
        ],
        "high_energy_intensity": True
    }
}


# ============================================
# SECTION 6: HELPER FUNCTIONS
# ============================================

def get_authoritative_sources(state: str) -> dict:
    """
    Returns authoritative sources for a state.
    Used by agents to know where to search
    for current policy information.

    Args:
        state: Two-letter state code

    Returns:
        dict with tier1 and tier2 sources
    """
    state = state.upper().strip()
    return STATE_AUTHORITATIVE_SOURCES.get(state, {})


def get_stable_facts(state: str) -> dict:
    """
    Returns stable reference facts for a state.
    These are safe to use without live verification
    because they change rarely.

    Args:
        state: Two-letter state code

    Returns:
        dict with utility names, regulators,
        ISO region, and unique characteristics
    """
    state = state.upper().strip()
    return STATE_STABLE_FACTS.get(state, {})


def get_search_queries(
    state: str,
    technology: str,
    size_kw: float,
    year: int| None = None
) -> list:
    """
    Builds search query strings for an agent
    to use when looking up current policy info.

    Args:
        state: Two-letter state code
        technology: Energy technology type
        size_kw: System size in kW
        year: Current year (defaults to current)

    Returns:
        List of search query strings
    """
    import datetime

    if year is None:
        year = datetime.datetime.now().year

    stable = get_stable_facts(state)
    _sources = get_authoritative_sources(state)

    # Get URLs for query templates
    puc_url = stable.get(
        "primary_regulator", {}
    ).get("website", "")

    efficiency_url = stable.get(
        "efficiency_program", {}
    ).get("website", "")

    # Build DSIRE URL
    dsire_url = f"programs.dsireusa.org/state/{state}"

    state_name = stable.get("state_name", state)

    # Build queries from templates
    queries = []
    for query_key, template in POLICY_SEARCH_QUERIES.items():
        query = template.format(
            state_name=state_name,
            year=year,
            puc_url=puc_url,
            dsire_url=dsire_url,
            efficiency_url=efficiency_url,
            technology=technology,
            size_kw=size_kw,
            program_name=technology
        )
        queries.append({
            "topic": query_key,
            "query": query
        })

    return queries


def get_naics_context(naics_code: str) -> dict:
    """
    Returns sector context for a NAICS code.
    Helps agents identify relevant technologies
    and policy programs.

    Args:
        naics_code: 3-6 digit NAICS code

    Returns:
        dict with sector name and relevant
        technologies
    """
    # Try exact match first then 3-digit prefix
    code_3 = str(naics_code)[:3]
    return NAICS_SECTOR_CONTEXT.get(
        naics_code,
        NAICS_SECTOR_CONTEXT.get(code_3, {})
    )