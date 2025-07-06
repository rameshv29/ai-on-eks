#!/usr/bin/env python3
"""
Test script for the Citymapper Agent MCP (Model Context Protocol) Server

This script tests the MCP endpoints to ensure they work correctly.
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List

import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import (
    Tool,
)


async def test_mcp_protocol(base_url: str = "http://localhost:8080"):
    """Test the Citymapper Agent MCP Protocol endpoints"""

    print(f"Testing Citymapper Agent MCP Protocol at {base_url}")
    print("=" * 50)

    try:
        # Create MCP client session
        async with streamablehttp_client(f"{base_url}/mcp/") as (read, write, get_session_id):
            async with ClientSession(read, write) as session:

                # Test 1: Initialize MCP Session
                print("1. Testing MCP session initialization...")
                try:
                    init_result = await session.initialize()
                    print("✅ MCP session initialized successfully")
                    print(f"   Protocol Version: {init_result.protocolVersion}")
                    print(f"   Server Name: {init_result.serverInfo.name}")
                    print(f"   Server Version: {init_result.serverInfo.version}")

                except Exception as e:
                    print(f"❌ MCP session initialization failed: {str(e)}")
                    return False

                print()

                # Test 2: List Available Tools
                print("2. Testing tool discovery...")
                try:
                    tools_result = await session.list_tools()
                    tools = tools_result.tools
                    print("✅ Tool discovery successful")
                    print(f"   Available Tools: {len(tools)}")

                    for tool in tools:
                        print(f"   - {tool.name}: {tool.description}")
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            schema = tool.inputSchema
                            if isinstance(schema, dict) and 'properties' in schema:
                                props = list(schema['properties'].keys())
                                print(f"     Parameters: {', '.join(props)}")

                except Exception as e:
                    print(f"❌ Tool discovery failed: {str(e)}")
                    return False

                print()

                # Test 3: Travel Planning Query
                print("3. Testing travel planning query...")
                try:
                    travel_query = "Plan a 3-day trip to San Francisco focusing on food and nature"
                    print(f"   Query: {travel_query}")

                    travel_result = await session.call_tool(
                        name="Citymapper Travel Agent",
                        arguments={"query": travel_query}
                    )

                    print("✅ Travel planning query successful")
                    if travel_result.content:
                        content = travel_result.content[0]
                        if hasattr(content, 'text'):
                            response_text = content.text
                            print(f"   Response: {response_text[:200]}...")
                        else:
                            print(f"   Response: {str(content)[:200]}...")

                except Exception as e:
                    print(f"❌ Travel planning query failed: {str(e)}")

                print()

                # Test 4: Activities Query
                print("4. Testing activities query...")
                try:
                    activities_query = "What outdoor activities are available in San Francisco?"
                    print(f"   Query: {activities_query}")

                    activities_result = await session.call_tool(
                        name="Citymapper Travel Agent",
                        arguments={"query": activities_query}
                    )

                    print("✅ Activities query successful")
                    if activities_result.content:
                        content = activities_result.content[0]
                        if hasattr(content, 'text'):
                            response_text = content.text
                            print(f"   Response: {response_text[:200]}...")
                        else:
                            print(f"   Response: {str(content)[:200]}...")

                except Exception as e:
                        print(f"❌ Activities query failed: {str(e)}")

                print()

                # Test 5: Interactive Travel Plan Generation
                print("5. Testing interactive travel plan generation...")
                try:
                    plan_query = "Generate an interactive travel plan for a weekend in San Francisco with food and nature focus"
                    print(f"   Query: {plan_query}")

                    plan_result = await session.call_tool(
                        name="Citymapper Travel Agent",
                        arguments={"query": plan_query}
                    )

                    print("✅ Interactive travel plan generation successful")
                    print("   Formatted Response:")
                    print("   " + "-" * 40)
                    if plan_result.content:
                        content = plan_result.content[0]
                        if hasattr(content, 'text'):
                            response_text = content.text
                            # Format the response nicely
                            lines = response_text.split('\n')
                            for line in lines[:10]:  # Show first 10 lines
                                print(f"   {line}")
                            if len(lines) > 10:
                                print("   ...")
                        else:
                            print(f"   {str(content)}")
                    print("   " + "-" * 40)

                except Exception as e:
                    print(f"❌ Interactive travel plan generation failed: {str(e)}")

                print()
                print("=" * 50)
                print("MCP Protocol testing completed!")
                return True

    except Exception as e:
        print(f"❌ MCP Protocol test failed: {str(e)}")
        # Print more detailed error information
        import traceback
        print("   Detailed error:")
        traceback.print_exc()
        return False


async def wait_for_server(base_url: str = "http://localhost:8080", timeout: int = 30):
    """Wait for the MCP server to be ready"""
    print(f"Waiting for MCP server at {base_url} to be ready...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                # Try to connect to the MCP endpoint
                response = await client.get(f"{base_url}/mcp/")
                # MCP server should return 406 for regular HTTP requests (expects SSE)
                if response.status_code in [200, 406]:  # 406 is expected for MCP endpoint
                    print("✅ MCP server is ready!")
                    return True
        except:
            pass
        await asyncio.sleep(1)

    print(f"❌ MCP server not ready after {timeout} seconds")
    return False


async def test_mcp_http_endpoint(base_url: str = "http://localhost:8080"):
    """Test basic HTTP connectivity to MCP server"""
    print("0. Testing MCP server HTTP connectivity...")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(f"{base_url}/mcp/")
            print("✅ MCP HTTP endpoint accessible")
            print(f"   Status Code: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            if response.status_code == 406:
                print("   Server correctly expects SSE connection (406 Not Acceptable)")
            return True
    except Exception as e:
        print(f"❌ MCP HTTP endpoint failed: {str(e)}")
        return False


async def main():
    """Main function to run the MCP client test."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else f"http://localhost:{os.getenv('MCP_PORT', '8080')}"

    if await wait_for_server(base_url):
        # First test basic HTTP connectivity
        http_ok = await test_mcp_http_endpoint(base_url)
        if not http_ok:
            print("Basic HTTP connectivity failed. Please check the MCP server.")
            sys.exit(1)

        print()

        # Then test full MCP protocol
        success = await test_mcp_protocol(base_url)
        if not success:
            sys.exit(1)
    else:
        print("MCP server is not responding. Please start the MCP server first:")
        print("uv run mcp-server")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())