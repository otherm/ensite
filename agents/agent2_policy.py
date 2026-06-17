# In agent2_policy.py

from config.state_data import (
    get_authoritative_sources,
    get_stable_facts,
    get_search_queries,
    get_naics_context
)

def node_gather_sources(agent_state: AgentState) -> AgentState:
    """
    Node 1: Get sources and stable facts.
    No LLM needed — just dictionary lookups.
    """
    # Get where to look
    agent_state["sources"] = get_authoritative_sources(
        state["state"]
    )
    # Get what we know for certain
    agent_state["stable_facts"] = get_stable_facts(
        agent_state["state"]
    )
    # Get search queries to use
    agent_state["search_queries"] = get_search_queries(
        agent_state["state"],
        agent_state["technology"],
        agent_state["system_size_kw"]
    )
    # Get NAICS context
    agent_state["naics_context"] = get_naics_context(
        agent_state["naics_code"]
    )
    return agent_state


def node_llm_research(agent_state: AgentState) -> AgentState:
    """
    Node 2: LLM searches authoritative sources
    for CURRENT policy information.
    """
    # LLM receives:
    # - Exactly WHERE to look (tier1_sources URLs)
    # - Exactly WHAT to search for (search_queries)
    # - Stable facts it can rely on
    # - NAICS context for relevance

    prompt = f"""
You are researching current energy policies for ENSITE.

FACILITY:
State: {agent_state['state']}
Technology: {agent_state['technology']}
Size: {agent_state['system_size_kw']} kW
NAICS: {agent_state['naics_code']}

STABLE FACTS YOU CAN RELY ON:
{agent_state['stable_facts']}

AUTHORITATIVE SOURCES TO CHECK:
{agent_state['sources']['tier1_sources']}

SEARCH QUERIES TO USE:
{agent_state['search_queries']}

NAICS SECTOR CONTEXT:
{agent_state['naics_context']}

Please search the authoritative sources listed above
and provide CURRENT policy information including:
1. Current RPS eligibility for {agent_state['technology']}
2. Current net metering rules and credit rates
3. Current interconnection process tier for {agent_state['system_size_kw']} kW
4. Currently open incentive programs
5. Source URLs and dates for all information found

Flag any information older than 90 days.
Flag any conflicts between sources.
"""
    # LLM does the live research here
    # using its web search capability
