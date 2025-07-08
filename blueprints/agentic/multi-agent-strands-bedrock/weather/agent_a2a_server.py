"""A2A server implementation for the AI Agent."""

from strands import Agent
from strands.multiagent.a2a import A2AAgent
from agent import get_agent
from agent_memory_lost import MemoryLostConversationManager


def a2a_agent():
    """Start the A2A server for the AI Agent."""
    strands_agent = get_agent(conversation_manager=MemoryLostConversationManager())
    strands_a2a_agent = A2AAgent(
        agent=strands_agent
    )
    strands_a2a_agent.serve()


if __name__ == "__main__":
    a2a_agent()
