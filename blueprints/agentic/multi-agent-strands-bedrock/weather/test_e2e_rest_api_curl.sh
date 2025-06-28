#!/bin/bash

# =============================================================================
# 🌤️  Weather Agent Workshop - API Testing Script
# =============================================================================
# This script demonstrates how to interact with the Weather Agent REST API
# Perfect for workshop participants to test the deployed agent
# =============================================================================

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}🌤️  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}\n"
}

# Function to print step information
print_step() {
    echo -e "${YELLOW}📋 Step $1: $2${NC}"
}

# Function to print query information
print_query() {
    echo -e "${PURPLE}❓ Query: $1${NC}"
    echo -e "${CYAN}🔗 Endpoint: $2${NC}"
    echo ""
}

# Function to make API call and format response
test_weather_api() {
    local query="$1"
    local step_num="$2"
    local description="$3"

    print_step "$step_num" "$description"
    print_query "$query" "http://localhost:3000/chat"

    echo -e "${GREEN}🚀 Sending request...${NC}"

    # Make the API call
    response=$(curl -X POST http://localhost:3000/chat \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d "{\"query\": \"$query\"}" \
        --silent \
        --show-error \
        --max-time 30)

    # Check if curl was successful
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Response received:${NC}"
        echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────┐${NC}"

        # Try to extract and format the response
        if command -v jq >/dev/null 2>&1; then
            # Use jq to pretty print and extract response
            formatted_response=$(echo "$response" | jq -r '.response // .message // .' 2>/dev/null)
            if [ "$formatted_response" != "null" ] && [ "$formatted_response" != "" ]; then
                echo -e "${NC}$formatted_response${NC}" | sed 's/^/│ /'
            else
                echo "$response" | jq . 2>/dev/null || echo "$response" | sed 's/^/│ /'
            fi
        else
            # Fallback without jq
            echo "$response" | sed 's/^/│ /'
        fi

        echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────┘${NC}"
    else
        echo -e "${RED}❌ Error: Failed to connect to the weather agent${NC}"
        echo -e "${YELLOW}💡 Make sure the weather agent is running on http://localhost:3000${NC}"
    fi

    echo ""
}

# Function to test health endpoint
test_health() {
    print_step "0" "Health Check"
    echo -e "${PURPLE}❓ Checking agent health${NC}"
    echo -e "${CYAN}🔗 Endpoint: http://localhost:3000/health${NC}"
    echo ""

    echo -e "${GREEN}🚀 Sending health check...${NC}"

    health_response=$(curl -X GET http://localhost:3000/health \
        --silent \
        --show-error \
        --max-time 10)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Health check successful:${NC}"
        echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────┐${NC}"
        if command -v jq >/dev/null 2>&1; then
            echo "$health_response" | jq . 2>/dev/null | sed 's/^/│ /' || echo "$health_response" | sed 's/^/│ /'
        else
            echo "$health_response" | sed 's/^/│ /'
        fi
        echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────┘${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        echo -e "${YELLOW}💡 The weather agent may not be running or accessible${NC}"
        return 1
    fi

    echo ""
}

# Main execution
main() {
    print_header "Weather Agent Workshop - API Testing"

    echo -e "${YELLOW}🎯 This script will test the Weather Agent REST API with various queries${NC}"
    echo -e "${YELLOW}📝 Perfect for workshop participants to see the agent in action!${NC}"
    echo ""

    # Test health endpoint first
    test_health
    if [ $? -ne 0 ]; then
        echo -e "${RED}⚠️  Cannot proceed with tests - agent is not responding${NC}"
        echo -e "${YELLOW}💡 Please ensure the weather agent is running with: kubectl port-forward service/weather-agent 3000:rest${NC}"
        exit 1
    fi

    # Test various weather queries
    test_weather_api "What is the weather forecast for New York?" "1" "Basic Weather Forecast"

    test_weather_api "Are there any weather alerts for Florida?" "2" "Weather Alerts Query"

    test_weather_api "What's the weather like in Seattle this week?" "3" "Weekly Weather Forecast"

    test_weather_api "Tell me about the weather conditions in San Francisco" "4" "Current Weather Conditions"

    test_weather_api "Is it going to rain in Chicago tomorrow?" "5" "Specific Weather Question"

    # Final summary
    print_header "Workshop Test Summary"
    echo -e "${GREEN}🎉 Weather Agent API testing completed!${NC}"
    echo -e "${CYAN}📊 Test Results:${NC}"
    echo -e "${YELLOW}   • Health Check: Passed ✅${NC}"
    echo -e "${YELLOW}   • Weather Forecasts: 5 queries tested 🌤️${NC}"
    echo -e "${YELLOW}   • API Endpoints: REST API (port 3000) 🔗${NC}"
    echo ""
    echo -e "${PURPLE}🔧 Additional Testing Options:${NC}"
    echo -e "${CYAN}   • MCP Protocol: Use test_mcp_client.py (port 8080)${NC}"
    echo -e "${CYAN}   • A2A Protocol: Use test_a2a_client.py (port 9000)${NC}"
    echo -e "${CYAN}   • REST API:     Use test_rest_api.py   (port 3000)${NC}"
    echo ""
    echo -e "${GREEN}✨ Workshop participants can now interact with the Weather Agent! ✨${NC}"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
