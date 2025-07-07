# Citymapper Travel Agent

A sophisticated travel planning assistant that provides comprehensive travel itineraries using specialized MCP servers for destinations, activities, dining, and route optimization.

## Features

- **Multi-Protocol Support**: MCP, A2A, and FastAPI interfaces
- **Activities Server**: Destination information, indoor/outdoor activities, and activity-tied dining
- **Mapper Server**: Route optimization and interactive HTML travel plan generation
- **State Management**: DynamoDB integration for conversation history
- **A2A Integration**: Works with orchestrator agent for coordinated travel planning

## Architecture

```
citymapper/
├── agent.py                    # Core agent logic
├── agent_config.py            # Configuration loader
├── agent.md                   # Agent configuration
├── mcp.json                   # MCP server configuration
├── agent_a2a_server.py        # A2A server implementation
├── agent_mcp_server.py        # MCP server implementation
├── agent_fastapi.py           # FastAPI server implementation
├── agent_state_manager.py     # DynamoDB state management
├── agent_interactive.py       # Interactive CLI
├── main.py                    # Entry points
├── pyproject.toml            # Dependencies
└── mcp-servers/
    ├── activities-mcp-server/
    │   ├── server.py
    │   ├── activities_data.json
    │   └── pyproject.toml
    └── mapper-mcp-server/
        ├── server.py
        └── pyproject.toml
```

## MCP Servers

### Activities MCP Server
Provides travel destination and activity information:
- `get_destination_info(city)` - Get destination overview and popular areas
- `get_indoor_activities(city, category, duration)` - Find indoor activities
- `get_outdoor_activities(city, category, duration)` - Find outdoor activities
- `get_activity_dining(city, activity_id)` - Get dining near activities
- `list_available_destinations()` - List supported destinations

### Mapper MCP Server
Provides route optimization and travel plan generation:
- `generate_interactive_travel_plan(city, days, focus, activities)` - Create HTML travel plans
- `optimize_route(locations)` - Optimize travel routes
- `get_location_coordinates(location_name, city)` - Get location coordinates

## Usage

### A2A Server (for Orchestrator Integration)
```bash
cd citymapper
python -m agent_a2a_server
```

### MCP Server
```bash
cd citymapper
python -m agent_mcp_server --transport stdio
```

### FastAPI Server
```bash
cd citymapper
python -m agent_fastapi
```

### Interactive CLI
```bash
cd citymapper
python -m agent_interactive
```

### All Servers
```bash
cd citymapper
python -m main
```

## Environment Variables

- `BEDROCK_MODEL_ID` - AWS Bedrock model ID (default: us.anthropic.claude-3-7-sonnet-20250219-v1:0)
- `MCP_PORT` - MCP server port (default: 8080)
- `A2A_PORT` - A2A server port (default: 9000)
- `FASTAPI_PORT` - FastAPI server port (default: 3000)
- `DYNAMODB_AGENT_STATE_TABLE_NAME` - DynamoDB table for state management
- `S3_BUCKET_NAME` - S3 bucket for travel plan storage (optional)
- `DEBUG` - Enable debug logging (1/true/yes)

## Integration with Orchestrator

The citymapper agent integrates with the orchestrator agent via A2A protocol. The orchestrator uses the `get_travel_planning` tool to delegate travel planning requests to the citymapper agent.

Example orchestrator usage:
```python
@tool
def get_travel_planning(query: str) -> str:
    """Get travel planning information including destinations, activities, dining, and interactive travel plans."""
    # Delegates to citymapper agent via A2A
```

## Supported Destinations

Currently supports:
- San Francisco, CA
- New York City, NY

Additional destinations can be added to `activities_data.json`.

## Deployment

### Production Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guides:
- 🚀 **EKS Deployment** with Helm charts
- 🐳 **Docker Compose** for local/development
- 📊 **Observability Setup** with self-hosted Langfuse
- 🧪 **Testing & Monitoring** procedures

### Quick Docker Compose Start
```bash
# Deploy with observability
./deploy-docker-compose.sh

# Access services
open http://localhost:3000  # Citymapper FastAPI
open http://localhost:3001  # Langfuse UI
```

## Deployment

### Production Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guides:
- 🚀 **EKS Deployment** with Helm charts
- 🐳 **Docker Compose** for local/development
- 📊 **Observability Setup** with self-hosted Langfuse
- 🧪 **Testing & Monitoring** procedures

### Quick Docker Compose Start
```bash
# Deploy with observability
./deploy-docker-compose.sh

# Access services
open http://localhost:3000  # Citymapper FastAPI
open http://localhost:3001  # Langfuse UI
```

## Dependencies

- strands-agents[a2a] >= 0.1.9
- mcp[cli] >= 1.9.4
- a2a-sdk >= 0.2.8
- fastapi >= 0.104.0
- boto3 >= 1.34.0
- rich, uvicorn, pyjwt, cryptography
- langfuse >= 3.1.0 (observability)
- ragas >= 0.2.0 (quality evaluation)
- langfuse >= 3.1.0 (observability)
- ragas >= 0.2.0 (quality evaluation)