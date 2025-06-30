# activities/server.py
from mcp.server import FastMCP
import json
import os
from typing import List, Dict, Any, Optional
import logging
from fastapi import Response
import sys

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.dynamodb_utils import (
    get_activities_by_city,
    get_item,
    health_check,
    initialize_dynamodb
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the Activities MCP server
mcp = FastMCP(
    name="Activities Recommendation Server",
    host="0.0.0.0",
    port=8004
)

# Add a health check route directly to the MCP server
@mcp.custom_route("/health", methods=["GET"])
async def health_check_endpoint(request):
    """
    Health check endpoint for ALB Target Group.
    Checks both service and DynamoDB health.
    """
    try:
        # Check DynamoDB connection
        if health_check():
            return Response(
                content="healthy - DynamoDB connected",
                status_code=200,
                media_type="text/plain"
            )
        else:
            return Response(
                content="unhealthy - DynamoDB not accessible",
                status_code=503,
                media_type="text/plain"
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            content=f"unhealthy - {str(e)}",
            status_code=503,
            media_type="text/plain"
        )

# Fallback to JSON data if DynamoDB is not available
DATA_FILE = os.path.join(os.path.dirname(__file__), "activities_data.json")

def load_activities_data_from_json() -> Dict[str, Any]:
    """Load activities data from the JSON file as fallback."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Activities data file {DATA_FILE} not found.")
            return {"cities": {}}
    except Exception as e:
        logger.error(f"Error loading activities data from JSON: {e}")
        return {"cities": {}}

def get_activities_data(city_id: str) -> List[Dict[str, Any]]:
    """Get activities data from DynamoDB or fallback to JSON"""
    try:
        # Try DynamoDB first
        if health_check():
            logger.info(f"Getting activities for {city_id} from DynamoDB")
            activities = get_activities_by_city(city_id)
            if activities:
                return activities
            else:
                logger.info(f"No activities found in DynamoDB for {city_id}")
        
        # Fallback to JSON
        logger.info(f"Falling back to JSON data for {city_id}")
        json_data = load_activities_data_from_json()
        city_data = json_data.get("cities", {}).get(city_id, {})
        return city_data.get("activities", [])
        
    except Exception as e:
        logger.error(f"Error getting activities data: {e}")
        # Final fallback to JSON
        json_data = load_activities_data_from_json()
        city_data = json_data.get("cities", {}).get(city_id, {})
        return city_data.get("activities", [])

@mcp.tool()
def get_activity_recommendations(city: str, category: str = None, duration: str = None, cost: str = None) -> Dict[str, Any]:
    """
    Get activity recommendations for a specific city.
    
    Parameters:
    - city: The city to get recommendations for
    - category: Optional filter for activity category (e.g., outdoor, museum, historical)
    - duration: Optional filter for activity duration (e.g., short, half-day, full-day)
    - cost: Optional filter for cost (e.g., free, low, medium, high)
    """
    try:
        city = city.lower().replace(" ", "_")
        logger.info(f"Getting activity recommendations for {city}")
        
        # Get activities from DynamoDB or JSON fallback
        activities = get_activities_data(city)
        
        if not activities:
            return {"error": "City not found or no activities available"}
        
        # Apply filters if provided
        if category:
            category = category.lower()
            activities = [a for a in activities if category in [c.lower() for c in a.get("categories", [])]]
        
        if duration:
            duration = duration.lower()
            activities = [a for a in activities if a.get("duration", "").lower() == duration]
        
        if cost:
            cost = cost.lower()
            activities = [a for a in activities if a.get("cost", "").lower() == cost]
        
        return {
            "city": city.replace("_", " ").title(),
            "activities": activities,
            "count": len(activities),
            "data_source": "DynamoDB" if health_check() else "JSON"
        }
        
    except Exception as e:
        logger.error(f"Error getting activity recommendations: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_activity_details(city: str, activity_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific activity in a city."""
    try:
        city = city.lower().replace(" ", "_")
        activity_id = activity_id.lower()
        logger.info(f"Getting details for activity {activity_id} in {city}")
        
        # Try DynamoDB first
        if health_check():
            activity = get_item(city, 'activities', activity_id)
            if activity:
                return {
                    "city": city.replace("_", " ").title(),
                    "activity": activity,
                    "data_source": "DynamoDB"
                }
        
        # Fallback to JSON search
        activities = get_activities_data(city)
        for activity in activities:
            if activity.get("id", "").lower() == activity_id:
                return {
                    "city": city.replace("_", " ").title(),
                    "activity": activity,
                    "data_source": "JSON"
                }
        
        return {"error": "Activity not found"}
        
    except Exception as e:
        logger.error(f"Error getting activity details: {e}")
        return {"error": str(e)}

@mcp.tool()
def list_activity_categories(city: str) -> Dict[str, Any]:
    """List all available activity categories in a specific city."""
    try:
        city = city.lower().replace(" ", "_")
        logger.info(f"Getting activity categories for {city}")
        
        activities = get_activities_data(city)
        
        if not activities:
            return {"error": "City not found or no activities available"}
        
        categories = set()
        for activity in activities:
            for category in activity.get("categories", []):
                categories.add(category.lower())
        
        return {
            "city": city.replace("_", " ").title(),
            "categories": list(categories),
            "count": len(categories),
            "data_source": "DynamoDB" if health_check() else "JSON"
        }
        
    except Exception as e:
        logger.error(f"Error getting activity categories: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_nature_activities(city: str) -> Dict[str, Any]:
    """Get nature-related activities in a specific city."""
    try:
        city = city.lower().replace(" ", "_")
        logger.info(f"Getting nature activities for {city}")
        
        activities = get_activities_data(city)
        
        if not activities:
            return {"error": "City not found or no activities available"}
        
        nature_activities = [
            a for a in activities 
            if any(c.lower() in ["nature", "outdoor", "park", "hiking", "garden"] 
                   for c in a.get("categories", []))
        ]
        
        return {
            "city": city.replace("_", " ").title(),
            "nature_activities": nature_activities,
            "count": len(nature_activities),
            "data_source": "DynamoDB" if health_check() else "JSON"
        }
        
    except Exception as e:
        logger.error(f"Error getting nature activities: {e}")
        return {"error": str(e)}

# Initialize DynamoDB on startup
try:
    logger.info("Initializing Activities Service...")
    if health_check():
        logger.info("✅ DynamoDB connection successful")
        initialize_dynamodb()
    else:
        logger.warning("⚠️ DynamoDB not available, will use JSON fallback")
except Exception as e:
    logger.error(f"Error during initialization: {e}")

# Start the MCP server
if __name__ == "__main__":
    logger.info("Starting Activities Recommendation Server on port 8004...")
    logger.info("Data source: DynamoDB (with JSON fallback)")
    mcp.run(transport="streamable-http")
