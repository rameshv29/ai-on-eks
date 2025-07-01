"""Agent module for providing AI assistant functionality."""

import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple

from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands.types.content import Messages

# Cache for MCP tools to avoid reloading on every get_agent() call
_mcp_tools_cache = None


@tool
def agent_tool(query: str) -> str:
    """
    Process and respond to weather forecast or alert queries.

    Args:
        query: The user's question or request

    Returns:
        A helpful response addressing the user's query
    """
    try:
        agent = get_agent()
        response = str(agent(query))
        if response:
            return response
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return "I apologize, but I encountered an error while processing your request. Please try again later."

    return "I apologize, but I couldn't properly analyze your question. Could you please rephrase or provide more context?"


def _load_agent_config() -> Tuple[str, str, str]:
    """
    Load agent configuration from agent.md file.

    Returns:
        Tuple[str, str, str]: (name, description, system_prompt)
    """
    # Get agent config file path from environment variable or use default
    config_file = os.getenv("AGENT_CONFIG_FILE", os.path.join(os.path.dirname(__file__), "agent.md"))

    if not os.path.exists(config_file):
        print(f"Agent config file not found at {config_file}")
        # Try fallback to cloudbot.md
        fallback_config = os.path.join(os.path.dirname(__file__), "cloudbot.md")
        if os.path.exists(fallback_config):
            print(f"Using fallback configuration: {fallback_config}")
            config_file = fallback_config
        else:
            raise FileNotFoundError(f"No agent configuration file found. Please provide either {config_file} or set AGENT_CONFIG_FILE environment variable.")

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the markdown content
        name = _extract_section(content, "Agent Name")
        description = _extract_section(content, "Agent Description")
        system_prompt = _extract_section(content, "System Prompt")

        if not name or not description or not system_prompt:
            raise ValueError(f"Agent configuration file {config_file} is missing required sections: Agent Name, Agent Description, or System Prompt")

        return name.strip(), description.strip(), system_prompt.strip()

    except Exception as e:
        print(f"Error reading agent config file {config_file}: {str(e)}")
        raise


def _extract_section(content: str, section_name: str) -> Optional[str]:
    """
    Extract a section from markdown content.

    Args:
        content: The markdown content
        section_name: The section header to look for

    Returns:
        Optional[str]: The section content or None if not found
    """
    # Pattern to match ## Section Name followed by content until next ## or end
    pattern = rf"##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return None

def get_agent(messages: Optional[Messages]=None) -> Agent:
    """
    Create and return an Agent instance with dynamically loaded MCP tools.

    Returns:
        Agent: A configured AI assistant agent with tools from enabled MCP servers
    """
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    bedrock_model = BedrockModel(model_id=model_id)

    # Load agent configuration from agent.md file
    agent_name, agent_description, system_prompt = _load_agent_config()

    try:
        # Load and combine tools from all enabled MCP servers (cached)
        all_tools = _get_cached_mcp_tools()

        # Create the agent with configuration from agent.md
        agent = Agent(
            name=agent_name,
            description=agent_description,
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=all_tools,
            messages=messages
        )

        return agent

    except Exception as e:
        print(f"Error getting agent: {str(e)}")
        # Return a fallback agent when MCP client fails
        fallback_agent = Agent(
            model=bedrock_model,
            system_prompt="""I am an AI Assistant, but I'm currently experiencing technical difficulties accessing my tools.
I apologize for the inconvenience. Please try again later or contact support if the issue persists.""",
            tools=[],
        )
        return fallback_agent


def _get_cached_mcp_tools() -> List[Any]:
    """Get MCP tools from cache or load them if not cached."""
    global _mcp_tools_cache
    if _mcp_tools_cache is None:
        _mcp_tools_cache = _load_mcp_tools_from_config()
    return _mcp_tools_cache


def _load_mcp_tools_from_config() -> List[Any]:
    """
    Load MCP tools from all enabled servers defined in mcp.json.

    Returns:
        List[Any]: Combined list of tools from all enabled MCP servers
    """
    config_path = os.path.join(os.path.dirname(__file__), "mcp.json")

    if not os.path.exists(config_path):
        print(f"MCP configuration file not found at {config_path}")
        return []

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading MCP configuration: {str(e)}")
        return []

    mcp_servers = config.get("mcpServers", {})
    all_tools = []

    for server_name, server_config in mcp_servers.items():
        if server_config.get("disabled", False):
            print(f"Skipping disabled MCP server: {server_name}")
            continue

        try:
            print(f"Loading tools from MCP server: {server_name}")
            mcp_client = _create_mcp_client_from_config(server_name, server_config)
            mcp_client.start()
            tools = mcp_client.list_tools_sync()
            all_tools.extend(tools)
            print(f"Loaded {len(tools)} tools from {server_name}")
        except Exception as e:
            print(f"Error loading tools from MCP server {server_name}: {str(e)}")
            continue

    print(f"Total tools loaded: {len(all_tools)}")
    return all_tools


def _create_mcp_client_from_config(server_name: str, server_config: Dict[str, Any]) -> MCPClient:
    """
    Create an MCP client based on server configuration.

    Args:
        server_name: Name of the MCP server
        server_config: Configuration dictionary for the server

    Returns:
        MCPClient: Configured MCP client

    Raises:
        ValueError: If server configuration is invalid
    """
    # Check if it's a URL-based server (streamable-http)
    if "url" in server_config:
        url = server_config["url"]
        print(f"Creating streamable-http MCP client for {server_name} at {url}")
        return MCPClient(
            lambda: streamablehttp_client(url)
        )

    # Check if it's a command-based server (stdio)
    elif "command" in server_config and "args" in server_config:
        command = server_config["command"]
        args = server_config["args"]
        env = server_config.get("env", {})

        if env:
            print(f"Creating stdio MCP client for {server_name} with command: {command} {' '.join(args)} and env vars: {list(env.keys())}")
        else:
            print(f"Creating stdio MCP client for {server_name} with command: {command} {' '.join(args)}")

        return MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command=command,
                    args=args,
                    env=env if env else None
                )
            )
        )

    else:
        raise ValueError(f"Invalid MCP server configuration for {server_name}: must have either 'url' or both 'command' and 'args'")



if __name__ == "__main__":
    agent_tool("Hello, how can you help me?")
