# food/server.py
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
    get_food_by_city,
    get_item,
    health_check,
    initialize_dynamodb
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the Food MCP server
mcp = FastMCP(
    name="Food Recommendation Server",
    host="0.0.0.0",
    port=8003
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
DATA_FILE = os.path.join(os.path.dirname(__file__), "food_data.json")

def load_food_data_from_json() -> Dict[str, Any]:
    """Load food data from the JSON file as fallback."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Food data file {DATA_FILE} not found.")
            return {"cities": {}}
    except Exception as e:
        logger.error(f"Error loading food data from JSON: {e}")
        return {"cities": {}}

def get_food_data(city_id: str) -> List[Dict[str, Any]]:
    """Get food data from DynamoDB or fallback to JSON"""
    try:
        # Try DynamoDB first
        if health_check():
            logger.info(f"Getting restaurants for {city_id} from DynamoDB")
            restaurants = get_food_by_city(city_id)
            if restaurants:
                return restaurants
            else:
                logger.info(f"No restaurants found in DynamoDB for {city_id}")
        
        # Fallback to JSON
        logger.info(f"Falling back to JSON data for {city_id}")
        json_data = load_food_data_from_json()
        city_data = json_data.get("cities", {}).get(city_id, {})
        return city_data.get("restaurants", [])
        
    except Exception as e:
        logger.error(f"Error getting food data: {e}")
        # Final fallback to JSON
        json_data = load_food_data_from_json()
        city_data = json_data.get("cities", {}).get(city_id, {})
        return city_data.get("restaurants", [])

@mcp.tool()
def get_restaurant_recommendations(city: str, cuisine: str = None, meal_time: str = None, price_range: str = None) -> Dict[str, Any]:
    """
    Get restaurant recommendations for a specific city.
    
    Parameters:
    - city: The city to get recommendations for
    - cuisine: Optional filter for cuisine type (e.g., Italian, Japanese)
    - meal_time: Optional filter for meal time (breakfast, lunch, dinner)
    - price_range: Optional filter for price range ($, $$, $$$, $$$$)
    """
    city = city.lower().replace(" ", "_")
    
    # Get restaurants from DynamoDB or JSON fallback
    restaurants = get_food_data(city)
    
    if not restaurants:
        return {"error": f"No restaurants found for {city}"}
    
    # Apply filters if provided
    if cuisine:
        cuisine = cuisine.lower()
        restaurants = [r for r in restaurants if cuisine in [c.lower() for c in r.get("categories", [])] or 
                      r.get("cuisine_type", "").lower() == cuisine]
    
    if meal_time:
        meal_time = meal_time.lower()
        restaurants = [r for r in restaurants if meal_time in [m.lower() for m in r.get("meal_times", [])]]
    
    if price_range:
        restaurants = [r for r in restaurants if r.get("price_range") == price_range]
    
    return {
        "city": city.replace("_", " ").title(),
        "restaurants": restaurants[:5],  # Limit to top 5
        "count": len(restaurants)
    }

@mcp.tool()
def get_local_cuisine_info(city: str) -> Dict[str, Any]:
    """Get information about local cuisine for a specific city."""
    city = city.lower().replace(" ", "_")
    
    # Get restaurants from DynamoDB or JSON fallback
    restaurants = get_food_data(city)
    
    if not restaurants:
        return {"error": f"No cuisine information found for {city}"}
    
    # Extract cuisine types from restaurants
    cuisines = set()
    for restaurant in restaurants:
        if restaurant.get("cuisine_type"):
            cuisines.add(restaurant["cuisine_type"])
        for category in restaurant.get("categories", []):
            cuisines.add(category.title())
    
    return {
        "city": city.replace("_", " ").title(),
        "available_cuisines": list(cuisines),
        "restaurant_count": len(restaurants),
        "sample_restaurants": [r["name"] for r in restaurants[:3]]
    }

@mcp.tool()
def list_available_cuisines(city: str) -> Dict[str, Any]:
    """List all available cuisines in a specific city."""
    city = city.lower().replace(" ", "_")
    
    if city not in food_data.get("cities", {}):
        return {"error": "City not found"}
    
    city_data = food_data["cities"][city]
    restaurants = city_data.get("restaurants", [])
    
    cuisines = list(set(r.get("cuisine") for r in restaurants if "cuisine" in r))
    
    return {
        "city": city_data.get("name", city),
        "cuisines": cuisines,
        "count": len(cuisines)
    }

@mcp.tool()
def get_food_markets(city: str) -> Dict[str, Any]:
    """Get information about food markets in a specific city."""
    city = city.lower().replace(" ", "_")
    
    if city not in food_data.get("cities", {}):
        return {"error": "City not found"}
    
    city_data = food_data["cities"][city]
    markets = city_data.get("food_markets", [])
    
    if not markets:
        return {"error": "Food market information not available for this city"}
    
    return {
        "city": city_data.get("name", city),
        "food_markets": markets,
        "count": len(markets)
    }

# Start the MCP server
if __name__ == "__main__":
    try:
        # Try to get data from JSON fallback to show city count
        fallback_data = load_food_data_from_json()
        city_count = len(fallback_data.get('cities', {}))
        logger.info(f"Starting Food Server with {city_count} cities available")
    except Exception as e:
        logger.warning(f"Could not load city count: {e}")
        logger.info("Starting Food Server")
    
    mcp.run(transport="streamable-http")
