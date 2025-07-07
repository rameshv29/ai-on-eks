"""Interactive command-line interface for the Citymapper Travel Agent."""

import logging
from rich.console import Console
from agent import get_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def interactive_agent():
    """Start an interactive command-line session with the Citymapper Travel Agent."""
    logger.info("Starting Citymapper Travel Agent Interactive Session")
    
    try:
        # Get the agent
        agent = get_agent()
        logger.info("Citymapper Travel Agent successfully created")

        # Interactive session
        console = Console()
        console.print("[bold green]Citymapper Travel Agent[/bold green]")
        console.print("Ask about travel plans, destinations, activities, etc. Type 'exit' to quit.")
        logger.info("Starting interactive session")

        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                logger.info("User requested to exit")
                break

            # Process the user input with the agent
            logger.info(f"Processing user input: '{user_input}'")
            try:
                response = agent(user_input)
                logger.info("Successfully generated response")
                console.print(f"\n[bold blue]Citymapper Agent:[/bold blue] {response}")
            except Exception as e:
                logger.error(f"Error generating response: {e}", exc_info=True)
                console.print(f"\n[bold red]Error:[/bold red] Failed to generate response: {str(e)}")

        logger.info("Interactive session ended")
    except Exception as e:
        logger.error(f"Error in interactive session: {e}", exc_info=True)
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    interactive_agent()