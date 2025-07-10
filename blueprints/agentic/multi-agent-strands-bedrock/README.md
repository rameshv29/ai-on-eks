# Multi-Agent System with Strands and Bedrock

This project demonstrates a multi-agent system built with [Strands](https://github.com/trychroma/strands) and AWS Bedrock. The system consists of three main components:

1. **Orchestrator Agent**: Coordinates interactions between agents and handles user requests
2. **Weather Agent**: Provides weather information for specific locations and dates
3. **Citymapper Agent**: Provides travel planning information and recommendations

## Architecture

The multi-agent system uses the following technologies:

- **AWS Bedrock**: For large language model inference
- **Strands**: For agent framework and tools
- **A2A Protocol**: For agent-to-agent communication
- **DynamoDB**: For state management
- **FastAPI**: For REST API endpoints
- **Docker**: For containerization and local development

## Prerequisites

- Docker and Docker Compose
- AWS account with Bedrock access (for production deployment)
- Python 3.11+

## Local Development

### Setup

1. Clone the repository
2. Navigate to the project directory
3. Create a `.env` file based on `.env.example`
4. Start the services:

```bash
docker-compose up -d
```

### Testing

You can test the orchestrator API with:

```bash
curl -X POST http://localhost:3000/prompt \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, can you help me plan a trip to Seattle?"}'
```

## Production Deployment

For production deployment, follow these steps:

1. Configure AWS credentials with access to Bedrock
2. Set the appropriate environment variables in the `.env` file
3. Deploy the system using the provided deployment scripts

## Components

### Orchestrator Agent

The orchestrator agent is responsible for:
- Handling user requests
- Coordinating interactions between agents
- Managing conversation state

### Weather Agent

The weather agent provides:
- Current weather conditions
- Weather forecasts
- Weather alerts

### Citymapper Agent

The citymapper agent provides:
- Travel planning recommendations
- Points of interest
- Transportation options

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

## License

This project is licensed under the Apache 2.0 License.

