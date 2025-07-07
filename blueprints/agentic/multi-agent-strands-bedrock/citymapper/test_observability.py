#!/usr/bin/env python3
"""Test script for observability integration."""

import os
import asyncio
from observability import observability, trace_agent_call


@trace_agent_call("Test Agent")
async def test_agent_function(query: str) -> str:
    """Test agent function with observability."""
    await asyncio.sleep(0.1)  # Simulate processing
    return f"Test response for: {query}"


async def test_observability():
    """Test observability functionality."""
    print("🧪 Testing Observability Integration...")
    print("=" * 50)
    
    # Test 1: Check if observability is enabled
    print("1. Testing observability status...")
    if observability.enabled:
        print("✅ Observability enabled (Langfuse configured)")
    else:
        print("⚠️ Observability disabled (set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)")
    
    print()
    
    # Test 2: Test agent tracing
    print("2. Testing agent tracing...")
    try:
        response = await test_agent_function("Plan a trip to San Francisco")
        print(f"✅ Agent function executed: {response}")
    except Exception as e:
        print(f"❌ Agent function failed: {e}")
    
    print()
    
    # Test 3: Test tool tracing
    print("3. Testing tool tracing...")
    try:
        observability.trace_tool_call(
            tool_name="test_tool",
            input_data={"query": "test"},
            output_data={"result": "success"},
            execution_time=0.1
        )
        print("✅ Tool tracing executed")
    except Exception as e:
        print(f"❌ Tool tracing failed: {e}")
    
    print()
    
    # Test 4: Test multi-agent communication tracing
    print("4. Testing multi-agent communication tracing...")
    try:
        observability.trace_multi_agent_communication(
            from_agent="Orchestrator",
            to_agent="Citymapper",
            message="Plan a trip",
            response="Trip planned"
        )
        print("✅ Multi-agent tracing executed")
    except Exception as e:
        print(f"❌ Multi-agent tracing failed: {e}")
    
    print()
    
    # Test 5: Test RAGAS evaluation
    print("5. Testing RAGAS evaluation...")
    try:
        scores = observability.evaluate_response_quality(
            query="What's the weather in San Francisco?",
            response="The weather in San Francisco is sunny with 72°F temperature.",
            context=["San Francisco weather data"]
        )
        if scores:
            print(f"✅ RAGAS evaluation completed: {scores}")
        else:
            print("⚠️ RAGAS evaluation skipped (requires configuration)")
    except Exception as e:
        print(f"❌ RAGAS evaluation failed: {e}")
    
    print()
    print("=" * 50)
    print("🎉 Observability testing completed!")
    
    if observability.enabled:
        print("✅ Full observability active - check Langfuse dashboard")
    else:
        print("💡 To enable full observability, set environment variables:")
        print("   export LANGFUSE_PUBLIC_KEY=your_key")
        print("   export LANGFUSE_SECRET_KEY=your_secret")
        print("   export LANGFUSE_HOST=https://cloud.langfuse.com")


if __name__ == "__main__":
    asyncio.run(test_observability())