# Citymapper MCP Blueprint for AI on EKS

AI-powered travel planning application using Model Context Protocol (MCP) architecture, designed for Amazon EKS deployment.

## Overview

This blueprint demonstrates how to build and deploy an AI travel planning assistant that generates interactive travel itineraries with maps, route optimization, and activity recommendations.

## Architecture

- **Activities Server** - Handles destinations, activities, and dining recommendations
- **Mapper Service** - Route optimization and interactive HTML generation
- **AI Agent** - Claude 3 Haiku integration via Amazon Bedrock

## Prerequisites

- Amazon EKS cluster
- AWS CLI configured
- Docker and kubectl
- Python 3.8+

## Quick Start

### Local Development
```bash
# Start services
docker-compose up -d

# Generate travel plan
docker-compose up --build demo
```

### EKS Deployment
```bash
# Deploy to your EKS cluster
kubectl apply -f k8s/
```

## Features

- **AI-Powered Planning** - Natural language travel requests
- **Interactive Maps** - Real-time route visualization
- **Activity Recommendations** - Indoor/outdoor activities with dining
- **S3 Integration** - Secure plan sharing with presigned URLs
- **Smart Scheduling** - Duplicate activity detection

## AWS Services

- **Amazon EKS** - Container orchestration
- **Amazon Bedrock** - LLM inference
- **Amazon S3** - File storage
- **Amazon DynamoDB** - Data persistence

## Usage

1. Start the services using Docker Compose
2. Access the demo at `http://localhost:5001`
3. Request a travel plan: "Plan a 3-day trip to San Francisco"
4. Get an interactive HTML plan with maps and routes

## Configuration

Set these environment variables:
```bash
AWS_PROFILE=your-profile
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

## Sample Output

The system generates interactive HTML travel plans with:
- Day-by-day itineraries
- Interactive maps with markers
- Route optimization
- Activity details and dining recommendations
- Shareable S3 links
