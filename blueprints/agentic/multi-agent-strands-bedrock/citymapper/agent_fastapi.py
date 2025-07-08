#!/usr/bin/env python3
"""
Citymapper Travel Agent FastAPI Server

Provides a FastAPI REST API interface for the travel agent, allowing HTTP clients
to interact with the agent functionality with conversation state management.
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import uvicorn
import jwt
import agent_state_manager
from agent import get_agent

COGNITO_JWKS_URL = os.environ.get('COGNITO_JWKS_URL')
# Disable authentication for testing if COGNITO_JWKS_URL contains localhost or is a test URL
TESTING_MODE = not COGNITO_JWKS_URL or 'localhost' in COGNITO_JWKS_URL or os.environ.get('DISABLE_AUTH') == '1'
jwks_client = jwt.PyJWKClient(COGNITO_JWKS_URL) if COGNITO_JWKS_URL and not TESTING_MODE else None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug logging
logger.info(f"COGNITO_JWKS_URL: {COGNITO_JWKS_URL}")
logger.info(f"Testing mode: {TESTING_MODE}")
logger.info(f"Authentication enabled: {not TESTING_MODE}")

# Pydantic models for request/response
class PromptRequest(BaseModel):
    text: str

class PromptResponse(BaseModel):
    text: str

class HealthResponse(BaseModel):
    status: str

# Initialize FastAPI app
app = FastAPI(
    title="Citymapper Travel Agent FastAPI",
    description="FastAPI REST API interface for the Citymapper Travel Agent",
    version="1.0.0"
)

def _get_jwt_claims(authorization_header: str) -> Any:
    if not jwks_client:
        # Return mock claims for testing when COGNITO_JWKS_URL is not set
        return {"sub": "test-user", "username": "test-user"}

    jwt_string = authorization_header.split(" ")[1]
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(jwt_string)
        claims = jwt.decode(jwt_string, signing_key.key, algorithms=["RS256"])
    except Exception as e:
            logger.error("Failed to parse authorization_header", exc_info=True)
            raise HTTPException(status_code=401, detail="Invalid authorization_header")
    print(claims)
    return claims

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy")

@app.post("/prompt", response_model=PromptResponse)
async def prompt(request: PromptRequest, authorization: Optional[str] = Header(None)):
    """Process prompt with the Citymapper Travel Agent"""
    # Validate and parse JWT token (optional for testing)
    try:
        logger.info(f"Testing mode: {TESTING_MODE}")
        logger.info(f"Authorization header present: {authorization is not None}")

        if not TESTING_MODE and not authorization:
            logger.info("Authentication required but no header provided")
            raise HTTPException(status_code=401, detail="Authorization header required")

        if authorization and not TESTING_MODE:
            claims = _get_jwt_claims(authorization)
            user_id = claims.get("sub")
            username = claims.get("username")
        else:
            # Use default values for testing when no auth is configured
            logger.info("Using test user credentials (testing mode)")
            user_id = "test-user"
            username = "test-user"

        logger.info(f"User authenticated. user_id={user_id} username={username}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to parse JWT", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid authorization token")

    # Process the prompt
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        prompt = request.text.strip()
        logger.info(f"User username: {username}")
        logger.info(f"User id: {user_id}")
        logger.info(f"User prompt: {prompt}")
        messages = agent_state_manager.restore(user_id)

        # Get agent instance (lazy loading)
        agent = get_agent(messages)

        # Process the text with the agent
        response = str(agent(prompt))

        agent_state_manager.save(user_id, agent)

        return PromptResponse(text=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing prompt request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process prompt request: {str(e)}" if os.getenv('DEBUG') else "Internal server error"
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Citymapper Travel Agent FastAPI",
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
    logger.info(f"Starting Citymapper Travel Agent FastAPI server on {host}:{port}")
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
