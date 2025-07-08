# Multi-Agent System Troubleshooting Guide

This document provides solutions to common issues encountered when running the multi-agent system.

## AWS Region Error

**Issue**: The citymapper agent fails with `botocore.exceptions.NoRegionError: You must specify a region.`

**Solution**: Modify the `agent_state_manager.py` file to explicitly set the region and endpoint URL:

```python
# Explicitly set region and endpoint URL from environment variables
aws_region = os.environ.get('AWS_REGION', 'us-west-2')
endpoint_url = os.environ.get('AWS_ENDPOINT_URL')

logger.info(f"Connecting to DynamoDB with region={aws_region}, endpoint_url={endpoint_url}")

ddb = boto3.resource('dynamodb', 
                    region_name=aws_region,
                    endpoint_url=endpoint_url)
```

## Missing agent_fastapi.py in Orchestrator

**Issue**: The orchestrator service fails with `Error loading ASGI app. Could not import module "agent_fastapi".`

**Solution**: Create an `agent_fastapi.py` file in the orchestrator directory with the necessary FastAPI setup.

## Bedrock Authentication Error

**Issue**: The orchestrator agent fails with `botocore.exceptions.ClientError: An error occurred (InternalFailure) when calling the ConverseStream operation`

**Solution**: Create a mock agent for testing when AWS Bedrock credentials are not properly configured:

```python
# Define a mock agent for testing
class MockAgent:
    def __call__(self, prompt):
        return f"This is a mock response to: {prompt}\n\nThe actual agent couldn't be initialized because AWS Bedrock credentials are not properly configured."

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
```

## Error Handling in API Endpoints

**Issue**: API endpoints return 500 errors when there are issues with the agent.

**Solution**: Improve error handling in the API endpoints to return helpful error messages:

```python
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
```

## Running the System Locally

To run the multi-agent system locally:

1. Make sure Docker and Docker Compose are installed
2. Navigate to the `blueprints/agentic/multi-agent-strands-bedrock` directory
3. Run `docker-compose up -d` to start all services
4. Test the orchestrator API with:
   ```bash
   curl -X POST http://localhost:3000/prompt -H "Content-Type: application/json" -d '{"text": "Hello, can you help me plan a trip to Seattle?"}'
   ```

## Running the System on AWS

To run the system on AWS:

1. Configure AWS credentials with access to Bedrock
2. Set the appropriate environment variables in the `.env` file
3. Deploy the system using the provided deployment scripts
