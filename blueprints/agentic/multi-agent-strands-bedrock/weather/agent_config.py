"""Agent configuration utilities for loading agent settings from markdown files."""

import os
import re
from typing import Optional, Tuple


def load_agent_config(config_file: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Load agent configuration from agent.md file.

    Args:
        config_file: Optional path to config file. If None, uses AGENT_CONFIG_FILE env var or default agent.md

    Returns:
        Tuple[str, str, str]: (name, description, system_prompt)

    Raises:
        FileNotFoundError: If no configuration file is found
        ValueError: If configuration file is missing required sections
    """
    # Get agent config file path from parameter, environment variable, or use default
    if config_file is None:
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
