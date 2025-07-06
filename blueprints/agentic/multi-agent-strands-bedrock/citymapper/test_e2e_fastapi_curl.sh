#!/bin/bash

# =============================================================================
# 🗺️  Citymapper Agent Workshop - FastAPI Testing Script
# =============================================================================
# This script demonstrates how to interact with the Citymapper Agent FastAPI
# Perfect for workshop participants to test the deployed FastAPI agent
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
    echo -e "${CYAN}🗺️  $1${NC}"
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
test_citymapper_fastapi() {
    local query="$1"
    local step_num="$2"
    local description="$3"

    print_step "$step_num" "$description"
    print_query "$query" "http://localhost:3000/prompt"

    echo -e "${GREEN}🚀 Sending request...${NC}"

    # Make the API call to FastAPI endpoint
    response=$(curl -X POST http://localhost:3000/prompt \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d "{\"text\": \"$query\"}" \
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
        echo -e "${RED}❌ Error: Failed to connect to the citymapper agent FastAPI${NC}"
        echo -e "${YELLOW}💡 Make sure the citymapper agent FastAPI is running on http://localhost:3000${NC}"
    fi

    echo ""
}

# Function to test health endpoint
test_health() {
    print_step "0" "Health Check"
    echo -e "${PURPLE}❓ Checking FastAPI agent health${NC}"
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
        echo -e "${YELLOW}💡 The citymapper agent FastAPI may not be running or accessible${NC}"
        return 1
    fi

    echo ""
}

# Main execution
main() {
    print_header "Citymapper Agent Workshop - FastAPI Testing"

    echo -e "${YELLOW}🎯 This script will test the Citymapper Agent FastAPI with various queries${NC}"
    echo -e "${YELLOW}📝 Perfect for workshop participants to see the FastAPI agent in action!${NC}"
    echo -e "${YELLOW}🚀 FastAPI provides automatic API documentation and validation${NC}"
    echo ""

    # Test health endpoint first
    test_health
    if [ $? -ne 0 ]; then
        echo -e "${RED}⚠️  Cannot proceed with tests - FastAPI agent is not responding${NC}"
        echo -e "${YELLOW}💡 Please ensure the citymapper agent FastAPI is running with: uvicorn app:app --host 0.0.0.0 --port 3000${NC}"
        exit 1
    fi

    # Test various travel planning queries
    test_citymapper_fastapi "Plan a 3-day trip to San Francisco focusing on food and nature" "1" "Travel Planning Query"

    test_citymapper_fastapi "What outdoor activities are available in San Francisco?" "2" "Activities Discovery"

    test_citymapper_fastapi "Generate an interactive travel plan for a weekend in San Francisco" "3" "Interactive Plan Generation"

    test_citymapper_fastapi "What are the best food experiences in San Francisco?" "4" "Food Recommendations"

    test_citymapper_fastapi "Create a nature-focused itinerary for Golden Gate Park" "5" "Nature Itinerary"

    test_citymapper_fastapi "Plan a day trip combining Golden Gate Bridge and local dining" "6" "Combined Experience Planning"

    # Final summary
    print_header "Workshop FastAPI Test Summary"
    echo -e "${GREEN}🎉 Citymapper Agent FastAPI testing completed!${NC}"
    echo -e "${CYAN}📊 Test Results:${NC}"
    echo -e "${YELLOW}   • Health Check: Passed ✅${NC}"
    echo -e "${YELLOW}   • Travel Planning: 6 queries tested 🗺️${NC}"
    echo -e "${YELLOW}   • API Endpoints: FastAPI (port 3000) 🚀${NC}"
    echo ""
    echo -e "${PURPLE}🔧 Additional Testing Options:${NC}"
    echo -e "${CYAN}   • MCP Protocol: Use test_e2e_mcp.py (port 8080)${NC}"
    echo -e "${CYAN}   • A2A Protocol: Use test_e2e_a2a.py (port 9000)${NC}"
    echo -e "${CYAN}   • FastAPI:      Use test_e2e_fastapi.py or test_e2e_fastapi_curl.sh (port 3000)${NC}"
    echo ""
    echo -e "${GREEN}🌐 FastAPI Features:${NC}"
    echo -e "${CYAN}   • Travel Planning API: Interactive itinerary generation${NC}"
    echo -e "${CYAN}   • Pydantic Validation: Automatic request/response validation${NC}"
    echo -e "${CYAN}   • Structured Endpoints: /health and /prompt${NC}"
    echo -e "${CYAN}   • Built-in Error Handling and Status Codes${NC}"
    echo ""
    echo -e "${GREEN}✨ Workshop participants can now interact with the FastAPI Citymapper Agent! ✨${NC}"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi