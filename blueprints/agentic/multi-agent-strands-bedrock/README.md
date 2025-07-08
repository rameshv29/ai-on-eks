# Multi-Agent System with Bedrock

A comprehensive multi-agent system built on AWS Bedrock that combines specialized agents for weather information and travel planning, orchestrated through a central coordinator.

## System Architecture

This system demonstrates the power of agent-to-agent (A2A) communication, allowing specialized agents to work together to solve complex user queries:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Weather Agent  │◄────►│  Orchestrator   │◄────►│ Citymapper Agent│
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                        ▲                        │
        │                        │                        │
        ▼                        │                        ▼
┌─────────────────┐              │              ┌─────────────────┐
│  Weather Data   │              │              │ Activities &     │
│  MCP Server     │              │              │ Mapper Servers   │
└─────────────────┘              │              └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │     User        │
                        │                 │
                        └─────────────────┘
```

### Components

1. **Orchestrator Agent**: Central coordinator that routes user queries to specialized agents
2. **Weather Agent**: Provides weather forecasts and conditions for locations worldwide
3. **Citymapper Agent**: Creates travel itineraries with activities, dining, and route optimization
4. **MCP Servers**: Specialized tool servers that provide domain-specific capabilities

## Quick Start

Deploy the entire multi-agent system with a single command:

```bash
cd blueprints/agentic/multi-agent-strands-bedrock
./deploy-multi-agent.sh
```

This will start:
- All agent services (Orchestrator, Weather, Citymapper)
- MCP servers for specialized tools
- Langfuse observability platform

### Access the System

- **Orchestrator FastAPI**: http://localhost:3000
- **Weather Agent FastAPI**: http://localhost:3001
- **Citymapper Agent FastAPI**: http://localhost:3002
- **Langfuse UI**: http://localhost:8000

## Environment Setup

Create a `.env` file in the `multi-agent-strands-bedrock` directory:

```
# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Bedrock Model
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0

# Port Configuration
ORCHESTRATOR_PORT=3000
WEATHER_FASTAPI_PORT=3001
CITYMAPPER_FASTAPI_PORT=3002
WEATHER_A2A_PORT=9000
CITYMAPPER_A2A_PORT=9001
WEATHER_MCP_PORT=8080
CITYMAPPER_MCP_PORT=8081

# Optional Configuration
DYNAMODB_AGENT_STATE_TABLE_NAME=agent-state-table
S3_BUCKET_NAME=travel-plans-bucket
DEBUG=1
```

## Testing the System

### End-to-End Test

Test the complete multi-agent system:

```bash
cd blueprints/agentic/multi-agent-strands-bedrock
python test_multi_agent.py
```

### Example Queries

Try these example queries with the orchestrator:

1. "What's the weather like in San Francisco today?"
2. "Plan a 3-day trip to New York City with focus on museums and parks"
3. "I'm planning a trip to San Francisco next week. What's the weather forecast and what activities would you recommend?"

## Individual Agent Documentation

For detailed information about each agent:

- [Orchestrator Agent](./orchestrator/README.md)
- [Weather Agent](./weather/README.md)
- [Citymapper Agent](./citymapper/README.md)

## Deployment Options

### Docker Compose (Development)

For local development and testing:

```bash
docker-compose up -d
```

### EKS Deployment (Production)

For production deployment on Amazon EKS:

```bash
cd blueprints/agentic/multi-agent-strands-bedrock
./deploy-eks.sh
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed production deployment instructions.

## Observability

This system includes Langfuse for comprehensive observability:

- Trace all agent interactions
- Monitor token usage and costs
- Evaluate response quality
- Track user feedback

Access the Langfuse UI at http://localhost:8000 after deployment.

## Architecture Details

### Agent-to-Agent (A2A) Communication

Agents communicate using the A2A protocol, which enables:
- Structured message passing between agents
- Tool delegation for specialized tasks
- Context preservation across agent boundaries
- Stateful conversations with multiple agents

### Model Configuration Protocol (MCP)

MCP enables agents to dynamically discover and use tools:
- Weather data retrieval tools
- Travel planning and route optimization tools
- Location-based activity recommendations

### State Management

All agents use DynamoDB for conversation state management:
- Persistent conversation history
- User session isolation
- Seamless conversation resumption

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on contributing to this project.
