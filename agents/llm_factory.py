"""
agents/llm_factory.py
=============================================
Single source of truth for LLM connections
in the ENSITE system.

All agents import get_llm() from here.
Never create LLM connections directly in
agent files.

Supported providers:
  ollama      Local Ollama (current)
  deepthought USNH DeepThought AI (pending)
  azure       Azure OpenAI (fallback)

To switch providers:
  Change LLM_PROVIDER in .env file
  No changes needed in agent files!

Author: ENSITE Project, UNH
Date: June 2026
"""

# ============================================
# SECTION 1: IMPORTS
# ============================================
import logging
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI, AzureChatOpenAI

from config.settings import (
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    DEEPTHOUGHT_API_KEY,
    DEEPTHOUGHT_BASE_URL,
    DEEPTHOUGHT_MODEL,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT
)

logger = logging.getLogger(__name__)


# ============================================
# SECTION 2: PROVIDER FUNCTIONS
# ============================================
# One function per provider.
# Each returns a LangChain chat model object.
# All return the same interface so agents
# do not need to know which provider is active.

def _get_ollama_llm():
    """
    Creates Ollama LLM connection.

    Ollama runs locally on your PC.
    No API key needed.
    Data never leaves your machine.
    USNH policy compliant for development.

    Returns:
        ChatOllama instance
    """
    logger.info(
        f"Creating Ollama LLM: "
        f"{OLLAMA_MODEL} at {OLLAMA_BASE_URL}"
    )

    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
        timeout=LLM_TIMEOUT
    )


def _get_deepthought_llm():
    """
    Creates DeepThought AI LLM connection.

    DeepThought runs on USNH servers.
    USNH policy compliant for production.
    Pending API details from USNH IT.

    Returns:
        ChatOpenAI instance pointed at
        DeepThought endpoint
    """
    if not DEEPTHOUGHT_API_KEY:
        raise ValueError(
            "DEEPTHOUGHT_API_KEY not set in .env. "
            "Contact USNH IT for API credentials."
        )
    if not DEEPTHOUGHT_BASE_URL:
        raise ValueError(
            "DEEPTHOUGHT_BASE_URL not set in .env. "
            "Contact USNH IT for API endpoint."
        )
    if not DEEPTHOUGHT_MODEL:
        raise ValueError(
            "DEEPTHOUGHT_MODEL not set in .env. "
            "Contact USNH IT for model name."
        )

    logger.info(
        f"Creating DeepThought LLM: "
        f"{DEEPTHOUGHT_MODEL} at {DEEPTHOUGHT_BASE_URL}"
    )

    # DeepThought uses OpenAI-compatible API
    # so ChatOpenAI works with a custom base_url
    return ChatOpenAI(
        model=DEEPTHOUGHT_MODEL,
        api_key=DEEPTHOUGHT_API_KEY,
        base_url=DEEPTHOUGHT_BASE_URL,
        temperature=LLM_TEMPERATURE,
        timeout=LLM_TIMEOUT
    )


def _get_azure_llm():
    """
    Creates Azure OpenAI LLM connection.

    Available through USNH Microsoft license.
    Use as fallback if DeepThought not ready.

    Returns:
        AzureChatOpenAI instance
    """
    if not AZURE_OPENAI_API_KEY:
        raise ValueError(
            "AZURE_OPENAI_API_KEY not set in .env"
        )
    if not AZURE_OPENAI_ENDPOINT:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT not set in .env"
        )

    logger.info(
        f"Creating Azure OpenAI LLM: "
        f"{AZURE_OPENAI_DEPLOYMENT}"
    )

    return AzureChatOpenAI(
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        temperature=LLM_TEMPERATURE,
        timeout=LLM_TIMEOUT
    )


# ============================================
# SECTION 3: MAIN FACTORY FUNCTION
# ============================================

def get_llm(provider: str = None):
    """
    Returns an LLM instance for the specified
    or configured provider.

    This is the ONLY function agents should call.
    Never instantiate LLM classes directly
    in agent files.

    Args:
        provider: Override the configured provider.
                  Options: "ollama", "deepthought", "azure"
                  If None uses LLM_PROVIDER from settings.

    Returns:
        LangChain chat model instance.
        All providers return the same interface
        so agents work identically regardless
        of which provider is active.

    Raises:
        ValueError: If provider is unknown or
                    required settings are missing.

    Example:
        from agents.llm_factory import get_llm

        llm = get_llm()
        response = llm.invoke("Hello")
        print(response.content)
    """

    # Use override if provided, otherwise
    # use setting from .env file
    active_provider = (
        provider.lower().strip()
        if provider
        else LLM_PROVIDER.lower().strip()
    )

    logger.info(
        f"LLM factory: provider={active_provider}"
    )

    if active_provider == "ollama":
        return _get_ollama_llm()

    elif active_provider == "deepthought":
        return _get_deepthought_llm()

    elif active_provider == "azure":
        return _get_azure_llm()

    else:
        raise ValueError(
            f"Unknown LLM provider: '{active_provider}'. "
            f"Valid options: ollama, deepthought, azure. "
            f"Check LLM_PROVIDER in your .env file."
        )


# ============================================
# SECTION 4: CONNECTION TEST
# ============================================

def test_llm_connection(provider: str = None) -> dict:
    """
    Tests that the LLM connection works.

    Sends a simple test message and checks
    for a valid response.

    Args:
        provider: Provider to test.
                  If None tests configured provider.

    Returns:
        dict with:
        - success: True/False
        - provider: Provider tested
        - model: Model name
        - response_preview: First 100 chars
        - error: Error message if failed
    """
    active_provider = provider or LLM_PROVIDER

    try:
        llm = get_llm(active_provider)

        # Send simple test message
        from langchain_core.messages import HumanMessage
        response = llm.invoke(
            [HumanMessage(
                content=(
                    "In one sentence, what is "
                    "net metering?"
                )
            )]
        )

        preview = response.content[:100]

        logger.info(
            f"LLM connection test passed: "
            f"{active_provider}"
        )

        return {
            "success": True,
            "provider": active_provider,
            "model": (
                OLLAMA_MODEL
                if active_provider == "ollama"
                else DEEPTHOUGHT_MODEL
                if active_provider == "deepthought"
                else AZURE_OPENAI_DEPLOYMENT
            ),
            "response_preview": preview,
            "error": None
        }

    except Exception as e:
        logger.error(
            f"LLM connection test failed: "
            f"{active_provider}: {e}"
        )
        return {
            "success": False,
            "provider": active_provider,
            "model": None,
            "response_preview": None,
            "error": str(e)
        }


# ============================================
# SECTION 5: MAIN
# ============================================

if __name__ == "__main__":
    """
    Run this file directly to test your
    LLM connection before running agents.

    Usage:
        python agents/llm_factory.py
    """

    print("\n" + "=" * 55)
    print("  ENSITE LLM Factory Test")
    print("  University of New Hampshire")
    print("=" * 55)

    print(f"\n  Configured provider: {LLM_PROVIDER}")

    # Test configured provider
    print(f"\n  Testing {LLM_PROVIDER}...")
    result = test_llm_connection()

    if result["success"]:
        print(f"  ✅ Connected successfully")
        print(f"  ✅ Model: {result['model']}")
        print(
            f"  ✅ Response: "
            f"{result['response_preview']}..."
        )
    else:
        print(f"  ❌ Connection failed")
        print(f"  ❌ Error: {result['error']}")

        if LLM_PROVIDER == "ollama":
            print(
                "\n  Troubleshooting:"
                "\n  1. Check Ollama is running:"
                "\n     http://localhost:11434"
                "\n  2. Check model is pulled:"
                f"\n     ollama pull {OLLAMA_MODEL}"
                "\n  3. Check OLLAMA_BASE_URL in .env"
            )
        elif LLM_PROVIDER == "deepthought":
            print(
                "\n  Troubleshooting:"
                "\n  1. Check DEEPTHOUGHT_API_KEY in .env"
                "\n  2. Check DEEPTHOUGHT_BASE_URL in .env"
                "\n  3. Contact USNH IT for credentials"
            )
        elif LLM_PROVIDER == "azure":
            print(
                "\n  Troubleshooting:"
                "\n  1. Check AZURE_OPENAI_API_KEY in .env"
                "\n  2. Check AZURE_OPENAI_ENDPOINT in .env"
            )

    print("\n" + "=" * 55 + "\n")