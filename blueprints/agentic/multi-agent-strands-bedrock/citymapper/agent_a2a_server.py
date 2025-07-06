"""A2A server implementation for the Citymapper Travel Agent."""

from strands.multiagent.a2a import A2AServer

from agent import get_agent


def a2a_agent():
    """Start the A2A server for the Citymapper Travel Agent."""
    strands_agent = get_agent()
    strands_a2a_agent = A2AServer(
        agent=strands_agent
    )
    strands_a2a_agent.serve()


if __name__ == "__main__":
    a2a_agent()