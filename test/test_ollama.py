"""
test_ollama.py
Quick test to verify Ollama is working
with your ENSITE project
"""
import requests
from langchain_ollama import ChatOllama

print("=" * 50)
print("ENSITE Ollama Connection Test")
print("=" * 50)

# Test 1: Is Ollama server responding?
print("\nTest 1: Checking Ollama server...")
try:
    response = requests.get(
        "http://localhost:11434",
        timeout=5
    )
    if "Ollama is running" in response.text:
        print("✅ Ollama server is running!")
    else:
        print(f"⚠️  Unexpected response: {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Ollama")
    print("   Try restarting Ollama from Start menu")

# Test 2: Can LangChain talk to Ollama?
print("\nTest 2: Testing LangChain connection...")
try:
    llm = ChatOllama(
        model="llama3.2",
        base_url="http://localhost:11434",
        temperature=0
    )
    response = llm.invoke(
        "In one sentence, what is net metering?"
    )
    print("✅ LangChain connected successfully!")
    print(f"   Model response: {response.content}")
except Exception as e:
    print(f"❌ LangChain connection failed: {e}")
    print("   Make sure llama3.2 is pulled:")
    print("   Run: ollama pull llama3.2")

print("\n" + "=" * 50)
print("If both tests pass you are ready to")
print("start building ENSITE agents!")
print("=" * 50)