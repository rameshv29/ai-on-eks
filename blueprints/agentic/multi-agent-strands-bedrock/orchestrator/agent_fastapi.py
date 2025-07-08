#!/usr/bin/env python3
"""
Orchestrator Agent FastAPI Server

Provides a FastAPI REST API interface for the orchestrator agent, allowing HTTP clients
to interact with the agent functionality.
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import uvicorn
import a2a_agent
from strands.models import BedrockModel
from strands import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug logging
logger.info(f"Starting Orchestrator Agent FastAPI server")

# Pydantic models for request/response
class PromptRequest(BaseModel):
    text: str

class PromptResponse(BaseModel):
    text: str

class HealthResponse(BaseModel):
    status: str

# Initialize FastAPI app
app = FastAPI(
    title="Orchestrator Agent FastAPI",
    description="FastAPI REST API interface for the Orchestrator Agent",
    version="1.0.0"
)

# Define a mock agent for testing
class MockAgent:
    def __call__(self, prompt):
        return f"This is a mock response to: {prompt}\n\nThe actual agent couldn't be initialized because AWS Bedrock credentials are not properly configured."

# Initialize the agent
# Initialize the agent
try:
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    bedrock_model = BedrockModel(model_id=model_id)
    agent = Agent(
        model=bedrock_model,
        system_prompt=a2a_agent.load_system_prompt(),
        tools=[a2a_agent.get_weather, a2a_agent.get_travel_planning]
    )
    logger.info("Successfully initialized Bedrock agent")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock model: {e}")
    # Create a mock agent for testing
    agent = MockAgent()
    logger.info("Using mock agent for testing")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy")

@app.post("/prompt", response_model=PromptResponse)
async def prompt(request: PromptRequest):
    """Process prompt with the Orchestrator Agent"""
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        prompt = request.text.strip()
        logger.info(f"User prompt: {prompt}")

        # Process the text with the agent
        response = agent(prompt)

        return PromptResponse(text=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing prompt request: {str(e)}", exc_info=True)
        # Return a mock response instead of raising an error
        return PromptResponse(text=f"I'm sorry, I encountered an error processing your request: {str(e)}\n\nThis is likely because AWS Bedrock credentials are not properly configured.")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Orchestrator Agent FastAPI",
        "endpoints": {
            "health": "/health",
            "prompt": "/prompt"
        }
    }

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "3000"))
    debug = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")

    # Start the server
    logger.info(f"Starting Orchestrator Agent FastAPI server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="debug" if debug else "info",
            reload=debug
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
