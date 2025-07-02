"""MCP server implementation for the AI Agent."""

import argparse
import os

from mcp.server.fastmcp import FastMCP
from agent import get_agent

from agent_config import load_agent_config
# Load agent configuration
agent_name, agent_description, system_prompt = load_agent_config()

# Initialize FastMCP server with dynamic name
mcp = FastMCP(agent_name)

@mcp.tool(name=agent_name, description=agent_description)
async def query_agent(query: str) -> str:
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
