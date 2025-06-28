"""MCP server implementation for the AI Agent."""

import argparse
import os

from mcp.server.fastmcp import FastMCP
from agent import get_agent

# Initialize FastMCP server
mcp = FastMCP("ai-agent")

@mcp.tool()
async def query_agent(query: str) -> str:
    """
    Process and respond to weather forecast or alert queries.

    Args:
        query: The user's input

    Returns:
        A response to the user's query
    """
    # Get agent configuration for server naming
    agent_instance = get_agent()
    return str(agent_instance(query))


def mcp_agent():
    """Main entry point for the AI agent MCP server."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AI Agent MCP Server')
    parser.add_argument(
        '--transport',
        choices=['stdio', 'streamable-http'],
        default='streamable-http',
        help='Transport protocol to use streamable-http(default) or stdio'
    )

    args = parser.parse_args()

    # Run MCP server with specified transport
    mcp.settings.port = int(os.getenv("MCP_PORT", "8080"))
    mcp.settings.host = '0.0.0.0'
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    mcp_agent()
