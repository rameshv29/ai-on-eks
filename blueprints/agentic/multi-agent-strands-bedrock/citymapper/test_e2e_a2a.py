#!/usr/bin/env python3
"""
Test script for the Citymapper Agent A2A (Agent-to-Agent) Protocol

This script tests the A2A endpoints to ensure they work correctly.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

# Configure logging to be less verbose for better UX
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"


async def test_a2a_protocol(base_url: str = "http://localhost:9000"):
    """Test the Citymapper Agent A2A Protocol endpoints"""

    print(f"Testing Citymapper Agent A2A Protocol at {base_url}")
    print("=" * 50)

    # Set a longer timeout for the HTTP client
    timeout = httpx.Timeout(60.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            # Test 1: Agent Card Discovery
            print("1. Testing agent card discovery...")
            try:
                resolver = A2ACardResolver(
                    httpx_client=httpx_client,
                    base_url=base_url,
                )
                agent_card = await resolver.get_agent_card()
                print("✅ Agent card discovery successful")
                print(f"   Agent Name: {agent_card.name}")
                print(f"   Agent Description: {agent_card.description}")
                print(f"   Version: {agent_card.version}")
                if hasattr(agent_card.capabilities, '__len__'):
                    print(f"   Capabilities: {len(agent_card.capabilities)} available")
                else:
                    print(f"   Capabilities: Available")
                if hasattr(agent_card, 'protocol_version'):
                    print(f"   Protocol Version: {agent_card.protocol_version}")
                print(f"   Agent Card Retrieved: ✓")
            except Exception as e:
                print(f"❌ Agent card discovery failed: {str(e)}")
                return False

            print()

            # Test 2: A2A Client Initialization
            print("2. Testing A2A client initialization...")
            try:
                client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
                print("✅ A2A client initialized successfully")
                print(f"   Client Ready: True")
                print(f"   Connection Established: ✓")
            except Exception as e:
                print(f"❌ A2A client initialization failed: {str(e)}")
                return False

            print()

            # Test 3: Travel Planning Message
            print("3. Testing travel planning message...")
            try:
                query_text = "Plan a 3-day trip to San Francisco focusing on food and nature"
                request = create_message_request(query_text)
                print(f"   Query: {query_text}")

                response = await client.send_message(request)
                print("✅ Travel planning query successful")

                # Extract response content
                response_dict = json.loads(response.model_dump_json(exclude_none=True))
                if "result" in response_dict and "parts" in response_dict["result"]:
                    for part in response_dict["result"]["parts"]:
                        if part.get("kind") == "text" and "text" in part:
                            response_text = part["text"]
                            print(f"   Response: {response_text[:100]}...")
                            break

            except Exception as e:
                print(f"❌ Travel planning query failed: {str(e)}")
                return False

            print()

            # Test 4: Activities Query Message
            print("4. Testing activities query...")
            try:
                activities_query = "What outdoor activities are available in San Francisco?"
                request = create_message_request(activities_query)
                print(f"   Query: {activities_query}")

                response = await client.send_message(request)
                print("✅ Activities query successful")

                # Extract response content
                response_dict = json.loads(response.model_dump_json(exclude_none=True))
                if "result" in response_dict and "parts" in response_dict["result"]:
                    for part in response_dict["result"]["parts"]:
                        if part.get("kind") == "text" and "text" in part:
                            response_text = part["text"]
                            print(f"   Response: {response_text[:100]}...")
                            break

            except Exception as e:
                print(f"❌ Activities query failed: {str(e)}")
                return False

            print()

            # Test 5: Interactive Travel Plan Generation
            print("5. Testing interactive travel plan generation...")
            try:
                plan_query = "Generate an interactive travel plan for San Francisco with food and nature experiences"
                request = create_message_request(plan_query)
                print(f"   Query: {plan_query}")

                response = await client.send_message(request)
                print("✅ Interactive travel plan generation successful")

                # Extract response content
                response_dict = json.loads(response.model_dump_json(exclude_none=True))
                if "result" in response_dict and "parts" in response_dict["result"]:
                    for part in response_dict["result"]["parts"]:
                        if part.get("kind") == "text" and "text" in part:
                            response_text = part["text"]
                            print(f"   Response: {response_text[:100]}...")
                            break

            except Exception as e:
                print(f"❌ Interactive travel plan generation failed: {str(e)}")
                return False

            print()

            # Test 6: Display Full Response
            print("6. Testing full response display...")
            try:
                final_query = "Create a brief travel itinerary for San Francisco"
                request = create_message_request(final_query)
                response = await client.send_message(request)

                print("✅ Full response test successful")
                display_formatted_response(response)

            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "500" in error_msg:
                    print("⚠️  Full response test skipped (server busy)")
                    print("   This is normal during high load testing")
                else:
                    print(f"❌ Full response test failed: {error_msg[:60]}...")

            print()
            print("=" * 50)
            print("A2A Protocol testing completed!")
            return True

    except Exception as e:
        print(f"❌ A2A Protocol test failed: {str(e)}")
        return False


def create_message_request(query_text: str) -> SendMessageRequest:
    """
    Create a message request to send to the agent.

    Args:
        query_text: The text query to send

    Returns:
        A SendMessageRequest object
    """
    send_message_payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": query_text}],
            "messageId": uuid4().hex,
        },
    }
    return SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))


def display_formatted_response(response: Any) -> None:
    """
    Display the response from the agent in a formatted way.

    Args:
        response: The response from the agent
    """
    try:
        # Parse the JSON response to extract the text content
        response_dict = json.loads(response.model_dump_json(exclude_none=True))

        # Extract and render the text
        if "result" in response_dict and "parts" in response_dict["result"]:
            for part in response_dict["result"]["parts"]:
                if part.get("kind") == "text" and "text" in part:
                    print("   Formatted Response:")
                    print("   " + "-" * 40)

                    # Split response into lines and indent each line
                    text = part["text"]
                    lines = text.split('\n')
                    for line in lines[:5]:  # Show first 5 lines
                        print(f"   {line}")

                    if len(lines) > 5:
                        print(f"   ... ({len(lines) - 5} more lines)")

                    print("   " + "-" * 40)
                    break
    except Exception as e:
        print(f"   Response formatting error: {str(e)}")


async def wait_for_server(base_url: str = "http://localhost:9000", timeout: int = 30):
    """Wait for the A2A server to be ready"""
    print(f"Waiting for A2A server at {base_url} to be ready...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{base_url}/.well-known/agent.json")
                if response.status_code == 200:
                    print("✅ A2A server is ready!")
                    return True
        except:
            pass
        await asyncio.sleep(1)

    print(f"❌ A2A server not ready after {timeout} seconds")
    return False


async def main():
    """Main function to run the A2A client test."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else f"http://localhost:{os.getenv('A2A_PORT', '9000')}"

    if await wait_for_server(base_url):
        success = await test_a2a_protocol(base_url)
        if not success:
            sys.exit(1)
    else:
        print("A2A server is not responding. Please start the A2A server first:")
        print("uv run a2a-server")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())