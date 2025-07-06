#!/usr/bin/env python3
"""Test script for Citymapper Travel Agent integration."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from agent import get_agent


def test_agent_creation():
    """Test that the agent can be created successfully."""
    print("Testing agent creation...")
    try:
        agent = get_agent()
        print("✅ Agent created successfully")
        print(f"Agent name: {agent.name}")
        print(f"Tools available: {len(agent.tool_registry.tools)}")
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False


def test_agent_query():
    """Test a simple query to the agent."""
    print("\nTesting agent query...")
    try:
        agent = get_agent()
        response = agent("List available destinations for travel planning.")
        print("✅ Agent query successful")
        print(f"Response: {response[:200]}...")
        return True
    except Exception as e:
        print(f"❌ Agent query failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Citymapper Travel Agent Integration")
    print("=" * 50)
    
    tests = [
        test_agent_creation,
        test_agent_query
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())