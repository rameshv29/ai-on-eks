from strands import Agent
from strands.types.content import Message, Messages
from strands.types.exceptions import ContextWindowOverflowException
from strands.agent.conversation_manager import ConversationManager, SlidingWindowConversationManager


class MemoryLostConversationManager(SlidingWindowConversationManager):
    """
    A conversation manager that resets the agent's message history to empty array.

    This class extends SlidingWindowConversationManager to inherit the reduce_context method
    but overrides apply_management to completely clear the agent's message history instead
    of using a sliding window approach.
    """

    def apply_management(self, agent: "Agent") -> None:
        """
        Override the apply_management method to reset agent messages to empty array.

        Args:
            _agent: The agent whose message history should be reset
        """
        # Reset the agent's messages to an empty array
        print("Check messages before resetting agent messages")
        print(agent.messages)  # Debugging
        agent.messages = []
