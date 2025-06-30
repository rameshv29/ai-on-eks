# citymapper_agent.py
import time
import uuid
from pydantic import BaseModel
from strands import Agent
from strands.tools.mcp import MCPClient
from starlette.requests import Request
from mcp.client.streamable_http import streamablehttp_client
import json
import asyncio
import os
import logging
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError
from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
session_table = dynamodb.Table(os.environ.get('SESSIONS_TABLE_NAME', 'CitymapperSessions'))

# Create FastAPI app for health check
app = FastAPI()

# Health check endpoint
@app.get("/health")
def health_check():
    return PlainTextResponse("OK", status_code=200)

@app.get("/tips")
def get_tips():
    return PlainTextResponse("\n📋 Try: 'Plan me a 3-day weekend trip to San Francisco focusing on food experiences and one day in nature.'",status_code=200)

@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    try:
        session_table.delete_item(
            Key={
                'session_id': session_id
            }
        )
        return {"message": "Session ended successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

def save_agent_state(agent, session_id):
    try:

        state = {
            "messages": agent.messages,
            "system_prompt": agent.system_prompt
        }

        # Save to DynamoDB with TTL (24 hours from now)
        ttl = int(time.time()) + 86400  # 24 hours from now

        session_table.put_item(
            Item={
                'session_id': session_id,
                'state': json.dumps(state),
                'last_updated': int(time.time()),
                'ttl': ttl
            }
        )
        logger.info(f"Saved agent state for session {session_id} to DynamoDB")
        return True
    except Exception as e:
        logger.error(f"Error saving agent state to DynamoDB: {e}")
        return False

def restore_agent_state(session_id):
    try:
        response = session_table.get_item(
            Key={
                'session_id': session_id
            }
        )

        if 'Item' not in response:
            logger.warning(f"No session found for ID {session_id}")
            return None

        state = json.loads(response['Item']['state'])

        # Update the last_updated timestamp
        session_table.update_item(
            Key={
                'session_id': session_id
            },
            UpdateExpression="set last_updated = :t, #ttl_attr = :ttl_val",  # Use expression attribute name for ttl
            ExpressionAttributeNames={
                '#ttl_attr': 'ttl'  # Define the expression attribute name
            },
            ExpressionAttributeValues={
                ':t': int(time.time()),
                ':ttl_val': int(time.time()) + 86400  # 24 hours from now
            }
        )

        agent = Agent(
            messages=state["messages"],
            system_prompt=state["system_prompt"]
        )
        logger.info(f"Restored agent state for session {session_id} from DynamoDB")
        return agent
    except Exception as e:
        logger.error(f"Error restoring agent state from DynamoDB: {e}")
        return None

def load_mcp_config(config_path: Optional[str] = None) -> Dict:
    """Load MCP server configurations from the config file"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_servers.json")
    
    servers = {}
    
    # Verify config file exists
    if os.path.exists(config_path):
        # Load config to get server URLs
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if "mcpServers" in config:
                for server_name, server_config in config["mcpServers"].items():
                    args = server_config.get("args", [])
                    if len(args) > 1:
                        server_url = args[1]
                        logger.info(f"Found server {server_name} with URL: {server_url}")
                        servers[server_name] = server_url
                    else:
                        logger.warning(f"Could not find URL for server {server_name} in MCP config")
            else:
                logger.warning("No MCP servers found in config")
        except Exception as e:
            logger.error(f"Error loading MCP config: {str(e)}")
    else:
        logger.warning(f"MCP config file not found at {config_path}")
    
    # Override with environment variables if available
    if "TRAVEL_SERVER" in os.environ:
        servers["travel"] = f"http://{os.environ['TRAVEL_SERVER']}:8001/mcp"
    if "WEATHER_SERVER" in os.environ:
        servers["weather"] = f"http://{os.environ['WEATHER_SERVER']}:8002/mcp"
    if "FOOD_SERVER" in os.environ:
        servers["food"] = f"http://{os.environ['FOOD_SERVER']}:8003/mcp"
    if "ACTIVITIES_SERVER" in os.environ:
        servers["activities"] = f"http://{os.environ['ACTIVITIES_SERVER']}:8004/mcp"
    if "MAPS_SERVER" in os.environ:
        servers["maps"] = f"http://{os.environ['MAPS_SERVER']}:8005/mcp"
    if "VISUALIZATION_SERVER" in os.environ:
        servers["visualization"] = f"http://{os.environ['VISUALIZATION_SERVER']}:8006/mcp"
    
    return servers

class AgentRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None

@app.post("/agent", response_model=AgentResponse)
async def query_agent(request: AgentRequest, req: Request, session_id: Optional[str] = Cookie(None)):
    req.scope["state"]["timeout"] = 300

    is_new_session = False
    if not session_id:
        session_id = str(uuid.uuid4())
        is_new_session = True


    # Connect to all MCP servers
    print("\nConnecting to MCP Servers...")
    
    # Load server configurations from the config file
    server_configs = load_mcp_config()
    
    # Create MCP clients for each server
    mcp_clients = {}
    for server_name, server_url in server_configs.items():
        mcp_clients[server_name] = MCPClient(lambda url=server_url: streamablehttp_client(url))
        print(f"Created client for {server_name} server at {server_url}")
    
    # Check if we have all required servers
    required_servers = ["travel", "weather", "food", "activities", "maps", "visualization"]
    missing_servers = [server for server in required_servers if server not in mcp_clients]
    
    if missing_servers:
        print(f"❌ Error: Missing required MCP servers: {', '.join(missing_servers)}")
        print("💡 Please check your mcp_servers.json configuration file.")
        return
    
    try:
        # Use context managers to ensure proper connection handling for the entire session
        with mcp_clients["travel"] as travel_server, \
             mcp_clients["weather"] as weather_server, \
             mcp_clients["food"] as food_server, \
             mcp_clients["activities"] as activities_server, \
             mcp_clients["maps"] as maps_server, \
             mcp_clients["visualization"] as visualization_server:

            citymapper = None
            if not is_new_session :
                citymapper = restore_agent_state(session_id)

            if not citymapper:
                print("here somehow")
                # Create the Citymapper agent with a system prompt
                citymapper = Agent(
                    system_prompt="""You are a sophisticated travel planning assistant that creates comprehensive travel itineraries.
                    
                    You have access to multiple specialized services through MCP tools:
                    1. Travel Information Server - For destination details and accommodations
                    2. Weather Information Server - For weather forecasts
                    3. Food Recommendation Server - For restaurant and food recommendations
                    4. Activities Recommendation Server - For activity suggestions based on interests
                    5. Maps and Routes Server - For location information and travel times
                    6. Visualization Server - For destination images and maps
                    
                    When a user asks for a travel plan:
                    1. Extract key information: destination, duration, and interests
                    2. Use the appropriate tools to gather information about the destination
                    3. Create a day-by-day itinerary with activities and meals
                    4. Include weather information and visualizations
                    5. Resolve scheduling conflicts between activities and meals
                    6. Present a comprehensive, well-organized travel plan
                    
                    Rules:
                    - You must use the tools provided by the MCP servers
                    - You must NOT make up information about destinations
                    - Tailor recommendations based on user interests
                    - Consider weather forecasts when planning outdoor activities
                    - Ensure reasonable travel times between locations
                    - Use the list_available_cities tool to check which cities are supported
                    - For each city, use the appropriate tools to get detailed information
                    
                    Format your response as a well-structured travel itinerary with:
                    - Destination overview
                    - Weather forecast
                    - Day-by-day plan with:
                      * Weather for the day
                      * Morning, afternoon, and evening activities
                      * Meal recommendations
                      * Travel times between locations
                    - Include image URLs for visualizations
                    """
                )
                print(f"Created new agent for session {session_id}")
            
            # List and add tools from each server to the agent
            print("Loading available tools from MCP servers...")
            
            # Travel server tools
            travel_tools = travel_server.list_tools_sync()
            print(f"Travel server tools: {[tool.tool_name for tool in travel_tools]}")
            citymapper.tool_registry.process_tools(travel_tools)
            
            # Weather server tools
            weather_tools = weather_server.list_tools_sync()
            print(f"Weather server tools: {[tool.tool_name for tool in weather_tools]}")
            citymapper.tool_registry.process_tools(weather_tools)
            
            # Food server tools
            food_tools = food_server.list_tools_sync()
            print(f"Food server tools: {[tool.tool_name for tool in food_tools]}")
            citymapper.tool_registry.process_tools(food_tools)
            
            # Activities server tools
            activities_tools = activities_server.list_tools_sync()
            print(f"Activities server tools: {[tool.tool_name for tool in activities_tools]}")
            citymapper.tool_registry.process_tools(activities_tools)
            
            # Maps server tools
            maps_tools = maps_server.list_tools_sync()
            print(f"Maps server tools: {[tool.tool_name for tool in maps_tools]}")
            citymapper.tool_registry.process_tools(maps_tools)
            
            # Visualization server tools
            visualization_tools = visualization_server.list_tools_sync()
            print(f"Visualization server tools: {[tool.tool_name for tool in visualization_tools]}")
            citymapper.tool_registry.process_tools(visualization_tools)
            
            # Start interactive travel planning session
            print("\n🌍 Citymapper Travel Planning Assistant")
            print("=" * 50)
            print("\n📋 Try: 'Plan me a 3-day weekend trip to San Francisco focusing on food experiences and one day in nature.'")

            result = citymapper(request.query)

            save_agent_state(citymapper, session_id)

            response = {"response": str(result), "success": True}
            response_obj = JSONResponse(content=response)
            if is_new_session:
                response_obj.set_cookie("session_id", session_id, httponly=True, max_age=3600)
            return response_obj
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return {"response": "", "success": False, "error": str(e)}

def main():
    """Main function to run the server"""
    import uvicorn

    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))

    # Start the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=120, timeout_graceful_shutdown=120)
    
if __name__ == "__main__":
    main()
